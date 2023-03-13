function ddpm_s = ddpm_mod(s, nbits)
% generate modulated ddpm signal from input
  
  phase = [0:length(s)-1];    
  count = mod(phase, 2^nbits);
  
  ddpm_s = zeros(size(s));
  
  for tidx = 1:length(s)
    for bidx = 1:nbits
      if bitand(count(tidx), (2^(nbits-bidx)-1) ) == 2^(nbits-1-bidx)
          if bitand(s(tidx),bitshift(1,bidx))
            ddpm_s(tidx) = 1;
          end
      end
    end
  end
  
end