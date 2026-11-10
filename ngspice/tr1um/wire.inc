* Distributed RC wire as an N-segment pi ladder.
*
*   X1 a b wire16 l=<length> w=<width> rsh=<ohm/sq> cpl=<F/m>
*
* wireN exists for N = 1, 2, 4, 8, 16, 32, 64 segments; `wire` is wire16.
* (ngspice cannot build a variable-length chain in a subcircuit, so wire2N is
* two wireN halves.) Total R = rsh * l / w. Total C = cpl * l, half of each
* segment's share on each end of the segment. A wire driven by an ideal source
* and left open therefore has Elmore delay (first moment of the step
* response) R C / 2 for ANY N; N only sets how well the ladder follows the
* line at higher frequencies.
*
* rsh and cpl have no default: TR-1um publishes neither (interconnect.csv lists
* them as explicit gaps). The caller supplies them from a source it cites. An
* omitted one stops ngspice with an unknown-parameter error instead of
* simulating a made-up wire. Per-layer geometry (width, spacing, thickness)
* is in interconnect.inc as .param tr1um_<layer>_<w|s|t>.
.subckt wire1 a b l=100u w=1.8u rsh=rsh_not_given cpl=cpl_not_given
R1 a b {rsh*l/w}
C1 a 0 {cpl*l/2}
C2 b 0 {cpl*l/2}
.ends
.subckt wire2 a b l=100u w=1.8u rsh=rsh_not_given cpl=cpl_not_given
X1 a m wire1 l={l/2} w={w} rsh={rsh} cpl={cpl}
X2 m b wire1 l={l/2} w={w} rsh={rsh} cpl={cpl}
.ends
.subckt wire4 a b l=100u w=1.8u rsh=rsh_not_given cpl=cpl_not_given
X1 a m wire2 l={l/2} w={w} rsh={rsh} cpl={cpl}
X2 m b wire2 l={l/2} w={w} rsh={rsh} cpl={cpl}
.ends
.subckt wire8 a b l=100u w=1.8u rsh=rsh_not_given cpl=cpl_not_given
X1 a m wire4 l={l/2} w={w} rsh={rsh} cpl={cpl}
X2 m b wire4 l={l/2} w={w} rsh={rsh} cpl={cpl}
.ends
.subckt wire16 a b l=100u w=1.8u rsh=rsh_not_given cpl=cpl_not_given
X1 a m wire8 l={l/2} w={w} rsh={rsh} cpl={cpl}
X2 m b wire8 l={l/2} w={w} rsh={rsh} cpl={cpl}
.ends
.subckt wire32 a b l=100u w=1.8u rsh=rsh_not_given cpl=cpl_not_given
X1 a m wire16 l={l/2} w={w} rsh={rsh} cpl={cpl}
X2 m b wire16 l={l/2} w={w} rsh={rsh} cpl={cpl}
.ends
.subckt wire64 a b l=100u w=1.8u rsh=rsh_not_given cpl=cpl_not_given
X1 a m wire32 l={l/2} w={w} rsh={rsh} cpl={cpl}
X2 m b wire32 l={l/2} w={w} rsh={rsh} cpl={cpl}
.ends
.subckt wire a b l=100u w=1.8u rsh=rsh_not_given cpl=cpl_not_given
X1 a b wire16 l={l} w={w} rsh={rsh} cpl={cpl}
.ends
