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

        print("\nContinuous models (libs.tech/combined) vs the tables' TT column\n")
        clib = os.path.join(prefix, "sky130", "sky130A", "libs.tech", "combined", "sky130.lib.spice")
        for name, dev, tt in ref.COMBINED_IDSAT:
            pol = -1 if dev.startswith("p") else 1
            sw = mos_sweeps(ng, work, "%s_combined" % dev, '.lib "%s" tt' % clib,
                            "X1 d g s 0 sky130_fd_pr__%s w=7 l=0.15" % dev, pol, ref.VDD, 0.05, 0.05,
                            ref.VDD, ref.TEMP, imeas="i(vs)", spiceinit=SPICEINIT)
            v = at(*sw["vg_sat"], ref.VDD)
            data[name + " combined"] = v
            rep.check("%s %s Idsat (continuous)" % (name, dev), "published", v,
                      tt * (1 - ref.COMBINED_TOL), tt * (1 + ref.COMBINED_TOL), "mA", 1e3,
                      "(TT column %.3f mA, %+.1f %%)" % (tt * 1e3, 100 * (v / tt - 1)))

        print("\nCorners, relative to TT (7/0.15 devices)\n")
        base = {}
        for corner in ("tt", "ff", "ss", "fs", "sf"):
            for dev in ("nfet_01v8", "pfet_01v8"):
                pol = -1 if dev.startswith("p") else 1
                sw = mos_sweeps(ng, work, "%s_%s_corner" % (dev, corner), '.lib "%s" %s' % (lib, corner),
                                "X1 d g s 0 sky130_fd_pr__%s w=7 l=0.15" % dev, pol, ref.VDD, 0.05, 0.05,
                                ref.VDD, ref.TEMP, imeas="i(vs)", spiceinit=SPICEINIT)
                base[(dev, corner)] = dict(vt=vt_max_gm(*sw["vg_lin"], 0.05), idsat=at(*sw["vg_sat"], ref.VDD))
        t = ref.CORNER_TOL
        for name, dev, qty, tt, corners in ref.CORNER_ROWS:
            for corner, val in corners.items():
                sim_tt, sim_c = base[(dev, "tt")][qty], base[(dev, corner)][qty]
                if qty == "idsat":
                    v, want, lo, hi, unit = sim_c / sim_tt, val / tt, val / tt * (1 - t[qty]), val / tt * (1 + t[qty]), "x TT"
                else:
                    v, want, unit = sim_c - sim_tt, val - tt, "V vs TT"
                    lo, hi = want - t[qty], want + t[qty]
                label = "%s %s %s" % (name, corner, "Idsat/TT" if qty == "idsat" else "Vt-TT")
                data[label] = v
                if (name, corner) in ref.KNOWN_DEVIATIONS:
                    rep.known(label, v, lo, hi, unit, 1, ref.KNOWN_DEVIATIONS[(name, corner)])
                else:
                    rep.check(label, "published", v, lo, hi, unit, 1, "(table %+.3f)" % want if qty == "vt" else "(table %.3f)" % want)
    return rep.summary(), data, rep.rows
