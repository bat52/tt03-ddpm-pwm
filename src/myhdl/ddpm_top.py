#!/usr/bin/env python3

import sys
import os
import argparse
import filecmp

# NB: this requires installing myHDL from github, as follows
# pip3 install git+https://github.com/myhdl/myhdl.git@master
from myhdl import *

# pip3 install git+https://github.com/bat52/pueda.git@master
from pueda.myhdl import *
from pueda.common import get_clean_work
from pueda.gtkw import gen_gtkw

from ddpm import pwm_ddpm, pwm_check
from sine_lut import sine_lut

NBIT_PWM   = 6
TOP_DUT    = 'bat52_pwm_ddpm_top'
TOP_TB     = 'tb_%s' % TOP_DUT

@block
def bat52_pwm_ddpm_top( io_in, io_out ):
    clk       = Signal(bool(0))
    resetn    = ResetSignal(bool(0), active=False, isasync=True)
    inval     = Signal(intbv(0)[NBIT_PWM:]) 

    pwm       = Signal(bool(0))
    ddpm      = Signal(bool(0))
    count_out = Signal(intbv(0)[NBIT_PWM:])
    sine_out  = Signal(intbv(0)[NBIT_PWM:])
    
    pwm_ddpm_i = pwm_ddpm(clk = clk, resetn = resetn, inval = inval, 
             pwm = pwm, ddpm   = ddpm, 
             nbits = NBIT_PWM, ddpm_en = True,
             count_out = count_out)
    
    sine_lut_i = sine_lut(nbits_amplitude = NBIT_PWM, nbits_phase = NBIT_PWM,
             in_index = count_out, sine_out = sine_out)
    
    @always_comb
    def in_proc():
        clk.next = io_in[0]
        resetn.next = io_in[1]
        inval.next[6:0] = io_in[8:2]    # one extra bit because myHDL is always signed

    @always_comb
    def out_proc():
        io_out.next[0] = pwm
        io_out.next[1] = ddpm
        io_out.next[8:2] = sine_out[6:0]

    return instances()

"""
def tt_top_gen(dump_en = True):
    work = get_clean_work('tt_top', makedir=True)

    # generate TT top
    top_i  = bat52_pwm_ddpm_top( Signal(intbv(0)[8:]), Signal(intbv(0)[8:]) )
    top_i.convert(hdl='Verilog', trace = dump_en, path = work)

    # copy generated files to top
    os.system('cp %s/* ../' % work)
    
    pass
    # return instances()
"""
    
@block
def tb_bat52_pwm_ddpm_top(period = 10, nbits = NBIT_PWM, convert_en = False, work = './',
       pwm_cycles_per_code = 4, cosim_en = False, dump_en = True, 
       top_gen = False, top_compare = False):
    
    inval     = Signal(intbv(0)[nbits:])
    pwm_out   = Signal(bool(0))
    ddpm_out  = Signal(bool(0))
    resetn    = ResetSignal(bool(0), active=False, isasync=True)
    clk       = Signal(bool(0))
    duration  = (2**nbits) * pwm_cycles_per_code * int(period)
    count_out = Signal(intbv(0)[nbits:])

    io_in     = Signal(modbv(0)[8:]) 
    io_out    = Signal(modbv(0)[8:]) 

    pwm_i  = bat52_pwm_ddpm_top( io_in, io_out )

    @always_comb
    def io_proc():
        io_in.next[0] = clk
        io_in.next[1] = resetn
        io_in.next[8:2] = inval[NBIT_PWM:0]
        pwm_out.next = io_out[0]
        ddpm_out.next = io_out[1]
        count_out.next = io_out[8:2]

    # checker instances
    pwm_c  = pwm_check(clk,resetn, nbits, inval, pwm_out,  'PWM')    
    ddpm_c = pwm_check(clk,resetn, nbits, inval, ddpm_out, 'DDPM', posedge_en = False)    

    if convert_en or cosim_en or top_compare:
        pwm_i.convert(hdl='Verilog', trace = dump_en, path = work)
        if top_compare:
            top_v = TOP_DUT + '.v'

            assert( filecmp.cmp(os.path.join(work,top_v), os.path.join('../',top_v)) == 0 )
        if top_gen:
            os.system('cp %s/* ../' % work)

    if cosim_en:
        topmodule = TOP_TB
        topfile  = topmodule + '.v'        
        src_dirs=[work]

        ports={'io_in': io_in, 'io_out': io_out}
        simname='ddpm'        

        pwm_h = myhdl_cosim_wrapper(topfile=topfile, topmodule=topmodule, src_dirs=src_dirs, simname=simname, duration=duration)
        # overwrite pwm_i
        pwm_i = pwm_h.dut_instance(ports=ports)

    @instance
    def genclk():
        while True:
            clk.next = not clk
            yield delay(int(period/2))
    
    @instance
    def geninput():        
        for val in range(2**nbits):
            # reset pulse
            inval.next = val
            resetn.next = 0
            yield delay(int(period/2))            
            # set input and exit reset
            resetn.next = 1
            yield delay(int(period/2))            

            # wait for a full cycle
            yield delay( duration )

    return instances()

def bat52_pwm_ddpm_top_tb_test_main(period = 10, convert_en = False, dump_en = True, 
              pwm_cycles_per_code = 3, cosim_en = False,
              top_gen = False, top_compare = False):
    
    work = get_clean_work('ddpm', makedir=True)    
    os.system('rm *.vcd')

    tb_i = tb_bat52_pwm_ddpm_top(period = period,
             convert_en = convert_en, dump_en = dump_en, cosim_en = cosim_en,
             pwm_cycles_per_code = pwm_cycles_per_code, work = work,
             top_gen = top_gen, top_compare = top_compare)
    
    nbits = NBIT_PWM
    pwmcycle = 2**nbits
    daccycle = 2**nbits * pwmcycle    
    duration = pwm_cycles_per_code * daccycle * period

    if not(cosim_en):
        tb_i.config_sim(trace=dump_en)
        tb_i.run_sim(duration=duration)
        if dump_en:
            sim_view(nbits = nbits)
    else: # cosim_en
        cosim = Simulation( tb_i )
        cosim.run(duration)
        if dump_en:
            cosim_view(nbits = nbits)        

    pass

def sim_view(nbits = 4):    
    vcd  = '%s.vcd' % TOP_TB
    gtkw = '%s.gtkw' % TOP_TB
    gen_gtkw_ddpm(gtkw, nbits=nbits)
    vcd_view(vcd, savefname=gtkw)

def cosim_view(nbits = 4):    
    vcd  = '../work_icarus/%s.vcd' % TOP_DUT
    gtkw = '%s.gtkw' % TOP_DUT
    gen_gtkw_ddpm_cosim(fname = gtkw, nbits = nbits)
    vcd_view(vcd, savefname=gtkw, block_en=False)     

def gen_gtkw_ddpm(fname = 'tb.gtkw', nbits = 4):

    groups = []

    # pwm mod
    groups.append(
        {
        'gname'            : '%s.' % TOP_TB,
        'bit_signals'      : ['clk', 'resetn', 'pwm_out'],
        'multibit_signals' : ['inval', 'count_out']
        }
    )    

    for pidx in range(2):
        # pwm check
        groups.append(
            {
            'gname'            : '%s.pwm_check%d.' % (TOP_TB, pidx),
            'bit_signals'      : ['clk', 'resetn', 'pwm_o', 'pwm_d_valid', 'pwm_error'],
            'multibit_signals' : ['pwm_i', 'pwm_d', 'pwdem%d.count' % pidx]
            }
        )

    gen_gtkw(fname = fname, nbits = nbits, groups = groups)

    pass

def gen_gtkw_ddpm_cosim(fname = 'tb.gtkw', nbits = 4):

    groups = []

    # pwm mod
    groups.append(
        {
        'gname'            : '%s.dut.' % TOP_TB, 
        'bit_signals'      : ['clk', 'resetn', 'pwm','ddpm'],
        'multibit_signals' : ['inval', 'count', 'ddpm_int_all']
        }
    )    

    gen_gtkw(fname = fname, nbits = nbits, groups = groups)

    pass

def cli(argv=[]):
    parser = argparse.ArgumentParser(description='DDPM/PWM myHDL TOP design')
    # register format options
    
    parser.add_argument("-d", "--dump_en",    help="Dump waveforms in simulation.", action='store_true' )
    parser.add_argument("-c", "--convert_en", help="Enable conversion to verilog.", action='store_true' )
    parser.add_argument("-s", "--cosim_en",   help="Enable cosimulation of myhdl TB with verilog IP.", action='store_true' )
    parser.add_argument("-t", "--top_gen",    help="Generate TinyTapeout top and TB." , action='store_true')
    parser.add_argument("-m", "--top_compare",help="Compared generated top and TinyTapeout top." , action='store_true')

    p = parser.parse_args(argv)
    return p

if __name__ == "__main__":
    p = cli(sys.argv[1:])

    # if p.top_gen:
    #    tt_top_gen()

    bat52_pwm_ddpm_top_tb_test_main( convert_en=p.convert_en, dump_en=p.dump_en, cosim_en = p.cosim_en, 
                                    top_gen = p.top_gen, top_compare = p.top_compare)