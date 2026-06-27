from ntt_sw_utils import (
    _ntt_shape,
    bit_rev_shuffle,
    find_ntt_modulus,
    generate_twiddle_factors,
    normalize_intt,
    ntt_naive,
    reverse_bits,
)

# in place NTT that supports
# DIT with natural order input --> bit reversed output
# DIT with bit reversed input --> natural order output
# DIF with natural order input --> bit reversed output
# DIF with bit reversed input --> natural order output

def _debug_standard_butterfly(upper_idx, lower_idx, twiddle_idx):
    print(
        f"Coefficient pair read ({upper_idx}, {lower_idx}); "
        f"write ({upper_idx}, {lower_idx}); twiddle index {twiddle_idx}"
    )

def ntt_dif_nr(in_arr, q, omegas, debug=False):
    n, num_stages = _ntt_shape(in_arr)
    buf = in_arr.copy()

    m = n
    if debug:
        print("\nNTT Length:", n)
        print("Algorithm: DIF-NR")
    for stage in range(num_stages):
        if debug:
            print()
            print("Stage:", stage)
        m >>= 1
        step = m << 1
        for block_start in range(0, n, step):
            twiddle_idx = 0
            for offset in range(m):
                upper_idx = block_start + offset
                lower_idx = upper_idx + m
                upper = buf[upper_idx]
                lower = buf[lower_idx]
                
                buf[upper_idx] = (upper + lower) % q
                buf[lower_idx] = ((upper - lower) * omegas[twiddle_idx]) % q

                if debug:
                    _debug_standard_butterfly(upper_idx, lower_idx, twiddle_idx)

            # if debug:
            #     print(f"step: {step}")
            # twiddle_idx += n // step
                twiddle_idx += (n >> (num_stages - stage))

    return buf

def ntt_dif_rn(in_arr, q, omegas, debug=False):
    n, num_stages = _ntt_shape(in_arr)
    buf = in_arr.copy()

    m = 1
    if debug:
        print("\nNTT Length:", n)
        print("Algorithm: DIF-RN")
    for stage in range(num_stages):
        if debug:
            print()
            print("Stage:", stage)
        step = m << 1
        for block_start in range(0, n, step):
            # twiddle_idx = m * reverse_bits(block_start // step, num_stages - stage - 1)
            twiddle_idx = m * reverse_bits(block_start >> (stage + 1), num_stages - stage - 1)
            for offset in range(m):
                upper_idx = block_start + offset
                lower_idx = upper_idx + m
                upper = buf[upper_idx]
                lower = buf[lower_idx]
                
                buf[upper_idx] = (upper + lower) % q
                buf[lower_idx] = ((upper - lower) * omegas[twiddle_idx]) % q

                if debug:
                    _debug_standard_butterfly(upper_idx, lower_idx, twiddle_idx)

        m <<= 1

    return buf

def ntt_dit_nr(in_arr, q, omegas, debug=False):
    n, num_stages = _ntt_shape(in_arr)
    buf = in_arr.copy()

    m = n
    if debug:
        print("\nNTT Length:", n)
        print("Algorithm: DIT-NR")
    for stage in range(num_stages):
        if debug:
            print()
            print("Stage:", stage)
        m >>= 1
        step = m << 1
        for block_start in range(0, n, step):
            # twiddle_idx = m * reverse_bits(block_start // step, stage)
            twiddle_idx = m * reverse_bits(block_start >> (num_stages - stage), stage)
            for offset in range(m):
                upper_idx = block_start + offset
                lower_idx = upper_idx + m
                upper = buf[upper_idx]
                lower = buf[lower_idx]
                
                lower_scaled = (lower * omegas[twiddle_idx]) % q

                buf[upper_idx] = (upper + lower_scaled) % q
                buf[lower_idx] = (upper - lower_scaled) % q

                if debug:
                    _debug_standard_butterfly(upper_idx, lower_idx, twiddle_idx)

    return buf

def ntt_dit_rn(in_arr, q, omegas, debug=False):
    n, num_stages = _ntt_shape(in_arr)
    buf = in_arr.copy()

    m = 1
    if debug:
        print("\nNTT Length:", n)
        print("Algorithm: DIT-RN")
    for stage in range(num_stages):
        if debug:
            print()
            print("Stage:", stage)
        step = m << 1

        for block_start in range(0, n, step):
            twiddle_idx = 0
            for offset in range(m):
                upper_idx = block_start + offset
                lower_idx = upper_idx + m
                upper = buf[upper_idx]
                lower_scaled = buf[lower_idx] * omegas[twiddle_idx]
                
                buf[upper_idx] = (upper + lower_scaled) % q
                buf[lower_idx] = (upper - lower_scaled) % q

                if debug:
                    _debug_standard_butterfly(upper_idx, lower_idx, twiddle_idx)

                # twiddle_idx += n // step
                twiddle_idx += (n >> (stage + 1))
        m <<= 1

    return buf


if __name__ == "__main__":
    
    debug = False
    ntt_len = 8
    in_arr = [x for x in range(ntt_len)]
    n = len(in_arr)
    bitwidth = 16
    ntt_type = "posicyclic"
    ntt_type = "negacyclic"

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
    in_bit_reversed = bit_rev_shuffle(in_arr)
    
    naive_ntt_result = ntt_naive(in_arr, q, omegas)
    
    dif_nr_result_bit_reversed = ntt_dif_nr(in_arr, q, omegas, debug=not debug)
    dif_nr_result = bit_rev_shuffle(dif_nr_result_bit_reversed)

    dit_nr_result_bit_reversed = ntt_dit_nr(in_arr, q, omegas, debug=debug)
    dit_nr_result = bit_rev_shuffle(dit_nr_result_bit_reversed)

    dif_rn_result = ntt_dif_rn(in_bit_reversed, q, omegas, debug=debug)
    dit_rn_result = ntt_dit_rn(in_bit_reversed, q, omegas, debug=debug)

    print("Input:", in_arr)
    print("Modulus:", q)
    print("NTT type:", ntt_type)
    print("NTT Twiddle factors:", omegas)
    print("INTT Twiddle factors:", inverse_omegas)

    naive_intt_scaled = ntt_naive(in_arr, q, inverse_omegas)
    naive_intt_result = normalize_intt(naive_intt_scaled, q)

    dif_nr_intt_result_bit_reversed = ntt_dif_nr(in_arr, q, inverse_omegas, debug=debug)
    dif_nr_intt_result = normalize_intt(bit_rev_shuffle(dif_nr_intt_result_bit_reversed), q)

    dit_nr_intt_result_bit_reversed = ntt_dit_nr(in_arr, q, inverse_omegas, debug=debug)
    dit_nr_intt_result = normalize_intt(bit_rev_shuffle(dit_nr_intt_result_bit_reversed), q)

    dif_rn_intt_result = normalize_intt(ntt_dif_rn(in_bit_reversed, q, inverse_omegas, debug=debug), q)
    dit_rn_intt_result = normalize_intt(ntt_dit_rn(in_bit_reversed, q, inverse_omegas, debug=debug), q)

    
    print()
    if naive_ntt_result == dif_nr_result == dit_nr_result == dif_rn_result == dit_rn_result:
        print("NTT Result:", naive_ntt_result)
        print()
        print("All NTT implementations produce the same result.")
    else:
        print("NTT (naive) :", naive_ntt_result)
        print("NTT (DIF-NR):", dif_nr_result)
        print("NTT (DIT-NR):", dit_nr_result)
        print("NTT (DIF-RN):", dif_rn_result)
        print("NTT (DIT-RN):", dit_rn_result)
        print()
        print("Discrepancy found between NTT implementations!")

    print()
    if naive_intt_result == dif_nr_intt_result == dit_nr_intt_result == dif_rn_intt_result == dit_rn_intt_result:
        print("INTT Result:", naive_intt_result)
        print()
        print("All INTT implementations produce the same result.")
    else:
        print("INTT (naive) :", naive_intt_result)
        print("INTT (DIF-NR):", dif_nr_intt_result)
        print("INTT (DIT-NR):", dit_nr_intt_result)
        print("INTT (DIF-RN):", dif_rn_intt_result)
        print("INTT (DIT-RN):", dit_rn_intt_result)
        print()
        print("Discrepancy found between INTT implementations!")
