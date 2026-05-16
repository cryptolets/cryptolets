#include "bigint_mul.h"
#include "tb_helper.h"

vector<string> run_per_row(vector<string>& samples_row) {
  ac_int<N, false> a = parse_ac_int<N>(samples_row[0]);
  ac_int<N, false> b = parse_ac_int<N>(samples_row[1]);
  ac_int<2*N, false> result = CCS_DESIGN(bigint_mul<N, MULTI_WORD>)(a, b);
  return {result.to_string(AC_DEC)};
}

// required for sc verify flow in Catapult
CCS_MAIN(int argc, char** argv) {
  run_tb(run_per_row, argv[1], argv[2]); // samples_file, output_file
  CCS_RETURN(0);
}
