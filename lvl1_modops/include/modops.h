#ifndef MODOPS_H
#define MODOPS_H

#include "modadd.h"
#include "modsub.h"
#include "modmul_mont.h"
#include "primitives.h"

// Backend to abstract away modops specific logic from point add code

struct ModOps {
    wide_t q;
#if MODMUL_TYPE == MODMUL_TYPE_MONT
    wide_t q_prime;
#elif MODMUL_TYPE == MODMUL_TYPE_BARRETT
    wide_t mu;
#endif

    // Constructor
#if MODMUL_TYPE == MODMUL_TYPE_MONT
    ModOps(wide_t q_, wide_t qp_) : q(q_), q_prime(qp_) {}
#elif MODMUL_TYPE == MODMUL_TYPE_BARRETT
    ModOps(wide_t q_, wide_t mu_) : q(q_), mu(mu_) {}
#endif

    inline wide_t modmul(wide_t x, wide_t y) const {
#if MODMUL_TYPE == MODMUL_TYPE_MONT
        return modmul_mont_core(x, y, q, q_prime);
#elif MODMUL_TYPE == MODMUL_TYPE_BARRETT
        return modmul_barrett_core(x, y, q, mu);
#endif
    }

    inline wide_t modsq(wide_t x) const {
#if MODMUL_TYPE == MODMUL_TYPE_MONT
        return modsq_mont_core(x, q, q_prime);
#elif MODMUL_TYPE == MODMUL_TYPE_BARRETT
        return modsq_barrett_core(x, q, mu);
#endif
    }

// special case where we are multiplying by a const
#if MODMUL_TYPE == MODMUL_TYPE_MONT

    #ifdef FIELD_A_MONT_HEX
        inline wide_t cmodmul_a(wide_t x) const {
            return cmodmul_a_mont_core(x, q, q_prime);
        }
    #endif

    #ifdef FIELD_D_MONT_HEX
        inline wide_t cmodmul_d(wide_t x) const {
            return cmodmul_d_mont_core(x, q, q_prime);
        }
    #endif

    #ifdef FIELD_K_MONT_HEX
        inline wide_t cmodmul_k(wide_t x) const {
            return cmodmul_k_mont_core(x, q, q_prime);
        }
    #endif

#elif MODMUL_TYPE == MODMUL_TYPE_BARRETT

    #ifdef FIELD_A_HEX
        inline wide_t cmodmul_a(wide_t x) const {
            return cmodmul_a_barrett_core(x, q, q_prime);
        }
    #endif

    #ifdef FIELD_D_HEX
        inline wide_t cmodmul_d(wide_t x) const {
            return cmodmul_d_barrett_core(x, q, q_prime);
        }
    #endif

    #ifdef FIELD_K_HEX
        inline wide_t cmodmul_k(wide_t x) const {
            return cmodmul_k_barrett_core(x, q, q_prime);
        }
    #endif

#endif

    // Other modops
    inline wide_t modadd(wide_t a, wide_t b) const {
        return modadd_core(a, b, q);
    }

    inline wide_t modsub(wide_t a, wide_t b) const {
        return modsub_core(a, b, q);
    }

    inline wide_t moddouble(wide_t a) const {
        return moddouble_core(a, q);
    }
};

#endif // MODOPS_H
