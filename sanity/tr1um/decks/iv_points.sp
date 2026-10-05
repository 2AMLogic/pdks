* TR-1um I-V sweeps for the Table I-2-7 points (template; filled in by
* sanity/tr1um/checks.py). W/L = 30/1 um, source and bulk at 0 V; for the
* PMOS the checks pass negative biases. Drain current written as i(vd).
.include "@MODELS@/ip62_models"
.temp 25
vd d 0 0
vg g 0 0
X1 d g 0 0 @DEVICE@ w=30u l=1u
.control
set wr_singlescale
* Id-Vg at |Vds| = 5 V
alter vd dc = @VDS5@
dc vg 0 @VG6@ @VSTEP@
wrdata @OUT@.idvg i(vd)
* Id-Vd at |Vgs| = 2..6 V, to |Vds| = 7 V
alter vg dc = @VG2@
dc vd 0 @VD7@ @VSTEP@
wrdata @OUT@.idvd2 i(vd)
alter vg dc = @VG3@
dc vd 0 @VD7@ @VSTEP@
wrdata @OUT@.idvd3 i(vd)
alter vg dc = @VG4@
dc vd 0 @VD7@ @VSTEP@
wrdata @OUT@.idvd4 i(vd)
alter vg dc = @VG5@
dc vd 0 @VD7@ @VSTEP@
wrdata @OUT@.idvd5 i(vd)
alter vg dc = @VG6@
dc vd 0 @VD7@ @VSTEP@
wrdata @OUT@.idvd6 i(vd)
.endc
.end
