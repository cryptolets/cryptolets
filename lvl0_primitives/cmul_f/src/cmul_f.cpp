#include "cmul_f.h"

// For experimenting in isolation
wide_t cmul_f(const wide_t a) {
    // return cmul_f_gen<BITWIDTH, Q_PRIME_NAF_LEN>(a, Q_PRIME, Q_PRIME_NAF);
    // return cmul_f_gen<2*BITWIDTH, MU_NAF_LEN>(a, MU, MU_NAF).slc<BITWIDTH>(2*BITWIDTH);
    return cmul_f_gen<BITWIDTH, Q_PRIME_NAF_LEN>(a, Q_PRIME, Q_PRIME_NAF).slc<BITWIDTH>(0);
};

// -- For higher level use --
// For modmul constant multiplications
wide_t cmul_q_prime(const wide_t x) {
    return cmul_f_gen<BITWIDTH, Q_PRIME_NAF_LEN>(x, Q_PRIME, Q_PRIME_NAF).slc<BITWIDTH>(0);
};

wide_2x_t cmul_q(const wide_t x) {
    return cmul_f_gen<BITWIDTH, Q_NAF_LEN>(x, Q, Q_NAF);
}

wide_t cmul_mu(const wide_2x_t x) {
    return cmul_f_gen<2*BITWIDTH, MU_NAF_LEN>(x, MU, MU_NAF).slc<BITWIDTH>(2*BITWIDTH);
}

// For field constant multiplications in montgomery domain
wide_2x_t cmul_field_a_mont(const wide_t x) {
    return cmul_f_gen<BITWIDTH, FIELD_A_MONT_NAF_LEN>(x, FIELD_A_MONT, FIELD_A_MONT_NAF);
}

wide_2x_t cmul_field_d_mont(const wide_t x) {
    return cmul_f_gen<BITWIDTH, FIELD_D_MONT_NAF_LEN>(x, FIELD_D_MONT, FIELD_D_MONT_NAF);
}

wide_2x_t cmul_field_k_mont(const wide_t x) {
    return cmul_f_gen<BITWIDTH, FIELD_K_MONT_NAF_LEN>(x, FIELD_K_MONT, FIELD_K_MONT_NAF);
}

// For field constant multiplications in normal domain (for barrett)
wide_2x_t cmul_field_a(const wide_t x) {
    return cmul_f_gen<BITWIDTH, FIELD_A_NAF_LEN>(x, FIELD_A_INT, FIELD_A_NAF);
}

wide_2x_t cmul_field_d(const wide_t x) {
    return cmul_f_gen<BITWIDTH, FIELD_D_NAF_LEN>(x, FIELD_D_INT, FIELD_D_NAF);
}

wide_2x_t cmul_field_k(const wide_t x) {
    return cmul_f_gen<BITWIDTH, FIELD_K_NAF_LEN>(x, FIELD_K_INT, FIELD_K_NAF);
}
