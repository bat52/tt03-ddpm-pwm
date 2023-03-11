#!/usr/bin/env python3

import sys
# import os
import argparse
# import shutil

# Import math Library
import math 

# NB: this requires installing myHDL from github, as follows
# pip3 install git+https://github.com/myhdl/myhdl.git@master
from myhdl import *

# pip3 install git+https://github.com/bat52/pueda.git@master
from pueda.myhdl import *
from pueda.common import get_clean_work, vcd_view
from pueda.yosys import yosys

from lut import lut_module

NBIT_LUT_PHASE     = 6
NBIT_LUT_AMPLITUDE = 6
TOP_DUT            = 'sine_lut'
TOP_TB             = 'tb_%s' % TOP_DUT

@block
def sine_lut_pi2( nbits_phase = NBIT_LUT_PHASE-2, nbits_amplitude = NBIT_LUT_AMPLITUDE-1,
             in_index = Signal(intbv(0)[NBIT_LUT_PHASE-2:]),
             sine_out = Signal(intbv(0)[NBIT_LUT_AMPLITUDE-2:])
            ):
    
    normf = 2**(nbits_amplitude - 1) - 1

    lut_vals = []                    
    for idx in range(2**nbits_phase):
        sinval_f = math.sin( math.pi*idx/(2**(nbits_phase+1)))
        sinval_i = round(normf * sinval_f)        
        lut_vals.append( sinval_i )
    
    lut_module_i = lut_module(lut_in = in_index, lut_out = sine_out,
                              nbits_in = nbits_phase, nbits_out = nbits_amplitude,
                              values_list = lut_vals)

    return instances()


@block
def sine_lut( nbits_amplitude = NBIT_LUT_AMPLITUDE, nbits_phase = NBIT_LUT_PHASE,
             in_index = Signal(intbv(0)[NBIT_LUT_PHASE:]),
             sine_out = Signal(intbv(0)[NBIT_LUT_AMPLITUDE:])
            ):
    
    ## signals
    in_index_pi2  = Signal(intbv(0)[nbits_phase-1:])
    in_index_msb2 = Signal(intbv(0)[2:])
    sine_pi2      = Signal(intbv(0)[nbits_amplitude-1:])
    sign          = Signal(bool(0))

    ## constants
    pi2           = 2**(nbits_phase-2)-1
    dc            = pi2

    @always_comb
    def gen_index_pi2_proc():
        if in_index[nbits_phase-2] == 0: # [0 - PI/2], [PI - 3/4PI]
            in_index_pi2.next[nbits_phase-1:0] = in_index[nbits_phase-2:0]            
        else: # in_index[nbits-2] == 1: # [PI/2 - PI], [3/4PI - 2PI]
            # index_pi2 = pi2 - in_index[nbits-2:0]
            # print( 'IN_INDEX = %d, PI2 = %d, INDEX_PI2 = %d' % (in_index,pi2,index_pi2) )
            in_index_pi2.next[nbits_phase-1:0] = pi2 - in_index[nbits_phase-2:0]

    @always_comb
    def gen_index_msb2_proc():
        in_index_msb2.next = in_index[nbits_phase:nbits_phase-2]
        
    @always_comb
    def gen_index_sign_proc():
        if (in_index_msb2 == 0) or (in_index_msb2 == 1): # 0 - PI
            sign.next = 0
        else: # (in_index[nbits:nbits-2] == 2) or (in_index[nbits:nbits-2] == 3): #  PI - 2PI
            sign.next = 1

    sine_lut_pi2_i = sine_lut_pi2(nbits_phase = nbits_phase-2, nbits_amplitude = nbits_amplitude-1, 
                                  in_index = in_index_pi2, sine_out = sine_pi2 )

    @always_comb
    def gen_sine_out_proc():
        if sign == 0:
            sine_out.next = dc + sine_pi2
        else: # if sign == 1:
            sine_out.next = dc - sine_pi2

    return instances()

@block
def tb_sine_lut(nbits_amplitude = NBIT_LUT_AMPLITUDE, nbits_phase = NBIT_LUT_PHASE, period = 2, 
                dump_en = False, convert_en = False, synth_en = False,
                work = './'):

    index = Signal(intbv(0)[nbits_phase:])
    sine  = Signal(intbv(0)[nbits_amplitude:])

    sine_i = sine_lut( nbits_amplitude = nbits_amplitude, nbits_phase = nbits_phase, 
                      in_index = index, sine_out = sine )

    if convert_en or synth_en:
        print('Converting myHDL to verilog...')
        sine_i.convert(hdl='Verilog', trace = dump_en, path = work)
        if synth_en:
            synth_out = yosys(top=TOP_DUT, src_dirs = [work], synth_en=synth_en, exclude_files=['%s.v' % TOP_TB])  

    @instance
    def geninput():        
        for val in range(2**nbits_phase):
            # reset pulse
            index.next = val
            yield delay(int(period/2))            
            
    return instances()

def sine_lut_main(nbits_amplitude = NBIT_LUT_AMPLITUDE, nbits_phase = NBIT_LUT_PHASE,
                  dump_en = False, convert_en = False, cosim_en = False, synth_en = False):

    work = get_clean_work('sine', makedir=True)
    os.system('rm *.vcd')

    duration = 2**(nbits_phase)
    tb_i = tb_sine_lut(nbits_amplitude = nbits_amplitude, nbits_phase = nbits_phase,  
                       dump_en = dump_en, convert_en = convert_en, synth_en = synth_en, work = work)

    if not(cosim_en):
        tb_i.config_sim(trace=dump_en)
        tb_i.run_sim(duration=duration)
        if dump_en:
            sim_view()
    else: # cosim_en
        cosim = Simulation( tb_i )
        cosim.run(duration)
        #if dump_en:
        #    cosim_view(nbits = nbits) 
    pass

def sim_view():    
    vcd  = TOP_TB + '.vcd'
    gtkw = TOP_TB + '.gtkw'
    vcd_view(vcd, savefname=gtkw) # , postcmd = ' &')    

def sine_lut_cli(argv=[]):
    parser = argparse.ArgumentParser(description='Sine generator myHDL design')
    # register format options
    
    parser.add_argument("-n", "--nbits",      help="#bits phase resolution", type=int, default = NBIT_LUT_PHASE)
    parser.add_argument("-r", "--resolution", help="#bits amplitude resolution", type=int, default = NBIT_LUT_AMPLITUDE)
    parser.add_argument("-d", "--dump_en",    help="Dump waveforms in simulation.", action='store_true' )
    parser.add_argument("-c", "--convert_en", help="Enable conversion to verilog.", action='store_true' )
    parser.add_argument("-s", "--cosim_en",   help="Enable cosimulation of myhdl TB with verilog IP.", action='store_true' )
    parser.add_argument("-y", "--synth_en",   help="Enable synthesis."            , action='store_true')

    p = parser.parse_args(argv)
    return p

if __name__ == "__main__":
    p = sine_lut_cli(sys.argv[1:])

    sine_lut_main(nbits_phase = p.nbits, nbits_amplitude=p.resolution, 
       convert_en=p.convert_en, dump_en=p.dump_en, cosim_en = p.cosim_en, synth_en = p.synth_en)