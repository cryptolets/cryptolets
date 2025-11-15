#!/usr/bin/env bash

# Global toggles
DRY_RUN=""               # "--dry-run" to enable
GEN_ONLY=""    # "--gen-only" to enable
NUM_THREADS=40
THREADS_PER_PROCESS=1

# Compose flags safely
FLAGS=()
[[ -n "${DRY_RUN}" ]] && FLAGS+=(--dry-run)
[[ -n "${GEN_ONLY}" ]] && FLAGS+=(--gen-only)

CORE="tcl_cores/catapult_padd_core.tcl"

echo "Running Single-Precision Short Weierstrass arbitrary nor sweep..."
python3 run.py point_add --threads ${NUM_THREADS} --tp ${THREADS_PER_PROCESS} \
  --core-script "${CORE}" \
  --sweep-file full_sweeps_configs/padd_sw_sweep_sp_arb_nor.yaml "${FLAGS[@]}" > run_logs/full_padd_sw_sp_arb_nor.log

echo "Running Single-Precision Twisted Edwards nor arbitrary sweep..."
python3 run.py point_add_te --threads ${NUM_THREADS} --tp ${THREADS_PER_PROCESS} \
  --core-script "${CORE}" \
  --sweep-file full_sweeps_configs/padd_te_sweep_sp_arb_nor.yaml "${FLAGS[@]}" > run_logs/full_padd_te_sp_arb_nor.log


# echo "Running Twisted Edwards CycloneMSM on ASIC sweep..."
# python3 run.py point_add_cyclonemsm --threads ${NUM_THREADS} --tp ${THREADS_PER_PROCESS} \
#   --core-script "${CORE}" \
#   --sweep-file full_sweeps_configs/padd_cyclonemsm_sweep.yaml "${FLAGS[@]}" > run_logs/full_padd_cyclonemsm.log

# Run normal sweeps first to cache clusters

echo "Running Single-Precision Short Weierstrass nor sweep..."
python3 run.py point_add --threads ${NUM_THREADS} --tp ${THREADS_PER_PROCESS} \
  --core-script "${CORE}" \
  --sweep-file full_sweeps_configs/padd_sw_sweep_sp_nor.yaml "${FLAGS[@]}" > run_logs/full_padd_sw_sp_nor.log

echo "Running Twisted Edwards CycloneMSM on ASIC nor sweep..."
python3 run.py point_add_cyclonemsm --threads ${NUM_THREADS} --tp ${THREADS_PER_PROCESS} \
  --core-script "${CORE}" \
  --sweep-file full_sweeps_configs/padd_cyclonemsm_sweep_nor.yaml "${FLAGS[@]}" > run_logs/full_padd_cyclonemsm_nor.log

# echo "Running Single-Precision Short Weierstrass sweep..."
# python3 run.py point_add --threads ${NUM_THREADS} --tp ${THREADS_PER_PROCESS} \
#   --core-script "${CORE}" \
#   --sweep-file full_sweeps_configs/padd_sw_sweep_sp.yaml "${FLAGS[@]}" > run_logs/full_padd_sw_sp.log

# echo "Running Single-Precision Short Weierstrass MNT4753 sweep..."
# python3 run.py point_add --threads ${NUM_THREADS} --tp ${THREADS_PER_PROCESS} \
#   --core-script "${CORE}" \
#   --sweep-file full_sweeps_configs/padd_sw_sweep_sp_mnt4753.yaml "${FLAGS[@]}" > run_logs/full_padd_sw_sp_mnt4753.log

# Run first to cache clusters 
echo "Running Single-Precision Twisted Edwards nor sweep..."
python3 run.py point_add_te --threads ${NUM_THREADS} --tp ${THREADS_PER_PROCESS} \
  --core-script "${CORE}" \
  --sweep-file full_sweeps_configs/padd_te_sweep_sp_nor.yaml "${FLAGS[@]}" > run_logs/full_padd_te_sp_nor.log

# echo "Running Single-Precision Twisted Edwards ED448 nor sweep..."
python3 run.py point_add_te --threads ${NUM_THREADS} --tp ${THREADS_PER_PROCESS} \
  --core-script "${CORE}" \
  --sweep-file full_sweeps_configs/padd_te_sweep_sp_ed448_nor.yaml "${FLAGS[@]}" > run_logs/full_padd_te_sp_ed448_nor.log

# MNT4753 sweeps separate because they take a long time to run
echo "Running Single-Precision Short Weierstrass MNT4753 nor sweep..."
python3 run.py point_add --threads ${NUM_THREADS} --tp ${THREADS_PER_PROCESS} \
  --core-script "${CORE}" \
  --sweep-file full_sweeps_configs/padd_sw_sweep_sp_mnt4753_nor.yaml "${FLAGS[@]}" > run_logs/full_padd_sw_sp_mnt4753_nor.log

# echo "Running Single-Precision Twisted Edwards sweep..."
# python3 run.py point_add_te --threads ${NUM_THREADS} --tp ${THREADS_PER_PROCESS} \
#   --core-script "${CORE}" \
#   --sweep-file full_sweeps_configs/padd_te_sweep_sp.yaml "${FLAGS[@]}" > run_logs/full_padd_te_sp.log

# echo "Running Single-Precision Twisted Edwards ED448 sweep..."
# python3 run.py point_add_te --threads ${NUM_THREADS} --tp ${THREADS_PER_PROCESS} \
#   --core-script "${CORE}" \
#   --sweep-file full_sweeps_configs/padd_te_sweep_sp_ed448.yaml "${FLAGS[@]}" > run_logs/full_padd_te_sp_ed448.log


# echo "Running Single-Precision Twisted Edwards arbitrary sweep..."
# python3 run.py point_add_te --threads ${NUM_THREADS} --tp ${THREADS_PER_PROCESS} \
#   --core-script "${CORE}" \
#   --sweep-file full_sweeps_configs/padd_te_sweep_sp_arb.yaml "${FLAGS[@]}" > run_logs/full_padd_te_sp_arb.log

# echo "Running Single-Precision Short Weierstrass arbitrary sweep..."
# python3 run.py point_add --threads ${NUM_THREADS} --tp ${THREADS_PER_PROCESS} \
#   --core-script "${CORE}" \
#   --sweep-file full_sweeps_configs/padd_sw_sweep_sp_arb.yaml "${FLAGS[@]}" > run_logs/full_padd_sw_sp_arb.log

# echo "Running Multi-Precision Short Weierstrass sweep..."
# python3 run.py point_add --threads ${NUM_THREADS} --tp ${THREADS_PER_PROCESS} \
#   --core-script "${CORE}" \
#   --sweep-file full_sweeps_configs/padd_sw_sweep_mp.yaml "${FLAGS[@]}" > run_logs/full_padd_sw_mp.log

# echo "Running Multi-Precision Twisted Edwards sweep..."
# python3 run.py point_add_te --threads ${NUM_THREADS} --tp ${THREADS_PER_PROCESS} \
#   --core-script "${CORE}" \
#   --sweep-file full_sweeps_configs/padd_te_sweep_mp.yaml "${FLAGS[@]}" > run_logs/full_padd_te_mp.log

# Custom II>1 for pareto optimal points
# python3 run.py point_add --run-only --threads ${NUM_THREADS} --tp ${THREADS_PER_PROCESS} > run_logs/ii_ge_2_padd.log
# python3 run.py point_add_te --run-only --threads ${NUM_THREADS} --tp ${THREADS_PER_PROCESS} > run_logs/ii_ge_2_padd_te.log
# python3 run.py point_add_cyclonemsm --run-only --threads ${NUM_THREADS} --tp ${THREADS_PER_PROCESS} > run_logs/ii_ge_2_padd_cyclonemsm.log