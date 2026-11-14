"""GF180MCU sanity checks: Idsat and Vth0 against GF's EP targets, Ioff and
subthreshold slope against the electrical spec limits. Sources, extraction
definitions and tolerances: reference.py. Run via sanity/run.py --pdk gf180mcu.
"""

import os
import tempfile

import re

import reference as ref
from common import (Report, at, elmore_ladder, gap_check, load_interconnect, mos_sweeps, ngspice, render,
                    results, ss_min, tc_fit, vt_max_gm)

DECKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ngspice", "gf180mcu")
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


def interconnect(rep, ngdir, ng, work, data):
    _, val, num, wire_inc = load_interconnect(ngdir, "gf180mcu")
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
    expect = {(m, q) for m in ref.METALS for q in ref.GAP_QUANTITIES} | {(v, q) for v in ref.VIAS for q in ref.GAP_VIA_QUANTITIES}
    gap_check(rep, data, val, expect)
    print()
    lay = ref.ELMORE_LAYER
    rsh, w = num(lay, "rsheet"), num(lay, "width_min") * 1e-9
    elmore_ladder(rep, data, ng, wire_inc, work, ref.ELMORE_SEGMENTS, dict(ref.ELMORE, w=w), rsh,
                  ref.ELMORE_L, w, ref.ELMORE_CPL, ref.ELMORE_RS, ref.ELMORE_CL, ref.ELMORE_TOL)
    print()

def mismatch_deck(ng, work, models, name, mm, w, l, par, n, seed):
    deck = render(os.path.join(DECKS, "mismatch.sp.in"), work, name, MODELS_DIR=models, NGSPICE=ng,
                  MM=mm, W=w, L=l, PAR=par, N=n, SEED=seed)
    return results(ngspice(ng, deck, cwd=work))


def noise_deck(ng, work, models, name, bias):
    deck = render(os.path.join(DECKS, "noise.sp.in"), work, name, MODELS_DIR=models, NGSPICE=ng,
                  VGLO=bias["VG"] - 0.002, VGHI=bias["VG"] + 0.002, **bias)
    return results(ngspice(ng, deck, cwd=work))


def noise_scan(models):
    """MOS .models in sm141064.spice: (count, number missing noia/ntnoi/ef)."""
    text = open(os.path.join(models, "sm141064.spice")).read()
    n = absent = 0
    for b in re.split(r"(?im)^\.model\s+", text)[1:]:
        if b.split("\n", 1)[0].split()[1].lower() not in ("nmos", "pmos"):
            continue
        n += 1
        absent += any(not re.search(r"(?im)^\+\s*%s\s*=" % k, b) for k in ("noia", "ntnoi", "ef"))
    return n, absent


def mismatch_and_noise(rep, data, models, ng, work):
    n = ref.MISMATCH_N
    print("\nMismatch (Monte Carlo, sw_stat_mismatch=1), 3.3 V nFET, %d pairs per area" % n)
    print("  Published: only plotted fit lines (digitised); the model's own coefficients are the derived reference.\n")
    runs = []
    for w, l, par, seed in ref.MISMATCH_AREAS:
        r = mismatch_deck(ng, work, models, "mm_%g_%g_%g" % (w, l, par), 1, w, l, par, n, seed)
        runs.append(("%g/%g par %g" % (w, l, par), r))
        data["mismatch %g/%g par %g" % (w, l, par)] = r
        rep.info("sigma(Vtlin) %g/%g par %g" % (w, l, par), r["sigma_vtlin_V"], "mV", 1e3)
    for key, label, n_s in (("avt_model_mVum", "AVT", 2 * n), ("aidsat_model_pcum", "AIdsat", n)):
        vals = [r[key] for _, r in runs]
        mean = sum(vals) / len(vals)
        t = ref.mc_tol(n_s)
        for tag, r in runs:
            rep.check("%s*sqrt(Aeff) %s" % (label, tag), "derived", r[key], mean * (1 - t), mean * (1 + t),
                      "mV um" if key.startswith("avt") else "%um", 1, "(area scaling; mean %.3g, +-%.0f %%)" % (mean, 100 * t))
    mean_avt = sum(r["avt_model_mVum"] for _, r in runs) / len(runs)
    t = ref.mc_tol(6 * n)
    rep.check("AVT vs model par_vth", "derived", mean_avt, ref.PAR_VTH * (1 - t), ref.PAR_VTH * (1 + t), "mV um", 1,
              "(model par_vth %.3f; 3 sampling errors of 3x2N devices)" % ref.PAR_VTH)
    t = ref.mc_tol(n)
    for tag, r in runs:
        rep.check("AIdsat floor %s" % tag, "bound", r["aidsat_model_pcum"], ref.PAR_K * (1 - t), 1e9, "%um", 1,
                  "(model par_k %.3f %%um; Vth mismatch adds to it: measured/par_k %.2f)" % (ref.PAR_K, r["aidsat_model_pcum"] / ref.PAR_K))
    r = runs[0][1]
    rep.known("sigma(dVtlin)*sqrt(WL) vs published", r["avt_dvt_mVum"], ref.PUB_AVT * (1 - ref.PUB_TOL),
              ref.PUB_AVT * (1 + ref.PUB_TOL), "mV um", 1, ref.MISMATCH_KNOWN["avt"])
    rep.known("sigma(dIdsat)*sqrt(WL) vs published", r["aidsat_pcum"], ref.PUB_AIDSAT * (1 - ref.PUB_TOL),
              ref.PUB_AIDSAT * (1 + ref.PUB_TOL), "%um", 1, ref.MISMATCH_KNOWN["aidsat"])
    off = mismatch_deck(ng, work, models, "mm_off", 0, 10, 1, 1, 3, 1)
    rep.check("mismatch off: sigma(Vtlin)", "derived", off["sigma_vtlin_V"], 0, 1e-7, "V", 1, "(sw_stat_mismatch=0; 0.1 uV allows for the solver noise of the interpolated Vtlin, 1e4 below the spread)")
    a = mismatch_deck(ng, work, models, "mm_rep1", 1, 10, 1, 1, 3, 5)
    b = mismatch_deck(ng, work, models, "mm_rep2", 1, 10, 1, 1, 3, 5)
    rep.check("same seed, same result", "derived", abs(a["sigma_vtlin_V"] - b["sigma_vtlin_V"]) + abs(a["sigma_didsat_rel"] - b["sigma_didsat_rel"]),
              0, 0, "V", 1, "(setseed + reset)")

    print("\nNoise, 3.3 V nFET %(W)g/%(L)g um, Vg %(VG)g V, Vd %(VD)g V (ngspice .noise, 27 C)\n" % ref.NOISE_BIAS)
    r = noise_deck(ng, work, models, "noise_long", ref.NOISE_BIAS)
    data["noise long"] = r
    lo, hi = ref.GAMMA_LONG
    rep.check("thermal gamma (4kT*gamma*gm) 10/5", "derived", r["gamma_thermal"], lo, hi, "", 1, "(long-channel theory 2/3 .. 1)")
    lo, hi = ref.NYQUIST
    rep.check("Nyquist S_id/(4kT*gds) at Vds=0", "derived", r["nyquist_ratio"], lo, hi, "", 1)
    rep.check("flicker slope 1..100 Hz = -ef", "derived", r["flicker_slope"], -ref.EF - ref.FLICKER_SLOPE_TOL,
              -ref.EF + ref.FLICKER_SLOPE_TOL, "", 1, "(model ef %.2f)" % ref.EF)
    rep.info("flicker level at 1 Hz (input, V^2/Hz)", r["sv_flicker_1Hz_V2"], "V2/Hz", 1, "(no published value: gap)")
    short = noise_deck(ng, work, models, "noise_short", ref.NOISE_BIAS_SHORT)
    data["noise short"] = short
    rep.info("thermal gamma 10/0.28", short["gamma_thermal"], "", 1, "(information; no long-channel claim)")
    nm, absent = noise_scan(models)
    rep.check("noise scan: MOS model count", "derived", float(nm), ref.NOISE_SCAN_MODELS, ref.NOISE_SCAN_MODELS, "", 1)
    rep.check("noise scan: models missing noia/ntnoi/ef", "derived", float(absent), ref.NOISE_ABSENT_MODELS, ref.NOISE_ABSENT_MODELS, "", 1,
              "(the 2 pfet_06v0 lack ntnoi; BSIM4 default equals the others' value)")
    print("\nGaps (not estimated):")
    for g in ref.GAPS:
        print("  - " + g)


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
        mismatch_and_noise(rep, data, models, ng, work)
    return rep.summary(), data, rep.rows
