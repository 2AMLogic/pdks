"""SKY130 sanity checks: threshold voltage, saturation current and leakage of
the 1.8 V nFET and pFET (plus the LVT nFET and LVT/HVT pFET) against SkyWater's published e-test windows. Sources
and definitions: reference.py. Run via sanity/run.py --pdk sky130.
"""

import math
import glob
import os
import re
import tempfile

import reference as ref
from common import (Report, at, elmore_ladder, gap_check, load_interconnect, mos_sweeps, ngspice, render,
                    results, vt_max_gm)

SPICEINIT = "set ngbehavior=hsa\nset ng_nomodcheck\n"
DECKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ngspice", "sky130")


def mismatch_deck(ng, work, prefix, name, corner, w, l, m, n, seed):
    deck = render(os.path.join(DECKS, "mismatch.sp.in"), work, name, PDK_DIR=os.path.join(prefix, "sky130", "sky130A"),
                  NGSPICE=ng, CORNER=corner, W=w, L=l, M=m, N=n, SEED=seed)
    return results(ngspice(ng, deck, cwd=work, spiceinit=SPICEINIT))


def noise_deck(ng, work, prefix, name, bias):
    deck = render(os.path.join(DECKS, "noise.sp.in"), work, name, PDK_DIR=os.path.join(prefix, "sky130", "sky130A"),
                  NGSPICE=ng, VGLO=bias["VG"] - 0.002, VGHI=bias["VG"] + 0.002, **bias)
    return results(ngspice(ng, deck, cwd=work, spiceinit=SPICEINIT))


def noise_scan(prefix):
    """Models in every *.pm3.spice (corner variants excluded) and those lacking
    noise parameters: (files, models, noia == 0 count, {file: [(count, missing)]})."""
    spice = os.path.join(prefix, "sky130", "sky130A", "libs.ref", "sky130_fd_pr", "spice")
    files = [f for f in sorted(glob.glob(os.path.join(spice, "*.pm3.spice")))
             if not re.search(r"__(ff|fs|sf|ss|leak|tt_leak)\.pm3", f)]
    models = zero = absent = 0
    ef = set()
    for f in files:
        for b in re.split(r"(?im)^\.model\s+", open(f).read())[1:]:
            if "mos" not in b.split("\n", 1)[0].lower():
                continue
            models += 1
            miss = [k for k in ("noia", "ntnoi", "tnoia") if not re.search(r"(?im)^\+\s*%s\s*=" % k, b)]
            absent += bool(miss)
            m = re.search(r"(?im)^\+\s*noia\s*=\s*([-0-9.e+]+)\s*$", b)
            zero += bool(m) and float(m.group(1)) == 0
            if os.path.basename(f) == "sky130_fd_pr__nfet_01v8__tt.pm3.spice":
                ef.add(re.search(r"(?im)^\+\s*ef\s*=\s*(\S+)", b).group(1))
    return len(files), models, zero, absent, ef


def mismatch_and_noise(rep, data, prefix, ng, work):
    print("\nMismatch (Monte Carlo, library corner tt_mm: mc_mm_switch=1), 1.8 V nFET, %d pairs per area" % ref.MISMATCH_N)
    print("  No published reference exists (reference.py); checks are derived from the model files.\n")
    n = ref.MISMATCH_N
    runs = []
    for w, l, m, seed in ref.MISMATCH_AREAS:
        r = mismatch_deck(ng, work, prefix, "mm_%g_%g_%g" % (w, l, m), "tt_mm", w, l, m, n, seed)
        runs.append(("%g/%g x%g" % (w, l, m), r))
        data["mismatch %g/%g x%g" % (w, l, m)] = r
        rep.info("sigma(dVgs) %g/%g x%g" % (w, l, m), r["sigma_dvgs_V"], "mV", 1e3)
    for key, label, n_s in (("avt_dvgs_mVum", "AVT(dVgs)", n), ("avt_mVum", "AVT(Vt)", 2 * n), ("abeta_pcum", "ABeta", 2 * n)):
        vals = [r[key] for _, r in runs]
        mean = sum(vals) / len(vals)
        t = ref.mc_tol(n_s)
        for (tag, r) in runs:
            rep.check("%s*sqrt(A) %s" % (label, tag), "derived", r[key], mean * (1 - t), mean * (1 + t),
                      "%s" % ("%um" if key == "abeta_pcum" else "mV um"), 1, "(area scaling; mean %.3g, +-%.0f %%)" % (mean, 100 * t))
    vt_floor = ref.VTH0_SLOPE * 1e3
    t = ref.mc_tol(2 * n)
    for (tag, r) in runs:
        rep.check("AVT(Vt) floor %s" % tag, "bound", r["avt_mVum"], vt_floor * (1 - t), 1e9, "mV um", 1,
                  "(model vth0_slope %.3f mV um; measured/slope %.2f)" % (vt_floor, r["avt_mVum"] / vt_floor))
    rep.info("ABeta vs model toxe_slope", sum(r["abeta_pcum"] for _, r in runs) / len(runs), "%um", 1,
             "(model toxe_slope %.3f %%um; beta ~ 1/tox)" % (ref.TOXE_SLOPE * 100))
    off = mismatch_deck(ng, work, prefix, "mm_off", "tt", 1, 0.5, 1, 3, 1)
    rep.check("mismatch off (corner tt): sigma(dVgs)", "derived", off["sigma_dvgs_V"], 0, 1e-9, "V", 1, "(mc_mm_switch=0)")
    a = mismatch_deck(ng, work, prefix, "mm_rep1", "tt_mm", 1, 0.5, 1, 3, 5)
    b = mismatch_deck(ng, work, prefix, "mm_rep2", "tt_mm", 1, 0.5, 1, 3, 5)
    rep.check("same seed, same result", "derived", abs(a["sigma_dvgs_V"] - b["sigma_dvgs_V"]) + abs(a["sigma_vt_V"] - b["sigma_vt_V"]),
              0, 0, "V", 1, "(setseed + reset)")

    print("\nNoise, 1.8 V nFET %(W)g/%(L)g um, Vg %(VG)g V, Vd %(VD)g V (ngspice .noise, 27 C)\n" % ref.NOISE_BIAS)
    r = noise_deck(ng, work, prefix, "noise_long", ref.NOISE_BIAS)
    data["noise long"] = r
    lo, hi = ref.GAMMA_LONG
    rep.known("thermal gamma (4kT*gamma*gm) 7/8", r["gamma_thermal"], lo, hi, "", 1, ref.NOISE_KNOWN["gamma"])
    lo, hi = ref.NYQUIST
    rep.known("Nyquist S_id/(4kT*gds) at Vds=0", r["nyquist_ratio"], lo, hi, "", 1, ref.NOISE_KNOWN["nyquist"])
    sl = r["flicker_slope"]
    rep.check("flicker slope 1..100 Hz = -ef", "derived", sl, -ref.EF - ref.FLICKER_SLOPE_TOL, -ref.EF + ref.FLICKER_SLOPE_TOL, "", 1,
              "(model ef %.2f)" % ref.EF)
    rep.info("flicker level at 1 Hz (input, V^2/Hz)", r["sv_flicker_1Hz_V2"], "V2/Hz", 1, "(no published value: gap)")
    short = noise_deck(ng, work, prefix, "noise_short", ref.NOISE_BIAS_SHORT)
    data["noise short"] = short
    rep.info("thermal gamma 7/0.15", short["gamma_thermal"], "", 1, "(information; no long-channel claim)")

    nf, nm, zero, absent, ef = noise_scan(prefix)
    rep.check("noise scan: models with noia = 0", "bound", zero, 0, 0, "", 1, "(%d models in %d files)" % (nm, nf))
    rep.check("noise scan: models missing noia/ntnoi/tnoia", "derived", absent, ref.NOISE_ABSENT_MODELS, ref.NOISE_ABSENT_MODELS, "", 1,
              "(listed in reference.NOISE_ABSENT)")
    rep.check("noise scan: nfet_01v8 ef in every bin", "derived", float(len(ef)), 1, 1, "", 1, "(value %s)" % ", ".join(sorted(ef)))
    rep.check("noise scan: model counts", "derived", float(nm), ref.NOISE_SCAN_MODELS, ref.NOISE_SCAN_MODELS, "", 1)
    print("\nGaps (not estimated):")
    for g in ref.GAPS:
        print("  - " + g)


def interconnect(rep, ngdir, ng, work, data):
    _, val, num, wire_inc = load_interconnect(ngdir, "sky130")
    print("\nInterconnect: layer table vs [SKYR], [SKYRES], [SKYC] (reference.py)\n")
    for lay, (w, s) in ref.METALS.items():
        rep.check("%s width" % lay, "published", num(lay, "width_min"), w, w, "nm", 1)
        rep.check("%s spacing" % lay, "published", num(lay, "spacing_min"), s, s, "nm", 1)
        rep.check("%s pitch = width + spacing" % lay, "derived", num(lay, "pitch"), w + s, w + s, "nm", 1)
        rs = ref.RSHEET[lay]
        rep.check("%s sheet resistance" % lay, "published", num(lay, "rsheet"), rs, rs, "ohm/sq", 1)
    for lay, (w, s) in ref.CUTS.items():
        rep.check("%s width" % lay, "published", num(lay, "width_min"), w, w, "nm", 1)
        rep.check("%s spacing" % lay, "published", num(lay, "spacing_min"), s, s, "nm", 1)
    order = [num(l, "rsheet") for l in ("li1", "met1", "met3", "met5")]
    rep.check("sheet resistance li1 > met1 > met3 > met5", "derived", float(order == sorted(order, reverse=True)
              and len(set(order)) == 4), 1, 1, "", 1)
    for name, mat, pre in (("parallel-plate", ref.CAP_AREA, "c_area_to_"), ("fringe up", ref.CAP_FRINGE_UP, "c_fringe_up_to_"),
                           ("fringe down", ref.CAP_FRINGE_DOWN, "c_fringe_down_to_")):
        same = all(abs(num(a, pre + b) - float(v)) < 1e-9 for (a, b), v in mat.items())
        rep.check("%s capacitance table, %d entries" % (name, len(mat)), "published", float(same), 1, 1, "", 1)
    # Derived physics: the coupling to a farther layer is smaller (parallel
    # plate falls as 1/d, fringe as the field shields).
    layers = ["li1", "met1", "met2", "met3", "met4", "met5"]
    for pre, label in (("c_area_to_", "parallel-plate"), ("c_fringe_up_to_", "fringe-up")):
        mono = True
        for i, lo in enumerate(layers[:-2]):
            c = [num(lo, pre + up) for up in layers[i + 1:]]
            mono &= all(a > b for a, b in zip(c, c[1:]))
        rep.check("%s capacitance falls with separation" % label, "derived", float(mono), 1, 1, "", 1)
    expect = {(m, q) for m in ref.METALS for q in ref.GAP_QUANTITIES} | {(v, q) for v in ref.CUTS for q in ref.GAP_CUT_QUANTITIES}
    gap_check(rep, data, val, expect)
    print()
    lay = ref.ELMORE_LAYER
    rsh, w = num(lay, "rsheet"), num(lay, "width_min") * 1e-9
    elmore_ladder(rep, data, ng, wire_inc, work, ref.ELMORE_SEGMENTS, dict(ref.ELMORE, w=w), rsh,
                  ref.ELMORE_L, w, ref.ELMORE_CPL, ref.ELMORE_RS, ref.ELMORE_CL, ref.ELMORE_TOL)
    print()


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
        print("")
        mismatch_and_noise(rep, data, prefix, ng, work)
        interconnect(rep, os.path.join(prefix, "sky130", "ngspice"), ng, work, data)
    return rep.summary(), data, rep.rows
