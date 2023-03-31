function ddpm_s = ddpm_mod(s, nbits)
% generate modulated ddpm signal from input
  
  phase = [0:length(s)-1];    
  count = mod(phase, 2^nbits);
  
  ddpm_s = zeros(size(s));
  
  if 0
    % loop form (slower)
    
    for tidx = 1:length(s)
      for bidx = 1:nbits
        if bitand(count(tidx), (2^(nbits-bidx)-1) ) == 2^(nbits-1-bidx)
            if bitand(s(tidx),bitshift(1,bidx))
              ddpm_s(tidx) = 1;
            end
        end
      end
    end
  
  else
    % matrix form (faster)
  
   for bidx = 1:nbits
    idxs = find( 
    (bitand(count, (2^(nbits-bidx)-1) ) == 2^(nbits-1-bidx) ) &
    ( bitand(s,bitshift(1,bidx)) > 0 )
    );        
    
    % size(idxs)

    ddpm_s(idxs) = ones(size(idxs));
   end
  
  end
    
end