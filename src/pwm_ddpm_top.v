`timescale 1ns/10ps

module bat52_pwm_ddpm_top (
    input [7:0] io_in,
    output [7:0] io_out
);

wire clk;
wire resetn;
wire [5:0] inval;
wire pwm;
wire ddpm;

// inputs
assign clk    =  io_in[0];
assign resetn =  io_in[1];
assign inval  =  io_in[7:2];

// outputs
assign io_out[0] = pwm;
assign io_out[1] = ddpm;
assign io_out[7] = clk; // echo just to show it is alive

pwm_ddpm dut (
    .clk(clk),
    .resetn(resetn),
    .inval(inval),
    .pwm(pwm),
    .ddpm(ddpm) 
    );

endmodule