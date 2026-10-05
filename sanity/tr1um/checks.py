"""TR-1um sanity checks: drain current of the 5 V NMOS and PMOS at the
Table I-2-7 bias points against Tokai Rika's published simulation curves.
Sources and caveats: reference.py. Run via sanity/run.py --pdk tr1um.
"""

import os
import tempfile

import reference as ref
from common import Report, at, ngspice, render

DECK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "decks", "iv_points.sp")


def sweep(path, pol):
    xs, ys = [], []
    with open(path) as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 2:
                xs.append(pol * float(parts[0]))
                ys.append(abs(float(parts[1])))
    return xs, ys


def run(prefix, ng):
    models = os.path.join(prefix, "tr1um", "TR-1um", "libs.tech", "spice", "models")
    if not os.path.exists(os.path.join(models, "ip62_models")):
        raise SystemExit("TR-1um models not found under %s (run bootstrap.sh --pdk tr1um)" % models)
    rep, data = Report(), {}
    print("TR-1um typical, %d C, W/L = 30/1 um. Sources and caveats: sanity/tr1um/reference.py\n" % ref.TEMP)
    with tempfile.TemporaryDirectory(prefix="tr1um-sanity-") as work:
        curves = {}
        for dev in ("NMOS", "PMOS"):
            pol = -1 if dev == "PMOS" else 1
            out = os.path.join(work, dev)
            subs = dict(MODELS=models, DEVICE=dev, OUT=out, VDS5=pol * 5, VD7=pol * 7, VSTEP=pol * 0.01)
            subs.update({"VG%d" % v: pol * v for v in (2, 3, 4, 5, 6)})
            ngspice(ng, render(DECK, work, dev, **subs))
            curves[dev] = dict(idvg=sweep(out + ".idvg", pol),
                               **{"idvd%d" % v: sweep(out + ".idvd%d" % v, pol) for v in (2, 3, 4, 5, 6)})
        for dev, curve, vgs, vds, sim, meas in ref.POINTS:
            c = curves[dev]
            i = at(*c["idvg"], vgs) if curve == "Id-Vg" else at(*c["idvd%d" % vgs], vds)
            data["%s %s Vgs=%g Vds=%g" % (dev, curve, vgs, vds)] = i
            name = "%s %s |Vgs|=%g |Vds|=%g" % (dev, curve, vgs, vds)
            lo, hi = sim * (1 - ref.TOL), sim * (1 + ref.TOL)
            note = "(sim %.3g mA, %+.1f %%; measured %.3g mA)" % (sim * 1e3, 100 * (i / sim - 1), meas * 1e3)
            if (dev, curve, vgs) in ref.KNOWN_DEVIATIONS:
                rep.known(name, i, lo, hi, "mA", 1e3, ref.KNOWN_DEVIATIONS[(dev, curve, vgs)])
            else:
                rep.check(name, "published", i, lo, hi, "mA", 1e3, note)
    return rep.summary(), data, rep.rows
