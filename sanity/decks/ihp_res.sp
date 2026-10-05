* IHP poly resistor vs temperature (template; filled in by sanity/ihp_spec.py)
* A.i structures: R1 is one W x L stripe, RN is N stripes of (W/N) x L in
* parallel; 0.5 V across each. Swept over the A.af range, -40 to 125 C.
.lib "@MODELS@/cornerRES.lib" res_typ
v1 a 0 0.5
vn b 0 0.5
X1 a 0 0 @RES@ w=@W@u l=@L@u
@PARALLEL@
.control
foreach t @TEMPS@
  option temp=$t
  op
  echo "RESULT_R $t $&@v1[i] $&@vn[i]"
end
.endc
.end
