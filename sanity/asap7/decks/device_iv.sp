* ASAP7 single-fin I-V sweeps (template; @...@ is filled in by sanity/run.py)
*
* One fin, l = 20n drawn (the ASAP7 cell libraries' value; the cards add
* xl = 1n, giving the paper's 21 nm actual gate length). Source and bulk at
* 0 V. For a pFET the run script passes negative bias values, so the gate
* and drain are swept negative.
*
* Current is measured at the SOURCE (i(vs)), not the drain. [MEJ16]'s Ioff
* values equal the model's channel current IDS exactly, i.e. they exclude
* gate-induced drain leakage (GIDL), which flows into the drain terminal.
* Each sweep is written as two columns, the swept voltage and i(vs);
* sanity/run.py takes magnitudes.
.include @MODELS@
.temp 25
vd d 0 0
vg g 0 0
vs s 0 0
N1 d g s 0 @DEVICE@ l=20n nfin=1
.control
pre_osdi @OSDI@
set wr_singlescale
* Id-Vg at |Vds| = 0.05, 0.35, 0.7 V
alter vd dc = @VLIN@
dc vg 0 @VDD@ @VSTEP@
wrdata @OUT@.vg_lin i(vs)
alter vd dc = @VHALF@
dc vg 0 @VDD@ @VSTEP@
wrdata @OUT@.vg_half i(vs)
alter vd dc = @VDD@
dc vg 0 @VDD@ @VSTEP@
wrdata @OUT@.vg_sat i(vs)
* Id-Vd at |Vgs| = 0.35, 0.7 V
alter vg dc = @VHALF@
dc vd 0 @VDD@ @VSTEP@
wrdata @OUT@.vd_half i(vs)
alter vg dc = @VDD@
dc vd 0 @VDD@ @VSTEP@
wrdata @OUT@.vd_full i(vs)
.endc
.end
