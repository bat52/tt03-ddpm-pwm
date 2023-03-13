#!/usr/bin/env python3

import sys
import os
import argparse

# NB: this requires installing myHDL from github, as follows
# pip3 install git+https://github.com/myhdl/myhdl.git@master
from myhdl import *

# pip3 install git+https://github.com/bat52/pueda.git@master
from pueda.myhdl import *
from pueda.common import get_clean_work, vcd_view
from pueda.gtkw import gen_gtkw
from pueda.yosys import yosys

from sine_lut import sine_lut, NBIT_SINE_LUT_PHASE, NBIT_SINE_LUT_AMPLITUDE

NBIT_SD = NBIT_SINE_LUT_AMPLITUDE + 2
SD1_TOP = 'sd1_mod'
SD1_TB_TOP = 'tb_' + SD1_TOP

@block
def counter_up(clk, resetn, 
                 count_out = Signal(intbv(0)[4:]),
                 nbits = 4):
    
    count          =  Signal( intbv(0)[nbits:] )

    @always_seq(clk.negedge, reset=resetn)
    def count_proc():
        if count < count.max-1:
            count.next = count + 1            
        else:
            count.next = count.min
        pass

    @always_comb
    def count_out_proc():
        count_out.next = count

    return instances()

@block
def saturated_adder(a, b, out):

    @always_comb
    def delta_proc():
        if (a + b) > out.max-1:
            out.next = out.max-1
        elif (a + b) < out.min+1:
            out.next  = out.min+1
        else:
            out.next = a + b

    return instances()

@block
def sd1_mod(clk, resetn, nbits = NBIT_SD, inval = Signal(intbv(0)[NBIT_SD:]), sd_out = Signal(bool(0))):

    delta      = Signal( intbv(0)[nbits:] )
    qerr       = Signal( intbv(0)[nbits-1:] )

    delta_i = saturated_adder( inval,  qerr, delta)

    @always_seq(clk.negedge, reset=resetn)
    #@always_comb
    def quant_proc():        
        qerr.next[nbits-1:0] = delta[nbits-1:0]

    @always_seq(clk.negedge, reset=resetn)
    def sd_out_proc():        
        if delta > 2**(nbits-1):
            sd_out.next = 1
        else:
            sd_out.next = 0
    
    return instances()

@block
def tb_sd1_mod(work = './',
           nbit_sd = NBIT_SD,
           nbit_in = NBIT_SINE_LUT_PHASE, nbit_out = NBIT_SINE_LUT_AMPLITUDE,
           dump_en = False, cosim_en = False, convert_en = False,
           period = 2, duration = 2**NBIT_SINE_LUT_PHASE):    

    clk       = Signal(bool(0))
    resetn    = ResetSignal(bool(0), active=False, isasync=True)
    
    lut_in  = Signal(intbv(0)[nbit_in:])
    lut_out = Signal(intbv(0)[nbit_out:])

    sd_out = Signal(bool(0))

    sd1_i   = sd1_mod(clk, resetn, nbits = nbit_sd, inval = lut_out, sd_out = sd_out)
    count_i = counter_up(clk, resetn, count_out = lut_in, nbits = nbit_in)
    lut_i   = sine_lut( nbits_amplitude = nbit_out, nbits_phase = nbit_in,
                        in_index = lut_in, sine_out = lut_out)
    
    @instance
    def genclk():
        while True:
            clk.next = not clk
            yield delay(int(period/2))

    @instance
    def genreset():        
        resetn.next = 0
        yield delay(int(period/2))            
        # set input and exit reset
        resetn.next = 1
        yield delay(int(period/2))  

    # convert to check resulting verilog
    if convert_en or cosim_en:
        sd1_i.convert(hdl='Verilog', path = work, trace = dump_en)

    if cosim_en:
        topmodule=SD1_TB_TOP
        topfile  = topmodule + '.v'
        src_dirs=[work]

        ports={'clk':clk, 'resetn':resetn, 'inval': lut_out, 'sd_out' : sd_out}
        simname='sd1_sim'        

        sd1_h = myhdl_cosim_wrapper(topfile=topfile, topmodule=topmodule, src_dirs=src_dirs, simname=simname, duration=duration)
        # overwrite lut_i
        sd1_i = sd1_h.dut_instance(ports=ports)

    return instances()

def test_sd1_main( convert_en = False, dump_en = True, 
              cosim_en = False, 
              synth_en = False):
    
    work = get_clean_work('sd1', makedir=True)
    os.system('rm *.vcd')

    duration = 2**(NBIT_SINE_LUT_PHASE+1)-1

    tb_i = tb_sd1_mod(
             convert_en = convert_en, dump_en = dump_en, cosim_en = cosim_en,
             work = work, duration = duration) # synth_en=synth_en

    if not(cosim_en):
        tb_i.config_sim(trace=dump_en)
        tb_i.run_sim(duration=duration)
        if dump_en:
            sim_view()
    else: # cosim_en
        cosim = Simulation( tb_i )
        cosim.run(duration)
        if dump_en:
            cosim_view()
    pass

def sim_view(nbits = 4):    
    vcd  = SD1_TB_TOP + '.vcd'
    gtkw = SD1_TB_TOP +'.gtkw'
    # gen_gtkw_ddpm(gtkw, nbits=nbits)
    vcd_view(vcd, savefname=gtkw)

def cosim_view():    
    vcd  = os.path.join( '../work_icarus', SD1_TOP + '.vcd')
    gtkw = os.path.join( '../'           , SD1_TOP + '_cosim.gtkw')
    vcd_view(vcd, savefname=gtkw)

def sd1_cli(argv=[]):
    parser = argparse.ArgumentParser(description='1st order sigma delta myHDL design')
    # register format options
    
    parser.add_argument("-d", "--dump_en",    help="Dump waveforms in simulation.", action='store_true' )
    parser.add_argument("-c", "--convert_en", help="Enable conversion to verilog.", action='store_true' )
    parser.add_argument("-s", "--cosim_en",   help="Enable cosimulation of myhdl TB with verilog IP.", action='store_true' )
    # parser.add_argument("-y", "--synth_en",   help="Enable synthesis."            , action='store_true')

    p = parser.parse_args(argv)
    return p

if __name__ == "__main__":
    p = sd1_cli(sys.argv[1:])

    test_sd1_main(  convert_en = p.convert_en, 
                    dump_en    = p.dump_en, 
                    cosim_en   = p.cosim_en, 
                    # synth_en   = p.synth_en
                    )