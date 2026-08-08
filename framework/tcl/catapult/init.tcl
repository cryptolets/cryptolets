proc init_options {} {
    options defaults
    options set /Input/CppStandard c++14
    options set /Input/TargetPlatform x86_64
    options set Output/OutputVHDL false ;# we want only verilog output
    options set Output/RTLSchem false ;# rtl schematics take up a ton of space

    # SCVerify
    options set Flows/SCVerify/MAX_ERROR_CNT 1
    options set Flows/SCVerify/DEADLOCK_DETECTION true
    options set Flows/SCVerify/USE_OSCI true
    options set Flows/SCVerify/MISMATCHED_OUTPUTS_ONLY true

    # VCS RTL simulation and verification
    options set Flows/SCVerify/USE_QUESTASIM false
    options set Flows/SCVerify/USE_VCS true
    options set Flows/VCS/VCS_HOME /eda/synopsys/vcs/Y-2026.03/

    # Vivado
    options set Flows/Vivado/XILINX_VIVADO /eda/xilinx/2026.1/Vivado/

    # Design Compiler
    options set Flows/DesignCompiler/Path /eda/synopsys/syn/Y-2026.03/bin/
    options set Flows/DesignCompiler/ShellExe dc_shell
    options set Flows/DesignCompiler/OutNetlistFormat verilog
    options set Flows/DesignCompiler/GenerateGateSdf true
    options set Flows/DesignCompiler/EnablePowerReporting true
    options set Flows/DesignCompiler/DesignCompilerMode DC-Ultra
    options set Flows/DesignCompiler/MaxCores 8
}
