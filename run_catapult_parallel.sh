#!/bin/bash
# run_catapult_parallel.sh
# Parallel Catapult execution from JSON configs produced by generate_sweep.py

source utils/parallel_helpers.sh

CORE_CATAPULT_SCRIPT=$1
KERNEL_NAME=$2
CONFIG_FILE=$3
TOTAL_THREADS=$4
THREADS_PER_PROCESS=$5
RTL_FILE=$6
DRY_RUN_FLAG=${7:-}
GUI_FLAG=${8:-}

MAX_PARALLEL=$((TOTAL_THREADS / THREADS_PER_PROCESS))

export KERNEL_NAME
export RTL_FILE
export THREADS_PER_PROCESS

echo "========================================="
echo "Controlled Parallel Catapult Execution"
echo "========================================="
echo "Core TCL script: $CORE_CATAPULT_SCRIPT"
echo "Kernel: $KERNEL_NAME"
echo "Config file: $CONFIG_FILE"
echo "RTL mode: $RTL_FILE"
echo "Flags:"
echo "  Dry run: ${DRY_RUN_FLAG:-false}"
echo "  GUI mode: ${GUI_FLAG:-false}"
echo ""
echo "Core allocation:"
echo "  Total threads: $TOTAL_THREADS"
echo "  Threads per process: $THREADS_PER_PROCESS"
echo "  Max parallel processes: $MAX_PARALLEL"
echo "========================================="
echo ""

# --- Load configs and control flags ---
command -v jq >/dev/null || { echo "jq not found"; exit 1; }
[ -f "$CONFIG_FILE" ] || { echo "Missing config file: $CONFIG_FILE"; exit 1; }

# --- Load and export control flags ---
echo "Exporting control flags..."
while IFS="=" read -r key val; do
  # Skip empty lines
  [ -z "$key" ] && continue
  
  # Normalize booleans to lowercase true/false
  case "$val" in
    true|True|TRUE)  val=true ;;
    false|False|FALSE) val=false ;;
  esac

  export "$key"="$val"
  echo "  $key=$val"
done < <(jq -r '.control_flags | to_entries[] | "\(.key)=\(.value)"' "$CONFIG_FILE")
echo ""

CONFIGS=($(jq -r '.sweep_configs[] | @base64' "$CONFIG_FILE"))
TOTAL_CONFIGS=${#CONFIGS[@]}

echo "Loaded control flags and $TOTAL_CONFIGS configuration(s)"
echo ""

# --- GUI mode constraint ---
if [ "$GUI_FLAG" = "--gui" ] && [ "$TOTAL_CONFIGS" -gt 1 ]; then
  echo "Error: GUI mode supports only one configuration."
  echo "Current sweep has $TOTAL_CONFIGS configurations."
  echo "Please reduce sweep parameters to a single config."
  exit 1
fi

# --- Setup directories and counters ---
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$ROOT_DIR/logs/$KERNEL_NAME"
mkdir -p "$LOGS_DIR"

START_TIME=$(date +%s)
START_HUMAN=$(date "+%Y-%m-%d %H:%M:%S")

echo "Logs directory: $LOGS_DIR"
echo "Start time: $START_HUMAN"
echo ""

# Initialize counters and tracking arrays
declare -a active_pids=()
declare -A process_start_times=()  # Associative array to track start times by PID

completed_count=0
failed_count=0
running_count=0
config_num=0

echo "Starting controlled parallel Catapult synthesis..."
echo "========================================="
echo ""

# --- Run a single configuration (decode + execute) ---
run_config() {
  local SWEEP_KEY="$1"
	local log_file="$LOGS_DIR/catapult_${SWEEP_KEY}.log"
	export SWEEP_KEY

	if [ "$DRY_RUN_FLAG" != "--dry-run" ]; then
		if [ "$GUI_FLAG" = "--gui" ]; then
			catapult -f "$ROOT_DIR/$CORE_CATAPULT_SCRIPT"
		else
			catapult -shell -f "$ROOT_DIR/$CORE_CATAPULT_SCRIPT" > "$log_file" 2>&1
		fi
	fi

  # Note: exit code will be checked by wait_for_slot function
}

# --- Launch one configuration with controlled parallelism ---
launch_config() {
	((config_num++))

	local cfg_b64="$1"
	local config_params_print=""
	local log_suffix=""

	# Build a JSON object for this config
	local json_str="{"
	for kv in $(decode_config "$cfg_b64"); do
		key="${kv%%=*}"
		val="${kv#*=}"
		export "$kv"
		json_str+="\"$key\": \"$val\","

		short_key=$(python3 -c "from utils.naming_short import short; print(short('$key'))") 
		short_val=$(python3 -c "from utils.naming_short import short; print(short('$key', '$val'))")
		config_params_print+=" ${short_key}=${short_val}"
	done
	json_str="${json_str%,}}"  # remove trailing comma

	# Use Python encoder() to generate short form name
	sweep_key=$(python3 -c "import json; from utils.naming_short import encoder; print(encoder(json.loads('''$json_str''')))")

	# Wait for an available slot
	wait_for_slot

	run_config "$sweep_key" &
	new_pid=$!

	if [ -n "$new_pid" ]; then
		active_pids+=("$new_pid")
		process_start_times[$new_pid]=$(date +%s)
		((running_count++))

		current_time=$(date "+%H:%M:%S")
		echo "[$current_time][PID: $new_pid] Launched config: $config_num/$TOTAL_CONFIGS, Currently running: ${#active_pids[@]}/$MAX_PARALLEL processes"
		echo "  Config Params: $config_params_print"
		if [ "$DRY_RUN_FLAG" = "--dry-run" ]; then
			if [ "$GUI_FLAG" = "--gui" ]; then
				echo "  [DRY RUN]	catapult -f $ROOT_DIR/$CORE_CATAPULT_SCRIPT"
			else
				echo "  [DRY RUN] catapult -shell -f $ROOT_DIR/$CORE_CATAPULT_SCRIPT > $log_file 2>&1"
			fi
		fi
	else
		echo "ERROR: Failed to launch config $config_num/$TOTAL_CONFIGS"
		((failed_count++))
	fi
	echo ""
}

# --- Controlled parallel execution loop ---
for cfg_b64 in "${CONFIGS[@]}"; do
    launch_config "$cfg_b64"
done

echo "All configurations launched. Waiting for remaining processes to complete..."
wait_for_finish

# --- Summary ---
END_TIME=$(date +%s)
END_TIME_HUMAN=$(date "+%Y-%m-%d %H:%M:%S")
TOTAL_DURATION=$((END_TIME - START_TIME))
TOTAL_DURATION_STR=$(format_duration $TOTAL_DURATION)

echo ""
echo "========================================="
echo "Parallel Catapult synthesis completed!"
echo "========================================="
echo "Execution Summary:"
echo "  Started at: $START_HUMAN"
echo "  Ended at: $END_TIME_HUMAN"
echo "  Total execution time: $TOTAL_DURATION_STR"
echo ""
echo "Results Summary:"
echo "  Total configurations: $TOTAL_CONFIGS"
echo "  Completed successfully: $completed_count"
echo "  Failed configurations: $failed_count"
echo "  Success rate: $(( (completed_count * 100) / TOTAL_CONFIGS ))%"
echo ""
echo "Performance Summary:"
echo "  Average time per config: $(format_duration $((TOTAL_DURATION / TOTAL_CONFIGS)))"
if [ $completed_count -gt 0 ]; then
    echo "  Average time per successful config: $(format_duration $((TOTAL_DURATION / completed_count)))"
fi
echo "Core Utilization:"
echo "  Total threads: $TOTAL_THREADS"
echo "  Threads per process: $THREADS_PER_PROCESS"
echo "  Max parallel processes: $MAX_PARALLEL"
echo "  Peak thread usage: $((MAX_PARALLEL * THREADS_PER_PROCESS))"
echo "========================================="
echo ""
echo "Logs directory: $LOGS_DIR"
echo ""

exit $failed_count