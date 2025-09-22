// dfs_scheduler_updated.c
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <stdint.h>

const int MAX_LEVELS = 32; // maximum supported levels
const int MAX_DFS_LEVELS = 29;  // assume 3 level BFS PE group

// ---------------- helpers ----------------
static inline long pow2ll(int i) {
    return (1LL << i);
}

// ------------- start_cycle prepare -------------
typedef struct {
    long *start_cycle;
    long *start_cycle_lower_bits;
    int len;  // equals (size_exp - bfs_depth), the dfs levels count
} start_params_t;

start_params_t build_start_params(int size_exp, int bfs_depth, int PE_latency) {
    int nlevels = size_exp - bfs_depth;   // indices 0..nlevels-1
    start_params_t sp;
    sp.len = (nlevels > 0) ? nlevels : 0;

    if (sp.len <= 0) {
        sp.start_cycle = NULL;
        sp.start_cycle_lower_bits = NULL;
        return sp;
    }

    sp.start_cycle = (long*)calloc(sp.len, sizeof(long));
    sp.start_cycle_lower_bits = (long*)calloc(sp.len, sizeof(long));
    if (!sp.start_cycle || !sp.start_cycle_lower_bits) {
        fprintf(stderr, "OOM in build_start_params\n");
        exit(1);
    }

    sp.start_cycle[0] = 1;  // per spec

    for (int i = 1; i < sp.len; i++) {
        long gen_cycle = sp.start_cycle[i - 1] + pow2ll(i) + (long)PE_latency;

        int found = 0;
        long inc = 0;
        while (inc <= 65535) {
            inc += 1;
            long cand = gen_cycle + inc;
            int can_use = 1;

            // NOTE: compare against start_cycle[j-1] for j in [1..i]
            for (int j = 1; j <= i; j++) {
                long mask = pow2ll(j) - 1;           // 2^j - 1
                long a = cand & mask;               // cand mod 2^j
                long b = sp.start_cycle[j-1] & mask; // start_cycle[j-1] mod 2^j
                if (a == b) { can_use = 0; break; }
            }

            if (can_use) {
                sp.start_cycle[i] = cand;
                found = 1;
                break;
            }
        }

        if (!found) {
            // Fallback if nothing found in 65535 tries
            sp.start_cycle[i] = gen_cycle + 65536;
        }
    }

    // start_cycle_lower_bits[i] = start_cycle[i] & ((1<<i) - 1)
    for (int i = 0; i < sp.len; i++) {
        long mask = pow2ll(i + 1) - 1;   // (1<<(i+1)) - 1
        sp.start_cycle_lower_bits[i] = sp.start_cycle[i] & mask;
    }
    // index 0 is unused; leave as 0

    return sp;
}

// ---------------- simulate ----------------
typedef struct {
    int *vals;  // output_in per cycle
    int len;
} sim_result_t;

sim_result_t schedule(const start_params_t *sp, int size_exp, int bfs_depth) {
    sim_result_t sr;
    sr.vals = NULL;
    sr.len = 0;

    if (!sp || sp->len <= 0) return sr;

    int nlevels = sp->len;   // dfs level. 0..nlevels-1

    bool *start_enable = (bool*)calloc(MAX_DFS_LEVELS, sizeof(bool));  // nlevels
    if (!start_enable) {
        fprintf(stderr, "OOM in simulate\n");
        exit(1);
    }

    long clk = 0;
    for (int i = 0; i < MAX_DFS_LEVELS; i++) start_enable[i] = false;  // i < nlevels; i++
    // start_enable[0] = true;

    int start_cycle_all_enabled = 0;
    int last_i = 0;  // int last_i = 1;

    int cap = 1024*1024;
    int len = 0;
    int *res = (int*)malloc(cap * sizeof(int));
    if (!res) {
        fprintf(stderr, "OOM allocating result\n");
        exit(1);
    }

    while (1) {
        if (!start_cycle_all_enabled) {
            for (int i = 0; i < MAX_DFS_LEVELS; i++) { // last_i; i < nlevels; i++) {
                if (i < nlevels){
                    if (!start_enable[i] && clk >= sp->start_cycle[i]) {
                        start_enable[i] = true;
                        // last_i = i + 1;
                        if (i == nlevels - 1) {
                            start_cycle_all_enabled = 1;
                        }
                    }
                }
            }
        }

        int output_in = 0;
        for (int i = 0; i < MAX_DFS_LEVELS; i++) {  // for (int i = 1; i < nlevels; i++) {
            if (start_enable[i]) {
                long mask = pow2ll(i+1) - 1;  // pow2ll(i) - 1; // 2^(i+1) - 1
                if ((clk & mask) == sp->start_cycle_lower_bits[i]) {
                    output_in = i + bfs_depth + 1; // i + bfs_depth;
                }
            }
        }

        if (len == cap) {
            cap *= 2;
            int *nr = (int*)realloc(res, cap * sizeof(int));
            if (!nr) {
                fprintf(stderr, "OOM growing result\n");
                free(res);
                free(start_enable);
                exit(1);
            }
            res = nr;
        }
        res[len++] = output_in;

        if (output_in >= size_exp - 1) {
            break;
        }

        clk++;
        if (clk > (1LL << 40)) {  // safety guard
            fprintf(stderr, "Simulation aborted (clk runaway)\n");
            break;
        }
    }

    free(start_enable);
    sr.vals = res;
    sr.len = len;
    return sr;
}

// ---------------- main (demo) ----------------
int main(void) {
    // Example parameters (adjust as needed)
    int size_exp   = 10;  // workload size 2^size_exp
    int bfs_depth  = 3;
    int PE_latency = 1;  // 1 means the PE provide output in the next cycle.

    // 1) prepare start_cycle
    start_params_t sp = build_start_params(size_exp, bfs_depth, PE_latency);

    printf("Prepared start cycles (len=%d):\n", sp.len);
    for (int i = 0; i < sp.len; i++) {
        printf("  i=%d  start=%lld  lower_bits(2^%d)=%lld\n",
               i, sp.start_cycle[i], i, sp.start_cycle_lower_bits[i]);
    }

    // 2) simulate
    sim_result_t sr = schedule(&sp, size_exp, bfs_depth);

    // 3) print result per cycle
    printf("\nSimulation results (len=%d):\n", sr.len);
    for (int t = 0; t < sr.len; t++) {
        printf("cycle %d -> output_in=%d\n", t, sr.vals[t]);
    }

    // cleanup
    free(sp.start_cycle);
    free(sp.start_cycle_lower_bits);
    free(sr.vals);
    return 0;
}
