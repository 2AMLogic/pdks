* GF180MCU resistor or MIM capacitor vs temperature (template; filled in by
* sanity/gf180mcu/checks.py). A resistor gets 0.1 V DC; a capacitor's C
* comes from the imaginary part of the AC current at 100 kHz, V = 0.
.include "@MODELS@/design.ngspice"
.lib "@MODELS@/sm141064.ngspice" res_typical
.lib "@MODELS@/sm141064.ngspice" mimcap_typical
.lib "@MODELS@/sm141064.ngspice" cap_mim
v1 a 0 dc @VDC@ ac 1
@INSTANCE@
.control
foreach t @TEMPS@
  option temp=$t
  @MEASURE@
end
.endc
.end
