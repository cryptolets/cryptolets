proc init_options {questa dc vivado threads_per_process} {
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

    # RTL simulation and verification
    # QSIM_HOME stops Questa from picking up Catapult's MGC_HOME
    options set Flows/SCVerify/USE_QUESTASIM true
    options set Flows/QuestaSIM/Path $questa/linux_x86_64
    set ::env(QSIM_HOME) $questa

    # Questa reads the license server from SALT_LICENSE_SERVER
    if { [info exists ::env(MGLS_LICENSE_FILE)] } {
        set ::env(SALT_LICENSE_SERVER) $::env(MGLS_LICENSE_FILE)
    }

    # Vivado
    options set Flows/Vivado/XILINX_VIVADO $vivado

    # Design Compiler
    options set Flows/DesignCompiler/Path $dc/bin
    options set Flows/DesignCompiler/ShellExe dc_shell
    options set Flows/DesignCompiler/OutNetlistFormat verilog
    options set Flows/DesignCompiler/GenerateGateSdf true
    options set Flows/DesignCompiler/EnablePowerReporting true
    options set Flows/DesignCompiler/DesignCompilerMode DC-Ultra
    options set Flows/DesignCompiler/MaxCores $threads_per_process
}
