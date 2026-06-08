#!/bin/bash

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

# Decode one sweep config
decode_config() {
  echo "$1" | base64 --decode | jq -r 'to_entries[] | "\(.key)=\(.value)"'
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

# Wait for all remaining processes to finish
wait_for_finish() {
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
}