#!/usr/bin/env python3

import sys
import os
import argparse
import shutil

# NB: this requires installing myHDL from github, as follows
# pip3 install git+https://github.com/myhdl/myhdl.git@master
from myhdl import *

# pip3 install git+https://github.com/bat52/pueda.git@master
from pueda.myhdl import *
from pueda.common import get_clean_work, vcd_view
from pueda.gtkw import gen_gtkw
from pueda.yosys import yosys

from sd1_mod import sd1_mod

@block
def counter_down(clk, resetn, 
                 count_out = Signal(intbv(0)[4:]),
                 nbits = 4):
    
    count          =  Signal( intbv(2**nbits - 1)[nbits:] )

    @always_seq(clk.negedge, reset=resetn)
    def count_proc():
        if count > count.min:
            count.next = count - 1            
        else:
            count.next = count.max - 1
        pass

    @always_comb
    def count_out_proc():
        count_out.next = count

    return instances()

@block
def pwm_ddpm(clk, resetn, nbits = 4, 
             inval = Signal(intbv(0)[4:]), pwm=Signal(bool(0)), 
             ddpm = Signal(bool(0)), ddpm_en = True,
             sd_out = Signal(bool(0)), sd_en = True,
             count_out = Signal(intbv(0)[4:])):
    
    counter_i = counter_down(clk, resetn, 
                 count_out = count_out,
                 nbits = nbits)
    
    if ddpm_en:
        # ddpm signals 
        ddpm_int       = [Signal( bool(0) ) for _ in range(nbits) ]
        ddpm_int_all   = ConcatSignal(*ddpm_int)

    @always_comb
    def pwm_proc():
        if count_out < inval:
            pwm.next = 1
        else:
            pwm.next = 0
        pass

    if ddpm_en:
        @always_comb
        def ddpm_int_proc():
            for bidx in range(nbits):
                if (count_out & (2**(nbits-bidx)-1) ) == 2**(nbits-1-bidx):
                    ddpm_int[bidx].next = inval[bidx]
                else:
                    ddpm_int[bidx].next = 0
                pass

        @always_comb
        def ddpm_proc():
            if ddpm_int_all > 0:
                ddpm.next = 1
            else:
                ddpm.next = 0

    if sd_en:
        sd_i = sd1_mod(clk, resetn, nbits = nbits+1, inval = inval, sd_out = sd_out)

    return instances()

@block
def pwdem(clk, resetn, nbits = 4, inval=Signal(0), outval = Signal(intbv(0)[4:]) , valid = Signal(bool(0)), posedge_en = True):

    count = Signal( intbv(0)[nbits:] )

    if posedge_en:
        edge = clk.posedge
    else:
        edge = clk.negedge

    @always_seq(edge, reset=resetn)
    def count_proc():
        if not resetn:
            count.next = count.min
        else:
            if count >= count.max-1:
                count.next = count.min
            else:
                count.next = count + 1
        pass
    
    @always_seq(edge, reset=resetn)
    def out_proc():
        if not resetn:
            outval.next = 0
        else:
            if count == count.min:
                outval.next = inval
            else:
                if count < count.max - 1:
                    outval.next = outval + inval
                else:
                    outval.next = 0
        pass

    @always_comb
    def valid_proc():
        if count == count.max - 1:
            valid.next = 1
        else:
            valid.next = 0

    return instances()

@block
def pwm_check(clk, resetn, nbits, pwm_i, pwm_o, inst_name = '', posedge_en = True, tolerance = 1):

    pwm_d = Signal(intbv(0)[nbits:]) # demodulated pwm signal
    pwm_d_valid = Signal(bool(0))    # demodulated pwm signal valid (end of pwm cycle)
    pwm_error = Signal(bool(0))      # demodulated pwm signal wrong
    clk_valid = Signal(bool(0))
    input_valid = Signal(bool(1))    
    check_valid = Signal(bool(0))
    pwm_delta = Signal(intbv(0)[nbits:]) # pwm_in - pwm_out

    pwm_i_d = Signal(intbv(0)[nbits:]) # delayed input signal

    # pwm demodulator
    pwd_i = pwdem(clk,resetn, nbits, pwm_o, pwm_d, pwm_d_valid, posedge_en = posedge_en)

    if posedge_en:
        edge = clk.posedge
    else:
        edge = clk.negedge

    @always_comb
    def clk_valid_proc():
        if posedge_en:
            clk_valid.next = not(clk)
        else:
            clk_valid.next = clk

    @always_comb
    def check_valid_proc():
        if pwm_d_valid and resetn and clk_valid and input_valid:
            check_valid.next = 1
        else:
            check_valid.next = 0

    # @always_comb
    @always_seq(edge,reset=resetn)
    def check_proc():
        if check_valid:
            if pwm_delta <= tolerance:
                pwm_error.next = 0
            else:
                pwm_error.next = 1
                print('time: %d [timesteps], INSTANCE: %s ERROR!!! INPUT: %d, PWM: %d' % (now(), inst_name, pwm_i, pwm_d))
        else:
            pwm_error.next = 0

    @always_comb
    def pwm_delta_proc():
        if pwm_i > pwm_d:
            pwm_delta.next = pwm_i - pwm_d
        else:
            pwm_delta.next = pwm_d - pwm_i

    @always_seq(edge,reset=resetn)
    def pwm_i_d_proc():
        pwm_i_d.next = pwm_i

    @always_seq(edge,reset=resetn)
    def input_valid_proc():
        if not(resetn):
            input_valid.next = 1
        elif pwm_d_valid:
            input_valid.next = 1
        elif not(pwm_i == pwm_i_d):
            # input value changed during a cycle
            input_valid.next = 0
        
    return instances()

@block
def tb(period = 10, nbits = 4, convert_en = False, work = './',
       pwm_cycles_per_code = 4, cosim_en = False, 
       ddpm_en = False, sd_en = False,
       dump_en = True, synth_en = False):
    
    inval     = Signal(intbv(2**(nbits-1), 0, 2**nbits -1 )[nbits:])
    pwm_out   = Signal(bool(0))
    ddpm_out  = Signal(bool(0))
    sd_out    = Signal(bool(0))
    resetn    = ResetSignal(bool(0), active=False, isasync=True)
    clk       = Signal(bool(0))
    duration  = (2**nbits) * pwm_cycles_per_code * int(period)
    count_out = Signal(intbv(0)[nbits:])

    # if not(cosim_en):
    pwm_i  = pwm_ddpm(      clk,resetn, nbits, inval, pwm_out,  ddpm_out, 
                             ddpm_en = ddpm_en, sd_en = sd_en, sd_out = sd_out,
                             count_out = count_out)
    
    if convert_en or cosim_en or synth_en:
        pwm_i.convert(hdl='Verilog', trace = dump_en, path = work)
        if synth_en:
            synth_out = yosys(top='pwm_ddpm', src_dirs = [work], synth_en=synth_en, exclude_files=['tb_pwm_ddpm.v'])  

    # else:
    if cosim_en:
        topmodule='tb_pwm_ddpm'
        topfile  = topmodule + '.v'

        if synth_en:
            # create cosim work
            cosim_synth_work = get_clean_work('cosim_synth', makedir=True)

            # copy synth ouput            
            synth_file     = os.path.basename(synth_out['synth'])            
            synth_target   = os.path.join(cosim_synth_work ,synth_file)
            shutil.copyfile(synth_out['synth'], synth_target)

            # copy tb
            tb_fullfile = os.path.join(work            ,topfile)
            tb_target   = os.path.join(cosim_synth_work,topfile)
            shutil.copyfile(tb_fullfile, tb_target )

            src_dirs=[cosim_synth_work]
        else:
            src_dirs=[work]

        ports={'clk':clk, 'resetn':resetn, 'inval':inval, 'pwm': pwm_out,  'ddpm':ddpm_out, 'count_out' : count_out, 'sd_out': sd_out}
        simname='ddpm'        

        pwm_h = myhdl_cosim_wrapper(topfile=topfile, topmodule=topmodule, src_dirs=src_dirs, simname=simname, duration=duration)
        # overwrite pwm_i
        pwm_i = pwm_h.dut_instance(ports=ports)

    # checker instances
    pwm_c  = pwm_check(clk,resetn, nbits, inval, pwm_out,  'PWM')    
    if ddpm_en:
        ddpm_c = pwm_check(clk,resetn, nbits, inval, ddpm_out, 'DDPM', posedge_en = False)    

    # if sd_en: # sd cannot be checked like this
    #    sd_c = pwm_check(clk,resetn, nbits, inval, sd_out, 'SD')  

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

def gen_gtkw_ddpm(fname = 'tb.gtkw', nbits = 4):

    groups = []

    # pwm mod
    groups.append(
        {
        'gname'            : 'tb.pwm_ddpm0.',
        'bit_signals'      : ['clk', 'resetn', 'pwm','ddpm','sd_out'],
        'multibit_signals' : ['inval'] #, 'count']
        }
    )    

    for pidx in range(2):
        # pwm check
        groups.append(
            {
            'gname'            : 'tb.pwm_check%d.' % pidx,
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
        'gname'            : 'tb_pwm_ddpm.dut.',
        'bit_signals'      : ['clk', 'resetn', 'pwm','ddpm','sd_out'],
        'multibit_signals' : ['inval', 'count', 'ddpm_int_all']
        }
    )    

    gen_gtkw(fname = fname, nbits = nbits, groups = groups)

    pass

def sim_view(nbits = 4):    
    vcd  = 'tb.vcd'
    gtkw = 'tb.gtkw'
    gen_gtkw_ddpm(gtkw, nbits=nbits)
    vcd_view(vcd, savefname=gtkw)

def cosim_view(nbits = 4):    
    vcd  = '../work_icarus/pwm_ddpm.vcd'
    gtkw = 'dut.gtkw' 
    gen_gtkw_ddpm_cosim(fname = gtkw, nbits = nbits)
    vcd_view(vcd, savefname=gtkw, options=' -o ') # , block_en=False)    

def test_main(period = 10, nbits=4, convert_en = False, dump_en = True, 
              pwm_cycles_per_code = 3, 
              ddpm_en = False, sd_en = False,
              cosim_en = False, synth_en = False):
    
    work = get_clean_work('ddpm', makedir=True)
    os.system('rm *.vcd')

    tb_i = tb(period, nbits, 
             convert_en = convert_en, ddpm_en = ddpm_en, sd_en = sd_en, dump_en = dump_en, cosim_en = cosim_en,
             pwm_cycles_per_code = pwm_cycles_per_code, work = work, synth_en=synth_en)
    
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

def cli(argv=[]):
    parser = argparse.ArgumentParser(description='DDPM/PWM myHDL design')
    # register format options
    
    parser.add_argument("-n", "--nbits",      help="#bits ", type=int, default = 6)
    parser.add_argument("-d", "--dump_en",    help="Dump waveforms in simulation.", action='store_true' )
    parser.add_argument("-c", "--convert_en", help="Enable conversion to verilog.", action='store_true' )
    parser.add_argument("-p", "--ddpm_en",    help="Disable DDPM output."         , action='store_false', default = True )
    parser.add_argument("-z", "--sd_en",      help="Disable sigma-delta output."  , action='store_false', default = True )
    parser.add_argument("-s", "--cosim_en",   help="Enable cosimulation of myhdl TB with verilog IP.", action='store_true' )
    parser.add_argument("-y", "--synth_en",   help="Enable synthesis."            , action='store_true')
    # parser.add_argument("-t", "--top_gen",    help="Generate TT3 top and TB."     , action='store_true')

    p = parser.parse_args(argv)
    return p

if __name__ == "__main__":
    p = cli(sys.argv[1:])

    test_main(nbits = p.nbits, 
       convert_en=p.convert_en, dump_en=p.dump_en, 
       ddpm_en = p.ddpm_en, sd_en = p.sd_en,
       cosim_en = p.cosim_en, synth_en = p.synth_en)