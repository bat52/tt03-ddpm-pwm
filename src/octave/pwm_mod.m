function pwm_s = pwm_mod(s, nbit_pwm)
% generate modulated pwm signal from input
  
  phase = [0:length(s)-1];  
  
  pwm_phase = mod(phase, 2^nbit_pwm);
  pwm_s = zeros(1,length(s));
  idxs = find( (pwm_phase) - s < 0);
  pwm_s(idxs) = ones(1,length(idxs));
  
end