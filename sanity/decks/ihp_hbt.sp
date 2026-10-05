* IHP npn13G2 HBT checks (template; filled in by sanity/ihp_spec.py)
*   X1: one emitter, VBE = 0.7 V, VCB = 0      -> BETA, IC07 (A.n, A.ai)
*   X4: four emitters, VCE = 1.2 V, VBE swept  -> |h21| at 40 GHz (A.s)
.lib "@MODELS@/cornerHBT.lib" hbt_typ
.temp @TEMP@
.param vbe=0.85
vc1 c1 0 0.7
vb1 b1 0 0.7
X1 c1 b1 0 0 npn13G2 Nx=1
vc4 c4 0 1.2
vb4 b4 0 dc {vbe} ac 1
X4 c4 b4 0 0 npn13G2 Nx=4
.control
op
echo "RESULT ic07 $&@vc1[i]"
echo "RESULT ib07 $&@vb1[i]"
foreach v 0.80 0.82 0.84 0.86 0.88 0.90 0.92 0.94 0.96 0.98 1.00
  alterparam vbe=$v
  reset
  ac lin 1 40e9 40e9
  let h21 = abs(i(vc4)/i(vb4))
  echo "RESULT_H21 $v $&h21"
end
.endc
.end
