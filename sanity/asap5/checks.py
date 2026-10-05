"""ASAP5 r0p4 sanity checks: per-fin device parameters of all eight
nanowire FETs against Vashishtha and Clark 2022, Tables 8-9. Sources,
definitions and tolerances: reference.py. Run via sanity/run.py --pdk asap5.
"""

import os
import tempfile

import reference as ref
from common import Report, at, mos_sweeps, vt_cc


def run(prefix, ng):
    models = os.path.join(prefix, "asap5", "ngspice", "models", "asap5.lib")
    osdi = os.path.join(prefix, "tools", "bsimcmg107", "bsimcmg107.osdi")
    for f in (models, osdi):
        if not os.path.exists(f):
            raise SystemExit("not found: %s (run bootstrap.sh --pdk asap5)" % f)
    header = '.lib "%s" tt' % models
    rep, data = Report(), {}
    print("ASAP5 TT, %d C, VDD %.2f V, per fin (nfin = 2 nanowires). "
          "Sources: sanity/asap5/reference.py\n" % (ref.TEMP, ref.VDD))
    t = ref.TOL
    with tempfile.TemporaryDirectory(prefix="asap5-sanity-") as work:
        for dev, p in ref.DEVICES.items():
            pol = -1 if dev.startswith("p") else 1
            sw = mos_sweeps(ng, work, dev, header, "N1 d g s 0 %s nfin=2" % dev, pol, ref.VDD,
                            0.05, 0.05, ref.VDD, ref.TEMP, pre="pre_osdi " + osdi)
            vtl, vts = vt_cc(*sw["vg_lin"], ref.ICC), vt_cc(*sw["vg_sat"], ref.ICC)
            m = dict(
                idsat=at(*sw["vg_sat"], ref.VDD) * 1e6,
                ioff=at(*sw["vg_sat"], 0.0) * 1e12,
                vtsat=vts,
                dibl=1000 * (vtl - vts) / (ref.VDD - 0.05),
                ss=1000 * (vt_cc(*sw["vg_sat"], ref.ICC) - vt_cc(*sw["vg_sat"], ref.ICC / 10)),
                idsat_over_idlin=at(*sw["vd_full"], ref.VDD) / at(*sw["vd_full"], 0.05),
            )
            data[dev] = m
            for q, unit, rel in (("idsat", "uA", True), ("ioff", "pA", True), ("vtsat", "V", False),
                                 ("dibl", "mV/V", False), ("ss", "mV/dec", False)):
                lo, hi = (p[q] * (1 - t[q]), p[q] * (1 + t[q])) if rel else (p[q] - t[q], p[q] + t[q])
                name = "%s %s" % (dev, q)
                if (dev, q) in ref.KNOWN_DEVIATIONS:
                    rep.known(name, m[q], lo, hi, unit, 1, ref.KNOWN_DEVIATIONS[(dev, q)])
                else:
                    rep.check(name, "published", m[q], lo, hi, unit, 1)
            if dev in ref.IDSAT_OVER_IDLIN:
                rep.info(dev + " Idsat/Idlin", m["idsat_over_idlin"], "", 1,
                         "(paper %.2f, bias unstated)" % ref.IDSAT_OVER_IDLIN[dev])
            print()
    return rep.summary(), data, rep.rows
