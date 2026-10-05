* IHP MIM capacitor vs temperature (template; filled in by sanity/ihp_spec.py)
* A.k: V = 0, f = 100 kHz; C from the imaginary part of the AC current.
* Swept over the A.ad range, -40 to 125 C.
.lib "@MODELS@/cornerCAP.lib" cap_typ
vc c 0 dc 0 ac 1
X1 c 0 cap_cmim w=@W@u l=@L@u
.control
foreach t @TEMPS@
  option temp=$t
  ac lin 1 100k 100k
  let cc = -imag(i(vc))/(2*pi*100e3)
  echo "RESULT_C $t $&cc"
end
.endc
.end
