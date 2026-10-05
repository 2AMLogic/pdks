"""SKY130 sanity checks: threshold voltage, saturation current and leakage of
the 1.8 V nFET and pFET against SkyWater's published e-test windows. Sources
and definitions: reference.py. Run via sanity/run.py --pdk sky130.
"""

import math
import os
import tempfile

import reference as ref
from common import Report, at, mos_sweeps, vt_max_gm

SPICEINIT = "set ngbehavior=hsa\nset ng_nomodcheck\n"


def run(prefix, ng):
    lib = os.path.join(prefix, "sky130", "sky130A", "libs.tech", "ngspice", "sky130.lib.spice")
    if not os.path.exists(lib):
        raise SystemExit("not found: %s (run bootstrap.sh --pdk sky130)" % lib)
    header = '.lib "%s" tt' % lib
    rep, data = Report(), {}
    print("SKY130 TT, %d C, VDD %.1f V. Sources and definitions: sanity/sky130/reference.py\n" % (ref.TEMP, ref.VDD))
    sweeps = {}
    with tempfile.TemporaryDirectory(prefix="sky130-sanity-") as work:
        for name, dev, w, l, qty, lo, hi, tt in ref.ROWS:
            key = (dev, w, l)
            if key not in sweeps:
                pol = -1 if dev.startswith("p") else 1
                inst = "X1 d g s 0 sky130_fd_pr__%s w=%g l=%g" % (dev, w, l)
                tag = "%s_%g_%g" % (dev, w, l)
                sweeps[key] = mos_sweeps(ng, work, tag.replace(".", "p"), header, inst, pol, ref.VDD,
                                         0.05, 0.05, ref.VDD, ref.TEMP, imeas="i(vs)", spiceinit=SPICEINIT)
            sw = sweeps[key]
            label = "%s %s %g/%g" % (name, dev, w, l)
            if qty == "vt":
                v = vt_max_gm(*sw["vg_lin"], 0.05)
                if name in ref.KNOWN_DEVIATIONS:
                    rep.known(label + " Vt", v, lo, hi, "V", 1, ref.KNOWN_DEVIATIONS[name])
                else:
                    rep.check(label + " Vt", "published", v, lo, hi, "V", 1, "(TT column %.3f)" % tt)
            elif qty == "idsat":
                v = at(*sw["vg_sat"], ref.VDD)
                rep.check(label + " Idsat", "published", v, lo, hi, "mA", 1e3,
                          "(TT column %.3f mA, %+.1f %%)" % (tt * 1e3, 100 * (v / tt - 1)))
            else:
                v = math.log10(at(*sw["vg_off"], 0.0))
                rep.check(label + " Ioff", "bound", v, -99, hi, "log A", 1)
            data[name] = v
    return rep.summary(), data, rep.rows
