#include "bigint_add.h"
#include "tb_helper.h"

vector<string> run_per_row(vector<string>& samples_row) {
  ac_int<N, false> x = parse_ac_int<N>(samples_row[0]);
  ac_int<N, false> y = parse_ac_int<N>(samples_row[1]);
  ac_int<N+1, false> result = CCS_DESIGN(bigint_add_inst)(x, y);
  return {result.str()};
}

// required for sc verify flow in Catapult
CCS_MAIN() {
  run_tb(run_per_row);
  CCS_RETURN(0);
}