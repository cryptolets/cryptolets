#include "l0_int_cmul_top.h"
#include "tb_helper.h"

// The ports follow the constant, as the implementation defines them
static constexpr int CMUL_IN  = (CMUL_CONST == CMUL_MU) ? 2*BITWIDTH : BITWIDTH;
static constexpr int CMUL_OUT = (CMUL_CONST == CMUL_Q_PRIME
                              || CMUL_CONST == CMUL_MU)   ? BITWIDTH : 2*BITWIDTH;

vector<string> run_per_row(vector<string>& samples_row) {
  ac_int<CMUL_IN, false> x = parse_ac_int<CMUL_IN>(samples_row[0]);
  ac_int<CMUL_OUT, false> result;
  CCS_DESIGN(l0_int_cmul_top) dut;
  dut.run(x, result);
  return {result.to_string(AC_DEC)};
}

// required for sc verify flow in Catapult
CCS_MAIN(int argc, char** argv) {
  run_tb(run_per_row, argv[1], argv[2]); // samples_file, output_file
  CCS_RETURN(0);
}
