* Wire ladder vs the closed-form Elmore delay (template; filled in by sanity/common.py elmore())
*
* An ideal unit step drives source resistance RS into a wire of @N@ pi
* segments (wire.inc), loaded by CL. The simulated Elmore delay is the first
* moment of the step response, integral of (vin - vout) dt over the whole
* settling; the closed form is
*     RS (C + CL) + R (C / 2 + CL),  R = rsh l / w,  C = cpl l.
* RSH and CPL are test inputs stated by the calling PDK's reference constants
* (sanity/<pdk>/reference.py or sanity/ihp_spec.py), not process values unless it says so there.
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
