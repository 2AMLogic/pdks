"""ASAP7 r1p7 sanity checks: device I-V against Clark et al. 2016, plus
inverter VTC, FO4 and an 11-stage ring oscillator. Sources, extraction
definitions and tolerances: reference.py. Run via sanity/run.py --pdk asap7.
"""

import os
import tempfile

import reference as ref
from common import Report, at, ngspice, read_xy, render as _render, results, ss_decade, vt_cc

DECKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "decks")


def render(deck, out_dir, name, **subs):
    return _render(os.path.join(DECKS, deck), out_dir, name, **subs)


def characterise(ng, models, osdi, work, device):
    pol = -1 if device.startswith("pmos") else 1
    out = os.path.join(work, device)
    deck = render("device_iv.sp", work, device, MODELS=models, OSDI=osdi, DEVICE=device,
                  OUT=out, VDD=pol * ref.VDD, VHALF=pol * ref.VDD / 2,
                  VLIN=pol * 0.05, VSTEP=pol * 0.005)
    ngspice(ng, deck)
    lin = read_xy(out + ".vg_lin")
    sat = read_xy(out + ".vg_sat")
    vd_full = read_xy(out + ".vd_full")
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
    ngspice(ng, render("inverter_vtc.sp", work, "vtc_" + vt, MODELS=models, OSDI=osdi,
                       VT=vt, VDD=ref.VDD, OUT=out))
    vin, vout = read_xy(out + ".vtc")
    vm = next(vin[i] for i in range(len(vin)) if vout[i] <= vin[i])
    gain = max(abs((vout[i + 1] - vout[i]) / (vin[i + 1] - vin[i])) for i in range(len(vin) - 1))
    return dict(vm=vm, gain=gain, voh=vout[0], vol=vout[-1])


def fo4(ng, models, osdi, work, vt):
    r = results(ngspice(ng, render("fo4.sp", work, "fo4_" + vt, MODELS=models, OSDI=osdi,
                                   VT=vt, VDD=ref.VDD, VMID=ref.VDD / 2)))
    return dict(tphl=r["tphl"], tplh=r["tplh"], fo4=(r["tphl"] + r["tplh"]) / 2)


def ring(ng, models, osdi, work, vt):
    r = results(ngspice(ng, render("ring11.sp", work, "ring11_" + vt, MODELS=models, OSDI=osdi,
                                   VT=vt, VDD=ref.VDD, VMID=ref.VDD / 2)))
    period = r["five_periods"] / 5
    return dict(period=period, freq=1 / period, stage=period / (2 * ref.RO_STAGES))


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

    return rep.summary(), data, rep.rows
