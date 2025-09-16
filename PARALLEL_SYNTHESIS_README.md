# Parallel Catapult Synthesis Setup

## Overview
This setup provides controlled parallel execution of Catapult synthesis runs with proper core allocation management.

## Files Created
- **`run_catapult_parallel.sh`** - Main orchestration script
- **`catapult_mul_single_config.tcl`** - Single configuration handler
- **Modified `catapult_mul_core_asic.tcl`** - Added DC core configuration

## Core Allocation System

### Formula: K/M Parallel Processes
- **K** = Total available cores
- **M** = Cores used per process  
- **Result** = K/M parallel processes running simultaneously

### Your Configuration (40 cores, 4 cores per process)
- Total cores: 40
- Cores per DC process: 4
- Max parallel processes: 10
- Peak core usage: 40 cores (100% utilization)

## Usage

### Quick Start
```bash
# Make executable (first time only)
chmod +x run_catapult_parallel.sh

# Run all configurations in parallel
./run_catapult_parallel.sh
```

### Configuration
Edit the top of `run_catapult_parallel.sh`:
```bash
TOTAL_CORES=40          # Your total cores (K)
CORES_PER_PROCESS=4     # Cores per DC run (M)

# Sweep parameters
BITWIDTHS="64 192 256"
TARGET_IIS="1"
TARGET_CLOCKS="1 1.5 2"
MUL_TYPES="sb kar nor"
```

### Monitoring Progress
```bash
# Check overall progress
tail -f logs/catapult_*.log

# Monitor specific configuration
tail -f logs/catapult_sb_1ns_ii1_64bit.log

# List all log files
ls -la logs/
```

## How It Works

1. **Job Queue Management**: Script maintains exactly 10 processes running
2. **Slot Allocation**: When a process finishes, immediately starts the next queued job
3. **Core Utilization**: Each process uses 4 cores for Design Compiler
4. **Isolation**: Each configuration runs independently with its own log file
5. **Error Handling**: Failed runs are tracked separately

## Key Features

- **Controlled Parallelism**: Never exceeds your core limit
- **Optimal Resource Usage**: Maintains full utilization (40/40 cores)
- **Progress Tracking**: Real-time status of running/completed/failed jobs
- **Individual Logs**: Separate log file for each configuration
- **Graceful Handling**: Proper cleanup and error reporting

## Expected Output
```
=========================================
Controlled Parallel Catapult Synthesis
=========================================
Core allocation:
  Total cores: 40
  Cores per process: 4
  Max parallel processes: 10

Configurations to run:
  - sb, 1ns, II=1, 64bit
  - sb, 1.5ns, II=1, 64bit
  ...
Total configurations: 27
Will run with max 10 parallel processes

Launched config 1/27 (PID: 12345)
Currently running: 1/10 processes

...

Controlled parallel synthesis completed!
Total configurations: 27
Completed successfully: 25
Failed configurations: 2
Success rate: 92%
```

## Troubleshooting

### Common Issues
1. **License limits**: Ensure you have enough Catapult licenses for 10 parallel runs
2. **Memory usage**: Monitor system memory with many parallel processes
3. **Disk I/O**: Each process creates substantial temporary files

### Adjusting Parallelism
If you encounter issues, reduce parallelism:
```bash
# Example: Use only 20 cores with 4 cores each = 5 parallel processes
TOTAL_CORES=20
CORES_PER_PROCESS=4
```

### Log Analysis
Failed configurations will have error details in their log files:
```bash
grep -l "Error\|FAILED" logs/*.log
```
