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

# Read sweep params from tcl config file
declare -a SWEEPS_ALL=()           # names of arrays and maps
declare -a SWEEPS_PROJ_ORDER=()    # projection order

load_tcl_sweep_params() {
  local file=$1
  local inside_map=0
  local current_map=""

  while read -r line || [[ -n "$line" ]]; do
    # Strip trailing comments
    line=${line%%;#*}
    line=$(echo "$line" | xargs)   # trim whitespace
    [[ -z "$line" ]] && continue

    # Inside a multi-line map
    if [[ $inside_map -eq 1 ]]; then
      if [[ "$line" == "}" ]]; then
        inside_map=0
        current_map=""
        continue
      fi
      key=$(echo "$line" | awk '{print $1}')
      vals=$(echo "$line" | sed -E 's/^[^{]+\{([^}]*)\}.*/\1/')
      eval "$current_map[$key]=\"\$vals\""
      continue
    fi

    case "$line" in
      set\ *)
        var=$(echo "$line" | awk '{print $2}')
        rest=${line#*"$var"}

        # Multi-line map
        if [[ "$rest" =~ "{"$'\n'?$ ]]; then
          declare -g -A "$var"
          SWEEPS_ALL+=("$var")
          inside_map=1
          current_map=$var
          continue
        fi

        # Inline list
        if [[ "$rest" == *"{"*"}"* ]]; then
          val=$(echo "$rest" | cut -d\{ -f2 | cut -d\} -f1)
          if [[ $var == "SWEEPS_PROJ_ORDER" ]]; then
            SWEEPS_PROJ_ORDER=($val)
          else
            eval "$var=($val)"
            SWEEPS_ALL+=("$var")
          fi
        else
          # Scalar
          val=$(echo "$rest" | awk '{print $1}')
          eval "$var=$val"
          SWEEPS_ALL+=("$var")
        fi
        ;;
    esac
  done < "$file"
}

# Curve type to field a map
declare -A CURVE_TO_FIELD_A_MAP=(
  [BN254]=A0
  [BLS12_377]=A0
  [BLS12_381]=A0
  [SECP256K1]=A0
  [P_256]=ANEG3
  [P_521]=ANEG3
  [MNT4753]=A2
)

# Basically, so the bit nested for loop recursively and generalizes it
# It takes SWEEPS_PROJ_ORDER to define the order
declare -A SWEEP_STATE=()  # holds current param assignments
sweep_recurse() {
  local depth=$1
  local leaf_func=$2   # function to call at leaf

  if (( depth == ${#SWEEPS_PROJ_ORDER[@]} )); then
    # skip if FIELD_AS == "AVAR" and CURVE_TYPES == "RAND_CURVE" and Q_TYPES == "fixedq"
    if [[ -v SWEEP_STATE[FIELD_AS] ]] \
      && [[ -v SWEEP_STATE[CURVE_TYPES] ]] \
      && [[ -v SWEEP_STATE[Q_TYPES] ]] \
      && [[ ${SWEEP_STATE[FIELD_AS]} == "AVAR" ]] \
      && [[ ${SWEEP_STATE[CURVE_TYPES]} == "RAND_CURVE" ]] \
      && [[ ${SWEEP_STATE[Q_TYPES]} == "fixedq" ]]; then
      return
    fi
    
    # Call the leaf function with current sweep state
    "$leaf_func"
    return
  fi

  local name=${SWEEPS_PROJ_ORDER[$depth]}
  local values=()
  
  if declare -p "$name" 2>/dev/null | grep -q 'declare \-a'; then
    # normal array
    eval "values=(\"\${${name}[@]}\")"
  else
    # map: lookup using current bitwidth
    local bw=${SWEEP_STATE[BITWIDTHS]}
    eval "valstr=\"\${${name}[$bw]}\""
    read -ra values <<< "$valstr"
  fi

  # override FIELD_AS sweep for specific CURVE_TYPE (non-RAND_CURVE)
  if [[ $name == "FIELD_AS" ]] \
    && [[ -v SWEEP_STATE[CURVE_TYPES] ]] \
    && [[ ${SWEEP_STATE[CURVE_TYPES]} != "RAND_CURVE" ]]; then
    
    curve_type=${SWEEP_STATE[CURVE_TYPES]}
    values=("${CURVE_TO_FIELD_A_MAP[$curve_type]:-AVAR}")
  fi

  # override BITWIDTHS sweep for specific CURVE_TYPE (non-RAND_CURVE)
  if [[ $name == "BITWIDTHS" ]] \
    && [[ -v SWEEP_STATE[CURVE_TYPES] ]] \
    && [[ ${SWEEP_STATE[CURVE_TYPES]} != "RAND_CURVE" ]]; then
    
    json_fp="${ROOT_DIR}/field_const.json"
    curve_type=${SWEEP_STATE[CURVE_TYPES]}
    bitwidth=$(python3 -c "import json;d=json.load(open('$json_fp'));print(d['$curve_type']['bitwidth'])")
    values=("$bitwidth")
  fi

  # If MUL_TYPE is sb -> override KAR_MUL_DEPTH_MAP[BITWIDTH] = {BITWIDTH}
  if [[ $name == "KAR_MUL_DEPTH_MAP" ]] \
    && [[ ${SWEEP_STATE[MUL_TYPES]} == "sb" ]]; then
    local bw=${SWEEP_STATE[BITWIDTHS]}
    values=("$bw")
  fi

  # If MUL_TYPE is nor -> override both maps to {BITWIDTH}
  if [[ ${SWEEP_STATE[MUL_TYPES]} == "nor" ]]; then
    local bw=${SWEEP_STATE[BITWIDTHS]}
    if [[ $name == "KAR_MUL_DEPTH_MAP" ]] || [[ $name == "BASE_MUL_DEPTH_MAP" ]]; then
      values=("$bw")
    fi
  fi

  for v in "${values[@]}"; do
    SWEEP_STATE[$name]=$v
    sweep_recurse $((depth+1)) "$leaf_func"
  done
}

# Count total configurations and display them
count_configs() {
  ((total_configs++))
  local line="-"
  for k in "${SWEEPS_PROJ_ORDER[@]}"; do
    local key
    case "$k" in
      BASE_MUL_DEPTH_MAP) key="BASE_MUL_DEPTH" ;;
      KAR_MUL_DEPTH_MAP)  key="KAR_MUL_DEPTH"  ;;
      *)                  key="${k::-1}"       ;;  # strip trailing s
    esac
    line+=" $key=${SWEEP_STATE[$k]}"
  done
  echo "  $line"
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