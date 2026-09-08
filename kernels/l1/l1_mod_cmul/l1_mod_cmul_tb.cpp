#include "l1_mod_cmul_top.h"
#include "tb_helper.h"

// The reduction constant is q_prime for Montgomery and the wider mu for Barrett
#if MRED == MRED_BAR
static constexpr int RC_W = 2*BITWIDTH;
#else
static constexpr int RC_W = BITWIDTH;
#endif

vector<string> run_per_row(vector<string>& samples_row) {
  ac_int<BITWIDTH, false> x = parse_ac_int<BITWIDTH>(samples_row[0]);
  ac_int<RC_W, false> rc = parse_ac_int<RC_W>(samples_row[2]);

  ac_int<BITWIDTH, false> result;
  CCS_DESIGN(l1_mod_cmul_top) dut;

#if defined(Q_TYPE) && Q_TYPE == FIXED_Q
  dut.run(x, rc, result);
#else
  ac_int<BITWIDTH, false> q = parse_ac_int<BITWIDTH>(samples_row[1]);
  dut.run(x, q, rc, result);
#endif

  return {result.to_string(AC_DEC)};
}

// required for sc verify flow in Catapult
CCS_MAIN(int argc, char** argv) {
  run_tb(run_per_row, argv[1], argv[2]); // samples_file, output_file
  CCS_RETURN(0);
}
