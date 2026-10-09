;; place_record.il -- draw any circuit record as a schematic + standard testbench.
;;
;; The layout (rows, positions) is computed in Python (pdk.py plan) and passed in as
;; a plan; this file only places, labels and checks. Every terminal gets a short
;; stub and a net label (no routed wires), so any topology comes out readable and
;; exactly connected. The result is verified against the record: each terminal's
;; net must be the one the record names.
;;
;; plan: (nil cell "X" tbcell "X_TB"
;;            devs  ((nil id "NM0" kind "mos" alias "N1" w "7u" l "500n" m "1"
;;                        xy (0.0 0.0) orient "R0" conns (("Drain" "A") ...))
;;                   (nil id "C0" kind "lib" cell "cap" params (("c" "600f"))
;;                        xy (4.0 2.0) orient "R0" conns (("PLUS" "B") ("MINUS" "vout"))) ...)
;;            pins  (("vdd" "inputOutput" (x y)) ...)
;;            symleft ("gnd" "vdd" "vin2" "vin1")          ; symbol's left pins, bottom to top
;;            tb    (nil supply "vdd" ground "gnd" inn "vin1" inp "vin2" out "vout"
;;                       vdd "1.8" vcm "0.9" cl "2p"))

procedure( PRp_axis(kind role)
  if( kind == "mos" then
    cond( ( role == "Gate" || role == "Body" 'h ) ( t 'v ) )
  else nil ) )

;; terminal name for a record connection (MOS roles go through the device map)
procedure( PRp_term(d role)
  if( d->kind == "mos" PRb_role(PRb_entry(d->alias)->pins role) role ) )

procedure( PRp_place(cv d)
  let( ((inst nil))
    inst = if( d->kind == "mos"
               PRb_mos(cv d->alias d->id d->xy d->orient d->w d->l d->m)
               PRb_lib(cv d->cell d->id d->xy d->orient d->params) )
    foreach( c d->conns
      PRb_label(cv inst PRp_term(d car(c)) cadr(c) PRp_axis(d->kind car(c))) )
    inst ) )

;; mismatches between the drawn connectivity and the plan, as strings
procedure( PRp_verify(cv devs)
  let( ((bad nil) (inst nil) (got nil))
    foreach( d devs
      inst = car(setof(i cv~>instances i~>name == d->id))
      if( !inst then bad = cons(sprintf(nil "%s missing" d->id) bad)
        foreach( c d->conns
          got = PRb_termNet(inst PRp_term(d car(c)))
          unless( got == cadr(c)
            bad = cons(sprintf(nil "%s.%s=%L(want %s)" d->id car(c) got cadr(c)) bad) ) ) ) )
    bad ) )

;; the standard bench around the DUT symbol: unity-gain loop through a 1 T
;; inductor, AC at the inverting input through 1 T, load CL. Returns the bench's
;; intended connections (checked after schCheck has extracted connectivity)
procedure( PRp_bench(tb lib cell b)
  let( ((x0 nil) (devs nil))
    x0 = dbCreateInst(tb dbOpenCellViewByType(lib cell "symbol" "" "r") "X0" 0.0:0.0 "R0")
    foreach( pr list(list(b->supply "vdd") list(b->ground "gnd!") list(b->inn "vinn")
                     list(b->inp "vcm") list(b->out "vout"))
      PRb_label(tb x0 car(pr) cadr(pr)) )
    devs = list(
      list(nil 'id "V_DD" 'kind "lib" 'cell "vdc" 'params list(list("vdc" b->vdd)) 'xy list(-4.0 3.0) 'orient "R0"
           'conns list(list("PLUS" "vdd") list("MINUS" "gnd!")))
      list(nil 'id "V_CM" 'kind "lib" 'cell "vdc" 'params list(list("vdc" b->vcm)) 'xy list(-4.0 0.0) 'orient "R0"
           'conns list(list("PLUS" "vcm") list("MINUS" "gnd!")))
      list(nil 'id "V_AC" 'kind "lib" 'cell "vdc" 'params list(list("vdc" b->vcm) list("acm" "1")) 'xy list(-6.0 -2.0) 'orient "R0"
           'conns list(list("PLUS" "vac") list("MINUS" "gnd!")))
      list(nil 'id "L_FB" 'kind "lib" 'cell "ind" 'params list(list("l" "1T")) 'xy list(3.0 2.0) 'orient "R0"
           'conns list(list("PLUS" "vout") list("MINUS" "vinn")))
      list(nil 'id "C_AC" 'kind "lib" 'cell "cap" 'params list(list("c" "1T")) 'xy list(-3.0 -2.0) 'orient "R0"
           'conns list(list("PLUS" "vinn") list("MINUS" "vac")))
      list(nil 'id "C_L" 'kind "lib" 'cell "cap" 'params list(list("c" b->cl)) 'xy list(4.0 -1.0) 'orient "R0"
           'conns list(list("PLUS" "vout") list("MINUS" "gnd!"))) )
    foreach( d devs PRp_place(tb d) )
    PRb_lib(tb "gnd" "GND0" -4.0:-4.0 "R0" nil)
    ;; the DUT's terminals, in the same form, so one check covers the whole bench
    cons(list(nil 'id "X0" 'kind "lib"
              'conns list(list(b->supply "vdd") list(b->ground "gnd!") list(b->inn "vinn")
                          list(b->inp "vcm") list(b->out "vout")))
         devs) ) )

procedure( PR_placeRecord(plan)
  prog( (lib cv tb foreign chk chk2 bad bad2)
    lib = PR_CFG->target_lib
    PRb_loadMap()
    unless( PRb_entry("N1") && PRb_entry("P1") return("NOT BUILT: device map incomplete") )
    foreign = PRb_reset(lib list(plan->tbcell plan->cell))
    when( foreign
      return(sprintf(nil "NOT BUILT: %L exist(s) in the target library and were not created by this pipeline (left untouched)" foreign)) )
    ;; ---- the circuit
    cv = PRb_newSchematic(lib plan->cell)
    foreach( d plan->devs PRp_place(cv d) )
    foreach( p plan->pins PRb_pin(cv car(p) cadr(p) caddr(p)) )
    chk = schCheck(cv)
    bad = PRp_verify(cv plan->devs)
    dbSave(cv)
    PRb_symbol(lib plan->cell plan->symleft)
    unless( ddGetObj(lib plan->cell "symbol")
      return(sprintf(nil "PARTIAL: %s drawn (check %L, mismatches %L); symbol failed" plan->cell chk bad)) )
    ;; ---- the testbench
    tb = PRb_newSchematic(lib plan->tbcell)
    bad2 = PRp_bench(tb lib plan->cell plan->tb)
    chk2 = schCheck(tb)                       ; connectivity is extracted here
    bad2 = PRp_verify(tb bad2)
    dbSave(tb)
    PRb_show(lib list(plan->cell plan->tbcell))
    return(sprintf(nil "PLACED: %s %d devices, check errors %L warnings %L, mismatches %d %L | %s check errors %L warnings %L, mismatches %d %L"
                   plan->cell length(plan->devs) car(chk) cadr(chk) length(bad) bad
                   plan->tbcell car(chk2) cadr(chk2) length(bad2) bad2)) ) )
