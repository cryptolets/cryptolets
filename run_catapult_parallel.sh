#!/bin/bash

# run_catapult_parallel.sh
# Parallel execution of Catapult synthesis for mul_f configurations
# with controlled parallelism based on core allocation
#
# This script implements a job queue system that:
# 1. Calculates max parallel processes as K/M (total cores / cores per process)
# 2. Maintains exactly that many processes running at all times
# 3. Waits for a slot to free up before starting the next job
# 4. Tracks completion and provides detailed progress reporting

CORE_CATAPULT_SCRIPT=$1
PARAMS_TCL_SCRIPT=$2
KERNEL_NAME=$3
DRY_RUN_ARG=$4
GUI_ARG=$5

source utils/parallel_helpers.sh
load_tcl_sweep_params $PARAMS_TCL_SCRIPT # load params from tcl config file

# Core allocation configuration - MODIFY THESE VALUES AS NEEDED
TOTAL_CORES=40          # Total available cores (K)
DESIGN_COMPILER_THREADS=4     # Cores used per process (M) / Also for Vivado
export DESIGN_COMPILER_THREADS
MAX_PARALLEL=$((TOTAL_CORES / DESIGN_COMPILER_THREADS))  # K/M parallel processes

echo "========================================="
echo "Controlled Parallel Catapult Synthesis"
echo "========================================="
echo "Core allocation:"
echo "  Total cores: $TOTAL_CORES"
echo "  Cores per process: $DESIGN_COMPILER_THREADS"
echo "  Max parallel processes: $MAX_PARALLEL"
echo ""

# Record start time
START_TIME=$(date +%s)
START_TIME_HUMAN=$(date "+%Y-%m-%d %H:%M:%S")
echo "Synthesis started at: $START_TIME_HUMAN"
echo ""

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" # Get the script directory
LOGS_DIR="$ROOT_DIR/logs/$KERNEL_NAME"
mkdir -p $LOGS_DIR # Create logs directory if it doesn't exist

# Initialize counters and tracking arrays
declare -a active_pids=()
declare -A process_start_times=()  # Associative array to track start times by PID

total_configs=0
completed_count=0
failed_count=0
running_count=0

echo "Starting controlled parallel Catapult synthesis..."
echo "Configurations to run:"

# Count total configurations and display them
sweep_recurse 0 count_configs

echo "Total configurations: $total_configs"

# Check GUI mode constraints
if [ "$GUI_ARG" = "--gui" ] && [ "$total_configs" -gt 1 ]; then
    echo "Error: GUI mode can only be used with a single configuration."
    echo "Current sweep produces $total_configs configurations."
    echo "Please modify the parameters to generate only 1 configuration."
    exit 1
fi

echo "Will run with max $MAX_PARALLEL parallel processes"
echo ""

# What suffix to use for which paramter in the log file name
declare -A SWEEP_KEY_LOG_MAP=(
  [BITWIDTHS]=BW # bitwidth
  [TECH_TYPES]=TT # tech type
  [TARGET_IIS]=II # ii
  [MUL_TYPES]=MT # mul type
  [TARGET_PERIODS]=P # period
  [Q_TYPES]=QT # q_type
  [CURVE_TYPES]=CT # curve type
  [FIELD_AS]=FA # field a
  [BASE_MUL_DEPTH_MAP]=BM # base mul depth
  [KAR_MUL_DEPTH_MAP]=KAR # kar mul depth
)

# Function to run a single configuration
run_config() {
    local print_line="Starting:"
    local log_suffix=""
    export KERNEL_NAME="$KERNEL_NAME"
    export PARAMS_TCL_SCRIPT="$PARAMS_TCL_SCRIPT"

    for k in "${SWEEPS_PROJ_ORDER[@]}"; do
      # --- export key mapping (same logic as count_configs) ---
      local exp_key
      case "$k" in
        BASE_MUL_DEPTH_MAP) exp_key="BASE_MUL_DEPTH" ;;
        KAR_MUL_DEPTH_MAP)  exp_key="KAR_MUL_DEPTH"  ;;
        *)                  exp_key="${k::-1}"       ;;  # strip trailing s
      esac

      # --- log key mapping (explicit map, fallback to raw) ---
      local log_key="${SWEEP_KEY_LOG_MAP[$k]:-$k}"

      local val="${SWEEP_STATE[$k]}"

      export "${exp_key}"="$val"   # export for core catapult script

      print_line+=" $exp_key=$val"
      log_suffix+="${log_key^^}_${val}_"
    done
    local log_file="$LOGS_DIR/catapult_${log_suffix%_}.log"
    
    echo "$print_line"
    if [ "$DRY_RUN_ARG" = "--dry-run" ]; then 
      if [ "$GUI_ARG" = "--gui" ]; then
        echo "[DRY RUN] Would run: catapult -f $ROOT_DIR/$CORE_CATAPULT_SCRIPT"
      else
        echo "[DRY RUN] Would run: catapult -shell -f $ROOT_DIR/$CORE_CATAPULT_SCRIPT > $log_file 2>&1"
      fi
    else
      if [ "$GUI_ARG" = "--gui" ]; then
        catapult -f "$ROOT_DIR/$CORE_CATAPULT_SCRIPT"
      else
        catapult -shell -f "$ROOT_DIR/$CORE_CATAPULT_SCRIPT" > "$log_file" 2>&1
      fi
    fi

    # Note: exit code will be checked by wait_for_slot function
}

# Launch configurations with controlled parallelism
launch_config() {
  ((config_num++))

  # Wait for an available slot
  wait_for_slot

  # Build args in the defined order
  local args=()
  for k in "${SWEEPS_PROJ_ORDER[@]}"; do
    args+=("${SWEEP_STATE[$k]}")
  done

  # Launch command in background
  run_config "${args[@]}" &
  new_pid=$!

  if [ -n "$new_pid" ]; then
    active_pids+=("$new_pid")
    process_start_times[$new_pid]=$(date +%s)
    ((running_count++))

    current_time=$(date "+%H:%M:%S")
    echo "[$current_time] Launched config $config_num/$total_configs (PID: $new_pid)"
    echo "Currently running: ${#active_pids[@]}/$MAX_PARALLEL processes"
  else
    echo "ERROR: Failed to launch config $config_num/$total_configs"
    ((failed_count++))
  fi
  echo ""
}

sweep_recurse 0 launch_config

echo "All configurations launched. Waiting for remaining processes to complete..."
wait_for_finish # Wait for all remaining processes to finish

# Calculate total execution time
END_TIME=$(date +%s)
END_TIME_HUMAN=$(date "+%Y-%m-%d %H:%M:%S")
TOTAL_DURATION=$((END_TIME - START_TIME))
TOTAL_DURATION_STR=$(format_duration $TOTAL_DURATION)

echo ""
echo "========================================="
echo "Controlled parallel synthesis completed!"
echo "========================================="
echo "Execution Summary:"
echo "  Started at: $START_TIME_HUMAN"
echo "  Ended at: $END_TIME_HUMAN"
echo "  Total execution time: $TOTAL_DURATION_STR"
echo ""
echo "Results Summary:"
echo "  Total configurations: $total_configs"
echo "  Completed successfully: $completed_count"
echo "  Failed configurations: $failed_count"
echo "  Success rate: $(( (completed_count * 100) / total_configs ))%"
echo ""
echo "Performance Summary:"
echo "  Average time per config: $(format_duration $((TOTAL_DURATION / total_configs)))"
if [ $completed_count -gt 0 ]; then
    echo "  Average time per successful config: $(format_duration $((TOTAL_DURATION / completed_count)))"
fi
echo "========================================="
echo ""
echo "Core utilization summary:"
echo "  Total cores available: $TOTAL_CORES"
echo "  Cores per process: $DESIGN_COMPILER_THREADS"
echo "  Max parallel processes: $MAX_PARALLEL"
echo "  Peak core usage: $((MAX_PARALLEL * DESIGN_COMPILER_THREADS)) cores"
echo ""

# # Show log files location
# echo "Log files are available in: $ROOT_DIR/logs/"
# echo "Use 'ls -la logs/' to see individual log files"

exit $failed_count
