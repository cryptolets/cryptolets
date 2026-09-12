#include "l1_mod_mul_top.h"
#include "tb_helper.h"
#include "field_helper.h"

#if MRED == MRED_BAR
static constexpr int RC_W = 2*BITWIDTH;
#else
static constexpr int RC_W = BITWIDTH;
#endif

vector<string> run_per_row(vector<string>& samples_row) {
  ac_int<BITWIDTH, false> x = parse_ac_int<BITWIDTH>(samples_row[0]);
  ac_int<BITWIDTH, false> y = parse_ac_int<BITWIDTH>(samples_row[1]);
  ac_int<BITWIDTH, false> q = parse_ac_int<BITWIDTH>(samples_row[2]);
  ac_int<RC_W, false> rc = parse_ac_int<RC_W>(samples_row[3]);

  // A Montgomery multiplier works on operands scaled by R
#if MRED == MRED_MONT
  x = to_mont<FIELD>(x, q);
  y = to_mont<FIELD>(y, q);
#endif

  ac_int<BITWIDTH, false> result;
  CCS_DESIGN(l1_mod_mul_top) dut;

#if Q_TYPE == FIXED_Q && RC_TYPE == FIXED_RC
  dut.run(x, y, result);
#elif Q_TYPE == FIXED_Q
  dut.run(x, y, rc, result);
#elif RC_TYPE == FIXED_RC
  dut.run(x, y, q, result);
#else
  dut.run(x, y, q, rc, result);
#endif

#if MRED == MRED_MONT
  result = from_mont<FIELD>(result, q);
#endif

  return {result.to_string(AC_DEC)};
}

// required for sc verify flow in Catapult
CCS_MAIN(int argc, char** argv) {
  run_tb(run_per_row, argv[1], argv[2]); // samples_file, output_file
  CCS_RETURN(0);
}
