* Distributed RC wire as an N-segment pi ladder (IHP SG13G2 and SG13CMOS5L).
*
*   X1 a b wire16 l=<length> w=<width> rsh=<ohm/sq> cpl=<F/m>
*
* wireN exists for N = 1, 2, 4, 8, 16, 32, 64 segments; `wire` is wire16.
* (ngspice cannot build a variable-length chain in a subcircuit, so wire2N is
* two wireN halves.) Total R = rsh * l / w. Total C = cpl * l, half of each
* segment's share on each end of the segment. A wire driven by an ideal source
* and left open therefore has Elmore delay (first moment of the step
* response) R C / 2 for ANY N; N only sets how well the ladder follows the
* line at higher frequencies. Same interface as ASAP7's wire.inc.
*
* rsh and cpl have no default. IHP publishes a sheet resistance per layer
* (interconnect.csv, also as .param <pdk>_<layer>_rsh in interconnect.inc),
* but only AREA capacitances: no per-length capacitance (fringe and lateral
* coupling), which interconnect.csv lists as explicit gaps. The caller
* supplies cpl from a source it cites. An omitted rsh or cpl stops ngspice
* with an unknown-parameter error instead of simulating a made-up wire.
* Per-layer geometry is in interconnect.inc as .param <pdk>_<layer>_<w|s|t|p|h>
* (the w default below, 200n, is the Metal2-Metal5 minimum width).
.subckt wire1 a b l=100u w=200n rsh=rsh_not_given cpl=cpl_not_given
R1 a b {rsh*l/w}
C1 a 0 {cpl*l/2}
C2 b 0 {cpl*l/2}
.ends
.subckt wire2 a b l=100u w=200n rsh=rsh_not_given cpl=cpl_not_given
X1 a m wire1 l={l/2} w={w} rsh={rsh} cpl={cpl}
X2 m b wire1 l={l/2} w={w} rsh={rsh} cpl={cpl}
.ends
.subckt wire4 a b l=100u w=200n rsh=rsh_not_given cpl=cpl_not_given
X1 a m wire2 l={l/2} w={w} rsh={rsh} cpl={cpl}
X2 m b wire2 l={l/2} w={w} rsh={rsh} cpl={cpl}
.ends
.subckt wire8 a b l=100u w=200n rsh=rsh_not_given cpl=cpl_not_given
X1 a m wire4 l={l/2} w={w} rsh={rsh} cpl={cpl}
X2 m b wire4 l={l/2} w={w} rsh={rsh} cpl={cpl}
.ends
.subckt wire16 a b l=100u w=200n rsh=rsh_not_given cpl=cpl_not_given
X1 a m wire8 l={l/2} w={w} rsh={rsh} cpl={cpl}
X2 m b wire8 l={l/2} w={w} rsh={rsh} cpl={cpl}
.ends
.subckt wire32 a b l=100u w=200n rsh=rsh_not_given cpl=cpl_not_given
X1 a m wire16 l={l/2} w={w} rsh={rsh} cpl={cpl}
X2 m b wire16 l={l/2} w={w} rsh={rsh} cpl={cpl}
.ends
.subckt wire64 a b l=100u w=200n rsh=rsh_not_given cpl=cpl_not_given
X1 a m wire32 l={l/2} w={w} rsh={rsh} cpl={cpl}
X2 m b wire32 l={l/2} w={w} rsh={rsh} cpl={cpl}
.ends
.subckt wire a b l=100u w=200n rsh=rsh_not_given cpl=cpl_not_given
X1 a b wire16 l={l} w={w} rsh={rsh} cpl={cpl}
.ends
