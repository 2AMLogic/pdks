* Wire ladder vs the closed-form Elmore delay, IHP SG13G2 and SG13CMOS5L (template; filled in by sanity/ihp_spec.py)
*
* An ideal unit step drives source resistance RS into a wire of @N@ pi
* segments (wire.inc), loaded by CL. The simulated Elmore delay is the first
* moment of the step response, integral of (vin - vout) dt over the whole
* settling; the closed form is
*     RS (C + CL) + R (C / 2 + CL),  R = rsh l / w,  C = cpl l.
* RSH is the published Metal2 sheet resistance read from interconnect.csv; CPL is a test input (IHP publishes no per-length capacitance), see ihp_spec.py.
.include @WIRE_INC@
vin in 0 pulse(0 1 0 1p 1p 1 2)
rs in a @RS@
X1 a b wire@N@ l=@L@ w=@W@ rsh=@RSH@ cpl=@CPL@
cl b 0 @CL@
bd d 0 v='v(in)-v(b)'
.control
tran 1p @TSTOP@ 0 2p
meas tran elmore integ v(d) from=0 to=@TSTOP@
echo "RESULT elmore $&elmore"
.endc
.end
