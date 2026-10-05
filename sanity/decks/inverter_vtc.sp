* ASAP7 inverter voltage transfer curve (template; filled in by sanity/run.py)
*
* INVx1 sizing from asap7sc7p5t_28 (CDL/LVS): 3-fin nFET and pFET, l = 20n.
.include @MODELS@
.temp 25
vdd vdd 0 @VDD@
vin in 0 0
Nn out in 0 0 nmos_@VT@ l=20n nfin=3
Np out in vdd vdd pmos_@VT@ l=20n nfin=3
.control
pre_osdi @OSDI@
set wr_singlescale
dc vin 0 @VDD@ 0.001
wrdata @OUT@.vtc v(out)
.endc
.end
