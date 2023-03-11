#!/usr/bin/env python3

import os
from myhdl import *

from pueda.myhdl import *
from pueda.common import get_clean_work
# from pueda.yosys import yosys

LUT_NBIT_OUT = 8
LUT_NBIT_IN  = 4

LUT_TOP    = 'lut_module'
LUT_TB_TOP = 'tb_%s' % LUT_TOP

@block
def lut_module(nbits_out=LUT_NBIT_OUT, nbits_in=LUT_NBIT_IN, 
                 values_list = [*range(2**LUT_NBIT_IN)],
                 lut_in=Signal(intbv(0)[LUT_NBIT_IN:]),
                 lut_out=Signal(intbv(0)[LUT_NBIT_OUT:])):
       
    r_values_list = [*reversed(values_list)]    
    
    # create the lookup table using MyHDL Signal objects
    lut = []                    
    for idx in range(2**nbits_in):        
        lut.append( 
            Signal( 
                    intbv( r_values_list[idx] )[nbits_out:]
                )
        )

    # this foces myHDL to actually implement the constant values
    lut_c = ConcatSignal(*lut)
    
    @always_comb
    def lut_out_proc():
        lut_out.next = (lut_c >> (lut_in*nbits_out)) & (2**nbits_out - 1)

    return instances()

@block
def tb_lut(work = './',
           nbit_in = LUT_NBIT_IN, nbit_out = LUT_NBIT_OUT,
           dump_en = False, cosim_en = False, duration = 2**LUT_NBIT_IN):
    
    lut_in  = Signal(intbv(0)[nbit_in:])
    lut_out = Signal(intbv(0)[nbit_out:])

    lut_i = lut_module(lut_in = lut_in, lut_out = lut_out,
                       nbits_in = nbit_in, nbits_out = nbit_out)
    
    # convert to check resulting verilog
    lut_i.convert(hdl='Verilog', path = work, trace = dump_en)

    # else:
    if cosim_en:
        topmodule=LUT_TB_TOP
        topfile  = topmodule + '.v'
        src_dirs=[work]

        ports={'lut_in':lut_in, 'lut_out':lut_out}
        simname='lut_sim'        

        lut_h = myhdl_cosim_wrapper(topfile=topfile, topmodule=topmodule, src_dirs=src_dirs, simname=simname, duration=duration)
        # overwrite lut_i
        lut_i = lut_h.dut_instance(ports=ports)

    @instance
    def gen_lut_input_proc():        
        for val in range(2**nbit_in):
            lut_in.next = val
            yield delay(int(1))     
            print('IN: %d, OUT: %d' % (lut_in, lut_out) )
            assert(lut_out == lut_in)

    return instances()

def main(dump_en = False, cosim_en = True):
    work = get_clean_work('lut', makedir=True)
    os.system('rm *.vcd')

    duration = (2**LUT_NBIT_IN) 

    tb_i = tb_lut(work = work, duration = duration, dump_en = dump_en, cosim_en = cosim_en)
    
    if not(cosim_en):
        tb_i.config_sim(trace=dump_en)
        tb_i.run_sim(duration=duration)
        # if dump_en:
        #    sim_view()
    else: # cosim_en
        cosim = Simulation( tb_i )
        cosim.run(duration)
        #if dump_en:
        #    cosim_view(nbits = nbits) 
    pass

    return instances()

if __name__ == "__main__":
    main()