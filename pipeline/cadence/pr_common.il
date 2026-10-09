;; pr_common.il -- helpers shared by the PDK back end (loaded after pr_config.il,
;; which defines PR_CFG: work_dir, private_dir, ref_lib, ref_cell, tb_lib, tb_cell,
;; target_lib, technology).
;;
;; Transistors are placed from the private device map (aliases N1 / P1). No PDK
;; library, cell, pin or parameter name appears in this file, and none is ever
;; returned or printed. Cells are created only in the target library, marked with
;; the property PR_created, and only marked cells are ever deleted.

PR_MARK = "PR_created"

procedure( PRb_loadMap()
  load(strcat(PR_CFG->private_dir "/devmap.il")) )          ; defines PR_DEVMAP

procedure( PRb_entry(alias) car(setof(e PR_DEVMAP e->alias == alias)) )
procedure( PRb_role(alist role) cadr(assoc(role alist)) )
procedure( PRb_center(b) list((xCoord(car(b)) + xCoord(cadr(b))) / 2.0 (yCoord(car(b)) + yCoord(cadr(b))) / 2.0) )

;; set a CDF parameter by name on an instance (returns t if it existed)
procedure( PRb_set(inst pname val)
  let( ((cdf cdfGetInstCDF(inst)) (p nil))
    p = cdf && car(setof(x cdf~>parameters x~>name == pname))
    when( p p~>value = val t ) ) )

;; a transistor from the device map. Every parameter with a size role is set: a
;; device can carry several with the same role (total and finger width), equal at
;; one finger. The multiplier the netlister writes need not be the one in the map,
;; so every multiplier-like parameter is set too.
procedure( PRb_mos(cv alias name xy orient w l @optional (mult "1"))
  let( ((e PRb_entry(alias)) (master nil) (inst nil) (cdf nil))
    master = dbOpenCellViewByType(e->lib e->cell e->view "" "r")
    inst = dbCreateInst(cv master name xy orient)
    foreach( pr list(list("fingers" "1") list("mult" mult) list("length" l) list("width" w))
      foreach( q setof(x e->params car(x) == car(pr)) PRb_set(inst cadr(q) cadr(pr)) ) )
    cdf = cdfGetInstCDF(inst)
    foreach( p setof(x cdf~>parameters pcreMatchp("(?i)^(m|mult|multi|mf|mfactor|simm|multiplier)$" x~>name))
      p~>value = mult )
    inst ) )

;; a generic element (analogLib) with CDF parameters
procedure( PRb_lib(cv cell name xy orient params)
  let( ((master dbOpenCellViewByType("analogLib" cell "symbol" "" "r")) (inst nil))
    inst = dbCreateInst(cv master name xy orient)
    foreach( pr params PRb_set(inst car(pr) cadr(pr)) )
    inst ) )

;; wire stub from a terminal, pointing away from the instance, with a net label
;; axis: nil = along the dominant direction; 'h / 'v = forced (still pointing away)
procedure( PRb_label(cv inst term net @optional (axis nil))
  let( ((t0 nil) (ctr nil) (ic nil) (dx 0) (dy 0) (end nil) (w nil))
    t0 = car(setof(x inst~>master~>terminals x~>name == term))
    when( t0
      ctr = dbTransformPoint(PRb_center(car(t0~>pins)~>fig~>bBox) inst~>transform)
      ic = PRb_center(inst~>bBox)
      dx = xCoord(ctr) - xCoord(ic)  dy = yCoord(ctr) - yCoord(ic)
      end = if( (axis == 'h) || (!axis && abs(dx) >= abs(dy))
                list(xCoord(ctr) + if(dx >= 0 0.25 -0.25) yCoord(ctr))
                list(xCoord(ctr) yCoord(ctr) + if(dy >= 0 0.25 -0.25)) )
      w = schCreateWire(cv "route" "full" list(ctr end) 0 0 0 nil nil)
      schCreateWireLabel(cv car(w) end net "lowerCenter" "R0" "stick" 0.0625 nil)
      t ) ) )

;; a schematic pin with a short labelled stub, so it joins its net by name
procedure( PRb_pin(cv name dir xy)
  let( ((m dbOpenCellViewByType("basic" if(dir == "output" "opin" if(dir == "inputOutput" "iopin" "ipin")) "symbol" "" "r")))
    schCreatePin(cv m name dir nil xy "R0") ) )

;; the net a terminal of an instance is on (nil if unconnected)
procedure( PRb_termNet(inst term)
  let( ((it car(setof(x inst~>instTerms x~>name == term))))
    it && it~>net && it~>net~>name ) )

;; ------------------------------------------------------------------ symbols
procedure( PRb_symPin(sy name dir pt edge)
  let( ((net dbMakeNet(sy name)) (fig nil) (x xCoord(pt)) (y yCoord(pt)))
    dbCreateTerm(net name dir)
    dbCreateLine(sy list("pin" "drawing") list(pt edge))
    fig = dbCreateRect(sy list("pin" "drawing") list(list(x - 0.025 y - 0.025) list(x + 0.025 y + 0.025)))
    dbCreatePin(net fig name)
    dbCreateLabel(sy list("pin" "label") edge name if(dir == "output" "centerRight" "centerLeft") "R0" "stick" 0.05) ) )

;; dialog-free box symbol: `left` pins bottom to top, outputs on the right
procedure( PRb_symbol(lib cell left)
  let( ((sch dbOpenCellViewByType(lib cell "schematic" "" "r")) (sy nil) (right nil) (y 0) (h 0) (n 0))
    sy = dbOpenCellViewByType(lib cell "symbol" "schematicSymbol" "w")
    foreach( trm sch~>terminals
      when( trm~>direction == "output" right = cons(trm~>name right) ) )
    left = setof(x left member(x sch~>terminals~>name))
    n = max(length(left) length(right))
    h = 0.25 * (n + 1)
    dbCreateRect(sy list("device" "drawing") list(list(0.0 0.0) list(1.0 h)))
    dbCreateLabel(sy list("device" "label") list(0.5 h / 2.0) cell "centerCenter" "R0" "stick" 0.0625)
    y = 0.25
    ;; each symbol pin keeps its schematic terminal's direction
    foreach( nm left  PRb_symPin(sy nm car(setof(x sch~>terminals x~>name == nm))~>direction
                                 list(-0.25 y) list(0.0 y))  y = y + 0.25 )
    y = h / 2.0
    foreach( nm right PRb_symPin(sy nm "output" list(1.25 y) list(1.0 y))  y = y + 0.25 )
    dbCreateRect(sy list("instance" "drawing") list(list(-0.3 -0.1) list(1.3 h + 0.1)))
    dbCreateLabel(sy list("instance" "label") list(0.5 h + 0.05) "[@instanceName]" "lowerCenter" "R0" "stick" 0.0625)
    dbSave(sy)  dbClose(sy)
    t ) )

;; ------------------------------------------------------------------ cells
;; open a new schematic in the target library and mark it as ours
procedure( PRb_newSchematic(lib cell)
  let( ((cv dbOpenCellViewByType(lib cell "schematic" "schematic" "w")))
    dbCreateProp(cv PR_MARK "string" "analog_repro")
    cv ) )

;; is this cell one the pipeline created? (its schematic carries PR_MARK)
procedure( PRb_ours(lib cell)
  let( ((cv nil) (ok nil))
    when( ddGetObj(lib cell "schematic")
      cv = dbOpenCellViewByType(lib cell "schematic" "" "r")
      ok = cv && dbGetPropByName(cv PR_MARK) && t
      when( cv dbClose(cv) ) )
    ok ) )

;; delete the given cells from the target library -- only cells we created.
;; Returns the names that exist and are NOT ours (left untouched).
procedure( PRb_reset(lib cells)
  let( ((foreign nil))
    unless( lib == PR_CFG->target_lib error("PRb_reset: only the target library may be changed") )
    foreach( c cells
      cond(
        ( !ddGetObj(lib c) nil )
        ( !PRb_ours(lib c) foreign = cons(c foreign) )
        ( t
          foreach( w hiGetWindowList()
            let( ((cv car(errset(geGetWindowCellView(w)))))
              when( cv && dbIsId(cv) && cv~>libName == lib && cv~>cellName == c hiCloseWindow(w) ) ) )
          foreach( cv setof(x dbGetOpenCellViews() x~>libName == lib && x~>cellName == c) dbPurge(cv) )
          ddDeleteObj(ddGetObj(lib c)) ) ) )
    foreign ) )

;; reopen cells in editable windows (the GUI session only)
procedure( PRb_show(lib cells)
  when( isCallable('geOpen) && hiGetWindowList()
    foreach( c cells
      let( ((w car(errset(geOpen(?lib lib ?cell c ?view "schematic" ?mode "a")))))
        when( w errset(geFit(w)) ) ) ) ) )
