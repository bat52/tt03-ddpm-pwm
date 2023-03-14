// File: /media/marco/DATA/programming/rtl/ddpm/tt03-ddpm-pwm/src/myhdl/work_ddpm/bat52_pwm_ddpm_top.v
// Generated by MyHDL 0.11.42
// Date: Tue Mar 14 00:58:31 2023


`timescale 1ns/10ps

module bat52_pwm_ddpm_top (
    io_in,
    io_out
);


input [7:0] io_in;
output [7:0] io_out;
reg [7:0] io_out;

wire [5:0] count_out;
reg clk;
reg ddpm;
reg [5:0] inval;
reg pwm;
reg resetn;
reg sd;
reg [5:0] sine_out;
wire [5:0] pwm_ddpm0_ddpm_int_all;
reg [5:0] pwm_ddpm0_counter_down0_count;
reg [6:0] pwm_ddpm0_sd1_mod0_delta;
reg [5:0] pwm_ddpm0_sd1_mod0_qerr;
wire [1:0] sine_lut0_in_index_msb2;
reg [4:0] sine_lut0_in_index_pi2;
reg sine_lut0_sign;
wire [4:0] sine_lut0_sine_pi2;
wire [79:0] sine_lut0_sine_lut_pi20_lut_module0_lut_c;
reg pwm_ddpm0_ddpm_int [0:6-1];

assign pwm_ddpm0_ddpm_int_all[5] = pwm_ddpm0_ddpm_int[0];
assign pwm_ddpm0_ddpm_int_all[4] = pwm_ddpm0_ddpm_int[1];
assign pwm_ddpm0_ddpm_int_all[3] = pwm_ddpm0_ddpm_int[2];
assign pwm_ddpm0_ddpm_int_all[2] = pwm_ddpm0_ddpm_int[3];
assign pwm_ddpm0_ddpm_int_all[1] = pwm_ddpm0_ddpm_int[4];
assign pwm_ddpm0_ddpm_int_all[0] = pwm_ddpm0_ddpm_int[5];
assign sine_lut0_sine_lut_pi20_lut_module0_lut_c[80-1:75] = 'b11111;
assign sine_lut0_sine_lut_pi20_lut_module0_lut_c[75-1:70] = 'b11110;
assign sine_lut0_sine_lut_pi20_lut_module0_lut_c[70-1:65] = 'b11110;
assign sine_lut0_sine_lut_pi20_lut_module0_lut_c[65-1:60] = 'b11101;
assign sine_lut0_sine_lut_pi20_lut_module0_lut_c[60-1:55] = 'b11011;
assign sine_lut0_sine_lut_pi20_lut_module0_lut_c[55-1:50] = 'b11010;
assign sine_lut0_sine_lut_pi20_lut_module0_lut_c[50-1:45] = 'b11000;
assign sine_lut0_sine_lut_pi20_lut_module0_lut_c[45-1:40] = 'b10110;
assign sine_lut0_sine_lut_pi20_lut_module0_lut_c[40-1:35] = 'b10100;
assign sine_lut0_sine_lut_pi20_lut_module0_lut_c[35-1:30] = 'b10001;
assign sine_lut0_sine_lut_pi20_lut_module0_lut_c[30-1:25] = 'b01111;
assign sine_lut0_sine_lut_pi20_lut_module0_lut_c[25-1:20] = 'b01100;
assign sine_lut0_sine_lut_pi20_lut_module0_lut_c[20-1:15] = 'b01001;
assign sine_lut0_sine_lut_pi20_lut_module0_lut_c[15-1:10] = 'b00110;
assign sine_lut0_sine_lut_pi20_lut_module0_lut_c[10-1:5] = 'b00011;
assign sine_lut0_sine_lut_pi20_lut_module0_lut_c[5-1:0] = 'b00000;


always @(negedge clk, negedge resetn) begin: BAT52_PWM_DDPM_TOP_PWM_DDPM0_COUNTER_DOWN0_COUNT_PROC
    if (resetn == 0) begin
        pwm_ddpm0_counter_down0_count <= 63;
    end
    else begin
        if ((pwm_ddpm0_counter_down0_count > 0)) begin
            pwm_ddpm0_counter_down0_count <= (pwm_ddpm0_counter_down0_count - 1);
        end
        else begin
            pwm_ddpm0_counter_down0_count <= (64 - 1);
        end
        // pass
    end
end



assign count_out = pwm_ddpm0_counter_down0_count;


always @(inval, count_out) begin: BAT52_PWM_DDPM_TOP_PWM_DDPM0_PWM_PROC
    if ((count_out < inval)) begin
        pwm = 1;
    end
    else begin
        pwm = 0;
    end
    // pass
end


always @(inval, count_out) begin: BAT52_PWM_DDPM_TOP_PWM_DDPM0_DDPM_INT_PROC
    integer bidx;
    for (bidx=0; bidx<6; bidx=bidx+1) begin
        if ((($signed({1'b0, count_out}) & ((2 ** (6 - bidx)) - 1)) == (2 ** ((6 - 1) - bidx)))) begin
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


always @(inval, pwm_ddpm0_sd1_mod0_delta, pwm_ddpm0_sd1_mod0_qerr) begin: BAT52_PWM_DDPM_TOP_PWM_DDPM0_SD1_MOD0_SATURATED_ADDER0_DELTA_PROC
    if (((inval + pwm_ddpm0_sd1_mod0_qerr) > (128 - 1))) begin
        pwm_ddpm0_sd1_mod0_delta = (128 - 1);
    end
    else if (((inval + pwm_ddpm0_sd1_mod0_qerr) < (0 + 1))) begin
        pwm_ddpm0_sd1_mod0_delta = (0 + 1);
    end
    else begin
        pwm_ddpm0_sd1_mod0_delta = (inval + pwm_ddpm0_sd1_mod0_qerr);
    end
end


always @(negedge clk, negedge resetn) begin: BAT52_PWM_DDPM_TOP_PWM_DDPM0_SD1_MOD0_QUANT_PROC
    if (resetn == 0) begin
        pwm_ddpm0_sd1_mod0_qerr <= 0;
    end
    else begin
        pwm_ddpm0_sd1_mod0_qerr[(7 - 1)-1:0] <= pwm_ddpm0_sd1_mod0_delta[(7 - 1)-1:0];
    end
end


always @(negedge clk, negedge resetn) begin: BAT52_PWM_DDPM_TOP_PWM_DDPM0_SD1_MOD0_SD_OUT_PROC
    if (resetn == 0) begin
        sd <= 0;
    end
    else begin
        if (($signed({1'b0, pwm_ddpm0_sd1_mod0_delta}) > (2 ** (7 - 1)))) begin
            sd <= 1;
        end
        else begin
            sd <= 0;
        end
    end
end


always @(count_out) begin: BAT52_PWM_DDPM_TOP_SINE_LUT0_GEN_INDEX_PI2_PROC
    if ((count_out[(6 - 2)] == 0)) begin
        sine_lut0_in_index_pi2[(6 - 1)-1:0] = count_out[(6 - 2)-1:0];
    end
    else begin
        sine_lut0_in_index_pi2[(6 - 1)-1:0] = (15 - count_out[(6 - 2)-1:0]);
    end
end



assign sine_lut0_in_index_msb2 = count_out[6-1:(6 - 2)];


always @(sine_lut0_in_index_msb2) begin: BAT52_PWM_DDPM_TOP_SINE_LUT0_GEN_INDEX_SIGN_PROC
    if (((sine_lut0_in_index_msb2 == 0) || (sine_lut0_in_index_msb2 == 1))) begin
        sine_lut0_sign = 0;
    end
    else begin
        sine_lut0_sign = 1;
    end
end



assign sine_lut0_sine_pi2 = ((sine_lut0_sine_lut_pi20_lut_module0_lut_c >>> (sine_lut0_in_index_pi2 * 5)) & ((2 ** 5) - 1));


always @(sine_lut0_sign, sine_lut0_sine_pi2) begin: BAT52_PWM_DDPM_TOP_SINE_LUT0_GEN_SINE_OUT_PROC
    if ((sine_lut0_sign == 0)) begin
        sine_out = (31 + sine_lut0_sine_pi2);
    end
    else begin
        sine_out = (31 - sine_lut0_sine_pi2);
    end
end


always @(io_in) begin: BAT52_PWM_DDPM_TOP_IN_PROC
    clk = io_in[0];
    resetn = io_in[1];
    inval[6-1:0] = io_in[8-1:2];
end


always @(pwm, sd, sine_out, ddpm) begin: BAT52_PWM_DDPM_TOP_OUT_PROC
    io_out[0] = pwm;
    io_out[1] = ddpm;
    io_out[2] = sd;
    io_out[8-1:3] = sine_out[6-1:1];
end

endmodule
