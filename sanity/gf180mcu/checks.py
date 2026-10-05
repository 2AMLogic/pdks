"""GF180MCU sanity checks: Idsat and Vth0 against GF's EP targets, Ioff and
subthreshold slope against the electrical spec limits. Sources, extraction
definitions and tolerances: reference.py. Run via sanity/run.py --pdk gf180mcu.
"""

import os
import tempfile

import re

import reference as ref
from common import Report, at, mos_sweeps, ngspice, render, ss_min, vt_max_gm

PASSIVE_DECK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "decks", "passive_t.sp")


def tc_fit(ts, ys, t0):
    """Least-squares TC1 (ppm/K) of y(T) = y0 [1 + a dT + b dT^2]."""
    y0 = ys[ts.index(t0)]
    X = [(t - t0, (t - t0) ** 2) for t in ts]
    Z = [y / y0 - 1 for y in ys]
    sxx = sum(a * a for a, _ in X); sxy = sum(a * b for a, b in X); syy = sum(b * b for _, b in X)
    sxz = sum(a * z for (a, _), z in zip(X, Z)); syz = sum(b * z for (_, b), z in zip(X, Z))
    return (sxz * syy - syz * sxy) / (sxx * syy - sxy * sxy) * 1e6


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
        tc1 = tc_fit(ts, ys, 25.0)
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


def run(prefix, ng):
    models = os.path.join(prefix, "gf180mcu", "gf180mcu_fd_pr", "models", "ngspice")
    if not os.path.exists(os.path.join(models, "sm141064.ngspice")):
        raise SystemExit("GF180MCU models not found under %s (run bootstrap.sh --pdk gf180mcu)" % models)
    header = '.include "%s/design.ngspice"\n.lib "%s/sm141064.ngspice" typical' % (models, models)
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
            hdr = '.include "%s/design.ngspice"\n.lib "%s/sm141064.ngspice" %s' % (models, models, corner)
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
    return rep.summary(), data, rep.rows
