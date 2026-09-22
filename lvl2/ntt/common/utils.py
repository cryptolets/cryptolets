import math
from sympy.ntheory.primetest import isprime
from sympy.ntheory import primitive_root


def get_root_order(n, ntt_type):
    if ntt_type == "posicyclic":
        return n
    if ntt_type == "negacyclic":
        return 2 * n
    raise ValueError(f"Unsupported NTT type: {ntt_type}")

def check_ntt_modulus(n, q, ntt_type="posicyclic"):
    assert (n & (n - 1)) == 0, "NTT length must be a power of two"
    root_order = get_root_order(n, ntt_type)

    if q <= 2 or not isprime(q):
        raise ValueError("q must be a prime greater than 2")
    if (q - 1) % root_order != 0:
        raise ValueError(f"{ntt_type} NTT length {n} needs {root_order} to divide q - 1")
    return root_order

def find_ntt_modulus(n, bitwidth, ntt_type="posicyclic", seed=42):
    root_order = get_root_order(n, ntt_type)
    max_value = (1 << bitwidth) - 1
    min_value = 1 << (bitwidth - 1)
    max_m = (max_value - 1) // root_order
    min_m = (min_value - 1 + root_order - 1) // root_order
    if max_m < min_m:
        raise ValueError(f"No {bitwidth}-bit modulus can satisfy q = m*{root_order} + 1")

    # Search only valid NTT moduli q = m*root_order + 1, starting near 2^bitwidth.
    # For 256-bit q this is much faster than walking all primes and filtering q mod root_order.
    for m in range(max_m, min_m - 1, -1):
        q = m * root_order + 1
        if isprime(q):
            return q

    raise ValueError(f"Could not find {bitwidth}-bit prime q = m*{root_order} + 1")

def get_root_of_unity(root_order, q):
    assert (root_order & (root_order - 1)) == 0, "root order must be a power of two"

    b = (q - 1) // root_order
    generator = primitive_root(q)
    omega = pow(generator, b, q)

    assert pow(omega, root_order, q) == 1
    assert pow(omega, root_order // 2, q) != 1

    value = omega
    min_root = omega
    omega_squared = (omega * omega) % q
    while True:
        value = (value * omega_squared) % q
        if value < min_root:
            min_root = value
        if value == omega:
            break

    return min_root

def generate_twiddle_factors(
    n, q, precompute=False, x=0, b=0, omega=0, seed=42,
    ntt_type="posicyclic"
):
    # Produces `n` powers of the root required by the NTT type.
    # posicyclic: primitive n-th root, for x^n - 1.
    # negacyclic: primitive 2n-th root, for x^n + 1.
    root_order = check_ntt_modulus(n, q, ntt_type)

    if not precompute:
        omega = get_root_of_unity(root_order, q)
        if ntt_type == "negacyclic":
            omega = (omega * omega) % q
    else:
        if omega == 0 and x != 0 and b != 0:
            omega = pow(x, b, q)

    assert pow(omega, n, q) == 1
    assert pow(omega, n // 2, q) != 1

    omegas = [1]
    for i in range(n - 1):
        omegas.append((omegas[i] * omega) % q)

    # inverse omegas are w^0 and then the remaining reversed
    # inverse_omegas = [pow(w, q - 2, q) for w in omegas]
    inverse_omegas = [1] + [omegas[-i] for i in range(1, n)]

    return omegas, inverse_omegas

def normalize_intt(out, q):
    n = len(out)
    n_inv = pow(n, q - 2, q)
    return [(x * n_inv) % q for x in out]

def reverse_bits(number, bit_length):
    reversed = 0
    for i in range(0, bit_length):
        if (number >> i) & 1:
            reversed |= 1 << (bit_length - 1 - i)
    return reversed

def bit_rev_shuffle(input):
    out = input.copy()
    ntt_len = len(input)
    for i in range(ntt_len):
        rev_i = reverse_bits(i, ntt_len.bit_length() - 1)
        if rev_i > i:
            out[i] = input[rev_i]
            out[rev_i] = input[i]
    return out

def _ntt_shape(a):
    n = len(a)
    log2n = math.log2(n)
    assert log2n.is_integer()
    return n, int(log2n)

def ntt_naive(a, q, omegas, debug=False):
    n, _ = _ntt_shape(a)
    out = [0] * n

    if debug:
        print("\nNTT Length:", n)
        print("Algorithm: naive")

    for out_idx in range(n):
        if debug:
            print()
            print("Output index:", out_idx)
        for in_idx in range(n):
            twiddle_idx = (out_idx * in_idx) % n
            out[out_idx] = (out[out_idx] + a[in_idx] * omegas[twiddle_idx]) % q

            if debug:
                print(f"Twiddle index {twiddle_idx}")
    return out

if __name__ == "__main__":

    in_arr = [x for x in range(16)]
    n = len(in_arr)
    bitwidth = None
    ntt_type = "posicyclic"
    # ntt_type = "negacyclic"

    if bitwidth is None:
        for bitwidth in range(8, 256):
            try:
                q = find_ntt_modulus(n, bitwidth, ntt_type)
                print(f"Found modulus q={q} for bitwidth={bitwidth}")
                break
            except ValueError as e:
                print(f"Bitwidth {bitwidth}: {e}")
    else:
        q = find_ntt_modulus(n, bitwidth, ntt_type)

    omegas, inverse_omegas = generate_twiddle_factors(n, q, ntt_type=ntt_type)

    print(omegas)
    print(inverse_omegas)
