from ntt_sw_utils import (
    _ntt_shape,
    bit_rev_shuffle,
    find_ntt_modulus,
    generate_twiddle_factors,
    normalize_intt,
    ntt_naive,
)
from ntt_constant_geometry_sw_models import _debug_constant_geometry_butterfly

def ntt_stockham_dif(in_arr, q, omegas, debug=False):
    n, num_stages = _ntt_shape(in_arr)

    ping = in_arr.copy()
    pong = [0] * n

    if debug:
        print("\nNTT Length:", n)
        print("Algorithm: Stockham DIF")

    for stage in range(num_stages):
        # Number of butterfly groups processed so far.
        groups = 1 << stage

        # Butterflies within each group.
        half = n // (2 * groups)

        if debug:
            print(f"\nStage: {stage}")

        for group in range(groups):
            for j in range(half):
                # Inputs are separated by `half`.
                upper_read_idx = j + 2 * half * group
                lower_read_idx = upper_read_idx + half

                upper = ping[upper_read_idx]
                lower = ping[lower_read_idx]

                # Twiddle exponent for this DIF stage.
                twiddle_idx = j * groups
                omega = omegas[twiddle_idx]

                upper_result = (upper + lower) % q
                lower_result = ((upper - lower) * omega) % q

                # Outputs are compacted into adjacent regions.
                upper_write_idx = j + half * group
                lower_write_idx = j + half * (group + groups)

                pong[upper_write_idx] = upper_result
                pong[lower_write_idx] = lower_result

                if debug:
                    _debug_constant_geometry_butterfly(
                        "ping",
                        upper_read_idx,
                        lower_read_idx,
                        "pong",
                        upper_write_idx,
                        lower_write_idx,
                        twiddle_idx,
                    )

        ping, pong = pong, ping

    return ping

def ntt_stockham_dit(in_arr, q, omegas, debug=False):
    n, log_n = _ntt_shape(in_arr)
    ping = in_arr.copy()
    pong = [0] * n

    if debug:
        print("\nNTT Length:", n)
        print("Algorithm: Stockham DIT")

    for stage in range(log_n):
        groups = 1 << stage
        stride = n >> (stage + 1)

        if debug:
            print()
            print("Stage:", stage)

        for group in range(groups):
            twiddle_idx = group * stride
            omega = omegas[twiddle_idx]

            for lane in range(stride):
                # Reads from two halves of the current group.
                upper_read_idx = lane + (group << (log_n - stage))
                lower_read_idx = upper_read_idx + stride

                upper = ping[upper_read_idx]
                lower = ping[lower_read_idx]

                # DIT butterfly.
                lower_twiddled = (lower * omega) % q
                upper_result = (upper + lower_twiddled) % q
                lower_result = (upper - lower_twiddled) % q

                # Write consecutive logical streams into separate halves.
                upper_write_idx = lane + group * stride
                lower_write_idx = upper_write_idx + (n >> 1)

                pong[upper_write_idx] = upper_result
                pong[lower_write_idx] = lower_result

                if debug:
                    _debug_constant_geometry_butterfly(
                        "ping",
                        upper_read_idx,
                        lower_read_idx,
                        "pong",
                        upper_write_idx,
                        lower_write_idx,
                        twiddle_idx,
                    )

        ping, pong = pong, ping

    return ping

def ntt_stockham_dif_merged(in_arr, q, omegas, debug=False):
    n, log_n = _ntt_shape(in_arr)
    ping = in_arr.copy()
    pong = [0] * n

    if debug:
        print("\nNTT Length:", n)
        print("Algorithm: Stockham DIF")

    for stage in range(log_n):
        stride = n >> (stage + 1)
        lane_shift = log_n - 1 - stage
        groups = 1 << stage

        if debug:
            print()
            print("Stage:", stage)

        # butterfly_idx = group * stride + lane
        for butterfly_idx in range(n >> 1):
            group = butterfly_idx >> lane_shift
            lane = butterfly_idx & (stride - 1)

            # Read corresponding entries from the two halves of this group.
            upper_read_idx = lane + (group << (log_n - stage))
            lower_read_idx = upper_read_idx + stride

            upper = ping[upper_read_idx]
            lower = ping[lower_read_idx]

            # DIF: twiddle the difference output.
            # Unlike Stockham DIT, the twiddle varies with lane, not group.
            twiddle_idx = lane * groups
            omega = omegas[twiddle_idx]

            upper_result = (upper + lower) % q
            lower_result = ((upper - lower) * omega) % q

            # butterfly_idx == lane + group * stride
            upper_write_idx = butterfly_idx
            lower_write_idx = butterfly_idx + (n >> 1)

            pong[upper_write_idx] = upper_result
            pong[lower_write_idx] = lower_result

            if debug:
                _debug_constant_geometry_butterfly(
                    "ping",
                    upper_read_idx,
                    lower_read_idx,
                    "pong",
                    upper_write_idx,
                    lower_write_idx,
                    twiddle_idx,
                )

        ping, pong = pong, ping

    return ping

def ntt_stockham_dit_merged(in_arr, q, omegas, debug=False):
    n, log_n = _ntt_shape(in_arr)
    ping = in_arr.copy()
    pong = [0] * n

    if debug:
        print("\nNTT Length:", n)
        print("Algorithm: Stockham DIT")

    for stage in range(log_n):
        stride = n >> (stage + 1)
        lane_shift = log_n - 1 - stage

        if debug:
            print()
            print("Stage:", stage)

        # butterfly = group * stride + lane
        for butterfly_idx in range(n >> 1):
            group = butterfly_idx >> lane_shift
            lane = butterfly_idx & (stride - 1)

            # Reads from the two halves of group `group`.
            upper_read_idx = lane + (group << (log_n - stage))
            lower_read_idx = upper_read_idx + stride

            upper = ping[upper_read_idx]
            lower = ping[lower_read_idx]

            # One twiddle per group.
            twiddle_idx = group * stride
            omega = omegas[twiddle_idx]

            # DIT butterfly.
            lower_twiddled = (lower * omega) % q
            upper_result = (upper + lower_twiddled) % q
            lower_result = (upper - lower_twiddled) % q

            # Equivalent to lane + group * stride == butterfly_idx.
            upper_write_idx = butterfly_idx
            lower_write_idx = butterfly_idx + (n >> 1)

            pong[upper_write_idx] = upper_result
            pong[lower_write_idx] = lower_result

            if debug:
                _debug_constant_geometry_butterfly(
                    "ping",
                    upper_read_idx,
                    lower_read_idx,
                    "pong",
                    upper_write_idx,
                    lower_write_idx,
                    twiddle_idx,
                )

        ping, pong = pong, ping

    return ping

if __name__ == "__main__":
    
    debug = False
    ntt_len = 32
    in_arr = [x for x in range(ntt_len)]
    n = len(in_arr)
    bitwidth = 64
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
    in_bit_reversed = bit_rev_shuffle(in_arr)

    naive_ntt_result = ntt_naive(in_arr, q, omegas)
    
    stockham_result_dif = ntt_stockham_dif_merged(in_arr, q, omegas, debug=debug)
    stockham_result_dit = ntt_stockham_dit_merged(in_arr, q, omegas, debug=debug)


    print("Input:", in_arr)
    print("Modulus:", q)
    print("NTT type:", ntt_type)
    print("NTT Twiddle factors:", omegas)
    print("INTT Twiddle factors:", inverse_omegas)

    naive_intt_scaled = ntt_naive(in_arr, q, inverse_omegas)
    naive_intt_result = normalize_intt(naive_intt_scaled, q)

    stockham_intt_result_dif = normalize_intt(
    ntt_stockham_dif_merged(in_arr, q, inverse_omegas, debug=debug),
    q,
    )
    stockham_intt_result_dit = normalize_intt(
    ntt_stockham_dit_merged(in_arr, q, inverse_omegas, debug=debug),
    q,
    )

    print()
    if naive_ntt_result == stockham_result_dif and naive_ntt_result == stockham_result_dit:
        print("NTT Result:", naive_ntt_result)
        print()
        print("All NTT implementations produce the same result.")
    else:
        print("NTT (naive) :", naive_ntt_result)
        print("NTT (Stockham):", stockham_result)
        print()
        print("Discrepancy found between NTT implementations!")

    print()
    if naive_intt_result == stockham_intt_result_dif and naive_intt_result == stockham_intt_result_dit:
        print("INTT Result:", naive_intt_result)
        print()
        print("All INTT implementations produce the same result.")
    else:
        print("INTT (naive) :", naive_intt_result)
        print("INTT (Stockham):", stockham_intt_result)
        print()
        print("Discrepancy found between INTT implementations!")
