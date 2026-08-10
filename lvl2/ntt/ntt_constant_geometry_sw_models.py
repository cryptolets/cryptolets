from ntt_sw_utils import (
    _ntt_shape,
    bit_rev_shuffle,
    find_ntt_modulus,
    generate_twiddle_factors,
    normalize_intt,
    ntt_naive,
    reverse_bits,
)

# Constant-geometry NTT software models.

def _debug_constant_geometry_butterfly(
    read_buf, upper_read_idx, lower_read_idx,
    write_buf, upper_write_idx, lower_write_idx,
    twiddle_idx
):
    print(
        f"Coefficient pair read {read_buf}[{upper_read_idx}], {read_buf}[{lower_read_idx}]; "
        f"write {write_buf}[{upper_write_idx}], {write_buf}[{lower_write_idx}]; "
        f"twiddle index {twiddle_idx}"
    )

# Pease takes reversed inputs and outputs natural order
def ntt_dif_pease(in_arr, q, omegas, debug=False):
    n, num_stages = _ntt_shape(in_arr)
    ping = in_arr.copy()
    pong = [0] * n

    a_mask = (n >> 1) - 1
    b_mask = (n >> 1) - 1
    if debug:
        print("\nNTT Length:", n)
        print("Algorithm: Pease DIF")
    for stage in range(num_stages):
        if debug:
            print()
            print("Stage:", stage)

        for butterfly_idx in range(n // 2):
            if (stage % 2) == 0:
                read_buf = "ping"
                upper_read_idx = butterfly_idx << 1
                lower_read_idx = (butterfly_idx << 1) + 1
                upper = ping[upper_read_idx]
                lower = ping[lower_read_idx]
            else:
                read_buf = "pong"
                upper_read_idx = butterfly_idx << 1
                lower_read_idx = (butterfly_idx << 1) + 1
                upper = pong[upper_read_idx]
                lower = pong[lower_read_idx]

            if stage == num_stages - 1:
                twiddle_idx = 0
                omega = 1
            else:
                twiddle_idx = reverse_bits(butterfly_idx, num_stages - 1) & a_mask
                omega = omegas[twiddle_idx]

            lower_input = (upper - lower) % q
            upper_result = (upper + lower) % q
            lower_result = (omega * lower_input) % q

            if (stage % 2) == 0:
                write_buf = "pong"
                upper_write_idx = butterfly_idx
                lower_write_idx = butterfly_idx + (n >> 1)
                pong[upper_write_idx] = upper_result
                pong[lower_write_idx] = lower_result
            else:
                write_buf = "ping"
                upper_write_idx = butterfly_idx
                lower_write_idx = butterfly_idx + (n >> 1)
                ping[upper_write_idx] = upper_result
                ping[lower_write_idx] = lower_result

            if debug:
                _debug_constant_geometry_butterfly(
                    read_buf, upper_read_idx, lower_read_idx,
                    write_buf, upper_write_idx, lower_write_idx,
                    twiddle_idx
                )

        a_mask = (a_mask << 1) & b_mask
        
    return pong if (num_stages % 2) == 1 else ping


# Pease takes reversed inputs and outputs natural order
def ntt_dit_pease(in_arr, q, omegas, debug=False):
    n, num_stages = _ntt_shape(in_arr)
    ping = in_arr.copy()
    pong = [0] * n

    a_mask = 0
    b_mask = n >> 2
    if debug:
        print("\nNTT Length:", n)
        print("Algorithm: Pease DIT")
    for stage in range(num_stages):
        if debug:
            print()
            print("Stage:", stage)

        for butterfly_idx in range(n // 2):
            if (stage % 2) == 0:
                read_buf = "ping"
                upper_read_idx = butterfly_idx << 1
                lower_read_idx = (butterfly_idx << 1) + 1
                upper = ping[upper_read_idx]
                lower = ping[lower_read_idx]
            else:
                read_buf = "pong"
                upper_read_idx = butterfly_idx << 1
                lower_read_idx = (butterfly_idx << 1) + 1
                upper = pong[upper_read_idx]
                lower = pong[lower_read_idx]

            if stage == 0:
                twiddle_idx = 0
                omega = 1
            else:
                twiddle_idx = butterfly_idx & a_mask
                omega = omegas[twiddle_idx]

            lower_input = lower if stage == 0 else (lower * omega) % q
            upper_result = (upper + lower_input) % q
            lower_result = (upper - lower_input) % q

            if (stage % 2) == 0:
                write_buf = "pong"
                upper_write_idx = butterfly_idx
                lower_write_idx = butterfly_idx + (n >> 1)
                pong[upper_write_idx] = upper_result
                pong[lower_write_idx] = lower_result
            else:
                write_buf = "ping"
                upper_write_idx = butterfly_idx
                lower_write_idx = butterfly_idx + (n >> 1)
                ping[upper_write_idx] = upper_result
                ping[lower_write_idx] = lower_result

            if debug:
                _debug_constant_geometry_butterfly(
                    read_buf, upper_read_idx, lower_read_idx,
                    write_buf, upper_write_idx, lower_write_idx,
                    twiddle_idx
                )

        # need a_mask to right shift in a 1
        a_mask |= b_mask
        b_mask >>= 1

    return pong if (num_stages % 2) == 1 else ping

# Korn-Lambiotte takes natural order inputs and outputs reversed order
def ntt_dif_korn_lambiotte(in_arr, q, omegas, debug=False):
    n, num_stages = _ntt_shape(in_arr)
    ping = in_arr.copy()
    pong = [0] * n

    a_mask = (n >> 1) - 1
    b_mask = (n >> 1) - 1
    if debug:
        print("\nNTT Length:", n)
        print("Algorithm: Korn-Lambiotte DIF")
    for stage in range(num_stages):
        if debug:
            print()
            print("Stage:", stage)

        for butterfly_idx in range(n // 2):
            if (stage % 2) == 0:
                read_buf = "ping"
                upper_read_idx = butterfly_idx
                lower_read_idx = butterfly_idx + (n >> 1)
                upper = ping[upper_read_idx]
                lower = ping[lower_read_idx]
            else:
                read_buf = "pong"
                upper_read_idx = butterfly_idx
                lower_read_idx = butterfly_idx + (n >> 1)
                upper = pong[upper_read_idx]
                lower = pong[lower_read_idx]

            if stage == num_stages - 1:
                twiddle_idx = 0
                omega = 1
            else:
                twiddle_idx = butterfly_idx & a_mask
                omega = omegas[twiddle_idx]

            lower_input = (upper - lower) % q
            upper_result = (upper + lower) % q
            lower_result = (omega * lower_input) % q

            if (stage % 2) == 0:
                write_buf = "pong"
                upper_write_idx = butterfly_idx << 1
                lower_write_idx = (butterfly_idx << 1) + 1
                pong[upper_write_idx] = upper_result
                pong[lower_write_idx] = lower_result
            else:
                write_buf = "ping"
                upper_write_idx = butterfly_idx << 1
                lower_write_idx = (butterfly_idx << 1) + 1
                ping[upper_write_idx] = upper_result
                ping[lower_write_idx] = lower_result

            if debug:
                _debug_constant_geometry_butterfly(
                    read_buf, upper_read_idx, lower_read_idx,
                    write_buf, upper_write_idx, lower_write_idx,
                    twiddle_idx
                )

        a_mask = (a_mask << 1) & b_mask

    return pong if (num_stages % 2) == 1 else ping

# Korn-Lambiotte takes natural order inputs and outputs reversed order
def ntt_dit_korn_lambiotte(in_arr, q, omegas, debug=False):
    n, num_stages = _ntt_shape(in_arr)
    ping = in_arr.copy()
    pong = [0] * n

    a_mask = 0
    b_mask = n >> 2
    if debug:
        print("\nNTT Length:", n)
        print("Algorithm: Korn-Lambiotte DIT")
    for stage in range(num_stages):
        if debug:
            print()
            print("Stage:", stage)

        for butterfly_idx in range(n // 2):
            if (stage % 2) == 0:
                read_buf = "ping"
                upper_read_idx = butterfly_idx
                lower_read_idx = butterfly_idx + (n >> 1)
                upper = ping[upper_read_idx]
                lower = ping[lower_read_idx]
            else:
                read_buf = "pong"
                upper_read_idx = butterfly_idx
                lower_read_idx = butterfly_idx + (n >> 1)
                upper = pong[upper_read_idx]
                lower = pong[lower_read_idx]

            if stage == 0:
                twiddle_idx = 0
                omega = 1
            else:
                twiddle_idx = reverse_bits(butterfly_idx, num_stages - 1) & a_mask
                omega = omegas[twiddle_idx]

            lower_input = lower if stage == 0 else (lower * omega) % q
            upper_result = (upper + lower_input) % q
            lower_result = (upper - lower_input) % q

            if (stage % 2) == 0:
                write_buf = "pong"
                upper_write_idx = butterfly_idx << 1
                lower_write_idx = (butterfly_idx << 1) + 1
                pong[upper_write_idx] = upper_result
                pong[lower_write_idx] = lower_result
            else:
                write_buf = "ping"
                upper_write_idx = butterfly_idx << 1
                lower_write_idx = (butterfly_idx << 1) + 1
                ping[upper_write_idx] = upper_result
                ping[lower_write_idx] = lower_result

            if debug:
                _debug_constant_geometry_butterfly(
                    read_buf, upper_read_idx, lower_read_idx,
                    write_buf, upper_write_idx, lower_write_idx,
                    twiddle_idx
                )

        a_mask |= b_mask
        b_mask >>= 1

    return pong if (num_stages % 2) == 1 else ping


if __name__ == "__main__":
    
    debug = True
    ntt_len = 32
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

    dit_pease_result = ntt_dit_pease(in_bit_reversed, q, omegas, debug=debug)
    dif_pease_result = ntt_dif_pease(in_bit_reversed, q, omegas, debug=debug)

    dit_korn_lambiotte_result_reversed = ntt_dit_korn_lambiotte(in_arr, q, omegas, debug=debug)
    dit_korn_lambiotte_result = bit_rev_shuffle(dit_korn_lambiotte_result_reversed)

    dif_korn_lambiotte_result_reversed = ntt_dif_korn_lambiotte(in_arr, q, omegas, debug=debug)
    dif_korn_lambiotte_result = bit_rev_shuffle(dif_korn_lambiotte_result_reversed)

    print("Input:", in_arr)
    print("Modulus:", q)
    print("NTT type:", ntt_type)
    print("NTT Twiddle factors:", omegas)
    print("INTT Twiddle factors:", inverse_omegas)

    naive_intt_scaled = ntt_naive(in_arr, q, inverse_omegas)
    naive_intt_result = normalize_intt(naive_intt_scaled, q)

    dit_pease_intt_result = normalize_intt(ntt_dit_pease(in_bit_reversed, q, inverse_omegas, debug=debug), q)
    dif_pease_intt_result = normalize_intt(ntt_dif_pease(in_bit_reversed, q, inverse_omegas, debug=debug), q)

    dit_korn_lambiotte_intt_result_reversed = ntt_dit_korn_lambiotte(in_arr, q, inverse_omegas, debug=debug)
    dit_korn_lambiotte_intt_result = normalize_intt(bit_rev_shuffle(dit_korn_lambiotte_intt_result_reversed), q)

    dif_korn_lambiotte_intt_result_reversed = ntt_dif_korn_lambiotte(in_arr, q, inverse_omegas, debug=debug)
    dif_korn_lambiotte_intt_result = normalize_intt(bit_rev_shuffle(dif_korn_lambiotte_intt_result_reversed), q)
    
    print()
    if naive_ntt_result == dit_pease_result == dit_korn_lambiotte_result == dif_pease_result == dif_korn_lambiotte_result:
        print("NTT Result:", naive_ntt_result)
        print()
        print("All NTT implementations produce the same result.")
    else:
        print("NTT (naive) :", naive_ntt_result)
        print("NTT (Pease DIT):", dit_pease_result)
        print("NTT (Korn-Lambiotte DIT):", dit_korn_lambiotte_result)
        print("NTT (Pease DIF):", dif_pease_result)
        print("NTT (Korn-Lambiotte DIF):", dif_korn_lambiotte_result)
        print()
        print("Discrepancy found between NTT implementations!")

    print()
    if naive_intt_result == dit_pease_intt_result == dit_korn_lambiotte_intt_result == dif_pease_intt_result == dif_korn_lambiotte_intt_result:
        print("INTT Result:", naive_intt_result)
        print()
        print("All INTT implementations produce the same result.")
    else:
        print("INTT (naive) :", naive_intt_result)
        print("INTT (Pease DIT):", dit_pease_intt_result)
        print("INTT (Korn-Lambiotte DIT):", dit_korn_lambiotte_intt_result)
        print("INTT (Pease DIF):", dif_pease_intt_result)
        print("INTT (Korn-Lambiotte DIF):", dif_korn_lambiotte_intt_result)
        print()
        print("Discrepancy found between INTT implementations!")
