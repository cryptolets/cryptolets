`timescale 1ns/1ps

module tb_scheduler;

    // Parameters
    localparam MAX_DFS_LEVELS = 7;
    localparam SIZE_EXP = 10;
    localparam BFS_DEPTH = 3;

    // DUT signals
    reg clk, rst;
    reg [31:0] size_exp;
    reg [31:0] bfs_depth;
    reg [31:0] start_cycle        [0:MAX_DFS_LEVELS-1];
    reg [31:0] start_cycle_lower_bits [0:MAX_DFS_LEVELS-1];
    reg [32*MAX_DFS_LEVELS-1:0] start_cycle_flat;
    reg [32*MAX_DFS_LEVELS-1:0] start_cycle_lower_bits_flat;
    wire [31:0] output_in;
    wire done;

    // Instantiate DUT
    DFS_scheduler_inv_tree #(
        .MAX_DFS_LEVELS(MAX_DFS_LEVELS)
    ) dut (
        .clk(clk),
        .rst(rst),
        .size_exp(size_exp),
        .bfs_depth(bfs_depth),
        .start_cycle_flat(start_cycle_flat),
        .start_cycle_lower_bits_flat(start_cycle_lower_bits_flat),
        .output_in(output_in),
        .done(done)
    );

    // Clock generation
    initial clk = 0;
    always #0.5 clk = ~clk; // 1ns period

    integer i;

    initial begin
        // Initialize
        rst = 1;
        size_exp = SIZE_EXP;
        bfs_depth = BFS_DEPTH;

        // Set start_cycle values
        // PE pipeline cycle = 1:
        start_cycle[0] = 1;
        start_cycle[1] = 6;
        start_cycle[2] = 12;
        start_cycle[3] = 24;
        start_cycle[4] = 48;
        start_cycle[5] = 96;
        start_cycle[6] = 192;

        // PE pipeline cycle = 2:
        // start_cycle[0] = 1;
        // start_cycle[1] = 6;
        // start_cycle[2] = 16;
        // start_cycle[3] = 28;
        // start_cycle[4] = 52;
        // start_cycle[5] = 100;
        // start_cycle[6] = 196;

        // Calculate start_cycle_lower_bits
        for (i = 0; i < MAX_DFS_LEVELS; i = i + 1) begin
            start_cycle_lower_bits[i] = start_cycle[i] & ((1 << (i+1)) - 1);
        end

        // Flatten arrays into vectors
        for (i = 0; i < MAX_DFS_LEVELS; i = i + 1) begin
            start_cycle_flat[32*i +: 32] = start_cycle[i];
            start_cycle_lower_bits_flat[32*i +: 32] = start_cycle_lower_bits[i];
        end

        // Wait a few cycles for reset
        #2;
        rst = 0;

        // Run simulation until done
        $display("cycle | output_in");
        while (!done) begin
            @(posedge clk);
            $display("%5d | %2d", dut.cycle, output_in);
        end

        $display("Simulation finished at cycle %d", dut.cycle);
        $finish;
    end

endmodule