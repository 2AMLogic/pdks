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


def run(prefix, pdk, models, hbt):
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
        if hbt:
            print()
            data["hbt"] = hbt_checks(rep, ng, work, models, spiceinit)
    return rep.summary(), data, rep.rows
