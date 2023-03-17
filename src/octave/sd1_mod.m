
function sd_out = sd1_mod( inval,  nbits, nbits_out)
  
  if nargin < 3
    nbits_out = 1;
  end
  
  assert(nbits > nbits_out);

  sd_out = zeros(size(inval));
  delta  = zeros(size(inval));
  qerr   = zeros(size(inval));

  maxval = 2^nbits -1;
  minval = 0;
    
  for idx = 2:length(inval)
      delta(idx)  = saturated_adder( inval(idx),  qerr(idx-1),   maxval, minval);
      qerr(idx)   = bitand( delta(idx), 2^(nbits-nbits_out) - 1);
      sd_out(idx) = bitshift(delta(idx),-(nbits-nbits_out));
  end
    
  if 1
    fh = figure(541);
    
    subplot(411)
    stairs(inval);
    ylabel('input')
    hold on; grid on;
    
    subplot(412)
    stairs(delta,'r');
    hold on; grid on;
    ylabel('delta')
    
    subplot(413)
    stairs(qerr,'m'); 
    hold on; grid on;   
    ylabel('quant')
    
    subplot(414)
    stairs(sd_out,'m'); 
    hold on; grid on;   
    ylabel('out')
    
    saveas(fh, 'sd', 'png');
    close(fh);
  end
    
end

function ret = saturated_adder(a, b, maxval, minval)
  
    ret = a + b;
    
    maxidx = find(ret > maxval);
    ret(maxidx) = maxval * ones(size(maxidx));
    
    minidx = find(ret < minval);
    ret(maxidx) = minval * ones(size(maxidx));
   
end

