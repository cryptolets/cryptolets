// Verilog implementation of start_cycle parameter calculation and scheduler simulation

// module build_start_params #(
//     parameter PE_LATENCY = 2,
//     parameter MAX_LEVELS = 16 // set as needed
// )(
//     input wire [31:0] size_exp,
//     input wire [31:0] bfs_depth,
//     output reg [31:0] start_cycle [0:MAX_LEVELS-1],
//     output reg [31:0] start_cycle_lower_bits [0:MAX_LEVELS-1],
//     output reg [31:0] nlevels
// );
//     integer i, j, inc;
//     reg can_use;
//     reg [31:0] gen_cycle, cand, mask, a, b;

//     initial begin
//         nlevels = size_exp - bfs_depth;
//         for (i = 0; i < MAX_LEVELS; i = i + 1) begin
//             start_cycle[i] = 0;
//             start_cycle_lower_bits[i] = 0;
//         end

//         if (nlevels > 0) begin
//             start_cycle[0] = 1;
//             for (i = 1; i < nlevels; i = i + 1) begin
//                 gen_cycle = start_cycle[i-1] + (1 << i) + PE_LATENCY;
//                 inc = 0;
//                 while (inc <= 65535) begin
//                     inc = inc + 1;
//                     cand = gen_cycle + inc;
//                     can_use = 1;
//                     for (j = 1; j <= i; j = j + 1) begin
//                         mask = (1 << j) - 1;
//                         a = cand & mask;
//                         b = start_cycle[j-1] & mask;
//                         if (a == b) begin
//                             can_use = 0;
//                             disable inner_for;
//                         end
//                     end
//                     inner_for: if (can_use) begin
//                         start_cycle[i] = cand;
//                         disable while_loop;
//                     end
//                 end
//                 while_loop: if (!can_use) begin
//                     start_cycle[i] = gen_cycle + 65536;
//                 end
//             end
//             for (i = 0; i < nlevels; i = i + 1) begin
//                 mask = (1 << (i+1)) - 1;
//                 start_cycle_lower_bits[i] = start_cycle[i] & mask;
//             end
//         end
//     end
// endmodule

module DFS_scheduler_inv_tree #(
    // parameter MAX_LEVELS = 32,
    parameter MAX_DFS_LEVELS = 29  // assume 3 level BFS PE
)(
    input  wire        clk,
    input  wire        rst,
    input  wire [31:0] size_exp,
    input  wire [31:0] bfs_depth,
    input  wire [32*MAX_DFS_LEVELS-1:0] start_cycle_flat,
    input  wire [32*MAX_DFS_LEVELS-1:0] start_cycle_lower_bits_flat,
    output reg  [31:0] output_in, // output for the DFS PE as address to look up for its inputs
    output reg         done
);

    // Unpack flattened vectors into arrays
    reg [31:0] start_cycle        [0:MAX_DFS_LEVELS-1];
    reg [31:0] start_cycle_lower_bits [0:MAX_DFS_LEVELS-1];
    integer k;
    always @(*) begin
        for (k = 0; k < MAX_DFS_LEVELS; k = k + 1) begin
            start_cycle[k] = start_cycle_flat[32*k +: 32];
            start_cycle_lower_bits[k] = start_cycle_lower_bits_flat[32*k +: 32];
        end
    end

    reg [31:0] cycle; // current clock cycle count
    reg        start_enable [0:MAX_DFS_LEVELS-1];
    reg        start_cycle_all_enabled;
    reg [31:0] output_in_temp [0:MAX_DFS_LEVELS-1];
    integer    i;

    wire [31:0] nlevels = size_exp - bfs_depth;

    // Reset and initialization
    integer j;
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            cycle <= 0;
            output_in <= 0;
            done <= 0;
            start_cycle_all_enabled <= 0;
            for (j = 0; j < MAX_DFS_LEVELS; j = j + 1) begin
                start_enable[j] <= 0;
                output_in_temp[j] <= 0;
            end
        end else if (!done) begin
            // Enable start cycles
            if (!start_cycle_all_enabled) begin
                for (i = 0; i < MAX_DFS_LEVELS; i = i + 1) begin
                    if (i < nlevels) begin
                        if (!start_enable[i] && cycle >= start_cycle[i] - 1) begin
                            start_enable[i] <= 1;
                            if (i == nlevels - 1)
                                start_cycle_all_enabled <= 1;
                        end
                    end
                end
            end

            // Compute output_in_temp for each level
            for (i = 0; i < MAX_DFS_LEVELS; i = i + 1) begin
                if (i < nlevels && start_enable[i]) begin
                    if ((cycle & ((1 << (i+1)) - 1)) == start_cycle_lower_bits[i]) begin
                        output_in_temp[i] <= i + bfs_depth + 1;
                    end else begin
                        output_in_temp[i] <= 0;
                    end
                end else begin
                    output_in_temp[i] <= 0;
                end
            end

            // Pick the lowest index non-zero output_in_temp
            output_in <= 0;
            for (i = 0; i < MAX_DFS_LEVELS; i = i + 1) begin
                if (output_in_temp[i] != 0) begin  // && output_in == 0
                    output_in <= output_in_temp[i];
                end
            end

            // Check for completion
            if (output_in >= size_exp - 1) begin
                done <= 1;
            end else begin
                cycle <= cycle + 1;
            end
        end
    end

endmodule
