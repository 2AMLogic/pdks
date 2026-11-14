"""Reference values the ASAP7 sanity checks compare against.

Every reference value is copied from a cited source. The extraction
definitions (ICC below) are the ones that reproduce the published tables;
the tolerances were tightened after the first comparison showed agreement
to printed precision, and each says why it is that wide. Each check is one
of:

  published  - a value printed in a cited source, compared within a tolerance
  bound      - a published value that bounds ours from one side
  derived    - no published value exists; a physics or self-consistency
               check, stated as such in the README

Sources
-------
[MEJ16]   L. T. Clark, V. Vashishtha, L. Shifren, A. Gujja, S. Sinha, B. Cline,
          C. Ramamurthy, G. Yeric, "ASAP: A 7-nm finFET predictive process
          design kit," Microelectronics Journal 53 (2016) 105-115,
          doi:10.1016/j.mejo.2016.04.006. Tables 3 and 4 (p. 113): "typical
          corner parameters (per fin) at 25 C", VDD 0.7 V. Section 6.1 for
          the linear-current design assumption. (The PDK ships this paper as
          docs/mej_paper_asap7.pdf.)
[MSE17]   L. T. Clark, V. Vashishtha, D. M. Harris, S. Dietrich, Z. Wang,
          "Design flows and collateral for the ASAP7 7nm FinFET predictive
          process design kit," IEEE Int. Conf. on Microelectronic Systems
          Education (MSE), 2017. Section III: FO4 delays at 0.7 V, "including
          extracted layout resistance and capacitance".
"""

VDD = 0.7

# Extraction definitions. [MEJ16] does not state how Ioff, Vt or SS were
# extracted. Each definition below reproduces the published tables; none is
# fitted per device.
#
# Ioff: channel current at Vgs = 0, |Vds| = VDD, measured at the source.
#   [MEJ16]'s Ioff equals the model's channel current IDS to all printed
#   digits for all eight devices, so it excludes gate-induced drain leakage
#   (GIDL), which flows into the drain terminal and, for nmos_sram, is larger
#   than the channel current itself.
# Vt: constant current, ICC = 10 nA per fin, interpolated in log(Id).
#   This one value reproduces all 16 published Vt values (Vtlin at
#   |Vds| = 50 mV, Vtsat at |Vds| = VDD) within 4 mV. The common
#   100 nA * W/L criterion is about 60 mV off for every device, so 10 nA is
#   evidently what the authors used. It is one shared value inferred from
#   16 data points, not a per-device fit.
# SS: gate-voltage swing across the decade from ICC to 10 * ICC at
#   |Vds| = VDD. This reproduces all eight published values within 0.4 mV/dec.
# DIBL: (Vtlin - Vtsat) / DIBL_VDS_SPAN, the same two Vt values. The span is
#   0.85 V, not the 0.65 V the paper's own bias points span; it was recovered
#   by solving the published column for it, and it is the weakest-supported
#   definition in this file. See DIBL_VDS_SPAN below for the measurement, the
#   two pieces of counter-evidence and what it leaves unexplained.
ICC = 10e-9

# DIBL denominator, in V. [MEJ16] prints a DIBL column but states no
# definition, and the obvious one -- its own two drain biases, (0.7 - 0.05) V
# -- does not reproduce it. Earlier revisions of this file and of the README
# recorded that gap as "a uniform 1.32x" and "the 1.31x factor" respectively;
# measured at full precision it is neither, and it is not uniform: 1.2961 to
# 1.3275, mean 1.3143. Issue #71 therefore solved for the denominator the
# printed column implies, device by device, instead of testing one candidate:
#
#   D = (Vtlin - Vtsat) / DIBL_published      (V, our Vt, the paper's column)
#
#   device      Vtlin     Vtsat   Vtlin-Vtsat  published   implied   ours/paper
#                 (V)       (V)          (mV)     (mV/V)     D (V)    at 0.85 V
#   nmos_sram  0.268846  0.252646       16.200      19.23    0.8424       0.9911
#   nmos_rvt   0.187421  0.169098       18.323      21.31    0.8598       1.0116
#   nmos_lvt   0.119612  0.100681       18.931      22.32    0.8482       0.9979
#   nmos_slvt  0.057478  0.038228       19.250      22.55    0.8537       1.0043
#   pmos_sram  0.223214  0.202688       20.525      24.10    0.8517       1.0020
#   pmos_rvt   0.186762  0.160652       26.110      30.36    0.8600       1.0118
#   pmos_lvt   0.126849  0.100048       26.801      31.06    0.8629       1.0151
#   pmos_slvt  0.065381  0.038207       27.174      31.76    0.8556       1.0066
#
# The eight implied denominators span 0.8424 to 0.8629 V, mean 0.8543 V: a
# 2.4 % spread across devices whose Vtlin - Vtsat ranges from 16.2 to 27.2 mV,
# so the quantity the paper's column differs from ours by is a ratio, not an
# offset. (Fitting the gap as a constant offset in Vtlin - Vtsat instead needs
# 3.70 to 6.61 mV, a 56 % spread -- refuted.)
#
# 0.9 - 0.05 V = 0.85 V lies inside that range, 0.5 % below the mean, and it is
# the only round value of the span that does. Sweeping the denominator from
# 0.60 to 1.00 V in 0.05 V steps, the next candidates either side read 6.8 %
# high (0.80 V) and 5.1 % low (0.90 V), both outside the implied range -- so a
# bare 0.9 V supply, with no linear-bias subtraction, is refuted too. This is
# the README's "normalising to a 0.9 V supply" guess, tested and confirmed: the
# paper's column is its own Vtlin - Vtsat divided by a 0.85 V span.
#
# It is one shared span inferred from 8 data points, not a per-device fit --
# the same standard as ICC above. Two things it does not settle, both recorded
# because they point the other way:
#
#  - [MEJ16] section 6.1 assumes "drain induced barrier lowering (DIBL) is
#    around 30 mV/V following the best to date nFET published result". Our
#    nFETs at the un-normalised 0.65 V span read 24.9, 28.2, 29.1 and
#    29.6 mV/V, which is "around 30"; the printed nFET column (19.23 to
#    22.55) is not. So the 0.85 V span reproduces the paper's table while
#    making that table disagree with the paper's own prose target.
#  - ASAP5 is the same authors, the same journal and the same 0.7 V supply,
#    and there the un-normalised (0.7 - 0.05) V span reproduces seven of
#    eight printed values within 0.1 mV/V (sanity/asap5/reference.py). If
#    ASAP7's column is normalised, the group changed convention between the
#    two papers. ASAP5's agreement is also 5x tighter than the best ASAP7
#    achieves here, so ASAP7's residual scatter is not explained either.
#
# Why DIBL is a check anyway: the value is printed in a cited source and only
# the extraction definition is assumed, which is the same footing as Vtlin,
# Vtsat and SS -- those rest on an inferred ICC and are labelled "published".
DIBL_VDS_SPAN = 0.85

# Per-fin device parameters, [MEJ16] Tables 3 (nFET) and 4 (pFET).
# Units: currents in A, voltages in V, SS in mV/dec, DIBL in mV/V.
DEVICES = {
    "nmos_sram": dict(idsat=28.57e-6, ieff=13.07e-6, ioff=0.001e-9, vtsat=0.25, vtlin=0.27, ss=62.44, dibl=19.23),
    "nmos_rvt":  dict(idsat=37.85e-6, ieff=18.13e-6, ioff=0.019e-9, vtsat=0.17, vtlin=0.19, ss=63.03, dibl=21.31),
    "nmos_lvt":  dict(idsat=45.19e-6, ieff=23.56e-6, ioff=0.242e-9, vtsat=0.10, vtlin=0.12, ss=62.90, dibl=22.32),
    "nmos_slvt": dict(idsat=50.79e-6, ieff=28.67e-6, ioff=2.444e-9, vtsat=0.04, vtlin=0.06, ss=63.33, dibl=22.55),
    "pmos_sram": dict(idsat=26.90e-6, ieff=11.37e-6, ioff=0.004e-9, vtsat=0.20, vtlin=0.22, ss=64.34, dibl=24.10),
    "pmos_rvt":  dict(idsat=32.88e-6, ieff=14.08e-6, ioff=0.023e-9, vtsat=0.16, vtlin=0.19, ss=64.48, dibl=30.36),
    "pmos_lvt":  dict(idsat=39.88e-6, ieff=18.18e-6, ioff=0.230e-9, vtsat=0.10, vtlin=0.13, ss=64.44, dibl=31.06),
    "pmos_slvt": dict(idsat=45.60e-6, ieff=22.64e-6, ioff=2.410e-9, vtsat=0.04, vtlin=0.07, ss=64.94, dibl=31.76),
}

# Tolerances. The first comparison showed Idsat and Ieff agreeing to 4
# significant figures, so these are regression tolerances: tight enough to
# catch a wrong model card, corner, temperature, L/NFIN binding or .osdi
# build, with margin for printed rounding.
TOL = dict(
    idsat=0.02,     # relative
    # Ieff = (IH + IL) / 2, IH = Id(Vgs = VDD, Vds = VDD/2) read off the Id-Vd
    # sweep, IL = Id(Vgs = VDD/2, Vds = VDD) read off the Id-Vg sweep. This
    # is the Na et al. (IEDM 2002) definition; it checks both curve families.
    ieff=0.02,      # relative
    ioff_dec=0.15,  # decades; printed to as little as 1 significant figure
    vt=0.015,       # V; printed to 2 decimals (+-5 mV) plus 10 mV margin
    ss=2.0,         # mV/dec
    # DIBL: mV/V. The largest residual once DIBL_VDS_SPAN is assumed is
    # 0.470 mV/V (pmos_lvt, +1.5 %); 1.0 mV/V covers all eight with margin and
    # is the value sanity/asap5/reference.py already uses for this quantity.
    # It still bites: it admits only 0.85 mV of error in Vtlin - Vtsat, where
    # our absolute Vt values match the paper's columns to 4 mV. Perturbing
    # DIBL_VDS_SPAN by one 0.05 V step fails eight of the eight devices at
    # 0.80 V and seven of eight at 0.90 V (measured, issue #71).
    dibl=1.0,
)

# Reported, not checked:
#  - Idsat / Idlin. [MEJ16] section 6.1 says linear current "was assumed to
#    be 4.5x smaller than the saturation current", a design target with no
#    stated bias point. Printed at |Vds| = 50 mV for information.
IDSAT_OVER_IDLIN = 4.5

# [MSE17] FO4 inverter delays at 0.7 V, post-layout (extracted RC). Our FO4
# is pre-layout, so the published value is an upper bound; the lower bound
# rejects anything implausibly fast (wire RC is not more than half of it).
FO4_POSTLAYOUT = {"rvt": 8.1e-12, "lvt": 6.8e-12, "slvt": 6.0e-12}
FO4_LOWER_FRACTION = 0.5

# No published inverter VTC or ring-oscillator figure exists for ASAP7 (we
# searched the PDK paper, MSE 2017, the ICCAD 2017 tutorial and the cell
# library docs). These are derived checks, stated as such:
#  - VTC: switching threshold within 50 mV of VDD/2 for the equal-fin INVx1
#    ([MEJ16] Fig. 8 caption: pFET drive is about 90% of nFET), peak gain
#    above 5, and full-swing outputs (within 10 mV of the rails).
VTC_VM_TOL = 0.050
VTC_MIN_GAIN = 5.0
VTC_RAIL_TOL = 0.010
#  - Ring oscillator: per-stage delay T / (2 N) of an FO1 ring, as a fraction
#    of the simulated FO4 delay. Logical effort with parasitic delay p ~ 1
#    gives (1 + p) / (4 + p) = 0.4; we accept 0.25 to 0.6.
RO_STAGES = 11
RO_FO1_OVER_FO4 = (0.25, 0.6)

# ---------------------------------------------------------------------------
# Interconnect (pdks/asap7/interconnect.csv, installed as
# <prefix>/asap7/ngspice/interconnect.csv)
#
# [MEJ16] Table 1 ("Key layer lithography assumptions, widths and pitches")
# is the only per-layer geometry the PDK's documents publish: width and
# pitch for M1-M9 and the via layers. Section 4.4 states "Metal and via
# aspect ratios follow [13] at 2:1", which gives thickness (metal) and
# height (via) as 2 x width; that is a derived value. The DRM
# (docs/asap7_drm.pdf at the pinned commit) lists the layers and their DRC
# rules but no thickness, resistance or capacitance. Sheet resistance,
# its temperature coefficient, via resistance and capacitance per length are
# NOT published in the pinned repository: [MEJ16] section 6 says extraction
# models exist (Cu/Ru, with the size-effect resistivity of Pyzyna et al.) but
# prints no numbers, and the Calibre RCX deck is distributed separately by
# ASU and is not fetched. They are explicit gaps in the table, so there is
# nothing to check them against, and they are not estimated.
#
# Metal layer: (width, pitch) in nm, [MEJ16] Table 1 (drawn width = width).
METALS = {
    "M1": (18, 36), "M2": (18, 36), "M3": (18, 36),
    "M4": (24, 48), "M5": (24, 48),
    "M6": (32, 64), "M7": (32, 64),
    "M8": (40, 80), "M9": (40, 80),
}
# Via layer: width in nm, [MEJ16] Table 1 (VIA0-VIA3, VIA4-5, VIA6-7, VIA8).
VIAS = {"V1": 18, "V2": 18, "V3": 18, "V4": 24, "V5": 24, "V6": 32, "V7": 32, "V8": 40}
ASPECT = 2.0  # [MEJ16] section 4.4
GAP_QUANTITIES = ("rsheet", "rsheet_tcr", "c_iso_per_um", "c_pitch_per_um")  # per metal
GAP_VIA_QUANTITIES = ("r_via",)

# Wire-ladder check (derived: it tests our include against the closed form,
# not a published number). The deck drives an ideal step through RS into a
# wire of N pi segments loaded by CL. The simulated value is the first
# moment of the step response, integral of (vin - vout) dt, and the closed
# form is the Elmore delay
#     RS (C + CL) + R (C / 2 + CL),   R = RSH L / W,   C = CPL L.
# For a pi ladder this holds for every N (the distributed line's R C / 2).
# RSH and CPL below are TEST INPUTS chosen so the wire dominates; they are
# not ASAP7 values (ASAP7 publishes none, see above).
ELMORE = dict(l="20u", w="18n", rsh=50.0, cpl="0.2n", rs="1k", cl="1f", tstop="10n")
ELMORE_L, ELMORE_W, ELMORE_RSH, ELMORE_CPL = 20e-6, 18e-9, 50.0, 0.2e-9
ELMORE_RS, ELMORE_CL = 1e3, 1e-15
ELMORE_SEGMENTS = (1, 4, 64)
# Tolerance: the integral is trapezoidal on a 2 ps step (measured error
# ~1e-5) over 10 ns, about 58 time constants, so truncation is negligible;
# 1e-3 leaves margin for a different ngspice build.
ELMORE_TOL = 1e-3

# ---- Mismatch and noise (#45, part of #37) ------------------------------
# Nothing here is published for ASAP7, so every check below is derived from
# the pinned cards and the BSIM-CMG 107 source the OSDI is built from.
#
# What the authors say. The paper [MEJ16] (Clark et al. 2016) and the design manual
# (asap7_drm_201207a.pdf) give no variability, mismatch or noise statistics for
# the devices, nor a recommended method: searched the extracted text for
# variab, mismatch, monte, noise, flicker, statist. The only hits are
# process-variation remarks in the lithography discussion and a statement that
# Ge channels were rejected "when variability was evaluated" [73]; neither
# defines a device model. Recommendation: none stated.
# Verified against the pinned cards by sanity/predictive.py scan_cards (comment
# lines skipped): the three checksummed cards 7nm_{TT,FF,SS}_160803.pm (24 models).
#   - no statistical or mismatch construct (agauss, gauss, aunif, unif, mc_*,
#     mismatch*, monte*, sigma*, vary, lot, dev) in any card: 0 hits. So there is
#     no Monte Carlo deck and no Pelgrom check; the mismatch cell is "not modelled".
#   - no noise parameter (noia, noib, noic, ntnoi, ef, em, kf, af, lintnoi,
#     tnoimod) is set in any card (the "noise" section of each card is empty), so
#     BSIM-CMG 107's generic defaults apply (bsimcmg_body.include of the pinned
#     BSIM-CMG 107 source, lines 610-618): ef 1.0, em 4.1e7, noia 6.25e39,
#     noib 3.125e24, noic 8.75e7, ntnoi 1.0. They are not values fitted for ASAP7.
#     BSIM-CMG 107 has no tnoimod parameter; its thermal noise is the
#     charge-based expression sid = 4kT * ntnoi * ueff*qinv / (leff^2 + ueff*qinv*rds)
#     (BSIM4 tnoimod=0), shot noise of the gate currents, and thermal noise of
#     the source and drain resistances.
CARD_MODELS = 24

# Noise deck (ngspice/bsimcmg107/noise.sp.in, shared with ASAP5): nmos_rvt, nfin = 10, Vds = 0.7 V,
# 25 C, drain through an ideal inductor so the drain current noise appears across
# the device's own output impedance. Output-referred noise divided by the AC gain
# gives the input-referred spectrum; the drain current noise is that times gm.
NOISE_BIAS = dict(nfin=10, vg=0.3, vd=0.7)
# Placeholders of the shared deck that differ per PDK (L_CARD is comment text).
NOISE_DECK_VARS = dict(PDK="ASAP7", LIB="asap7.lib", L_CARD="l = 20n, nfin = 10", L_INST="l=20n ")
EF = 1.0                     # BSIM-CMG 107 default (the cards set none)
FLICKER_SLOPE_TOL = 0.01     # the model term is exactly f^-ef; allowance is numerical
# Nyquist (derived): a conductor in equilibrium has drain current noise
# 4kT*gds. With the drain at 0 V, the model's thermal term is
# 4kT*ntnoi*ueff*qinv/(leff^2 + ueff*qinv*rds), which equals 4kT*gds for
# ntnoi = 1 when gds comes from the channel alone, so S_id/(4kT*gds0) = 1.
# Read at 1 kHz (above the flicker term, which is zero at Vds = 0 anyway),
# gds0 from a +-1 mV drain step; 2 % allows for the finite difference.
# The ratio departs from 1 where something other than the channel enters the
# drain conductance or noise: the gate-current shot noise (2q*Ig), which grows
# with gate bias, and the junction/GIDL conductances, which carry no thermal
# term (the cause of any departure is not traced). Vg = 0.3 V here keeps the gate current negligible (measured at nfin 10: ratio 1.001 at 0.2 V, 1.010 at 0.3 V, 1.054 at 0.5 V).
NYQUIST = (0.98, 1.02)
# gamma (4kT*gamma*gm) is printed for information only. Long-channel theory
# (van der Ziel; Tsividis) gives 2/3 in strong-inversion saturation, but the
# total here also holds gate-current shot noise and resistor noise, and these
# short-channel devices are not in that regime, so no pass/fail band is claimed.

# Quantities for which no value could be found or derived; listed, not estimated.
GAPS = [
    "mismatch (threshold, current factor, Pelgrom coefficients): not modelled; the cards carry no statistical parameters and ASAP7 publishes none",
    "flicker-noise level: no published value; the model's BSIM-CMG default (noia, noib, noic) is printed as information only",
    "published thermal-noise gamma: none",
    "noise and mismatch of devices other than nmos_rvt (checked here: nmos_rvt only), and of resistors, capacitors and interconnect",
]
