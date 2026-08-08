#include "l1_mod_add.h"
#include "tb_helper.h"

#define FIXED_Q 0 // TODO: temporary

vector<string> run_per_row(vector<string>& samples_row) {
  ac_int<N, false> x = parse_ac_int<N>(samples_row[0]);
  ac_int<N, false> y = parse_ac_int<N>(samples_row[1]);
  ac_int<N, false> q = parse_ac_int<N>(samples_row[2]);

#if FIXED_Q
  ac_int<N+1, false> result = CCS_DESIGN(l1_mod_add<N>)(x, y);
#else
  ac_int<N+1, false> result = CCS_DESIGN(l1_mod_add<N>)(x, y, q);
#endif

  return {result.to_string(AC_DEC)};
}

// required for sc verify flow in Catapult
CCS_MAIN(int argc, char** argv) {
  run_tb(run_per_row, argv[1], argv[2]); // samples_file, output_file
  CCS_RETURN(0);
}