#include "l1_mod_add_top.h"
#include "tb_helper.h"

#define FIXED_Q 0 // TODO: temporary

vector<string> run_per_row(vector<string>& samples_row) {
  ac_int<BITWIDTH, false> x = parse_ac_int<BITWIDTH>(samples_row[0]);
  ac_int<BITWIDTH, false> y = parse_ac_int<BITWIDTH>(samples_row[1]);
  ac_int<BITWIDTH, false> q = parse_ac_int<BITWIDTH>(samples_row[2]);

#if FIXED_Q
  ac_int<BITWIDTH+1, false> result = CCS_DESIGN(l1_mod_add)(x, y);
#else
  ac_int<BITWIDTH+1, false> result = CCS_DESIGN(l1_mod_add)(x, y, q);
#endif

  return {result.to_string(AC_DEC)};
}

// required for sc verify flow in Catapult
CCS_MAIN(int argc, char** argv) {
  run_tb(run_per_row, argv[1], argv[2]); // samples_file, output_file
  CCS_RETURN(0);
}