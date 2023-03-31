#!/usr/bin/env octave

clear all;
close all;

profile off;
profile clear;
profile on;

% inputs
fclock = 12.5; # khz
if 0
  nbit_pwm_phase = 6;
  nbit_sine_phase = 6;
  nbit_pwm_amplitude = 6;
  nperiods = 10;
else
  nbit_pwm_phase = 8;
  nbit_sine_phase = 8;
  nbit_pwm_amplitude = 8;
  nperiods = 5; 
end

if 0
  nbit_pwm_phase = 10;
  nbit_sine_phase = 6;
  nbit_pwm_amplitude = nbit_pwm_phase;
  nperiods = 3; 
end

nbit_sd_amplitude = nbit_pwm_amplitude + 2;

% parameters
normf = 2^(nbit_pwm_amplitude-1) - 1;
dc  = 2^(nbit_pwm_amplitude-1) - 1;

nbit_phase = nbit_pwm_phase + nbit_sine_phase;

% generate time series
nsamples = (2^nbit_phase - 1)*nperiods;
phase  = [0 : nsamples-1];
t = (1/fclock) * phase;

% generate quantized sinewave
s = round( dc + normf * sin(2*pi*phase/(2^nbit_phase-1)) );
clear phase;

% generate pwm
pwm_s  = pwm_mod(s,nbit_pwm_phase);
ddpm_s = ddpm_mod(s,nbit_pwm_phase);
sd1_s  = sd1_mod(s,nbit_sd_amplitude);  
  
%% time domain plots  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if 0
  
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

if 0
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

##if 0 
##  figure(111);
##  stairs(t,s);
##  hold on; grid on;
##  stairs(t,max(s)*sd1_s,'r');
##  xlabel('time [ms]');
##  ylabel('amplitude [LSB]');
##  legend('quant sine','sd1');
##  xlim((1/fclock)*[0 (2^nbit_phase)-1]);
##end

if 1 
  fh = figure(1111);
  subplot(411)
  stairs(t,s);
  hold on; grid on;
  xlabel('time [ms]');
  ylabel('quant sine [LSB]');
  xlim((1/fclock)*[0 (2^nbit_phase)-1]);
  
  subplot(412)
  stairs(t,pwm_s);
  hold on; grid on;
  xlabel('time [ms]');
  ylabel('PWM [LSB]');
  xlim((1/fclock)*[0 (2^nbit_phase)-1]);  
  
  subplot(413)
  stairs(t,ddpm_s);
  hold on; grid on;
  xlabel('time [ms]');
  ylabel('DDPM [LSB]');
  xlim((1/fclock)*[0 (2^nbit_phase)-1]);  
  
  subplot(414)
  stairs(t,sd1_s);
  hold on; grid on;
  xlabel('time [ms]');
  ylabel('SD1 [LSB]');
  xlim((1/fclock)*[0 (2^nbit_phase)-1]);
  
  saveas(fh, 'timedomain', 'png');
  % close(fh)
end

%% freq domain plots %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
clear t;
if 0
  figno = 2;
  fs = fclock*1e3;
  plot_freq(s,fs,figno);
  plot_freq(pwm_s,fs,figno,'r');  
  legend('quant sine','pwm');
end

if 0
  figno = 3;
  fs = fclock*1e3;
  plot_freq(s,fs,figno);
  plot_freq(ddpm_s,fs,figno,'k');  
  legend('quant sine','ddpm');
end

if 0
  figno = 4;
  fs = fclock*1e3;
  plot_freq(s,fs,figno);
  plot_freq(sd1_s,fs,figno,'r');  
  legend('quant sine','sd1');
end

if 1
  figno = 5;
  fs = fclock*1e3;
  % plot_freq(s,fs,figno);  
  fh = plot_freq(pwm_s,fs,figno,'ro-');
  fh = plot_freq(ddpm_s,fs,figno,'k+-');  
  fh = plot_freq(sd1_s,fs,figno);  
  legend('pwm', 'ddpm', 'sd1','Location','southwest');
  saveas(fh, 'freqdomain', 'png');
  % close(fh)
end

profile off;
prof = profile ('info');
profshow(prof);
% profexplore(prof);
