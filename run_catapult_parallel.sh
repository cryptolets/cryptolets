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

# Core allocation configuration - MODIFY THESE VALUES AS NEEDED
TOTAL_CORES=40          # Total available cores (K)
CORES_PER_PROCESS=4     # Cores used per process (M)
MAX_PARALLEL=$((TOTAL_CORES / CORES_PER_PROCESS))  # K/M parallel processes

echo "========================================="
echo "Controlled Parallel Catapult Synthesis"
echo "========================================="
echo "Core allocation:"
echo "  Total cores: $TOTAL_CORES"
echo "  Cores per process: $CORES_PER_PROCESS"
echo "  Max parallel processes: $MAX_PARALLEL"
echo ""

# Record start time
START_TIME=$(date +%s)
START_TIME_HUMAN=$(date '+%Y-%m-%d %H:%M:%S')
echo "Synthesis started at: $START_TIME_HUMAN"
echo ""

# Configuration parameters
BITWIDTHS="64 192 256"
TARGET_IIS="1"
TARGET_CLOCKS="1 1.5 2"
MUL_TYPES="sb kar nor"

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to format elapsed time
format_duration() {
    local seconds=$1
    local hours=$((seconds / 3600))
    local minutes=$(((seconds % 3600) / 60))
    local secs=$((seconds % 60))
    
    if [ $hours -gt 0 ]; then
        printf "%02d:%02d:%02d" $hours $minutes $secs
    else
        printf "%02d:%02d" $minutes $secs
    fi
}

# Function to wait for a slot to become available
wait_for_slot() {
    while [ ${#active_pids[@]} -ge $MAX_PARALLEL ]; do
        # echo "Waiting for slot (${#active_pids[@]}/$MAX_PARALLEL processes running)..."
        
        # Check which processes have finished
        local new_pids=()
        for pid in "${active_pids[@]}"; do
            if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                # Process still running
                new_pids+=("$pid")
            else
                # Process finished
                if [ -n "$pid" ]; then
                    wait "$pid"
                    local exit_code=$?
                    local end_time=$(date +%s)
                    local process_duration=$((end_time - process_start_times[$pid]))
                    local duration_str=$(format_duration $process_duration)
                    
                    if [ $exit_code -eq 0 ]; then
                        echo "Process $pid completed successfully in $duration_str"
                        ((completed_count++))
                    else
                        echo "Process $pid failed in $duration_str (exit code: $exit_code)"
                        ((failed_count++))
                    fi
                    
                    # Clean up timing data
                    unset process_start_times[$pid]
                    
                    ((running_count--))
                    echo "Slot freed (${#new_pids[@]}/$MAX_PARALLEL processes running)"
                fi
            fi
        done
        active_pids=("${new_pids[@]}")
        
        # If still at max capacity, sleep briefly
        if [ ${#active_pids[@]} -ge $MAX_PARALLEL ]; then
            sleep 1
        fi
    done
}

# Function to run a single configuration
run_config() {
    local mul_type=$1
    local clk=$2
    local target_ii=$3
    local bitwidth=$4
    
    echo "Starting: mul_type=$mul_type, clk=${clk}ns, ii=$target_ii, bitwidth=${bitwidth}bit"
    
    # Set environment variables for the configuration
    export MUL_TYPE="$mul_type"
    export CLK="$clk"
    export TARGET_II="$target_ii"
    export BITWIDTH="$bitwidth"
    export DC_CORES="$CORES_PER_PROCESS"  # Pass cores info to Catapult
    
    # Create a unique log file for this configuration
    local log_file="$SCRIPT_DIR/logs/catapult_${mul_type}_${clk}ns_ii${target_ii}_${bitwidth}bit.log"
    
    # Run Catapult with the single configuration script
    catapult -shell -f "$SCRIPT_DIR/catapult_mul_single_config.tcl" > "$log_file" 2>&1
    
    # Note: exit code will be checked by wait_for_slot function
}

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

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
for mul_type in $MUL_TYPES; do
    for clk in $TARGET_CLOCKS; do
        for target_ii in $TARGET_IIS; do
            for bitwidth in $BITWIDTHS; do
                echo "  - $mul_type, ${clk}ns, II=$target_ii, ${bitwidth}bit"
                ((total_configs++))
            done
        done
    done
done

echo "Total configurations: $total_configs"
echo "Will run with max $MAX_PARALLEL parallel processes"
echo ""

# Launch configurations with controlled parallelism
config_num=0
for mul_type in $MUL_TYPES; do
    for clk in $TARGET_CLOCKS; do
        for target_ii in $TARGET_IIS; do
            for bitwidth in $BITWIDTHS; do
                ((config_num++))
                
                # Wait for an available slot
                wait_for_slot
                
                # Launch the configuration in background
                run_config "$mul_type" "$clk" "$target_ii" "$bitwidth" &
                new_pid=$!
                
                # Verify we got a valid PID
                if [ -n "$new_pid" ]; then
                    active_pids+=("$new_pid")
                    process_start_times[$new_pid]=$(date +%s)  # Record start time
                    ((running_count++))
                    
                    current_time=$(date '+%H:%M:%S')
                    echo "[$current_time] Launched config $config_num/$total_configs (PID: $new_pid)"
                    echo "Currently running: ${#active_pids[@]}/$MAX_PARALLEL processes"
                else
                    echo "ERROR: Failed to launch config $config_num/$total_configs"
                    ((failed_count++))
                fi
                echo ""
            done
        done
    done
done

echo "All configurations launched. Waiting for remaining processes to complete..."

# Wait for all remaining processes to finish
while [ ${#active_pids[@]} -gt 0 ]; do
    # echo "Waiting for ${#active_pids[@]} remaining processes..."
    
    new_pids=()
    for pid in "${active_pids[@]}"; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            # Process still running
            new_pids+=("$pid")
        else
            # Process finished
            if [ -n "$pid" ]; then
                wait "$pid"
                exit_code=$?
                end_time=$(date +%s)
                process_duration=$((end_time - process_start_times[$pid]))
                duration_str=$(format_duration $process_duration)
                
                if [ $exit_code -eq 0 ]; then
                    echo "Process $pid completed successfully in $duration_str"
                    ((completed_count++))
                else
                    echo "Process $pid failed in $duration_str (exit code: $exit_code)"
                    ((failed_count++))
                fi
                
                # Clean up timing data
                unset process_start_times[$pid]
                
                ((running_count--))
            fi
        fi
    done
    active_pids=("${new_pids[@]}")
    
    # Sleep briefly if there are still processes running
    if [ ${#active_pids[@]} -gt 0 ]; then
        sleep 2
    fi
done

# Calculate total execution time
END_TIME=$(date +%s)
END_TIME_HUMAN=$(date '+%Y-%m-%d %H:%M:%S')
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
echo "  Cores per process: $CORES_PER_PROCESS"
echo "  Max parallel processes: $MAX_PARALLEL"
echo "  Peak core usage: $((MAX_PARALLEL * CORES_PER_PROCESS)) cores"
echo ""

# Show log files location
echo "Log files are available in: $SCRIPT_DIR/logs/"
echo "Use 'ls -la logs/' to see individual log files"

exit $failed_count
