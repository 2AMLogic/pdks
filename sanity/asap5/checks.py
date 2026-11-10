"""ASAP5 r0p4 sanity checks: per-fin device parameters of all eight
nanowire FETs against Vashishtha and Clark 2022, Tables 8-9. Sources,
definitions and tolerances: reference.py. Run via sanity/run.py --pdk asap5.
"""

import csv
import os
import tempfile

import reference as ref
from common import Report, at, mos_sweeps, ngspice, render, results, vt_cc

DECKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "decks")


def elmore(ng, wire_inc, work, nseg):
    e = ref.ELMORE
    r = results(ngspice(ng, render(os.path.join(DECKS, "wire_elmore.sp"), work, "wire_elmore_%d" % nseg,
                                   WIRE_INC=wire_inc, N=nseg, L=e["l"], W=e["w"], RSH=e["rsh"], CPL=e["cpl"],
                                   RS=e["rs"], CL=e["cl"], TSTOP=e["tstop"])))
    R = ref.ELMORE_RSH * ref.ELMORE_L / ref.ELMORE_W
    C = ref.ELMORE_CPL * ref.ELMORE_L
    closed = ref.ELMORE_RS * (C + ref.ELMORE_CL) + R * (C / 2 + ref.ELMORE_CL)
    return r["elmore"], closed


def interconnect(rep, ngdir, ng, work, data):
    table = os.path.join(ngdir, "interconnect.csv")
    wire_inc = os.path.join(ngdir, "wire.inc")
    for f in (table, wire_inc):
        if not os.path.exists(f):
            raise SystemExit("not found: %s (run bootstrap.sh --pdk asap5)" % f)
    with open(table) as f:
        rows = list(csv.DictReader(f))
    val = {(r["layer"], r["quantity"]): r for r in rows}
    print("Interconnect: layer table vs [MEJ22] Table 5 and section 5.1 (reference.py)\n")
    for lay, (w, p) in ref.METALS.items():
        rep.check("%s width" % lay, "published", float(val[lay, "width_min"]["value"]), w, w, "nm", 1)
        rep.check("%s pitch" % lay, "published", float(val[lay, "pitch"]["value"]), p, p, "nm", 1)
        sp, th = float(val[lay, "spacing_min"]["value"]), float(val[lay, "thickness"]["value"])
        rep.check("%s spacing = pitch - width" % lay, "derived", sp, p - w, p - w, "nm", 1)
        rep.check("%s thickness = %.0f x width" % (lay, ref.ASPECT), "derived", th, ref.ASPECT * w, ref.ASPECT * w, "nm", 1)
    for lay, w in ref.VIAS.items():
        rep.check("%s width" % lay, "published", float(val[lay, "width_min"]["value"]), w, w, "nm", 1)
    gaps = [k for k, r in val.items() if r["status"] == "gap"]
    expect = {(m, q) for m in ref.METALS for q in ref.GAP_QUANTITIES} | {(v, q) for v in ref.VIAS for q in ref.GAP_VIA_QUANTITIES}
    # A value appearing where the paper publishes none must come with a source
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

        # Corners: [MEJ22] Fig. 16 shows them only as plots, so the check is
        # derived: Idsat orders ss < slow-mixed < tt < fast-mixed < ff. The
        # first letter of a corner is the nFET's, so an nFET is fast in fs,
        # a pFET in sf.
        print("Corners: ordering (derived; the paper plots corners, no table)\n")
        for dev in ref.DEVICES:
            pol = -1 if dev.startswith("p") else 1
            ids = {}
            for c in ("ss", "sf", "tt", "fs", "ff"):
                sw = mos_sweeps(ng, work, "%s_%s" % (dev, c), '.lib "%s" %s' % (models, c),
                                "N1 d g s 0 %s nfin=2" % dev, pol, ref.VDD, 0.05, 0.05, ref.VDD, ref.TEMP,
                                pre="pre_osdi " + osdi)
                ids[c] = at(*sw["vg_sat"], ref.VDD) * 1e6
            data[dev + "_corners_idsat_uA"] = ids
            fast, slow = ("fs", "sf") if pol > 0 else ("sf", "fs")
            order = [ids[c] for c in ("ss", slow, "tt", fast, "ff")]
            rep.check("%s Idsat ss<%s<tt<%s<ff" % (dev, slow, fast), "derived",
                      float(all(a < b for a, b in zip(order, order[1:]))), 1, 1, "", 1,
                      "(%s uA)" % " / ".join("%.1f" % v for v in order))

        interconnect(rep, os.path.join(prefix, "asap5", "ngspice"), ng, work, data)

    return rep.summary(), data, rep.rows
