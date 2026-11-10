"""GF180MCU sanity checks: Idsat and Vth0 against GF's EP targets, Ioff and
subthreshold slope against the electrical spec limits. Sources, extraction
definitions and tolerances: reference.py. Run via sanity/run.py --pdk gf180mcu.
"""

import csv
import os
import tempfile

import re

import reference as ref
from common import Report, at, mos_sweeps, ngspice, render, results, ss_min, tc_fit, vt_max_gm

WIRE_DECK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "decks", "wire_elmore.sp")
PASSIVE_DECK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "decks", "passive_t.sp")


def passives(rep, ng, work, models, data):
    print("Passives and temperature coefficients (-40 to 125 C)\n")
    temps = " ".join(str(t) for t in ref.TEMPS)
    for model, kind, geom, win, tcw in ref.PASSIVES:
        nodes = "a 0 0" if kind == "res" else "a 0"
        measure = ('op\n  echo "RESULT_X $t $&@v1[i]"' if kind != "cap" else
                   'ac lin 1 100k 100k\n  let cc = -imag(i(v1))/(2*pi*100e3)\n  echo "RESULT_X $t $&cc"')
        deck = render(PASSIVE_DECK, work, "p_" + model, MODELS=models, VDC=0 if kind == "cap" else 0.1,
                      INSTANCE="X1 %s %s %s" % (nodes, model, geom), TEMPS=temps, MEASURE=measure)
        log = ngspice(ng, deck, cwd=work)
        xs = [(float(t), abs(float(v))) for t, v in re.findall(r"^RESULT_X (\S+) (\S+)", log, re.M)]
        ts = [x[0] for x in xs]
        ys = [x[1] for x in xs] if kind == "cap" else [0.1 / x[1] for x in xs]
        y25 = ys[ts.index(25.0)]
        tc1 = tc_fit(ts, ys, 25.0)[0]
        data[model] = dict(tc1_ppm=tc1)
        if kind == "res":
            rs = y25 * 10 / 200
            data[model]["rsheet"] = rs
            rep.check(model + " Rsheet", "published", rs, win[0], win[2], "ohm/sq", 1, "(typ %g)" % win[1])
        elif kind == "cap":
            ca = y25 / (350 * 50) * 1e15
            data[model]["c_fF_um2"] = ca
            rep.check(model + " C/area", "published", ca, win[0], win[2], "fF/um2", 1, "(typ %g)" % win[1])
        lo, typ, hi = tcw
        name = model + " TC1"
        if lo is None and hi is None:
            rep.info(name, tc1, "ppm/K", 1, "(typ %g; no window published)" % typ)
        elif (model, "tc1") in ref.KNOWN_DEVIATIONS:
            rep.known(name, tc1, lo, hi, "ppm/K", 1, ref.KNOWN_DEVIATIONS[(model, "tc1")])
        else:
            rep.check(name, "published" if lo is not None else "bound", tc1,
                      -1e9 if lo is None else lo, hi, "ppm/K", 1, "(typ %g)" % typ)


def elmore(ng, wire_inc, work, nseg, rsh, w):
    e = ref.ELMORE
    r = results(ngspice(ng, render(WIRE_DECK, work, "wire_elmore_%d" % nseg,
                                   WIRE_INC=wire_inc, N=nseg, L=e["l"], W=w, RSH=rsh, CPL=e["cpl"],
                                   RS=e["rs"], CL=e["cl"], TSTOP=e["tstop"])))
    R = rsh * ref.ELMORE_L / w
    C = ref.ELMORE_CPL * ref.ELMORE_L
    closed = ref.ELMORE_RS * (C + ref.ELMORE_CL) + R * (C / 2 + ref.ELMORE_CL)
    return r["elmore"], closed


def interconnect(rep, ngdir, ng, work, data):
    table = os.path.join(ngdir, "interconnect.csv")
    wire_inc = os.path.join(ngdir, "wire.inc")
    for f in (table, wire_inc):
        if not os.path.exists(f):
            raise SystemExit("not found: %s (run bootstrap.sh --pdk gf180mcu)" % f)
    with open(table) as f:
        rows = list(csv.DictReader(f))
    val = {(r["layer"], r["quantity"]): r for r in rows}
    num = lambda lay, q: float(val[lay, q]["value"])  # noqa: E731
    print("\nInterconnect: layer table vs [DRM], [EPS], [IA] (reference.py)\n")
    lo, hi = ref.RSHEET_WINDOW
    for lay, (w, s) in ref.METALS.items():
        rep.check("%s width" % lay, "published", num(lay, "width_min"), w, w, "nm", 1)
        rep.check("%s spacing" % lay, "published", num(lay, "spacing_min"), s, s, "nm", 1)
        rep.check("%s pitch = width + spacing" % lay, "derived", num(lay, "pitch"), w + s, w + s, "nm", 1)
        rep.check("%s thickness" % lay, "published", num(lay, "thickness"), ref.THICKNESS, ref.THICKNESS, "nm", 1)
        rep.check("%s sheet resistance" % lay, "published", num(lay, "rsheet"), lo, hi, "ohm/sq", 1,
                  "(typ %g)" % ref.RSHEET)
        rep.check("%s sheet resistance temperature coefficient" % lay, "published", num(lay, "rsheet_tcr"),
                  ref.RSHEET_TC, ref.RSHEET_TC, "%/degC", 1)
    for lay, w in ref.VIAS.items():
        rep.check("%s width" % lay, "published", num(lay, "width_min"), w, w, "nm", 1)
        rep.check("%s spacing" % lay, "published", num(lay, "spacing_min"), w, w, "nm", 1)
        rep.check("%s resistance per via" % lay, "published", num(lay, "r_via"), ref.R_VIA, ref.R_VIA, "ohm", 1)
    gaps = [k for k, r in val.items() if r["status"] == "gap"]
    expect = {(m, q) for m in ref.METALS for q in ref.GAP_QUANTITIES} | {(v, q) for v in ref.VIAS for q in ref.GAP_VIA_QUANTITIES}
    # A value appearing where the documents publish none must come with a
    # source added to reference.py, so a gap turning into a number fails here.
    rep.check("unpublished quantities stay explicit gaps (%d)" % len(gaps), "derived",
              float(set(gaps) == expect), 1, 1, "", 1)
    data["interconnect_gaps"] = sorted("%s.%s" % k for k in gaps)
    print()
    lay = ref.ELMORE_LAYER
    rsh, w = num(lay, "rsheet"), num(lay, "width_min") * 1e-9
    for n in ref.ELMORE_SEGMENTS:
        sim, closed = elmore(ng, wire_inc, work, n, rsh, w)
        data["wire_elmore_%d" % n] = dict(simulated=sim, closed_form=closed)
        rep.check("wire ladder Elmore delay, %d segment%s" % (n, "" if n == 1 else "s"), "derived", sim,
                  closed * (1 - ref.ELMORE_TOL), closed * (1 + ref.ELMORE_TOL), "ps", 1e12,
                  "(closed form %.3f ps)" % (closed * 1e12))
    print()


def run(prefix, ng):
    models = os.path.join(prefix, "gf180mcu", "gf180mcu_fd_pr", "models", "ngspice")
    if not os.path.exists(os.path.join(models, "sm141064.spice")):
        raise SystemExit("GF180MCU models not found under %s (run bootstrap.sh --pdk gf180mcu)" % models)
    header = '.include "%s/design.spice"\n.lib "%s/sm141064.spice" typical' % (models, models)
    rep, data = Report(), {}
    print("GF180MCU typical, %d C, W = 10 um. Sources and tolerances: sanity/gf180mcu/reference.py\n" % ref.TEMP)
    with tempfile.TemporaryDirectory(prefix="gf180-sanity-") as work:
        for dev, p in ref.DEVICES.items():
            pol = -1 if dev.startswith("p") else 1
            inst = "M1 d g s 0 %s w=%gu l=%gu" % (dev, p["w"], p["l"])
            sw = mos_sweeps(ng, work, dev, header, inst, pol, p["vdd"], p["vlin"], p["vlin"],
                            p["voff"], ref.TEMP, vgstart=-0.5 if p["vth0"] < 0 else 0.0)
            w_um = p["w"]
            idsat = at(*sw["vg_sat"], p["vdd"]) / w_um * 1e6            # uA/um
            vg, il = sw["vg_lin"]
            vth0 = vt_max_gm(vg, il, p["vlin"])
            ioff = at(*sw["vg_off"], 0.0) / w_um * 1e12                   # pA/um at Vgs = 0
            ss = ss_min(vg, il, 1e-7 * p["w"] / p["l"])
            data[dev] = dict(idsat_uA_um=idsat, vth0=vth0, ioff_pA_um=ioff, ss=ss)
            t = ref.TOL
            rep.check(dev + " Idsat", "published", idsat, p["idsat"] * (1 - t["idsat"]), p["idsat"] * (1 + t["idsat"]), "uA/um", 1)
            rep.check(dev + " Vth0", "published", vth0, p["vth0"] - t["vth0"], p["vth0"] + t["vth0"], "V", 1)
            if p["ioff_max"] is not None:
                rep.check(dev + " Ioff", "bound", ioff, 0, p["ioff_max"], "pA/um", 1)
                rep.check(dev + " SS", "bound", ss, 0, ref.SS_MAX, "mV/dec", 1)
            print()

        print("Corners: [MRG] slow / fast EP targets at the ss / ff models\n")
        for corner, targets in ref.CORNERS.items():
            hdr = '.include "%s/design.spice"\n.lib "%s/sm141064.spice" %s' % (models, models, corner)
            for dev, (idsat_t, vth_t) in targets.items():
                p = ref.DEVICES[dev]
                pol = -1 if dev.startswith("p") else 1
                inst = "M1 d g s 0 %s w=%gu l=%gu" % (dev, p["w"], p["l"])
                sw = mos_sweeps(ng, work, "%s_%s" % (dev, corner), hdr, inst, pol, p["vdd"], p["vlin"],
                                p["vlin"], p["voff"], ref.TEMP, vgstart=-0.5 if min(p["vth0"], vth_t) < 0 else 0.0)
                idsat = at(*sw["vg_sat"], p["vdd"]) / p["w"] * 1e6
                vth0 = vt_max_gm(*sw["vg_lin"], p["vlin"])
                data["%s_%s" % (dev, corner)] = dict(idsat_uA_um=idsat, vth0=vth0)
                t = ref.TOL
                rep.check("%s %s Idsat" % (dev, corner), "published", idsat,
                          idsat_t * (1 - t["idsat"]), idsat_t * (1 + t["idsat"]), "uA/um", 1)
                rep.check("%s %s Vth0" % (dev, corner), "published", vth0,
                          vth_t - t["vth0"], vth_t + t["vth0"], "V", 1)
            print()

        passives(rep, ng, work, models, data)
        interconnect(rep, os.path.join(prefix, "gf180mcu", "ngspice"), ng, work, data)
    return rep.summary(), data, rep.rows
