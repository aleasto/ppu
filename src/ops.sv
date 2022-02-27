module ops #(
        parameter N = 4
    )(
        input [OP_SIZE-1:0] op,

        input [PIF_SIZE-1:0] pif1,
        input [PIF_SIZE-1:0] pif2,

        output sign_out,
        output [TE_SIZE-1:0] te_out,
        output [FRAC_FULL_SIZE-1:0] frac_full
    );


    wire sign1, sign2, sign_out;
    wire [TE_SIZE-1:0] te1, te2;
    wire [MANT_SIZE-1:0] mant1, mant2;
    wire [FRAC_FULL_SIZE-1:0] mant_out;

    assign {sign1, te1, mant1} = pif1;
    assign {sign2, te2, mant2} = pif2;

    core_op #(
        .N(N)
    ) core_op_inst (
        .op(op),
        .sign1(sign1),
        .sign2(sign2),
        .te1(te1),
        .te2(te2),
        .mant1(mant1),
        .mant2(mant2),
        .te_out_core_op(te_out),
        .mant_out_core_op(mant_out)
    );

    sign_decisor # (
    ) sign_decisor (
        .sign1(sign1),
        .sign2(sign2),
        .op(op),
        .sign(sign_out)
    );



    /*
        include the part below in core_op.sv and change name of signal to frac_out or smth

    */
    // chopping off the two MSB representing the 
    // non-fractional components i.e. ones and tens.
    assign frac_full = op == DIV
        ? mant_out : /* ADD, SUB, and MUL */
          mant_out << 2; 

endmodule
