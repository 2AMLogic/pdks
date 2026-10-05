* MOSFET I-V sweeps shared by the sanity checks (template; filled in by
* sanity/<pdk>/checks.py). Source and bulk at 0 V. For a pFET the checks
* pass negative bias values. Each sweep is written as two columns: the
* swept voltage and the drain-source current, measured at @IMEAS@.
*
* vg_lin  Id-Vg at Vds = @VLIN@
* vg_aux  Id-Vg at Vds = @VAUX@   (a second low-drain sweep, e.g. for DIBL)
* vg_sat  Id-Vg at Vds = @VDD@
* vg_off  Id-Vg at Vds = @VOFF@   (the Ioff bias, which can exceed VDD)
* vd_full Id-Vd at Vgs = @VDD@
* Gate sweeps start at @VGSTART@ (below 0 for depletion-mode devices).
@HEADER@
.temp @TEMP@
vd d 0 0
vg g 0 0
vs s 0 0
@INSTANCE@
.control
@PRE@
set wr_singlescale
alter vd dc = @VLIN@
dc vg @VGSTART@ @VDD@ @VSTEP@
wrdata @OUT@.vg_lin @IMEAS@
alter vd dc = @VAUX@
dc vg @VGSTART@ @VDD@ @VSTEP@
wrdata @OUT@.vg_aux @IMEAS@
alter vd dc = @VDD@
dc vg @VGSTART@ @VDD@ @VSTEP@
wrdata @OUT@.vg_sat @IMEAS@
alter vd dc = @VOFF@
dc vg @VGSTART@ @VDD@ @VSTEP@
wrdata @OUT@.vg_off @IMEAS@
alter vg dc = @VDD@
dc vd 0 @VDD@ @VSTEP@
wrdata @OUT@.vd_full @IMEAS@
.endc
.end
