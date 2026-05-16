#include "bigint_sq.h"
#include "tb_helper.h"

vector<string> run_per_row(vector<string>& samples_row) {
  // TODO: parse kernel inputs from samples_row
  // ac_int<N, false> x = parse_ac_int<N>(samples_row[0]);
  {OUTPUT_TYPE} result = CCS_DESIGN(bigint_sq<{TEMPLATE_PARAMS}>)({KERNEL_INPUTS});
  return {result.to_string(AC_DEC)};
}

// required for sc verify flow in Catapult
CCS_MAIN(int argc, char** argv) {
  run_tb(run_per_row, argv[1], argv[2]); // samples_file, output_file
  CCS_RETURN(0);
}
