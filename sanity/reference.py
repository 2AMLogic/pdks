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
ICC = 10e-9

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
)

# Reported, not checked:
#  - DIBL. Our Vtlin and Vtsat each match the paper within 4 mV, yet our
#    DIBL = (Vtlin - Vtsat) / (0.7 - 0.05) is a uniform 1.32x the paper's
#    DIBL column for all eight devices, and no natural alternative (other
#    drain-bias pairs, other current levels) reproduces it. That points to
#    an unstated normalisation, not a model difference, so DIBL is printed
#    for information only.
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
