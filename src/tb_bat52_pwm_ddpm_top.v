module tb_bat52_pwm_ddpm_top;

reg [7:0] io_in;
wire [7:0] io_out;

initial begin
    $from_myhdl(
        io_in
    );
    $to_myhdl(
        io_out
    );
end

bat52_pwm_ddpm_top dut(
    io_in,
    io_out
);

endmodule
