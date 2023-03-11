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
# from pueda.common import get_clean_work, vcd_view
# from pueda.gtkw import gen_gtkw

NBIT_LUT = 6

@block
def sine_lut_pi2( nbits = NBIT_LUT-2, 
             in_index = Signal(intbv(0)[NBIT_LUT-2:]),
             sine_out = Signal(intbv(0)[NBIT_LUT-2:])
            ):
    
    lut = []
    normf = 2**(nbits - 1) - 1
                
    for idx in range(2**nbits):
        sinval_f = math.sin( math.pi*idx/(2**nbits))
        sinval_i = round(normf * sinval_f)
        lut.append( 
            Signal( 
                    intbv( sinval_i )[nbits:]
                )
        )

    @always_comb
    def lut_pi4():
        sine_out.next = lut[in_index]

    return instances()


@block
def sine_lut( nbits = NBIT_LUT, 
             in_index = Signal(intbv(0)[NBIT_LUT:]),
             sine_out = Signal(intbv(0)[NBIT_LUT:])
            ):

    in_index_pi2  = Signal(intbv(0)[nbits-1:])
    in_index_msb2 = Signal(intbv(0)[2:])
    sine_pi2      = Signal(intbv(0)[nbits-1:])
    # pi2           = Signal(intbv(2**(nbits-2)-1)[nbits-2:])
    pi2           = 2**(nbits-2)-1
    dc            = Signal(intbv(2**(nbits-2)-1)[nbits-2:])
    sign          = Signal(bool(0))

    @always_comb
    def gen_index_pi2_proc():
        if in_index[nbits-2] == 0: # [0 - PI/2], [PI - 3/4PI]
            in_index_pi2.next[nbits-1:0] = in_index[nbits-2:0]            
        else: # in_index[nbits-2] == 1: # [PI/2 - PI], [3/4PI - 2PI]
            # index_pi2 = pi2 - in_index[nbits-2:0]
            # print( 'IN_INDEX = %d, PI2 = %d, INDEX_PI2 = %d' % (in_index,pi2,index_pi2) )
            in_index_pi2.next[nbits-1:0] = pi2 - in_index[nbits-2:0]

    @always_comb
    def gen_index_msb2_proc():
        in_index_msb2.next = in_index >> (nbits - 2) # in_index[nbits:nbits-2]
        
    @always_comb
    def gen_index_sign_proc():
        if (in_index_msb2 == 0) or (in_index_msb2 == 1): # 0 - PI
            sign.next = 0
        else: # (in_index[nbits:nbits-2] == 2) or (in_index[nbits:nbits-2] == 3): #  PI - 2PI
            sign.next = 1

    sine_lut_pi2_i = sine_lut_pi2(nbits = nbits-1, in_index = in_index_pi2, sine_out = sine_pi2 )

    @always_comb
    def gen_sine_out_proc():
        if sign == 0:
            sine_out.next = dc + sine_pi2
        else: # if sign == 1:
            sine_out.next = dc - sine_pi2

    return instances()

@block
def sine_lut_tb(nbits = NBIT_LUT, period = 2):

    index = Signal(intbv(0)[nbits:])
    sine  = Signal(intbv(0)[nbits:])

    sine_i = sine_lut( nbits = nbits, in_index = index, sine_out = sine )

    @instance
    def geninput():        
        for val in range(2**nbits):
            # reset pulse
            index.next = val
            yield delay(int(period/2))            
            
    return instances()

def sine_lut_main(nbits = 6, dump_en = False, convert_en = False, cosim_en = False, synth_en = False):

    # work = get_clean_work('sine', makedir=True)
    os.system('rm *.vcd')

    duration = 2**(nbits+1)
    tb_i = sine_lut_tb()

    if not(cosim_en):
        tb_i.config_sim(trace=dump_en)
        tb_i.run_sim(duration=duration)
        if dump_en:
            sim_view(nbits = nbits)
    else: # cosim_en
        cosim = Simulation( tb_i )
        cosim.run(duration)
        #if dump_en:
        #    cosim_view(nbits = nbits) 
    pass

def sim_view(nbits = NBIT_LUT):    
    vcd  = 'sine_lut_tb.vcd'
    gtkw = 'sine_lut_tb.gtkw'
    vcd_view(vcd, savefname=gtkw)    

def sine_lut_cli(argv=[]):
    parser = argparse.ArgumentParser(description='Sine generator myHDL design')
    # register format options
    
    parser.add_argument("-n", "--nbits",      help="#bits ", type=int, default = NBIT_LUT)
    parser.add_argument("-d", "--dump_en",    help="Dump waveforms in simulation.", action='store_true' )
    parser.add_argument("-c", "--convert_en", help="Enable conversion to verilog.", action='store_true' )
    parser.add_argument("-s", "--cosim_en",   help="Enable cosimulation of myhdl TB with verilog IP.", action='store_true' )
    parser.add_argument("-y", "--synth_en",   help="Enable synthesis."            , action='store_true')

    p = parser.parse_args(argv)
    return p

if __name__ == "__main__":
    p = sine_lut_cli(sys.argv[1:])

    sine_lut_main(nbits = p.nbits, 
       convert_en=p.convert_en, dump_en=p.dump_en, cosim_en = p.cosim_en, synth_en = p.synth_en)