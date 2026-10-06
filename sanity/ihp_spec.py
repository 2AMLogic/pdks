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
"""

import math
import os
import re
import tempfile

from common import Report, at, mos_sweeps, ngspice, render, results, vt_cc, vt_max_gm

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
CORNER_ROWS = {
    # class: {polarity: (Vt row, Idsat row)}
    "lv": {1: ("VTN10x013", "IDSN013"), -1: ("VTP10x013", "IDSP013")},
    "hv": {1: ("VTNHV10x045", "IDSNHV045"), -1: ("VTPHV10x04", "IDSPHV04")},
}
CORNER_TOL = dict(vt=0.010, idsat=0.05)
CORNER_KNOWN = {
    ("IDSP013", "mos_ss"): "LV pFET ss corner is 5.3 % under the spec minimum (161 vs 170 uA/um); "
                           "the other seven corner limits land within 2 mV or 1 %",
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


def tc_fit(ts, ys, t0=27.0):
    """Least-squares TC1, TC2 (in ppm/K, ppm/K^2) of y(T) = y0 [1 + a dT + b dT^2]."""
    y0 = ys[ts.index(t0)]
    X = [(t - t0, (t - t0) ** 2) for t in ts]
    Z = [y / y0 - 1 for y in ys]
    sxx = sum(a * a for a, _ in X); sxy = sum(a * b for a, b in X); syy = sum(b * b for _, b in X)
    sxz = sum(a * z for (a, _), z in zip(X, Z)); syz = sum(b * z for (_, b), z in zip(X, Z))
    det = sxx * syy - sxy * sxy
    return (sxz * syy - syz * sxy) / det * 1e6, (syz * sxx - sxz * sxy) / det * 1e6


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


def run(prefix, pdk, models, hbt, meas_src=None):
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
    return rep.summary(), data, rep.rows
