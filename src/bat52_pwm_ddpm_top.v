// File: /media/marco/DATA/programming/rtl/ddpm/tt03-ddpm-pwm/src/myhdl/work_tt_top/bat52_pwm_ddpm_top.v
// Generated by MyHDL 0.11.42
// Date: Thu Mar  2 00:23:53 2023


`timescale 1ns/10ps

module bat52_pwm_ddpm_top (
    io_in,
    io_out
);


input [7:0] io_in;
output [7:0] io_out;
wire [7:0] io_out;

reg pwm;
reg ddpm;
wire [4:0] empty_out;
wire clk;
wire [5:0] inval;
wire [7:0] outs;
wire resetn;
reg [5:0] pwm_ddpm0_count;
wire [5:0] pwm_ddpm0_ddpm_int_all;
reg pwm_ddpm0_ddpm_int [0:6-1];

assign empty_out = 5'd0;
assign outs[7] = clk;
assign outs[7-1:2] = empty_out;
assign outs[1] = ddpm;
assign outs[0] = pwm;
assign pwm_ddpm0_ddpm_int_all[5] = pwm_ddpm0_ddpm_int[0];
assign pwm_ddpm0_ddpm_int_all[4] = pwm_ddpm0_ddpm_int[1];
assign pwm_ddpm0_ddpm_int_all[3] = pwm_ddpm0_ddpm_int[2];
assign pwm_ddpm0_ddpm_int_all[2] = pwm_ddpm0_ddpm_int[3];
assign pwm_ddpm0_ddpm_int_all[1] = pwm_ddpm0_ddpm_int[4];
assign pwm_ddpm0_ddpm_int_all[0] = pwm_ddpm0_ddpm_int[5];


always @(negedge clk, negedge resetn) begin: BAT52_PWM_DDPM_TOP_PWM_DDPM0_COUNT_PROC
    if (resetn == 0) begin
        pwm_ddpm0_count <= 63;
    end
    else begin
        if ((pwm_ddpm0_count > 0)) begin
            pwm_ddpm0_count <= (pwm_ddpm0_count - 1);
        end
        else begin
            pwm_ddpm0_count <= (64 - 1);
        end
        // pass
    end
end


always @(pwm_ddpm0_count, inval) begin: BAT52_PWM_DDPM_TOP_PWM_DDPM0_PWM_PROC
    if ((pwm_ddpm0_count < inval)) begin
        pwm = 1;
    end
    else begin
        pwm = 0;
    end
    // pass
end


always @(pwm_ddpm0_count, inval) begin: BAT52_PWM_DDPM_TOP_PWM_DDPM0_DDPM_INT_PROC
    integer bidx;
    for (bidx=0; bidx<6; bidx=bidx+1) begin
        if ((($signed({1'b0, pwm_ddpm0_count}) & ((2 ** (6 - bidx)) - 1)) == (2 ** ((6 - 1) - bidx)))) begin
            pwm_ddpm0_ddpm_int[bidx] = inval[bidx];
        end
        else begin
            pwm_ddpm0_ddpm_int[bidx] = 0;
        end
        // pass
    end
end


always @(pwm_ddpm0_ddpm_int_all) begin: BAT52_PWM_DDPM_TOP_PWM_DDPM0_DDPM_PROC
    if ((pwm_ddpm0_ddpm_int_all > 0)) begin
        ddpm = 1;
    end
    else begin
        ddpm = 0;
    end
end



assign clk = io_in[0];
assign resetn = io_in[1];
assign inval = io_in[7-1:2];



assign io_out = outs;

endmodule
