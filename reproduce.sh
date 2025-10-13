python3 run.py point_add_te --threads 40 --tp 1 \
    --core-script tcl_cores/catapult_padd_core.tcl \
    --sweep-file full_sweeps_configs/padd_te_sweep_sp_nor.yaml --dry-run > run_padd_te_sp_nor.log

python3 run.py point_add --threads 40 --tp 1 \
    --core-script tcl_cores/catapult_padd_core.tcl \
    --sweep-file full_sweeps_configs/padd_sw_sweep_sp_nor.yaml --dry-run > run_padd_sw_sp_nor.log


python3 run.py point_add_te --threads 40 --tp 1 \
    --core-script tcl_cores/catapult_padd_core.tcl \
    --sweep-file full_sweeps_configs/padd_te_sweep_sp.yaml --dry-run > run_padd_te_sp.log

python3 run.py point_add --threads 40 --tp 1 \
    --core-script tcl_cores/catapult_padd_core.tcl \
    --sweep-file full_sweeps_configs/padd_sw_sweep_sp.yaml --dry-run > run_padd_sw_sp.log


python3 run.py point_add_te --threads 40 --tp 1 \
    --core-script tcl_cores/catapult_padd_core.tcl \
    --sweep-file full_sweeps_configs/padd_te_sweep_mp.yaml --dry-run > run_padd_te_mp.log

python3 run.py point_add --threads 40 --tp 1 \
    --core-script tcl_cores/catapult_padd_core.tcl \
    --sweep-file full_sweeps_configs/padd_sw_sweep_mp.yaml --dry-run > run_padd_sw_mp.log

