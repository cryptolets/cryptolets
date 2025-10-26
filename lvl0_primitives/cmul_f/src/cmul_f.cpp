#include "cmul_f.h"

// For experimenting in isolation
wide_t cmul_f(const wide_t a) {
    return (a * Q_PRIME).slc<BITWIDTH>(0);
};

// -- For heigher level use --
// For modmul constant multiplications
wide_t cmul_q_prime(const wide_t x) {
    return (x * Q_PRIME).slc<BITWIDTH>(0);
};

wide_2x_t cmul_q(const wide_t x) {
    return x * Q;
}

wide_t cmul_mu(const wide_2x_t x) {
    // When specific curves MU ends up being BITWIDTH+1, so doing (2xBITWIDTH) x (2xBITWIDTH)
    // takes a lot of compile time, so we can reduce the MU bitwidth at compile time
    // to reduce compile runtime
    return ((ac_int<4*BITWIDTH, false>)(x * (MU.slc<MU_BIT_LEN>(0)))).slc<BITWIDTH>(2 * BITWIDTH);
}

// For field constant multiplications in montgomery domain
wide_2x_t cmul_field_a_mont(const wide_2x_t x) {
    return x * FIELD_A_MONT;
}

wide_2x_t cmul_field_d_mont(const wide_2x_t x) {
    return x * FIELD_D_MONT;
}

wide_2x_t cmul_field_k_mont(const wide_2x_t x) {
    return x * FIELD_K_MONT;
}

// For field constant multiplications in normal domain (for barrett)
wide_2x_t cmul_field_a(const wide_2x_t x) {
    return x * FIELD_A_INT;
}

wide_2x_t cmul_field_d(const wide_2x_t x) {
    return x * FIELD_D_INT;
}

wide_2x_t cmul_field_k(const wide_2x_t x) {
    return x * FIELD_K_INT;
}