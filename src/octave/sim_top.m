#!/usr/bin/env octave

clear all;
close all;

% inputs
fclock = 12.5; # khz
nbit_pwm_phase = 6;
nbit_sine_phase = 6;
nbit_pwm_amplitude = 6;
nperiods = 10;

% parameters
normf = 2^(nbit_pwm_amplitude-3) - 1;
dc    = 2^(nbit_pwm_amplitude-3) - 1;
nbit_phase = nbit_pwm_phase + nbit_sine_phase;

% generate time series
nsamples = (2^nbit_phase - 1)*nperiods;
phase  = [0 : nsamples-1];
t = (1/fclock) * phase;

% generate quantized sinewave
s = round( dc + normf * sin(2*pi*phase/(2^nbit_phase-1)) );

% generate pwm
pwm_s  = pwm_mod(s,nbit_pwm_phase);
ddpm_s = ddpm_mod(s,nbit_pwm_phase);
sd1_s  = sd1_mod(s,nbit_pwm_amplitude);  
  
if 1
  % time domain plot
  figure(1);
  # subplot(11);
  stairs(t,s);
  hold on; grid on;
  stairs(t,max(s)*pwm_s,'r');
  xlabel('time [ms]');
  ylabel('amplitude [LSB]');
  legend('quant sine','pwm');
  xlim((1/fclock)*[0 (2^nbit_phase)-1]);
end

if 1
  figure(11);
  # subplot(212);
  stairs(t,s);
  hold on; grid on;
  stairs(t,max(s)*ddpm_s,'r');
  xlabel('time [ms]');
  ylabel('amplitude [LSB]');
  legend('quant sine','ddpm');
  xlim((1/fclock)*[0 (2^nbit_phase)-1]);
end

if 1 
  figure(111);
  stairs(t,s);
  hold on; grid on;
  stairs(t,max(s)*sd1_s,'r');
  xlabel('time [ms]');
  ylabel('amplitude [LSB]');
  legend('quant sine','sd1');
  xlim((1/fclock)*[0 (2^nbit_phase)-1]);
end

% freq domain plot
if 1
  figno = 2;
  fs = fclock*1e3;
  plot_freq(s,fs,figno);
  plot_freq(pwm_s,fs,figno,'r');  
  legend('quant sine','pwm');
end

if 1
  figno = 3;
  fs = fclock*1e3;
  plot_freq(s,fs,figno);
  plot_freq(ddpm_s,fs,figno,'k');  
  legend('quant sine','ddpm');
end

if 1
  figno = 4;
  fs = fclock*1e3;
  plot_freq(s,fs,figno);
  plot_freq(sd1_s,fs,figno,'r');  
  legend('quant sine','sd1');
end