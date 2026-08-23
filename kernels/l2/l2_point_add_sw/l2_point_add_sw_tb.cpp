#include "l2_point_add_sw_top.h"
#include "tb_helper.h"
#include "ec_helper.h"

// The reduction constant is q_prime for Montgomery and the wider mu for Barrett
#if MRED == MRED_BAR
static constexpr int RC_W = 2*BITWIDTH;
#else
static constexpr int RC_W = BITWIDTH;
#endif

vector<string> run_per_row(vector<string>& samples_row) {
  PointAff<FIELD> P, Q;
  P.x = parse_ac_int<BITWIDTH>(samples_row[0]);
  P.y = parse_ac_int<BITWIDTH>(samples_row[1]);
  Q.x = parse_ac_int<BITWIDTH>(samples_row[2]);
  Q.y = parse_ac_int<BITWIDTH>(samples_row[3]);
  ac_int<BITWIDTH, false> q = parse_ac_int<BITWIDTH>(samples_row[4]);
  ac_int<RC_W, false> rc = parse_ac_int<RC_W>(samples_row[5]);

  PointJac<FIELD> R;
  CCS_DESIGN(l2_point_add_sw_top) dut;

#if Q_TYPE == FIXED_Q
  dut.run(aff_to_jac<FIELD>(P), aff_to_jac<FIELD>(Q), rc, R);
#else
  dut.run(aff_to_jac<FIELD>(P), aff_to_jac<FIELD>(Q), q, rc, R);
#endif

  // Two jacobian points can hold the same affine one, so the answer is affine
  PointAff<FIELD> A = jac_to_aff<FIELD>(R, q);
  return {A.x.to_string(AC_DEC), A.y.to_string(AC_DEC)};
}

// required for sc verify flow in Catapult
CCS_MAIN(int argc, char** argv) {
  run_tb(run_per_row, argv[1], argv[2]); // samples_file, output_file
  CCS_RETURN(0);
}
