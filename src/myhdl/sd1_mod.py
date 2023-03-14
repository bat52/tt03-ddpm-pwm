#!/usr/bin/env python3

import sys
import os
import argparse
from ast import literal_eval
import matplotlib.pyplot as plt
import numpy as np

# NB: this requires installing myHDL from github, as follows
# pip3 install git+https://github.com/myhdl/myhdl.git@master
from myhdl import *

# pip3 install git+https://github.com/bat52/pueda.git@master
from pueda.myhdl import *
from pueda.common import get_clean_work, vcd_view

# https://pypi.org/project/vcdvcd/
from vcdvcd import VCDVCD

from sine_lut import sine_lut, NBIT_SINE_LUT_PHASE, NBIT_SINE_LUT_AMPLITUDE

NBIT_SD = NBIT_SINE_LUT_AMPLITUDE + 2
NBIT_SD_PRESCALER = NBIT_SINE_LUT_PHASE
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
           nbit_prescaler = NBIT_SD_PRESCALER,
           dump_en = False, cosim_en = False, convert_en = False,
           period = 2, duration = 2**NBIT_SINE_LUT_PHASE):    

    clk       = Signal(bool(0))
    resetn    = ResetSignal(bool(0), active=False, isasync=True)

    count_out = Signal(intbv(0)[nbit_in+nbit_prescaler:])
    lut_in  = Signal(intbv(0)[nbit_in:])
    lut_out = Signal(intbv(0)[nbit_out:])

    sd_out = Signal(bool(0))

    sd1_i   = sd1_mod(clk, resetn, nbits = nbit_sd, inval = lut_out, sd_out = sd_out)
    count_i = counter_up(clk, resetn, count_out = count_out, nbits = nbit_in+nbit_prescaler)
    lut_i   = sine_lut( nbits_amplitude = nbit_out, nbits_phase = nbit_in,
                        in_index = lut_in, sine_out = lut_out)
    
    @always_comb
    def lut_in_proc():
        lut_in.next = count_out[nbit_in+nbit_prescaler:nbit_prescaler]
    
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

    nperiods = 5
    duration = nperiods * 2**(NBIT_SINE_LUT_PHASE+NBIT_SD_PRESCALER+1)-1

    tb_i = tb_sd1_mod(
             convert_en = convert_en, dump_en = dump_en, cosim_en = cosim_en,
             work = work, duration = duration) # synth_en=synth_en

    if not(cosim_en):
        tb_i.config_sim(trace=dump_en)
        tb_i.run_sim(duration=duration)
        if dump_en:
            vcd  = SD1_TB_TOP + '.vcd'
            sim_view(vcd)
            # sim_postproc(vcd)
    else: # cosim_en
        cosim = Simulation( tb_i )
        cosim.run(duration)
        if dump_en:
            cosim_view()
    pass

def sim_view(vcd):    
    fname = os.path.splitext(vcd)[0]
    gtkw = fname + '.gtkw'
    # gen_gtkw_ddpm(gtkw, nbits=nbits)
    vcd_view(vcd, savefname=gtkw, block_en=False)
    return vcd

def vcd_tv2list(tv,fmt='dec'):
    time = []
    value = []
    for e in tv:

        if   fmt == 'dec':
            vstr = e[1]
        elif fmt == 'bin':
            vstr = '0b' + str.strip(e[1])
        elif fmt == 'hex':    
            vstr = '0h' + str.strip(e[1])
        else:
            print('unsupported format "%s" !!!' % fmt)
            assert(False)

        value.append(literal_eval(vstr))
        time.append(e[0])
    return {'value':value,'time':time}

def vcd_resample(s, fs=1):

    # generate time series
    tmin = min(s['time'])
    tmax = max(s['time'])
    t = np.arange(tmin,tmax,fs)
    sout = np.interp(t, s['time'], s['value'])
    # sout = f(t)

    return {'value':sout, 'time': t}    

def vcd_get_signal(vcdh,sname,fmt = 'dec', resample_en = False, fs=1e9):
    signal = vcdh[sname]
    # tv is a list of Time/Value delta pairs for this signal.
    s = vcd_tv2list(signal.tv,fmt = fmt)
    if resample_en:
        s = vcd_resample(s)
    return s 

def sim_postproc(fname):
    vcd = VCDVCD(fname)

    # List all human readable signal names.
    # print(vcd.references_to_ids.keys())

    # View all signal data.
    # print(vcd.data)

    # Get a signal by human readable name.
    sd_out  = vcd_get_signal( vcd, SD1_TB_TOP + '.sd_out' ,            resample_en=True)
    lut_out = vcd_get_signal( vcd, SD1_TB_TOP + '.lut_out', fmt='bin', resample_en=True)

    if True:
        plt.figure(1)
        plt.step(sd_out['time'],sd_out['value'])
        plt.xlabel('time [ns]')
        plt.ylabel('sd_out')
        plt.show()

    if True:
        plt.figure(2)
        plt.step(lut_out['time'],lut_out['value'])
        plt.xlabel('time [ns]')
        plt.ylabel('lut_out [LSB]')
        plt.show()

    sdf = np.array(lut_out['value']) 
    sdf = np.fft.fft(sdf)
    sdf = np.absolute(sdf)
    sdf = sdf / np.max(sdf)
    sdf = 20*np.log10(sdf)

    plt.figure(3)
    plt.semilogx(sdf)
    plt.grid(True)
    plt.xlabel('freq')
    plt.ylabel('sd_out [dBc]')
    plt.show()

    pass

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