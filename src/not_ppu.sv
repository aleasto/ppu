/*


*/

// `define N (16)
// `define ES (1)

// `ifdef ALTERA_RESERVED_QIS
// `define NO_ES_FIELD
// `endif

module not_ppu #(
        parameter N = `N,
        parameter ES = `ES
    )(
        input   [N-1:0]         p1,
        input   [N-1:0]         p2,
        input   [OP_SIZE-1:0]   op,
        output  [N-1:0]         pout
    );
    
    
    wire [K_SIZE-1:0] k1, k2;
`ifndef NO_ES_FIELD
    wire [ES-1:0] exp1, exp2;
`endif

    wire [MANT_SIZE-1:0] mant1, mant2;
    wire [(3*MANT_SIZE)-1:0] mant_out_ops;
    wire [TE_SIZE-1:0] te1, te2, te_out_ops;

    wire sign1, sign2;


    wire [N-1:0] p1_cond, p2_cond;
    wire is_special_or_trivial;
    wire [N-1:0] pout_special_or_trivial;
    input_conditioning #(
         .N(N)
    ) input_conditioning (
        .p1_in(p1),
        .p2_in(p2),
        .op(op),
        .p1_out(p1_cond),
        .p2_out(p2_cond),
        .is_special_or_trivial(is_special_or_trivial),
        .pout_special_or_trivial(pout_special_or_trivial)
    );


    wire [PIF_SIZE-1:0] pif1, pif2;

    posit_to_pif #(
        .N(N),
        .ES(ES)
    ) posit_to_pif1 (
        .p_cond(p1_cond),
        .pif(pif1)
    );


    posit_to_pif #(
        .N(N),
        .ES(ES)
    ) posit_to_pif2 (
        .p_cond(p2_cond),
        .pif(pif2)
    );


    wire [TE_SIZE-1:0] ops_te_out;
    wire [FRAC_FULL_SIZE-1:0] ops_frac_full;

    wire sign_out_ops;
    ops #(
        .N(N)
    ) ops_inst (
        .op(op),
        
        .pif1(pif1),
        .pif2(pif2),
        .sign_out(sign_out_ops),
        .te_out(ops_te_out),
        .frac_full(ops_frac_full)
    );


    pif_to_posit #(
        .N(N),
        .ES(ES)
    ) pif_to_posit_inst (
        .te(ops_te_out),
        .frac_full(ops_frac_full),

        .frac_lsb_cut_off(0), // frac_lsb_cut_off
        .posit(pout_non_special_pre_sign)
    );




    wire [N-1:0] pout_non_special_pre_sign, pout_non_special;
    set_sign #(
        .N(N)
    ) set_sign_inst (
        .posit_in(pout_non_special_pre_sign),
        .sign(sign_out_ops),
        .posit_out(pout_non_special)
    );


    assign pout = is_special_or_trivial ? pout_special_or_trivial : pout_non_special;

endmodule



`ifdef TEST_BENCH_NOT_PPU

module tb_not_ppu;
    parameter N = `N;
    parameter ES = `ES;

    reg [N-1:0]  p1, p2;
    reg [OP_SIZE-1:0] op;
    reg [100:0] op_ascii;
    wire [N-1:0] pout;

    reg [300:0] p1_ascii, p2_ascii, pout_ascii, pout_gt_ascii;

    
    reg [N-1:0] pout_ground_truth, pout_hwdiv_expected;
    reg diff_pout_ground_truth, diff_pout_hwdiv_exp, pout_off_by_1;
    reg [N:0] test_no;

    reg [100:0] count_errors;

    not_ppu #(
        .N      (N),
        .ES     (ES)
    ) not_ppu_inst (
        .p1     (p1),
        .p2     (p2),
        .op     (op),
        .pout   (pout)
    );

    
    always @(*) begin
        diff_pout_ground_truth = pout === pout_ground_truth ? 0 : 1'bx;
        pout_off_by_1 = abs(pout - pout_ground_truth) == 0 ? 0 : abs(pout - pout_ground_truth) == 1 ? 1 : 'bx;
        diff_pout_hwdiv_exp = (op != DIV) ? 'hz : pout === pout_hwdiv_expected ? 0 : 1'bx;
    end




    reg [10-1:0] nn, ee;
    initial begin

        $dumpfile({"tb_ppu_P",`STRINGIFY(`N),"E",`STRINGIFY(`ES),".vcd"});
        $dumpvars(0, tb_not_ppu);                        

        
        if (N == 8 && ES == 0) begin
            `include "../test_vectors/tv_posit_ppu_P8E0.sv"
        end

        if (N == 8 && ES == 4) begin
            `include "../test_vectors/tv_posit_ppu_P8E4.sv"
        end

        if (N == 5 && ES == 1) begin
            `include "../test_vectors/tv_posit_ppu_P5E1.sv"
        end

        if (N == 16 && ES == 1) begin
            `include "../test_vectors/tv_posit_ppu_P16E1.sv"
        end

        if (N == 32 && ES == 2) begin
            `include "../test_vectors/tv_posit_ppu_P32E2.sv"
        end


        #10;
        $finish;
    end

endmodule
`endif
