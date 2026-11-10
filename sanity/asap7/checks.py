"""ASAP7 r1p7 sanity checks: device I-V against Clark et al. 2016, plus
inverter VTC, FO4, an 11-stage ring oscillator, the interconnect table
and derived noise checks (no mismatch statistics exist). Sources, extraction
definitions and tolerances: reference.py. Run via sanity/run.py --pdk asap7.
"""

import csv
import glob
import os
import tempfile

import predictive
import reference as ref
from common import Report, at, mos_sweeps, ngspice, read_xy, render, results, ss_decade, vt_cc

DECKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "decks")


def characterise(ng, models, osdi, work, device, tag=None):
    pol = -1 if device.startswith("pmos") else 1
    # Current is measured at the SOURCE (i(vs)), not the drain: [MEJ16]'s Ioff
    # values equal the model's channel current IDS exactly, i.e. they exclude
    # gate-induced drain leakage (GIDL), which flows into the drain terminal.
    # One fin, l = 20n drawn (the cell libraries' value; the cards add xl = 1n,
    # giving the paper's 21 nm actual gate length). No aux sweep is needed,
    # and Ioff is read at Vgs = 0, Vds = VDD.
    sw = mos_sweeps(ng, work, tag or device, ".include " + models,
                    "N1 d g s 0 %s l=20n nfin=1" % device, pol, ref.VDD,
                    0.05, 0.05, ref.VDD, 25, imeas="i(vs)", pre="pre_osdi " + osdi)
    lin, sat, vd_full = sw["vg_lin"], sw["vg_sat"], sw["vd_full"]
    vdd, h = ref.VDD, ref.VDD / 2
    idsat = at(*sat, vdd)
    vtlin, vtsat = vt_cc(*lin, ref.ICC), vt_cc(*sat, ref.ICC)
    return dict(
        idsat=idsat,
        ieff=(at(*vd_full, h) + at(*sat, h)) / 2,
        ioff=at(*sat, 0.0),
        vtlin=vtlin,
        vtsat=vtsat,
        ss=ss_decade(*sat, ref.ICC),
        dibl=1000 * (vtlin - vtsat) / (vdd - 0.05),
        idsat_over_idlin=at(*vd_full, vdd) / at(*vd_full, 0.05),
        # the Id-Vg and Id-Vd sweeps must agree where they meet, (VDD, VDD)
        sweep_mismatch=abs(at(*vd_full, vdd) - idsat) / idsat,
    )


def vtc(ng, models, osdi, work, vt):
    out = os.path.join(work, "vtc_" + vt)
    ngspice(ng, render(os.path.join(DECKS, "inverter_vtc.sp"), work, "vtc_" + vt, MODELS=models, OSDI=osdi,
                       VT=vt, VDD=ref.VDD, OUT=out))
    vin, vout = read_xy(out + ".vtc")
    vm = next(vin[i] for i in range(len(vin)) if vout[i] <= vin[i])
    gain = max(abs((vout[i + 1] - vout[i]) / (vin[i + 1] - vin[i])) for i in range(len(vin) - 1))
    return dict(vm=vm, gain=gain, voh=vout[0], vol=vout[-1])


def fo4(ng, models, osdi, work, vt):
    r = results(ngspice(ng, render(os.path.join(DECKS, "fo4.sp"), work, "fo4_" + vt, MODELS=models, OSDI=osdi,
                                   VT=vt, VDD=ref.VDD, VMID=ref.VDD / 2)))
    return dict(tphl=r["tphl"], tplh=r["tplh"], fo4=(r["tphl"] + r["tplh"]) / 2)


def ring(ng, models, osdi, work, vt):
    r = results(ngspice(ng, render(os.path.join(DECKS, "ring11.sp"), work, "ring11_" + vt, MODELS=models, OSDI=osdi,
                                   VT=vt, VDD=ref.VDD, VMID=ref.VDD / 2)))
    period = r["five_periods"] / 5
    return dict(period=period, freq=1 / period, stage=period / (2 * ref.RO_STAGES))


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
            raise SystemExit("not found: %s (run bootstrap.sh --pdk asap7)" % f)
    with open(table) as f:
        rows = list(csv.DictReader(f))
    val = {(r["layer"], r["quantity"]): r for r in rows}
    print("Interconnect: layer table vs [MEJ16] Table 1 and section 4.4 (reference.py)\n")
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
    models = os.path.join(prefix, "asap7", "ngspice", "models", "7nm_TT.pm")
    osdi = os.path.join(prefix, "tools", "bsimcmg107", "bsimcmg107.osdi")
    for f in (models, osdi):
        if not os.path.exists(f):
            raise SystemExit("not found: %s (run bootstrap.sh --pdk asap7)" % f)
    rep = Report()
    data = {}
    with tempfile.TemporaryDirectory(prefix="asap7-sanity-") as work:
        print("ASAP7 TT, 25 C, VDD %.2f V. Sources and tolerances: sanity/asap7/reference.py\n" % ref.VDD)
        for dev, pub in ref.DEVICES.items():
            m = characterise(ng, models, osdi, work, dev)
            data[dev] = m
            t = ref.TOL
            rep.check(dev + " Idsat", "published", m["idsat"], pub["idsat"] * (1 - t["idsat"]), pub["idsat"] * (1 + t["idsat"]), "uA", 1e6)
            rep.check(dev + " Ieff", "published", m["ieff"], pub["ieff"] * (1 - t["ieff"]), pub["ieff"] * (1 + t["ieff"]), "uA", 1e6)
            rep.check(dev + " Ioff", "published", m["ioff"], pub["ioff"] / 10 ** t["ioff_dec"], pub["ioff"] * 10 ** t["ioff_dec"], "nA", 1e9)
            rep.check(dev + " Vtlin", "published", m["vtlin"], pub["vtlin"] - t["vt"], pub["vtlin"] + t["vt"], "V", 1)
            rep.check(dev + " Vtsat", "published", m["vtsat"], pub["vtsat"] - t["vt"], pub["vtsat"] + t["vt"], "V", 1)
            rep.check(dev + " SS", "published", m["ss"], pub["ss"] - t["ss"], pub["ss"] + t["ss"], "mV/dec", 1)
            rep.check(dev + " Id-Vg/Id-Vd agree", "derived", m["sweep_mismatch"], 0, 1e-3, "", 1)
            rep.info(dev + " DIBL", m["dibl"], "mV/V", 1, "(paper prints %.2f; see reference.py)" % pub["dibl"])
            rep.info(dev + " Idsat/Idlin", m["idsat_over_idlin"], "", 1, "(paper's design target ~%.1f)" % ref.IDSAT_OVER_IDLIN)
            print()

        v = vtc(ng, models, osdi, work, "rvt")
        data["vtc_rvt"] = v
        rep.check("INVx1 RVT VTC switching point", "derived", v["vm"], ref.VDD / 2 - ref.VTC_VM_TOL, ref.VDD / 2 + ref.VTC_VM_TOL, "V", 1)
        rep.check("INVx1 RVT VTC peak gain", "derived", v["gain"], ref.VTC_MIN_GAIN, float("inf"), "", 1)
        rep.check("INVx1 RVT VTC VOH", "derived", v["voh"], ref.VDD - ref.VTC_RAIL_TOL, ref.VDD, "V", 1)
        rep.check("INVx1 RVT VTC VOL", "derived", v["vol"], 0, ref.VTC_RAIL_TOL, "V", 1)
        print()

        fo4s = {}
        for vt, pub in ref.FO4_POSTLAYOUT.items():
            f = fo4(ng, models, osdi, work, vt)
            data["fo4_" + vt] = f
            fo4s[vt] = f["fo4"]
            rep.check("FO4 delay %s (pre-layout)" % vt.upper(), "bound", f["fo4"], pub * ref.FO4_LOWER_FRACTION, pub, "ps", 1e12)
        rep.check("FO4 ordering RVT > LVT > SLVT", "derived", float(fo4s["rvt"] > fo4s["lvt"] > fo4s["slvt"]), 1, 1, "", 1)
        print()

        r = ring(ng, models, osdi, work, "rvt")
        data["ring11_rvt"] = r
        lo, hi = ref.RO_FO1_OVER_FO4
        rep.check("11-stage RO RVT stage delay / FO4", "derived", r["stage"] / fo4s["rvt"], lo, hi, "", 1,
                  "(f = %.2f GHz, stage %.2f ps)" % (r["freq"] / 1e9, r["stage"] * 1e12))
        print()

        # Corners: [MEJ16] shows FF/SS only as plots (Figs. 9-10), so the
        # check is derived: Idsat and Ioff order SS < TT < FF for every device.
        print("Corners: SS < TT < FF ordering (derived; the paper plots corners, no table)\n")
        mdir = os.path.dirname(models)
        for dev in ref.DEVICES:
            cs = {c: characterise(ng, os.path.join(mdir, "7nm_%s.pm" % c), osdi, work, dev, dev + "_" + c)
                  if c != "TT" else data[dev] for c in ("SS", "TT", "FF")}
            data[dev + "_corners"] = {c: dict(idsat=v["idsat"], ioff=v["ioff"]) for c, v in cs.items()}
            ok = all(cs["SS"][q] < cs["TT"][q] < cs["FF"][q] for q in ("idsat", "ioff"))
            rep.check("%s SS<TT<FF (Idsat, Ioff)" % dev, "derived", float(ok), 1, 1, "", 1,
                      "(Idsat %.1f / %.1f / %.1f uA)" % tuple(cs[c]["idsat"] * 1e6 for c in ("SS", "TT", "FF")))

        interconnect(rep, os.path.join(prefix, "asap7", "ngspice"), ng, work, data)

        cards = sorted(glob.glob(os.path.join(prefix, "asap7", "asap7_pdk_r1p7", "models", "hspice", "7nm_*_160803.pm")))
        ngdir = os.path.join(prefix, "asap7", "ngspice")
        predictive.checks(rep, data, ref, cards, ngdir, os.path.join(DECKS, "..", "..", "..", "ngspice", "asap7", "noise.sp.in"),
                          osdi, ng, work)

    return rep.summary(), data, rep.rows
