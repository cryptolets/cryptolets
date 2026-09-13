#!/usr/bin/env bash
set -e

THREADS=300
THREADS_PER_PROCESS=8
RUN="./.venv/bin/python -m tessera run"
OPTS="-t $THREADS -p $THREADS_PER_PROCESS"

# Quick start
$RUN l1_mod_add -s test/sweeps/quick_start_l1_mod_add.yaml $OPTS --only syn
$RUN l1_mod_add -s test/sweeps/quick_start_l1_mod_add.yaml $OPTS --from gls --to pwr

# L0
$RUN l0_int_add  -s test/sweeps/l0_int.yaml      $OPTS --from syn --to pwr
$RUN l0_int_sub  -s test/sweeps/l0_int.yaml      $OPTS --from syn --to pwr
$RUN l0_int_mul  -s test/sweeps/l0_int_mul.yaml  $OPTS --from syn --to pwr
$RUN l0_int_sq   -s test/sweeps/l0_int_mul.yaml  $OPTS --from syn --to pwr
$RUN l0_int_cmul -s test/sweeps/l0_int_cmul.yaml $OPTS --from syn --to pwr

# L1
$RUN l1_mod_add  -s test/sweeps/l1_mod.yaml      $OPTS --from syn --to pwr
$RUN l1_mod_sub  -s test/sweeps/l1_mod.yaml      $OPTS --from syn --to pwr
$RUN l1_mod_mul  -s test/sweeps/l1_mod_mul.yaml  $OPTS --from syn --to pwr
$RUN l1_mod_cmul -s test/sweeps/l1_mod_cmul.yaml $OPTS --from syn --to pwr

# L2
$RUN l2_point_dbl_sw -s test/sweeps/l2_point_dbl_sw.yaml $OPTS --from syn --to pwr
$RUN l2_point_add_sw -s test/sweeps/l2_point_add_sw.yaml $OPTS --from syn --to pwr
$RUN l2_point_add_te -s test/sweeps/l2_point_add_te.yaml $OPTS --from syn --to pwr
