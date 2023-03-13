## Copyright (C) 2023 marco
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <https://www.gnu.org/licenses/>.

## -*- texinfo -*-
## @deftypefn {} {@var{retval} =} plot_freq (@var{input1}, @var{input2})
##
## @seealso{}
## @end deftypefn

## Author: marco <marco@Latitude-E6440>
## Created: 2023-03-12

function fh = plot_freq ( s, fs, figno, color)
  
  if nargin < 3
    fh = figure();
  else
    fh = figure(figno);
  endif
  
  if nargin < 4
    color = 'b';
  endif

  sf   = abs(fft(s));
  sn   = sf/max(sf); % normalize
  sf   = 20*log10(sn);

  freq = (fs/length(sf))*[0:length(sf)-1];

  hold on; grid on;
  semilogx(freq,sf);
  xlabel('freq [Hz]');
  ylabel('amplitude [dBc]');
  ylim([-100 0]);
  xlim([1 freq(round(length(sf)/2))]);
  
endfunction
