* ASAP7 fanout-of-4 inverter delay (template; filled in by sanity/run.py)
*
* A chain of five inverters, each four times the size of the one before
* (3, 12, 48, 192, 768 fins per device), so every stage drives a load of
* four copies of itself. The measured stage is x4 (12 fins) driving x16;
* the x1 stage in front shapes a realistic input edge and the x64/x256
* stages give x16 a realistic load. Pre-layout: no wire RC.
.include @MODELS@
.temp 25
.subckt inv in out vdd nf=3
Nn out in 0 0 nmos_@VT@ l=20n nfin={nf}
Np out in vdd vdd pmos_@VT@ l=20n nfin={nf}
.ends
vdd vdd 0 @VDD@
vin in 0 pulse(0 @VDD@ 20p 10p 10p 200p 400p)
X1 in  n1 vdd inv nf=3
X2 n1  n2 vdd inv nf=12
X3 n2  n3 vdd inv nf=48
X4 n3  n4 vdd inv nf=192
X5 n4  n5 vdd inv nf=768
.control
pre_osdi @OSDI@
tran 0.1p 800p
meas tran tphl trig v(n1) val=@VMID@ rise=2 targ v(n2) val=@VMID@ fall=2
meas tran tplh trig v(n1) val=@VMID@ fall=2 targ v(n2) val=@VMID@ rise=2
echo "RESULT tphl $&tphl"
echo "RESULT tplh $&tplh"
.endc
.end
