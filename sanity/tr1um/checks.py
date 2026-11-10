"""TR-1um sanity checks: drain current of the 5 V NMOS and PMOS at the
Table I-2-7 bias points against Tokai Rika's published simulation curves,
plus the interconnect layer table against the published design rules and
the wire.inc ladder against the closed-form Elmore delay.
Sources and caveats: reference.py. Run via sanity/run.py --pdk tr1um.
"""

import csv
import os
import tempfile

import reference as ref
from common import Report, at, ngspice, read_xy, render, results

DECKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "decks")
DECK = os.path.join(DECKS, "iv_points.sp")


def elmore(ng, wire_inc, work, nseg):
    e = ref.ELMORE
    r = results(ngspice(ng, render(os.path.join(DECKS, "wire_elmore.sp"), work, "wire_elmore_%d" % nseg,
                                   WIRE_INC=wire_inc, N=nseg, L=e["l"], W=e["w"], RSH=e["rsh"], CPL=e["cpl"],
                                   RS=e["rs"], CL=e["cl"], TSTOP=e["tstop"])))
    R = ref.ELMORE_RSH * ref.ELMORE_L / ref.ELMORE_W
    C = ref.ELMORE_CPL * ref.ELMORE_L
    closed = ref.ELMORE_RS * (C + ref.ELMORE_CL) + R * (C / 2 + ref.ELMORE_CL)
    return r["elmore"], closed


def interconnect(rep, ngdir, drfile, ng, work, data):
    table = os.path.join(ngdir, "interconnect.csv")
    wire_inc = os.path.join(ngdir, "wire.inc")
    for f in (table, wire_inc, drfile):
        if not os.path.exists(f):
            raise SystemExit("not found: %s (run bootstrap.sh --pdk tr1um)" % f)
    with open(table) as f:
        rows = list(csv.DictReader(f))
    val = {(r["layer"], r["quantity"]): r for r in rows}
    # The constants in reference.py are what the fetched [DR] file prints.
    with open(drfile) as f:
        dr = {r[0]: float(r[4]) for r in csv.reader(f) if len(r) > 4 and r[0] in ref.DR_RULES and r[4]}
    print("Interconnect: layer table vs the design-rule table [DR] (reference.py)\n")
    rep.check("reference constants match the fetched [DR] file (%d rules)" % len(ref.DR_RULES), "published",
              float(dr == ref.DR_RULES), 1, 1, "", 1)
    for lay, (w, s) in ref.METALS.items():
        rep.check("%s width" % lay, "published", float(val[lay, "width_min"]["value"]), w, w, "um", 1)
        rep.check("%s spacing" % lay, "published", float(val[lay, "spacing_min"]["value"]), s, s, "um", 1)
        p = float(val[lay, "pitch"]["value"])
        rep.check("%s pitch = width + spacing" % lay, "derived", p, w + s, w + s, "um", 1)
    for lay, w in ref.VIAS.items():
        rep.check("%s width" % lay, "published", float(val[lay, "width_min"]["value"]), w, w, "um", 1)
    gaps = [k for k, r in val.items() if r["status"] == "gap"]
    expect = {(m, q) for m in ref.METALS for q in ref.GAP_QUANTITIES} | {(v, q) for v in ref.VIAS for q in ref.GAP_VIA_QUANTITIES}
    # A value appearing where the documents print none must come with a source
    # added to reference.py, so a gap turning into a number fails here.
    rep.check("unpublished quantities stay explicit gaps (%d)" % len(gaps), "derived",
              float(set(gaps) == expect), 1, 1, "", 1)
    data["interconnect_gaps"] = sorted("%s.%s" % k for k in gaps)
    print()
    for n in ref.ELMORE_SEGMENTS:
        sim, closed = elmore(ng, wire_inc, work, n)
        data["wire_elmore_%d" % n] = dict(simulated=sim, closed_form=closed)
        rep.check("wire ladder Elmore delay, %d segment%s" % (n, "" if n == 1 else "s"), "derived", sim,
                  closed * (1 - ref.ELMORE_TOL), closed * (1 + ref.ELMORE_TOL), "ps", 1e12,
                  "(closed form %.3f ps)" % (closed * 1e12))
    print()


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
            curves[dev] = dict(idvg=read_xy(out + ".idvg", pol),
                               **{"idvd%d" % v: read_xy(out + ".idvd%d" % v, pol) for v in (2, 3, 4, 5, 6)})
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
        print()
        interconnect(rep, os.path.join(prefix, "tr1um", "ngspice"),
                     os.path.join(prefix, "tr1um", "TR-1um", "Document", "TR-1um_Drawing_Layer_DR_Table.csv"),
                     ng, work, data)
    return rep.summary(), data, rep.rows
