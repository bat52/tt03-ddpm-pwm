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

@block
def pwm_ddpm(clk, resetn, nbits = 4, inval = Signal(intbv(0)[4:]), pwm=Signal(bool(0)), ddpm = Signal(bool(0)), ddpm_en = True):
    count          =  Signal( intbv(2**nbits - 1)[nbits:] )
    
    if ddpm_en:
        # ddpm signals 
        ddpm_int       = [Signal( bool(0) ) for _ in range(nbits) ]
        ddpm_int_all   = ConcatSignal(*ddpm_int)

    @always_seq(clk.negedge, reset=resetn)
    def count_proc():
        if count > count.min:
            count.next = count - 1            
        else:
            count.next = count.max - 1
        pass

    @always_comb
    def pwm_proc():
        if count < inval:
            pwm.next = 1
        else:
            pwm.next = 0
        pass

    if ddpm_en:
        @always_comb
        def ddpm_int_proc():
            for bidx in range(nbits):
                if (count & (2**(nbits-bidx)-1) ) == 2**(nbits-1-bidx):
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
def pwm_check(clk, resetn, nbits, pwm_i, pwm_o, inst_name = '', posedge_en = True):

    pwm_d = Signal(intbv(0)[nbits:])
    pwm_d_valid = Signal(bool(0))
    pwm_error = Signal(bool(0))
    clk_valid = Signal(bool(0))

    pwd_i = pwdem(clk,resetn, nbits, pwm_o, pwm_d, pwm_d_valid, posedge_en = posedge_en)

    @always_comb
    def clk_valid_proc():
        if posedge_en:
            clk_valid.next = not(clk)
        else:
            clk_valid.next = clk

    @always_comb
    # @always_seq(clk.posedge,reset=resetn)
    def check():
        if pwm_d_valid and resetn and clk_valid:
            if pwm_i == pwm_d:
                pwm_error.next = 0
            else: #if not(pwm_i == pwm_d):
                pwm_error.next = 1
                print('time: %d [timesteps], INSTANCE: %s ERROR!!! INPUT: %d, PWM: %d' % (now(), inst_name, pwm_i, pwm_d))
        else:
            pwm_error.next = 0

    return instances()

@block
def tb(period = 10, nbits = 4, convert_en = False, work = './',
       pwm_cycles_per_code = 4, cosim_en = False, ddpm_en = False, dump_en = True, synth_en = False):
    
    inval    = Signal(intbv(2**(nbits-1), 0, 2**nbits -1 )[nbits:])
    pwm_out  = Signal(bool(0))
    ddpm_out = Signal(bool(0))
    resetn   = ResetSignal(bool(0), active=False, isasync=True)
    clk      = Signal(bool(0))
    duration = (2**nbits) * pwm_cycles_per_code * int(period)

    # if not(cosim_en):
    pwm_i  = pwm_ddpm(      clk,resetn, nbits, inval, pwm_out,  ddpm_out, ddpm_en = ddpm_en)
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

        ports={'clk':clk, 'resetn':resetn, 'inval':inval, 'pwm': pwm_out,  'ddpm':ddpm_out}
        simname='ddpm'        

        pwm_h = myhdl_cosim_wrapper(topfile=topfile, topmodule=topmodule, src_dirs=src_dirs, simname=simname, duration=duration)
        # overwrite pwm_i
        pwm_i = pwm_h.dut_instance(ports=ports)

    # checker instances
    pwm_c  = pwm_check(clk,resetn, nbits, inval, pwm_out,  'PWM')    
    if ddpm_en:
        ddpm_c = pwm_check(clk,resetn, nbits, inval, ddpm_out, 'DDPM', posedge_en = False)    

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
        'gname'            : 'tb.pwm.',
        'bit_signals'      : ['clk', 'resetn', 'pwm_o'],
        'multibit_signals' : ['inval', 'count']
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
        'bit_signals'      : ['clk', 'resetn', 'pwm','ddpm'],
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
    vcd_view(vcd, savefname=gtkw)    

def test_main(period = 10, nbits=4, convert_en = False, dump_en = True, 
              pwm_cycles_per_code = 3, ddpm_en = False, cosim_en = False, 
              synth_en = False):
    
    work = get_clean_work('ddpm', makedir=True)
    os.system('rm *.vcd')

    tb_i = tb(period, nbits, 
             convert_en = convert_en, ddpm_en = ddpm_en, dump_en = dump_en, cosim_en = cosim_en,
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
    
    parser.add_argument("-n", "--nbits",      help="#bits ", type=int, default = 4)
    parser.add_argument("-d", "--dump_en",    help="Dump waveforms in simulation.", action='store_true' )
    parser.add_argument("-c", "--convert_en", help="Enable conversion to verilog.", action='store_true' )
    parser.add_argument("-p", "--ddpm_en",    help="Disable DDPM output."         , action='store_false', default = True )
    parser.add_argument("-s", "--cosim_en",   help="Enable cosimulation of myhdl TB with verilog IP.", action='store_true' )
    parser.add_argument("-y", "--synth_en",   help="Enable synthesis."            , action='store_true')

    p = parser.parse_args(argv)
    return p

if __name__ == "__main__":
    p = cli(sys.argv[1:])
    test_main(nbits = p.nbits, 
              convert_en=p.convert_en, dump_en=p.dump_en, ddpm_en = p.ddpm_en, cosim_en = p.cosim_en, synth_en = p.synth_en)