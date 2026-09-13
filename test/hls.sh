#!/usr/bin/env bash
set -e

THREADS=40
THREADS_PER_PROCESS=1
RUN="./.venv/bin/python -m tessera run"
OPTS="-t $THREADS -p $THREADS_PER_PROCESS"

# Quick start
$RUN l1_mod_add -s test/sweeps/quick_start_l1_mod_add.yaml $OPTS --to rtl
./.venv/bin/python -m tessera analyze l1_mod_add
$RUN l1_mod_mul -s test/sweeps/quick_start_l1_mod_mul.yaml $OPTS --to rtl

# L0
$RUN l0_int_add  -s test/sweeps/l0_int.yaml      $OPTS --to rtl
$RUN l0_int_sub  -s test/sweeps/l0_int.yaml      $OPTS --to rtl
$RUN l0_int_mul  -s test/sweeps/l0_int_mul.yaml  $OPTS --to rtl
$RUN l0_int_sq   -s test/sweeps/l0_int_mul.yaml  $OPTS --to rtl
$RUN l0_int_cmul -s test/sweeps/l0_int_cmul.yaml $OPTS --to rtl

# L1
$RUN l1_mod_add  -s test/sweeps/l1_mod.yaml      $OPTS --to rtl
$RUN l1_mod_sub  -s test/sweeps/l1_mod.yaml      $OPTS --to rtl
$RUN l1_mod_mul  -s test/sweeps/l1_mod_mul.yaml  $OPTS --to rtl
$RUN l1_mod_cmul -s test/sweeps/l1_mod_cmul.yaml $OPTS --to rtl

# L2
$RUN l2_point_dbl_sw -s test/sweeps/l2_point_dbl_sw.yaml $OPTS --to rtl
$RUN l2_point_add_sw -s test/sweeps/l2_point_add_sw.yaml $OPTS --to rtl
$RUN l2_point_add_te -s test/sweeps/l2_point_add_te.yaml $OPTS --to rtl
