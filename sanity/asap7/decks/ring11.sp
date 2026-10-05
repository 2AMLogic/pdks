* ASAP7 11-stage ring oscillator (template; filled in by sanity/run.py)
*
* Eleven INVx1-sized inverters (3-fin nFET and pFET, l = 20n) in a loop,
* each loaded only by the next stage's gate. Pre-layout: no wire RC.
.include @MODELS@
.temp 25
.subckt inv in out vdd
Nn out in 0 0 nmos_@VT@ l=20n nfin=3
Np out in vdd vdd pmos_@VT@ l=20n nfin=3
.ends
vdd vdd 0 @VDD@
X1  n1  n2  vdd inv
X2  n2  n3  vdd inv
X3  n3  n4  vdd inv
X4  n4  n5  vdd inv
X5  n5  n6  vdd inv
X6  n6  n7  vdd inv
X7  n7  n8  vdd inv
X8  n8  n9  vdd inv
X9  n9  n10 vdd inv
X10 n10 n11 vdd inv
X11 n11 n1  vdd inv
.ic v(n1)=0 v(n2)=@VDD@
.control
pre_osdi @OSDI@
tran 0.1p 1000p uic
meas tran five_periods trig v(n1) val=@VMID@ rise=5 targ v(n1) val=@VMID@ rise=10
echo "RESULT five_periods $&five_periods"
.endc
.end
