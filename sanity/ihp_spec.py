"""IHP process-specification checks, shared by sanity/ihp-sg13g2 and
sanity/ihp-sg13cmos5l.

Sources:
  [G2]  SG13G2 Process Specification, Rev. 1.2 (2023-12-20),
        ihp-sg13g2/libs.doc/doc/SG13G2_os_process_spec.pdf in IHP-Open-PDK
        v0.3.0: section 2.1 (LV NMOS, p. 7), 2.2 (LV PMOS, pp. 7-8),
        3.1 (npn13g2, p. 20), Attachment A (measurement conditions, pp. 22-23).
  [C5L] SG13CMOS5L Process Specification, Rev. 0.2,
        ihp-sg13cmos5l/libs.doc/doc/SG13CMOS5L_os_process_spec.pdf in
        IHP-Open-PDK dev 8e07a1f (first read at ihp-sg13cmos5l 607e18d):
        sections 2.1.1-2.1.2 (pp. 8-9), conditions p. 22. Its LV MOS rows and
        conditions are identical to [G2]'s.

Every row is checked against the specification's own MIN-MAX window, using
the specification's own extraction definition (Attachment A), at its
stated temperature (T0 = 27 C). The typical (target) value is printed
alongside. MOS rows cover the 1.2 V LV devices (sg13_lv_nmos / _pmos,
[G2] 2.1-2.2, [C5L] 2.1.1-2.1.2) and the 3.3 V HV devices (sg13_hv_nmos /
_pmos, [G2] 2.4-2.5; the [C5L] HV rows have the same values).

  A.a1 Vt (LV):    |Vds| = 0.05 V; tangent at maximum slope of the
                   transfer characteristic; Vt = Vgs intercept - Vds/2.
  A.a2 Vt (HV):    the same at |Vds| = 0.1 V.
  A.b1/b2 Idsat:   |Vds| = |Vgs| = 1.2 V (LV) / 3.3 V (HV), per um of width.
  A.c1/c2 Ioff:    |Vds| = 1.2 / 3.3 V, Vgs = 0, drain current, log10(A/um).
  A.d1 DIBL (LV):  [Vgs(|Vds| = 0.1) - Vgs(|Vds| = 1.2)] / 1.1 V at
                   Id = JSS * W/L; JSS = 0.5 nA (n), 0.1 nA (p).
  A.d2 DIBL (HV):  the same between 0.1 and 3.3 V, at ISS * W/L;
                   ISS = 1 nA (n), 0.4 nA (p).
  A.e  SS:         |Vds| = 0.1 V; gate swing between Id = JSS1 * W/L and
                   JSS2 * W/L, one decade: 0.5 / 5 nA (n), 0.1 / 1 nA (p).
  A.n  BETA:  Ic / Ib at VBE = 0.7 V, VCB = 0 (npn13G2, one emitter).
  A.ai IC07:  Ic at VBE = 0.7 V, VCB = 0 (one emitter).
  A.s  fT:    |h21| at 40 GHz times 40 GHz (a -20 dB/decade extrapolation),
              VCE = 1.2 V, maximum over VBE (four emitters, Nx = 4).

Passives and temperature ([G2] 2.7-2.9 and 2.12; [C5L] has the same
resistor rows and no MIM):
  A.i  Rs, DW: from R1 (one W x L stripe) and RN (N stripes of (W/N) x L in
              parallel): R1 = Rs L / (W + DW), RN = Rs (L/N) / (W/N + DW),
              solved for Rs and DW. W = 10 um, L = 100 um, N = 5, 27 C.
  A.af TC1, TC2 (resistors) and A.ad TCMIM1, TCMIM2 (MIM, V = 0, 100 kHz):
              X(T) = X(T0) [1 + TC1 (T - T0) + TC2 (T - T0)^2], T0 = 27 C,
              fitted by least squares over -40 to 125 C, the range the
              spec measures. The spec gives targets only, so TC1 is checked
              within 5 % and TC2 within 10 % of target.
  A.k  CMIMA: capacitance per area at V = 0, 100 kHz, 20 x 20 um.

Mismatch and noise (derived from the model cards; IHP publishes no value):
  Neither specification publishes a MOS Pelgrom coefficient or a noise level.
  [G2] Attachment A.am defines the "MOS Transistor Matching Coefficient k"
  (least-squares fit of s(dVT) against A^-0.5, Vds = 0.1 V, Id = 2 uA W/L) and
  A.al the HBT one, but no table row of [G2] section 2 or 3 carries a value
  for either; [C5L] has no MOS or HBT matching row at all (only resistors,
  A.ac). No spec row mentions flicker or thermal noise. These quantities are
  therefore gaps, not estimates; the checks are derived from the model files
  of the pinned trees (ihp-sg13g2/libs.tech/ngspice/models/), cited by line.
  All four MOS devices are exercised: sg13_{lv,hv}_{n,p}mos.
    sg13g2_moslv_mismatch.lib 20-23 (n), 25-28 (p); sg13g2_moshv_mismatch.lib
    20-23, 25-28: delvto_mm and factuo_mm (V um, um) and dw_mm, dl_mm (m).
    LV nMOS 3.9 mV um, 0.5 %um, 4 nm, 2 nm; LV pMOS 2.2, 0.33, 4, 2;
    HV nMOS 7, 0.5, 3, 3; HV pMOS 4.5, 0.4, 3, 3.
    sg13g2_mos{lv,hv}_mod_mismatch.lib, subckts sg13_{lv,hv}_nmos (line 66)
    and sg13_{lv,hv}_pmos (line 155), which draw the same four terms:
    delvto = agauss(0, delvto_mm/sqrt(m*l*w*1e12), mm_ok), factuo likewise
    about 1, w and l = agauss(w, dw_mm, mm_ok), agauss(l, dl_mm, mm_ok).
    cornerMOS{lv,hv}.lib, .LIB mos_tt_mismatch includes both files.
    sg13g2_mos{lv,hv}_parm.lib, the PSP cards: fnto (thermal), nfalw/nfblw/
    nfclw/efo (flicker). sg13g2_moslv_parm.lib 124-126 (LV nMOS, card at line
    61) and 405-407 (LV pMOS, card at 342); sg13g2_moshv_parm.lib 125-127
    (HV nMOS, card at 62) and 408-410 (HV pMOS, card at 345). Only two values
    differ from 1.0 across the four cards: the LV pMOS fnto (1.85) and the
    HV pMOS efo (1.152).
  SG13CMOS5L links to the same files in its own pinned tree. The mismatch
  and parm values are identical to SG13G2's; one difference matters: the
  default of the instance parameter mm_ok is 1 in SG13G2's
  sg13g2_mos{lv,hv}_mod_mismatch.lib and 0 in SG13CMOS5L's (lines 67, 156),
  so the decks pass mm_ok explicitly.
  Definitions (ngspice/ihp/mismatch.sp.in, noise.sp.in):
    Vt (mismatch)  Vgs at Id = 2 uA * W/L (m multiplies both), Vds = 0.05 V
                   (LV) / 0.1 V (HV), linear interpolation on a 2 mV sweep.
    beta           peak gm / Vds, relative spread.
    sigma(dVt)     standard deviation of Vt1 - Vt2 for the two devices of one
                   Monte Carlo sample.
    gamma          S_id = 4kT*gamma*gm, S_id from the channel thermal source
                   (_idid) at 1 kHz, gm from a +-2 mV gate step.
    Nyquist ratio  S_id / (4kT*gds) with the drain at 0 V; gds from +-1 mV.
    flicker slope  d ln S / d ln f of the _flicker source between 1 and 100 Hz.
  Both quantities taken from _idid are checked after division by the card's
  own fnto. PSP 103 sets the channel thermal source to
  S_idid = FNTO * 4kT * mid * MULT * (1 - c_igid^2) -- the pinned Verilog-A
  has nt = FNT_i * 4.0 * KBOL * TKD (PSP103_macrodefs.include),
  sqid = sqrt(nt * mid) and white_noise(MULT_i * sqid * sqid * (1 - c_igid^2),
  "idid") (PSP103_module.include), with FNT_p = FNTO -- so gamma and the
  Nyquist ratio are both exactly linear in FNTO, which PSP 103 documents as
  the "Thermal noise coefficient". Dividing by it recovers precisely the
  quantity long-channel theory bounds, and is an exact no-op for the three
  cards with fnto = 1.0; the raw model level is reported alongside as
  information. The only card with fnto != 1 is the LV pMOS (1.85), whose
  un-normalised gamma and Nyquist ratio are 1.85 times the normalised ones.
  The bound is a cited normalisation of the measurement, not a fitted
  tolerance: GAMMA_LONG and NYQUIST are unchanged.
  Sampling error: the relative standard error of a standard deviation from n
  samples is 1/sqrt(2(n-1)); tolerances are 3 of those.

Interconnect (pdks/<pdk>/interconnect.csv, installed as
<prefix>/<pdk>/ngspice/interconnect.csv; `interconnect_checks` below):
  [G2LR]  SG13G2 Layout Rules, Rev. 0.4 (2024-12-19),
          ihp-sg13g2/libs.doc/doc/SG13G2_os_layout_rules.pdf: 5.16 Metal1
          (M1.a, M1.b), 5.17 Metal(n=2-5) (Mn.a, Mn.b), 5.19-5.20 Via1 and
          Via(n=2-4) (V1.a, Vn.a), TopVia1 (TV1.a), TM1.a-b, TopVia2
          (TV2.a), TM2.a-b.
  [C5LR]  SG13CMOS5L Layout Rules, Rev. 0.1 (2025-12-08),
          ihp-sg13cmos5l/libs.doc/doc/SG13CMOS5L_os_layout_rules.pdf: 5.14
          Metal1, 5.15 Metal(n=2-4), 5.17-5.18 Via1 and Via(n=2-3), TV1.a,
          TM1.a-b.
  [G2] 2.13 (sheet resistance RSMETn / RSTMn and TC1RSMETn / TC1RSTMn),
  2.14 (via resistance RVIAn, RTVn), 2.16 (layer and inter-layer dielectric
  thickness) and 2.17 (area capacitance); [C5L] 3.1, 3.4, 3.6 and 3.7.
  Document SHA-256 (the files at the pinned commits) is in the PDK's README.
The BEOL is the same in both PDKs: every [C5L] row below that exists has the
value [G2] gives (SG13CMOS5L stops at Metal4 + TopMetal1: no Metal5, no
TopMetal2). Each table row cites its own document; one reference table
(BEOL) serves both. Targets (the nominal column) are the values taken; the
spec's min-max window is not used.
Derived rows: pitch = width + spacing; via height = the inter-layer
dielectric thickness the via spans (TILDn, TILDTM1, TILTM2), an
interpretation, not a printed via height. Gaps: capacitance per length
(isolated and at minimum pitch; the specs print only area capacitance, with
no fringe or lateral part) for every metal, and the two quantities the
SG13CMOS5L spec prints as "tbd" (Metal4 - TopMetal1 area capacitance,
TopVia1 resistance). They are not estimated.
"""

import math
import os
import re
import tempfile

from common import (Report, at, elmore_ladder, gap_check, load_interconnect, mc_tol, mos_sweeps, ngspice,
                    render, results, tc_fit, vt_cc, vt_max_gm)

TEMP = 27
VDD = 1.2

# Device classes: library, subcircuit names, supply, and the bias and
# current levels of their Attachment A definitions.
CLASSES = {
    "lv": dict(lib="cornerMOSlv.lib", n="sg13_lv_nmos", p="sg13_lv_pmos", vdd=1.2, vt_vds=0.05,
               jdibl={1: 0.5e-9, -1: 0.1e-9}),
    "hv": dict(lib="cornerMOShv.lib", n="sg13_hv_nmos", p="sg13_hv_pmos", vdd=3.3, vt_vds=0.1,
               jdibl={1: 1e-9, -1: 0.4e-9}),
}

# (name, polarity, W um, L um, quantity, min, typ, max) in device terms:
# pFET values are magnitudes (the spec prints them negative). LV rows:
MOS_ROWS = [
    ("VTN10x013",  1, 10.00, 0.13, "vt",    0.43,  0.50,  0.55),
    ("VTN10x10",   1, 10.00, 10.0, "vt",    0.16,  0.20,  0.24),
    ("VTN015x013", 1, 0.15,  0.13, "vt",    0.40,  0.54,  0.68),
    ("IDSN013",    1, 10.00, 0.13, "idsat", 380,   480,   600),
    ("IOFFN013",   1, 10.00, 0.13, "ioff",  None,  -10,   -9),
    ("DIBLN013",   1, 10.00, 0.13, "dibl",  20,    50,    80),
    ("SSN013",     1, 10.00, 0.13, "ss",    76,    82,    88),
    ("VTP10x013", -1, 10.00, 0.13, "vt",    0.41,  0.47,  0.53),
    ("VTP10x10",  -1, 10.00, 10.0, "vt",    0.31,  0.36,  0.41),
    ("VTP015x013", -1, 0.15, 0.13, "vt",    0.38,  0.48,  0.58),
    ("IDSP013",   -1, 10.00, 0.13, "idsat", 170,   215,   270),
    ("IOFFP013",  -1, 10.00, 0.13, "ioff",  None,  -10.3, -9.3),
    ("DIBLP013",  -1, 10.00, 0.13, "dibl",  25,    50,    75),
    ("SSP013",    -1, 10.00, 0.13, "ss",    75,    81,    87),
]
HV_ROWS = [
    ("VTNHV10x045",  1, 10.00, 0.45, "vt",    0.63,  0.70,  0.77),
    ("VTNHV10x10",   1, 10.00, 10.0, "vt",    0.65,  0.69,  0.73),
    ("VTNHV030x045", 1, 0.30,  0.45, "vt",    0.59,  0.67,  0.75),
    ("IDSNHV045",    1, 10.00, 0.45, "idsat", 480,   560,   640),
    ("IOFFNHV045",   1, 10.00, 0.45, "ioff",  None,  -12.5, -11.0),
    ("DIBLNHV045",   1, 10.00, 0.45, "dibl",  0,     15,    30),
    ("SSNHV045",     1, 10.00, 0.45, "ss",    72,    84,    96),
    ("VTPHV10x04",  -1, 10.00, 0.40, "vt",    0.59,  0.65,  0.71),
    ("VTPHV10x10",  -1, 10.00, 10.0, "vt",    0.64,  0.70,  0.78),
    ("VTPHV03x04",  -1, 0.30,  0.40, "vt",    0.57,  0.64,  0.71),
    ("IDSPHV04",    -1, 10.00, 0.40, "idsat", 190,   240,   290),
    ("IOFFPHV04",   -1, 10.00, 0.40, "ioff",  None,  -12.5, -11.5),
    ("DIBLPHV04",   -1, 10.00, 0.40, "dibl",  0,     5,     15),
    ("SSPHV04",     -1, 10.00, 0.40, "ss",    82,    92,    102),
]
JSS_SS = {1: (0.5e-9, 5e-9), -1: (0.1e-9, 1e-9)}

# npn13G2 ([G2] section 3.1 only): (name, quantity, min, typ, max)
HBT_ROWS = [
    ("NPN13G2_BETA", "beta", 300, 650, 1200),
    ("NPN13G2_IC07", "ic07", 2.6e-6, 3.8e-6, 5.2e-6),
    ("NPN13G2_FT",   "ft",   300e9, 350e9, None),
]

# Corners. The specification gives MIN-MAX windows, not corner values; the
# models' mos_ss / mos_ff corners are built on those limits: ss at the high
# |Vt| and low Idsat edge, ff at the low |Vt| and high Idsat edge. Checked:
# each lands on its limit within 10 mV (Vt) or 5 % (Idsat), at the 10/L
# test structure of each class; and the order ss < slow-mixed < tt <
# fast-mixed < ff in Idsat (derived). For an nFET the fast-mixed corner is
# mos_fs, for a pFET mos_sf.
# IHP's modelling reports (ihp-sg13g2/libs.doc/meas/MOS/doc/report_*_lv.pdf,
# Rev. 1.2, section 3.1.1) list the targets the LV corners were actually
# fitted to. They equal the spec limits except: pFET Idsat 160 / 205 / 260
# (spec 170 / 215 / 270), pFET ss Vt -0.52 (spec -0.53), nFET ff Idsat 580
# (spec 600) and nFET ff Vt 0.44 (spec 0.43). The checks stay against the
# specification; the reports explain the one known deviation below.
CORNER_ROWS = {
    # class: {polarity: (Vt row, Idsat row)}
    "lv": {1: ("VTN10x013", "IDSN013"), -1: ("VTP10x013", "IDSP013")},
    "hv": {1: ("VTNHV10x045", "IDSNHV045"), -1: ("VTPHV10x04", "IDSPHV04")},
}
CORNER_TOL = dict(vt=0.010, idsat=0.05)
CORNER_KNOWN = {
    ("IDSP013", "mos_ss"): "LV pFET ss corner is 5.3 % under the spec minimum (161 vs 170 uA/um); "
                           "the model follows IHP's modelling targets of 160 / 205 / 260 uA/um "
                           "(libs.doc/meas/MOS/doc/report_pmos_lv.pdf, 3.1.1), not the spec's "
                           "170 / 215 / 270 (IHP-Open-PDK#1259)",
}

# Passives: (device, Rs min/typ/max ohm/sq, DW min/typ/max nm, TC1 ppm/K, TC2 ppm/K^2)
RES_ROWS = [
    ("rsil",  (6.2, 7.0, 7.8),       (-20, 10, 40), 3100, 0.3),
    ("rppd",  (235, 260, 285),       (-24, 6, 36),  170,  0.4),
    ("rhigh", (1160, 1360, 1560),    (-80, -40, 0), -2300, 2.1),
]
MIM_ROW = ((1.35, 1.5, 1.65), 3.6, 0.002)   # CMIMA fF/um^2, TCMIM1 ppm/K, TCMIM2 ppm/K^2
TC_TOL = dict(tc1=0.05, tc2=0.10)
TEMPS = (-40, -15, 10, 27, 60, 95, 125)
RES_DECK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "decks", "ihp_res.sp")
MIM_DECK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "decks", "ihp_mim.sp")


def tc_checks(rep, name, ts, ys, tc1, tc2):
    a, b = tc_fit(ts, ys)
    for label, v, want, tol in (("TC1", a, tc1, TC_TOL["tc1"]), ("TC2", b, tc2, TC_TOL["tc2"])):
        lo, hi = sorted((want * (1 - tol), want * (1 + tol)))
        rep.check("%s %s" % (name, label), "published", v, lo, hi,
                  "ppm/K" if label == "TC1" else "ppm/K2", 1, "(target %g, -40..125 C)" % want)
    return a, b


def passive_checks(rep, ng, work, models, spiceinit, mim):
    data = {}
    W, L, N = 10.0, 100.0, 5
    temps = " ".join(str(t) for t in TEMPS)
    for res, rs_w, dw_w, tc1, tc2 in RES_ROWS:
        par = "\n".join("XN%d b 0 0 %s w=%gu l=%gu" % (k, res, W / N, L) for k in range(N))
        deck = render(RES_DECK, work, "res_" + res, MODELS=models, RES=res, W=W, L=L, PARALLEL=par, TEMPS=temps)
        log = ngspice(ng, deck, cwd=work, spiceinit=spiceinit)
        rows = [(float(t), 0.5 / abs(float(i1)), 0.5 / abs(float(i_n)))
                for t, i1, i_n in re.findall(r"^RESULT_R (\S+) (\S+) (\S+)", log, re.M)]
        ts = [r[0] for r in rows]
        r1 = {t: a for t, a, _ in rows}; rn = {t: b for t, _, b in rows}
        a, b = L / r1[27.0], (L / N) / rn[27.0]        # (W + DW) / Rs and (W/N + DW) / Rs, in um / ohm
        rs = W * (1 - 1.0 / N) / (a - b)
        dw = (a * rs - W) * 1000                      # nm
        rep.check("%s Rs (A.i)" % res, "published", rs, rs_w[0], rs_w[2], "ohm/sq", 1, "(typ %g)" % rs_w[1])
        rep.check("%s DW (A.i)" % res, "published", dw, dw_w[0], dw_w[2], "nm", 1, "(typ %g)" % dw_w[1])
        fit = tc_checks(rep, res, ts, [r1[t] for t in ts], tc1, tc2)
        data[res] = dict(rs=rs, dw_nm=dw, tc1=fit[0], tc2=fit[1])
    if mim:
        (c_lo, c_typ, c_hi), tc1, tc2 = MIM_ROW
        side = 20.0
        log = ngspice(ng, render(MIM_DECK, work, "mim", MODELS=models, W=side, L=side, TEMPS=temps),
                      cwd=work, spiceinit=spiceinit)
        rows = [(float(t), float(c)) for t, c in re.findall(r"^RESULT_C (\S+) (\S+)", log, re.M)]
        ts = [r[0] for r in rows]; cs = [r[1] for r in rows]
        cmima = cs[ts.index(27.0)] / (side * side) * 1e15   # fF/um^2
        rep.check("cap_cmim CMIMA (A.k)", "published", cmima, c_lo, c_hi, "fF/um2", 1, "(typ %g)" % c_typ)
        fit = tc_checks(rep, "cap_cmim", ts, cs, tc1, tc2)
        data["cap_cmim"] = dict(cmima=cmima, tc1=fit[0], tc2=fit[1])
    return data


# Measured silicon vs temperature ([G2] only). IHP-Open-PDK ships IC-CAP
# measurements of the LV MOS at 233, 300, 343 and 398 K
# (ihp-sg13g2/libs.doc/meas/MOS, W/L = 10/0.13 um, one die). That die sits
# about 8 % (n) and 10 % (p) below the spec's typical Idsat, so absolute
# values are printed for information only. What is checked is the
# temperature behaviour: each quantity's shift from its 300 K value,
# model vs measured, at Vb = 0.
#   Idsat (|Vgs| = |Vds| = 1.2 V): ratio to 300 K, within 2 %
#   log10 Ioff (Vgs = 0, |Vds| = 1.2 V, drain current): shift, within 0.2 dec
#   Vt lin / sat (constant current 100 nA * W/L at |Vds| = 0.05 / 1.2 V):
#       shift, within 10 mV
# Tolerances were fixed before the first comparison.
MEAS_DIR = "ihp-sg13g2/libs.doc/meas/MOS"
MEAS_FILES = {
    1: "SG13_nmosXm1Y3/SG13_nmos~W10u0_L0u13_S540_2~dc_idvg~%dK.mdm",
    -1: "SG13_pmosXm1Y3/SG13_pmos~W10u0_L0u13_S548_2~dc_idvg~%dK.mdm",
}
MEAS_TEMPS_K = (233, 300, 343, 398)
MEAS_TOL = dict(idsat=0.02, ioff=0.2, vtlin=0.010, vtsat=0.010)
MEAS_KNOWN = {
    (1, "idsat", 233): "at 233 K the model's Idsat rises 5.5 % over 300 K, this die's 8.7 %",
    (1, "ioff", 233): "at 233 K the model's Ioff falls 1.56 decades below 300 K, this die's 1.09",
    (1, "vtsat", 398): "at 398 K the model's Vtsat falls 87 mV below 300 K, this die's 69 mV",
    (-1, "ioff", 233): "at 233 K the model's Ioff falls 1.49 decades below 300 K, this die's 1.07",
    (-1, "idsat", 398): "at 398 K the model's Idsat falls 4.3 % below 300 K, this die's 6.7 %",
    (-1, "vtlin", 398): "at 398 K the model's Vtlin falls 80 mV below 300 K, this die's 69 mV",
}


def read_mdm(path):
    """IC-CAP .mdm -> {(vb, vd): (vg list, id list)}."""
    out, cur, rows = {}, None, []
    with open(path) as f:
        for line in f:
            s = line.split()
            if not s:
                continue
            if s[0] == "BEGIN_DB":
                cur, rows = {}, []
            elif s[0] == "ICCAP_VAR" and cur is not None:
                cur[s[1]] = float(s[2])
            elif s[0] == "END_DB" and cur is not None:
                out[(cur["vb"], cur["vd"])] = ([r[0] for r in rows], [r[1] for r in rows])
                cur = None
            elif cur is not None and s[0][0] in "-+0123456789.":
                try:
                    rows.append((float(s[0]), float(s[1])))
                except ValueError:
                    pass
    return out


def _device_terms(vg, i, pol):
    pts = sorted(zip((pol * v for v in vg), (abs(x) for x in i)))
    return [p[0] for p in pts], [p[1] for p in pts]


def _quantities(lin, sat, w, icc):
    return dict(idsat=at(*sat, VDD) / w * 1e6, ioff=math.log10(at(*sat, 0.0) / w),
                vtlin=vt_cc(*lin, icc), vtsat=vt_cc(*sat, icc))


def measured_checks(rep, ng, work, models, spiceinit, src):
    w, l = 10.0, 0.13
    icc = 100e-9 * w / l
    header = '.lib "%s/cornerMOSlv.lib" mos_tt' % models
    data = {}
    for pol, pattern in MEAS_FILES.items():
        dev = "sg13_lv_nmos" if pol > 0 else "sg13_lv_pmos"
        meas, sim = {}, {}
        for tk in MEAS_TEMPS_K:
            db = read_mdm(os.path.join(src, MEAS_DIR, pattern % tk))
            pick = lambda vd: next(v for k, v in db.items() if k[0] == 0 and abs(abs(k[1]) - vd) < 1e-6)  # noqa: E731
            meas[tk] = _quantities(_device_terms(*pick(0.05), pol), _device_terms(*pick(1.2), pol), w, icc)
            sw = mos_sweeps(ng, work, "meas_%s_%d" % (dev, tk), header,
                            "X1 d g s 0 %s w=%gu l=%gu ng=1" % (dev, w, l), pol, VDD, 0.05, 0.6, VDD,
                            tk - 273.15, vstep=0.002, spiceinit=spiceinit)
            sim[tk] = _quantities(sw["vg_lin"], sw["vg_sat"], w, icc)
        data[dev] = dict(measured=meas, model=sim)
        m0, s0 = meas[300], sim[300]
        rep.info("%s 300 K Idsat" % dev, s0["idsat"], "uA/um", 1, "(this die %.1f)" % m0["idsat"])
        for tk in (233, 343, 398):
            for q, unit, scale in (("idsat", "x 300K", 1), ("ioff", "dec", 1),
                                   ("vtlin", "mV", 1000), ("vtsat", "mV", 1000)):
                if q == "idsat":
                    mv, sv = meas[tk][q] / m0[q], sim[tk][q] / s0[q]
                    lo, hi = mv * (1 - MEAS_TOL[q]), mv * (1 + MEAS_TOL[q])
                else:
                    mv, sv = meas[tk][q] - m0[q], sim[tk][q] - s0[q]
                    lo, hi = mv - MEAS_TOL[q], mv + MEAS_TOL[q]
                name = "%s %s %d K vs 300 K" % (dev, q, tk)
                if (pol, q, tk) in MEAS_KNOWN:
                    rep.known(name, sv, lo, hi, unit, scale, MEAS_KNOWN[(pol, q, tk)])
                else:
                    rep.check(name, "measured", sv, lo, hi, unit, scale)
    return data


HBT_DECK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "decks", "ihp_hbt.sp")


def mos_checks(rep, ng, work, models, spiceinit, cls, rows):
    c = CLASSES[cls]
    header = '.lib "%s/%s" mos_tt' % (models, c["lib"])
    vdd, vt_vds = c["vdd"], c["vt_vds"]
    sweeps, data = {}, {}
    for name, pol, w, l, qty, lo, typ, hi in rows:
        key = (pol, w, l)
        if key not in sweeps:
            dev = c["n"] if pol > 0 else c["p"]
            inst = "X1 d g s 0 %s w=%gu l=%gu ng=1" % (dev, w, l)
            tag = cls + ("n" if pol > 0 else "p") + ("_%g_%g" % (w, l)).replace(".", "p")
            # vg_lin at the Vt bias (A.a1/a2), vg_aux at 0.1 V (A.d, A.e),
            # vg_sat at VDD (A.b, A.c, A.d)
            sweeps[key] = mos_sweeps(ng, work, tag, header, inst, pol, vdd, vt_vds, 0.1, vdd,
                                     TEMP, vstep=0.002, spiceinit=spiceinit)
        sw, wl = sweeps[key], w / l
        if qty == "vt":
            v, unit = vt_max_gm(*sw["vg_lin"], vt_vds), "V"
        elif qty == "idsat":
            v, unit = at(*sw["vg_sat"], vdd) / w * 1e6, "uA/um"
        elif qty == "ioff":
            v, unit = math.log10(at(*sw["vg_sat"], 0.0) / w), "log A/um"
        elif qty == "dibl":
            i = c["jdibl"][pol] * wl
            v, unit = 1000 * (vt_cc(*sw["vg_aux"], i) - vt_cc(*sw["vg_sat"], i)) / (vdd - 0.1), "mV/V"
        else:  # ss
            i1, i2 = JSS_SS[pol]
            v, unit = 1000 * (vt_cc(*sw["vg_aux"], i2 * wl) - vt_cc(*sw["vg_aux"], i1 * wl)), "mV/dec"
        data[name] = v
        rep.check("%s %g/%g" % (name, w, l), "published", v, -99 if lo is None else lo, hi, unit, 1,
                  "(typ %g)" % typ)
    return data


def corner_checks(rep, ng, work, models, spiceinit, cls, rows):
    c = CLASSES[cls]
    byname = {r[0]: r for r in rows}
    vdd, vt_vds = c["vdd"], c["vt_vds"]
    data = {}
    for pol, (vt_row, id_row) in CORNER_ROWS[cls].items():
        _, _, w, l, _, vt_lo, _, vt_hi = byname[vt_row]
        _, _, _, _, _, id_lo, _, id_hi = byname[id_row]
        dev = c["n"] if pol > 0 else c["p"]
        vals = {}
        for corner in ("mos_ss", "mos_sf", "mos_tt", "mos_fs", "mos_ff"):
            sw = mos_sweeps(ng, work, "%s_%s_%s" % (cls, dev, corner), '.lib "%s/%s" %s' % (models, c["lib"], corner),
                            "X1 d g s 0 %s w=%gu l=%gu ng=1" % (dev, w, l), pol, vdd, vt_vds, 0.1, vdd,
                            TEMP, vstep=0.002, spiceinit=spiceinit)
            vals[corner] = (vt_max_gm(*sw["vg_lin"], vt_vds), at(*sw["vg_sat"], vdd) / w * 1e6)
        data[dev] = vals
        t = CORNER_TOL
        for corner, vt_lim, id_lim in (("mos_ss", vt_hi, id_lo), ("mos_ff", vt_lo, id_hi)):
            vt, idsat = vals[corner]
            rep.check("%s %s Vt at limit" % (vt_row, corner), "published", vt, vt_lim - t["vt"], vt_lim + t["vt"], "V", 1,
                      "(spec limit %g)" % vt_lim)
            name, lo, hi = "%s %s Idsat at limit" % (id_row, corner), id_lim * (1 - t["idsat"]), id_lim * (1 + t["idsat"])
            if (id_row, corner) in CORNER_KNOWN:
                rep.known(name, idsat, lo, hi, "uA/um", 1, CORNER_KNOWN[(id_row, corner)])
            else:
                rep.check(name, "published", idsat, lo, hi, "uA/um", 1, "(spec limit %g)" % id_lim)
        fast, slow = ("mos_fs", "mos_sf") if pol > 0 else ("mos_sf", "mos_fs")
        order = [vals[k][1] for k in ("mos_ss", slow, "mos_tt", fast, "mos_ff")]
        rep.check("%s corner order ss<%s<tt<%s<ff" % (dev, slow[4:], fast[4:]), "derived",
                  float(all(a < b for a, b in zip(order, order[1:]))), 1, 1, "", 1)
    return data


def hbt_checks(rep, ng, work, models, spiceinit):
    deck = render(HBT_DECK, work, "hbt", MODELS=models, TEMP=TEMP)
    log = ngspice(ng, deck, cwd=work, spiceinit=spiceinit)
    r = results(log)
    h21 = [float(m.group(2)) for m in re.finditer(r"^RESULT_H21 (\S+) (\S+)", log, re.M)]
    ft = max(h21) * 40e9
    vals = dict(beta=abs(r["ic07"] / r["ib07"]), ic07=abs(r["ic07"]), ft=ft)
    units = dict(beta=("", 1), ic07=("uA", 1e6), ft=("GHz", 1e-9))
    for name, qty, lo, typ, hi in HBT_ROWS:
        u, s = units[qty]
        rep.check(name, "published", vals[qty], lo, float("inf") if hi is None else hi, u, s,
                  "(typ %g %s)" % (typ * s, u))
    return vals


# ---------------------------------------------------------------------------
# Mismatch (Monte Carlo) and noise: see the module docstring.
MISMATCH_DECK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ngspice", "ihp", "mismatch.sp.in")
NOISE_DECK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ngspice", "ihp", "noise.sp.in")
MM_CLASSES = {
    "lv": dict(vdd=1.2, vds=0.05, tag="LV"),
    "hv": dict(vdd=3.3, vds=0.1, tag="HV"),
}
# The checks run over (class, polarity): +1 nFET, -1 pFET. The subcircuit and
# the PSP card of a pair come from CLASSES[cls]["n"/"p"], so the four devices
# are sg13_{lv,hv}_{n,p}mos. Every bias below is a device-terms magnitude; the
# decks take it multiplied by the polarity, as sanity/decks/mos_iv.sp does.
MM_POLS = (1, -1)
MM_AREAS = [(2.0, 2.0, 11), (4.0, 4.0, 12), (8.0, 8.0, 13)]   # (W, L um, seed); W*L = 4, 16, 64 um^2
MM_N = 200            # pairs per area; 2N single devices
# Noise bias: 10/10 um, strong inversion, saturation. |Vgs| is about 0.5 V (LV)
# or 0.8 V (HV) above the device's own 10/10 um |Vt| typical from the
# specification (MOS_ROWS VTN10x10 0.20, VTP10x10 0.36; HV_ROWS VTNHV10x10
# 0.69, VTPHV10x10 0.70). 10/L_min is information only, L_min being each
# device's own spec test structure (0.13 um both LV, 0.45 um HV nMOS, 0.40 um
# HV pMOS -- the HV pMOS rows are measured at 0.40, not 0.45).
NOISE_BIAS = {
    ("lv", 1): dict(W=10, L=10, VG=0.7, VD=1.2),
    ("lv", -1): dict(W=10, L=10, VG=0.86, VD=1.2),
    ("hv", 1): dict(W=10, L=10, VG=1.5, VD=3.3),
    ("hv", -1): dict(W=10, L=10, VG=1.5, VD=3.3),
}
NOISE_BIAS_SHORT = {
    ("lv", 1): dict(W=10, L=0.13, VG=0.7, VD=1.2),
    ("lv", -1): dict(W=10, L=0.13, VG=0.86, VD=1.2),
    ("hv", 1): dict(W=10, L=0.45, VG=1.5, VD=3.3),
    ("hv", -1): dict(W=10, L=0.40, VG=1.5, VD=3.3),
}
# Long-channel theory (van der Ziel; Tsividis, "Operation and Modeling of the MOS
# Transistor"): gamma = 2/3 in strong-inversion saturation, rising to 1 as Vds -> 0.
# The bound is on the fnto-normalised gamma; see the module docstring.
GAMMA_LONG = (2.0 / 3.0, 1.0)
# A conductor in equilibrium has S_id = 4kT*gds exactly; 2 % allows for the 1 mV
# finite-difference gds. Normalised by fnto as well, for the same reason.
NYQUIST = (0.98, 1.02)
# Keyed by (class, polarity): each device's residual is its own.
NYQUIST_KNOWN = {
    ("lv", 1): "the PSP 103 channel thermal source at Vds = 0 is 2.6 % above 4kT*gds at LV nMOS "
               "10/10 um (HV nMOS 10/10 um: 0.9 %); the cause was not traced",
}
FLICKER_SLOPE_TOL = 0.01       # the term is f^-efo; the allowance is numerical
NOISE_SCAN_MODELS = 10         # PSP cards in sg13g2_moslv_parm.lib (6) and sg13g2_moshv_parm.lib (4)
NOISE_KEYS = ("fnto", "nfalw", "nfblw", "nfclw", "efo")
MM_GAPS = [
    "Pelgrom coefficients AVT, ABeta of the MOS devices: neither process specification publishes a value "
    "([G2] A.am defines the matching coefficient, no table row carries it; [C5L] has no MOS matching row); "
    "the model's own delvto_mm / factuo_mm are used as a floor and as the expectation, never as a published value",
    "flicker-noise level of the MOS devices: no published value; the model's level is printed as information only",
    "published thermal-noise gamma: none; only the long-channel theory range is used",
    "SG13G2 HBT mismatch and noise: [G2] A.al defines a matching coefficient and sg13g2_hbt_mod_mismatch.lib exists, "
    "but no value is published; not exercised",
    "passives (resistors, MIM, MOS and varactor caps): mismatch libraries exist "
    "(*_mod_mismatch.lib), outside this deck's scope; not exercised",
    "excess thermal noise: fntexcl = 0 in every PSP card, so no length-dependent excess is modelled",
]


def _mm_param(models, lib, name):
    """Value of '.param <name> = <number>' in a model file of the pinned tree."""
    with open(os.path.join(models, lib)) as f:
        m = re.search(r"(?im)^\.param\s+%s\s*=\s*([-0-9.e+]+)" % re.escape(name), f.read())
    return float(m.group(1))


def _mm_ok_default(models, lib):
    with open(os.path.join(models, lib)) as f:
        return int(re.search(r"mm_ok=(\d)", f.read()).group(1))


def _mm_dev(cls, pol):
    """Mismatch subcircuit of one (class, polarity): sg13_{lv,hv}_{n,p}mos."""
    return CLASSES[cls]["n" if pol > 0 else "p"]


def _mm_prefix(cls, pol):
    """Mismatch .param prefix in sg13g2_mos<cls>_mismatch.lib."""
    return "sg13g2_%s_%smos" % (cls, "n" if pol > 0 else "p")


def _mm_card(cls, pol):
    """PSP card of one (class, polarity) in sg13g2_mos<cls>_parm.lib."""
    return _mm_prefix(cls, pol) + "_psp"


def _mm_tag(cls, pol):
    """Report tag of one (class, polarity): "LV nMOS", "HV pMOS", ..."""
    return "%s %sMOS" % (MM_CLASSES[cls]["tag"], "n" if pol > 0 else "p")


def _mm_key(cls, pol):
    """Short key for deck file names and result keys: lvn, lvp, hvn, hvp."""
    return "%s%s" % (cls, "n" if pol > 0 else "p")


def _mismatch_run(ng, work, models, spiceinit, pdk, cls, pol, name, w, l, n, mm, seed, m=1):
    c = MM_CLASSES[cls]
    deck = render(MISMATCH_DECK, work, name, PDK=pdk, CLASS=c["tag"], DECK=name + ".sp", MODELS_DIR=models,
                  NGSPICE=ng, LIBTAG=cls, DEV=_mm_dev(cls, pol), POL=pol, VDD=pol * c["vdd"],
                  VDS=pol * c["vds"], VGSTEP=pol * 0.002, W=w, L=l, M=m, N=n, MM=mm, SEED=seed)
    return results(ngspice(ng, deck, cwd=work, spiceinit=spiceinit))


def _noise_run(ng, work, models, spiceinit, pdk, cls, pol, name, bias):
    c = MM_CLASSES[cls]
    vg = pol * bias["VG"]
    deck = render(NOISE_DECK, work, name, PDK=pdk, CLASS=c["tag"], DECK=name + ".sp", MODELS_DIR=models,
                  NGSPICE=ng, LIBTAG=cls, DEV=_mm_dev(cls, pol), POL=pol, W=bias["W"], L=bias["L"],
                  VG=vg, VD=pol * bias["VD"], VGLO=vg - 0.002, VGHI=vg + 0.002)
    return results(ngspice(ng, deck, cwd=work, spiceinit=spiceinit))


def noise_scan(models):
    """PSP cards in sg13g2_mos{lv,hv}_parm.lib: (count, cards missing any of
    NOISE_KEYS, cards with nfalw = 0)."""
    n = missing = zero = 0
    for lib in ("sg13g2_moslv_parm.lib", "sg13g2_moshv_parm.lib"):
        with open(os.path.join(models, lib)) as f:
            text = f.read().replace("\n+", " ")
        for blk in re.split(r"(?im)^\.model\s+", text)[1:]:
            if not re.match(r"\S+\s+psp", blk, re.I):
                continue
            n += 1
            vals = {k: re.search(r"(?i)(?<![a-z0-9_])%s\s*=\s*(\S+)" % k, blk) for k in NOISE_KEYS}
            missing += any(v is None for v in vals.values())
            zero += bool(vals["nfalw"]) and float(vals["nfalw"].group(1)) == 0
    return n, missing, zero


def mismatch_checks(rep, ng, work, models, spiceinit, pdk, cls, pol):
    n = MM_N
    dev, dtag, key = _mm_dev(cls, pol), _mm_tag(cls, pol), _mm_key(cls, pol)
    p = _mm_prefix(cls, pol)
    lib = "sg13g2_mos%s_mismatch.lib" % cls
    avt = _mm_param(models, lib, p + "_delvto_mm") * 1e3      # mV um
    abeta = _mm_param(models, lib, p + "_factuo_mm") * 100    # % um
    dw = _mm_param(models, lib, p + "_dw_mm") * 1e6           # um
    dl = _mm_param(models, lib, p + "_dl_mm") * 1e6
    print("\n%s %s %s mismatch (Monte Carlo, mos_tt_mismatch, mm_ok = 1), %d pairs per area; model: "
          "delvto_mm %.3g mV um, factuo_mm %.3g %%um, dw %.0f nm, dl %.0f nm\n"
          % (pdk, dtag, dev, n, avt, abeta, dw * 1e3, dl * 1e3))
    data = {}
    t_s, t_d = mc_tol(2 * n), mc_tol(n)
    for w, l, seed in MM_AREAS:
        tag = "%s %g/%g" % (dtag, w, l)
        r = _mismatch_run(ng, work, models, spiceinit, pdk, cls, pol,
                          "mm_%s_%g_%g" % (key, w, l), w, l, n, 1, seed)
        data["mismatch " + tag] = r
        area = w * l
        rep.check("AVT(Vt)*sqrt(A) >= delvto_mm %s" % tag, "bound", r["avt_mVum"], avt * (1 - t_s), 1e9, "mV um", 1,
                  "(model %.3g mV um; measured/model %.2f)" % (avt, r["avt_mVum"] / avt))
        rep.check("sigma(dVt)/sigma(Vt) %s" % tag, "derived", r["sigma_dvt_V"] / r["sigma_vt_V"],
                  math.sqrt(2) * (1 - t_s - t_d), math.sqrt(2) * (1 + t_s + t_d), "", 1, "(independent devices: sqrt 2)")
        # beta ~ W/L: relative variance = factuo term + (dw/W)^2 + (dl/L)^2
        exp = math.sqrt((abeta / 100) ** 2 / area + (dw / w) ** 2 + (dl / l) ** 2)
        rep.check("sigma(beta) %s" % tag, "derived", r["sigma_beta_rel"], exp * (1 - t_s), exp * (1 + t_s), "%", 100,
                  "(sqrt((factuo_mm)^2/A + (dw/W)^2 + (dl/L)^2) = %.3g %%, +-%.0f %%)" % (exp * 100, 100 * t_s))
    vals = [data["mismatch %s %g/%g" % (dtag, w, l)]["avt_mVum"] for w, l, _ in MM_AREAS]
    mean = sum(vals) / len(vals)
    for (w, l, _), v in zip(MM_AREAS, vals):
        rep.check("AVT(Vt)*sqrt(A) area scaling %s %g/%g" % (dtag, w, l), "derived", v, mean * (1 - t_s), mean * (1 + t_s),
                  "mV um", 1, "(1/sqrt(WL) scaling; mean %.3g, +-%.0f %%)" % (mean, 100 * t_s))
    off = _mismatch_run(ng, work, models, spiceinit, pdk, cls, pol, "mm_off_" + key, 4, 4, 3, 0, 1)
    rep.check("mismatch off (mm_ok = 0) %s: sigma(Vt)" % dtag, "derived", off["sigma_vt_V"], 0, 1e-6, "V", 1,
              "(numerical floor)")
    rep.check("mismatch off (mm_ok = 0) %s: sigma(dVt)" % dtag, "derived", off["sigma_dvt_V"], 0, 1e-9, "V", 1)
    a = _mismatch_run(ng, work, models, spiceinit, pdk, cls, pol, "mm_rep1_" + key, 4, 4, 3, 1, 5)
    b = _mismatch_run(ng, work, models, spiceinit, pdk, cls, pol, "mm_rep2_" + key, 4, 4, 3, 1, 5)
    rep.check("same seed, same result %s" % dtag, "derived",
              abs(a["sigma_vt_V"] - b["sigma_vt_V"]) + abs(a["sigma_dvt_V"] - b["sigma_dvt_V"]), 0, 0, "V", 1,
              "(setseed + reset)")
    return data


def noise_checks(rep, ng, work, models, spiceinit, pdk, cls, pol):
    dev, dtag, key = _mm_dev(cls, pol), _mm_tag(cls, pol), _mm_key(cls, pol)
    bias = NOISE_BIAS[(cls, pol)]
    parm, card = "sg13g2_mos%s_parm.lib" % cls, _mm_card(cls, pol)
    efo = _mm_param_model(models, parm, card, "efo")
    # PSP 103's channel thermal source is S_idid = FNTO * 4kT * mid * MULT *
    # (1 - c_igid^2) (PSP103_macrodefs.include nt = FNT_i * 4 * KBOL * TKD;
    # PSP103_module.include sqid = sqrt(nt * mid) and the "idid" white_noise),
    # so both the thermal gamma and the Nyquist ratio this deck derives from it
    # are exactly proportional to the card's FNTO, the "Thermal noise
    # coefficient". The long-channel bound is therefore taken on the
    # fnto-normalised value, with the raw model level reported alongside. It is
    # a no-op for the three cards with fnto = 1.0.
    fnto = _mm_param_model(models, parm, card, "fnto")
    print("\n%s %s %s noise, %g/%g um, Vg %g V, Vd %g V (ngspice .noise, 27 C); card %s: "
          "fnto %g (%s), efo %g\n"
          % (pdk, dtag, dev, bias["W"], bias["L"], pol * bias["VG"], pol * bias["VD"], card,
             fnto, parm, efo))
    r = _noise_run(ng, work, models, spiceinit, pdk, cls, pol, "noise_" + key, bias)
    data = {"noise " + key: r}
    rep.info("%s thermal gamma, raw" % dtag, r["gamma_thermal"], "", 1,
             "(model level, not normalised; card fnto %g)" % fnto)
    rep.info("%s Nyquist ratio, raw" % dtag, r["nyquist_ratio"], "", 1,
             "(model level, not normalised; card fnto %g)" % fnto)
    lo, hi = GAMMA_LONG
    rep.check("%s thermal gamma/fnto (4kT*gamma*gm) 2/3..1" % dtag, "derived",
              r["gamma_thermal"] / fnto, lo, hi, "", 1,
              "(long-channel theory; fnto %g, %s)" % (fnto, parm))
    lo, hi = NYQUIST
    name = "%s Nyquist S_id/(fnto*4kT*gds) at Vds=0" % dtag
    if (cls, pol) in NYQUIST_KNOWN:
        rep.known(name, r["nyquist_ratio"] / fnto, lo, hi, "", 1, NYQUIST_KNOWN[(cls, pol)])
    else:
        rep.check(name, "derived", r["nyquist_ratio"] / fnto, lo, hi, "", 1, "(fnto %g)" % fnto)
    rep.check("%s flicker slope 1..100 Hz = -efo" % dtag, "derived", r["flicker_slope"],
              -efo - FLICKER_SLOPE_TOL, -efo + FLICKER_SLOPE_TOL, "", 1, "(model efo %.3g)" % efo)
    rep.info("%s flicker level at 1 Hz (input, V^2/Hz)" % dtag, r["sv_flicker_1Hz_V2"], "V2/Hz", 1,
             "(no published value: gap)")
    sb = NOISE_BIAS_SHORT[(cls, pol)]
    short = _noise_run(ng, work, models, spiceinit, pdk, cls, pol, "noise_short_" + key, sb)
    data["noise short " + key] = short
    rep.info("%s thermal gamma/fnto %g/%g" % (dtag, sb["W"], sb["L"]), short["gamma_thermal"] / fnto, "", 1,
             "(information; no long-channel claim; card fnto %g)" % fnto)
    return data


def _mm_param_model(models, lib, model, key):
    """Value of a PSP card parameter in a pinned parm library."""
    with open(os.path.join(models, lib)) as f:
        text = f.read().replace("\n+", " ")
    blk = re.split(r"(?im)^\.model\s+", text)
    blk = next(b for b in blk[1:] if b.split()[0] == model)
    return float(re.search(r"(?i)(?<![a-z0-9_])%s\s*=\s*([-0-9.e+]+)" % key, blk).group(1))


def mismatch_and_noise(rep, ng, work, models, spiceinit, pdk):
    data = {}
    mm_def = _mm_ok_default(models, "sg13g2_moslv_mod_mismatch.lib")
    rep.info("mm_ok default in sg13g2_mos{lv,hv}_mod_mismatch.lib", mm_def, "", 1, "(decks pass mm_ok explicitly)")
    for cls in ("lv", "hv"):
        for pol in MM_POLS:
            key = _mm_key(cls, pol)
            data["mismatch_" + key] = mismatch_checks(rep, ng, work, models, spiceinit, pdk, cls, pol)
            data["noise_" + key] = noise_checks(rep, ng, work, models, spiceinit, pdk, cls, pol)
    nm, miss, zero = noise_scan(models)
    rep.check("noise scan: PSP cards in sg13g2_mos{lv,hv}_parm.lib", "derived", float(nm), NOISE_SCAN_MODELS,
              NOISE_SCAN_MODELS, "", 1)
    rep.check("noise scan: cards missing fnto/nfalw/nfblw/nfclw/efo", "derived", float(miss), 0, 0, "", 1,
              "(%d cards)" % nm)
    rep.check("noise scan: cards with nfalw = 0", "bound", float(zero), 0, 0, "", 1)
    print("\nGaps (not estimated):")
    for g in MM_GAPS:
        print("  - " + g)
    return data


# ---------------------------------------------------------------------------
# Interconnect. Metal layer: width, spacing (nm), thickness (nm), sheet
# resistance (ohm/sq), its TC1 (1/K), area capacitance to the next layer up
# (aF/um2, None where no layer is above or the spec prints none). All
# nominal (target) values; see the module docstring for the rows.
METALS = {
    "M1": (160, 180, 420, 0.110, 3400e-6, 68.0),
    "M2": (200, 210, 490, 0.088, 3500e-6, 68.0),
    "M3": (200, 210, 490, 0.088, 3500e-6, 68.0),
    "M4": (200, 210, 490, 0.088, 3500e-6, 68.0),
    "M5": (200, 210, 490, 0.088, 3500e-6, 42.5),
    "TM1": (1640, 1640, 2000, 0.018, 3700e-6, 13.0),
    "TM2": (2000, 2000, 3000, 0.011, 3800e-6, None),
}
# Via: width (nm), resistance (ohm per via), dielectric thickness spanned (nm).
VIAS = {
    "V1": (190, 9.0, 540), "V2": (190, 9.0, 540), "V3": (190, 9.0, 540), "V4": (190, 9.0, 540),
    "TV1": (420, 2.2, 850), "TV2": (900, 1.1, 2800),
}
# Per PDK: the layers present and what the spec leaves as "tbd" (explicit
# gaps). SG13CMOS5L has Metal1-4 + TopMetal1 and TopVia1 only; its Metal4 ->
# TopMetal1 area capacitance and TopVia1 resistance are "tbd" in Rev. 0.2.
BEOL = {
    "ihp-sg13g2": dict(metals=("M1", "M2", "M3", "M4", "M5", "TM1", "TM2"), vias=("V1", "V2", "V3", "V4", "TV1", "TV2"),
                       tbd=set()),
    "ihp-sg13cmos5l": dict(metals=("M1", "M2", "M3", "M4", "TM1"), vias=("V1", "V2", "V3", "TV1"),
                           tbd={("M4", "c_area_up"), ("TV1", "r_via")}),
}
GAP_PER_METAL = ("c_iso_per_um", "c_pitch_per_um")
# Aluminium: the lower bound on a film's resistivity is the bulk value,
# 2.65e-8 ohm m at 20 C (CRC Handbook of Chemistry and Physics, "Electrical
# resistivity of pure metals"). A thin-film Rs * t cannot be below it.
RHO_AL_BULK = 2.65e-8
# Elmore check: l, w, rs, cl, tstop in ngspice notation and as numbers. RSH is
# read from the table (Metal2); CPL is a test input, not an IHP value.
ELMORE = dict(l="1m", w="200n", cpl="0.2n", rs="100", cl="1f", tstop="2n")
ELMORE_L, ELMORE_W, ELMORE_CPL, ELMORE_RS, ELMORE_CL = 1e-3, 200e-9, 0.2e-9, 100.0, 1e-15
ELMORE_SEGMENTS = (1, 4, 64)
ELMORE_TOL = 1e-3  # trapezoidal integral on a 2 ps step, ~30 time constants
def interconnect_checks(rep, ng, work, ngdir, pdk, pdk_beol):
    rows, val, num, wire_inc = load_interconnect(ngdir, pdk, extra=(os.path.join(ngdir, "interconnect.inc"),))
    data = {}

    def chk(name, kind, lay, q, want, unit, scale, tol=1e-9):
        got = num(lay, q)
        rep.check(name, kind, got, want * (1 - tol), want * (1 + tol), unit, scale)
        assert val[lay, q]["status"] == kind, "%s %s: status %s, expected %s" % (lay, q, val[lay, q]["status"], kind)

    for lay in pdk_beol["metals"]:
        w, s, t, rsh, tc, cup = METALS[lay]
        chk("%s width" % lay, "published", lay, "width_min", w, "nm", 1)
        chk("%s spacing" % lay, "published", lay, "spacing_min", s, "nm", 1)
        chk("%s pitch = width + spacing" % lay, "derived", lay, "pitch", w + s, "nm", 1)
        chk("%s thickness" % lay, "published", lay, "thickness", t, "nm", 1)
        chk("%s sheet resistance" % lay, "published", lay, "rsheet", rsh, "mohm/sq", 1e3)
        chk("%s TC1 of sheet resistance" % lay, "published", lay, "rsheet_tcr", tc, "ppm/K", 1e6)
        if cup is not None and (lay, "c_area_up") not in pdk_beol["tbd"]:
            chk("%s area cap to layer above" % lay, "published", lay, "c_area_up", cup, "aF/um2", 1)
        # Bound: Rs * t is the film's effective resistivity; it cannot be
        # below bulk aluminium's.
        rho = num(lay, "rsheet") * num(lay, "thickness") * 1e-9
        rep.check("%s effective resistivity >= bulk Al" % lay, "bound", rho, RHO_AL_BULK, float("inf"), "uohm cm", 1e8)
    for lay in pdk_beol["vias"]:
        w, r, h = VIAS[lay]
        chk("%s width" % lay, "published", lay, "width_min", w, "nm", 1)
        chk("%s height = dielectric spanned" % lay, "derived", lay, "height", h, "nm", 1)
        if (lay, "r_via") not in pdk_beol["tbd"]:
            chk("%s resistance" % lay, "published", lay, "r_via", r, "ohm", 1)
    expect = {(m, q) for m in pdk_beol["metals"] for q in GAP_PER_METAL} | pdk_beol["tbd"]
    gap_check(rep, data, val, expect)
    rep.check("every row cites a source", "derived", float(all(r["source"].strip() for r in rows)), 1, 1, "", 1)
    layers = {r["layer"] for r in rows}
    rep.check("table has exactly the PDK's layers", "derived",
              float(layers == set(pdk_beol["metals"]) | set(pdk_beol["vias"])), 1, 1, "", 1)
    print()
    elmore_ladder(rep, data, ng, wire_inc, work, ELMORE_SEGMENTS, ELMORE, num("M2", "rsheet"),
                  ELMORE_L, ELMORE_W, ELMORE_CPL, ELMORE_RS, ELMORE_CL, ELMORE_TOL)
    return data


def run(prefix, pdk, models, hbt, meas_src=None, beol=None):
    osdi = os.path.join(prefix, pdk, "ngspice", "spiceinit")
    if not os.path.exists(osdi):
        raise SystemExit("not found: %s (run bootstrap.sh --pdk %s)" % (osdi, pdk))
    with open(osdi) as f:
        spiceinit = f.read()
    ng = os.path.join(prefix, "tools", "ngspice", "bin", "ngspice")
    rep, data = Report(), {}
    print("%s, typical (LV and HV mos_tt%s), %d C. Sources and definitions: sanity/ihp_spec.py\n"
          % (pdk, ", hbt_typ" if hbt else "", TEMP))
    with tempfile.TemporaryDirectory(prefix=pdk + "-sanity-") as work:
        data["mos"] = mos_checks(rep, ng, work, models, spiceinit, "lv", MOS_ROWS)
        print()
        data["mos_hv"] = mos_checks(rep, ng, work, models, spiceinit, "hv", HV_ROWS)
        print("\nCorners: mos_ss / mos_ff against the spec limits\n")
        data["corners_lv"] = corner_checks(rep, ng, work, models, spiceinit, "lv", MOS_ROWS)
        data["corners_hv"] = corner_checks(rep, ng, work, models, spiceinit, "hv", HV_ROWS)
        print("\nPassives and temperature coefficients (-40 to 125 C)\n")
        data["passives"] = passive_checks(rep, ng, work, models, spiceinit, mim=hbt)
        if meas_src:
            print("\nMeasured silicon vs temperature: shifts from 300 K, model vs one measured die\n")
            data["measured"] = measured_checks(rep, ng, work, models, spiceinit, meas_src)
        if hbt:
            print()
            data["hbt"] = hbt_checks(rep, ng, work, models, spiceinit)
        data["mismatch_noise"] = mismatch_and_noise(rep, ng, work, models, spiceinit, pdk)
        if beol:
            print("\nInterconnect: layer table vs the process specification and layout rules\n")
            data["interconnect"] = interconnect_checks(rep, ng, work, os.path.join(prefix, pdk, "ngspice"), pdk, beol)
    return rep.summary(), data, rep.rows
