;; devmap_extract.il -- build the private device map from the designer's reference
;; schematic (PR_CFG->ref_lib / ref_cell), without reporting any PDK name.
;; Runs in batch after pr_config.il (PR_CFG).
;;
;; Reads (never writes) the reference schematic, finds the instances whose master
;; comes from a device library (any library that is not basic/analogLib or one of
;; the designer's own libraries under PR_CFG->work_dir -- its name is never
;; printed), classifies each master as NMOS or PMOS by what its source/drain/body
;; connect to (a supply net -> PMOS, a ground net -> NMOS), and records, per
;; master: library, cell, view, pin names mapped to Drain/Gate/Source/Body, and
;; the CDF parameter names for width, length, multiplier and fingers.
;;
;; The map is written to PR_CFG->private_dir/devmap.il. The only lines printed are
;; "DEVMAP:" summaries with neutral aliases (N1, P1) and found / not-found flags.

PR_SRC_LIB  = PR_CFG->ref_lib
PR_SRC_CELL = PR_CFG->ref_cell
PR_TECH     = PR_CFG->technology
PR_GENERIC  = '("basic" "analogLib" "cdsDefTechLib" "ahdlLib" "sheets")
PR_OWN      = setof(l ddGetLibList() pcreMatchp(strcat("^" PR_CFG->work_dir "/") l~>readPath))~>name
procedure( PR_isDeviceLib(n) !member(n PR_GENERIC) && !member(n PR_OWN) )
PR_OUT      = strcat(PR_CFG->private_dir "/devmap.il")

procedure( PR_norm(n)   ; lower case, global-net "!" removed
  let( ((s lowerCase(n)))
    if( strlen(s) > 1 && substring(s strlen(s) 1) == "!" then substring(s 1 strlen(s) - 1) else s ) ) )
PR_srcSupply = nil
procedure( PR_isSupply(n) pcreMatchp("^(vdd|vcc|avdd|dvdd|vdda|vdd[0-9_a-z]*)$" PR_norm(n)) || member(n PR_srcSupply) )
procedure( PR_isGround(n) pcreMatchp("^(gnd|vss|gnda|avss|dvss|0|gnd[0-9_a-z]*|vss[0-9_a-z]*)$" PR_norm(n)) )

;; pin name -> role, from the usual naming (D/G/S/B, drain/gate/source/bulk)
procedure( PR_pinRole(p)
  let( ((n lowerCase(p)))
    cond(
      ( pcreMatchp("^(d|drain|dr)$" n) "Drain" )
      ( pcreMatchp("^(g|gate)$" n) "Gate" )
      ( pcreMatchp("^(s|source|src)$" n) "Source" )
      ( pcreMatchp("^(b|bulk|body|sub|substrate|well)$" n) "Body" )
      ( t nil ) ) ) )

;; CDF parameter name -> size role
procedure( PR_paramRole(p)
  let( ((n lowerCase(p)))
    cond(
      ( pcreMatchp("^(w|width|wf|fw|wtot|totalw)$" n) "width" )
      ( pcreMatchp("^(l|length|lr)$" n) "length" )
      ( pcreMatchp("^(m|mult|multi|multiplier|mf)$" n) "mult" )
      ( pcreMatchp("^(nf|fingers|finger|nfinger|nfing)$" n) "fingers" )
      ( t nil ) ) ) )

let( (lib masters cv kind pins params cdf found line summary nN nP nAmb nOther nInst nSch out)
  masters = makeTable("masters" nil)
  nInst = 0  nSch = 0
  lib = ddGetObj(PR_SRC_LIB)
  unless( lib
    printf("DEVMAP: ERROR source library not found\n")
    exit() )
  foreach( cell setof(c lib~>cells c~>name == PR_SRC_CELL)
    when( member("schematic" cell~>views~>name)
      cv = dbOpenCellViewByType(PR_SRC_LIB cell~>name "schematic" "" "r")
      when( cv
        nSch = nSch + 1
        ;; a net on the + side of a DC source whose - side is ground is a supply
        PR_srcSupply = nil
        foreach( src setof(i cv~>instances i~>libName == "analogLib" && member(i~>cellName '("vdc" "vsource")))
          let( ((plus nil) (minus nil))
            foreach( it src~>instTerms
              when( it~>net
                when( upperCase(it~>name) == "PLUS" plus = it~>net~>name )
                when( upperCase(it~>name) == "MINUS" minus = it~>net~>name ) ) )
            when( plus && minus && PR_isGround(minus) && !PR_isGround(plus)
              PR_srcSupply = cons(plus PR_srcSupply) ) ) )
        foreach( inst cv~>instances
          when( PR_isDeviceLib(inst~>libName)
            nInst = nInst + 1
            let( ((key strcat(inst~>libName "/" inst~>cellName "/" inst~>viewName))
                  (vdd nil) (gnd nil) (e nil))
              ;; classify by source/drain/body only: a gate can sit on any driven net
              foreach( it inst~>instTerms
                when( it~>net && PR_pinRole(it~>name) != "Gate"
                  when( PR_isSupply(it~>net~>name) vdd = t )
                  when( PR_isGround(it~>net~>name) gnd = t ) ) )
              e = masters[key]
              unless( e
                e = list(nil 'lib inst~>libName 'cell inst~>cellName 'view inst~>viewName
                         'vdd nil 'gnd nil 'nterm length(inst~>instTerms) 'inst inst~>name
                         'cv list(PR_SRC_LIB cell~>name) )
                masters[key] = e )
              when( vdd putprop(e t 'vdd) )
              when( gnd putprop(e t 'gnd) ) ) ) )
        dbClose(cv) ) ) )

  ;; classify each master, collect pin and parameter roles
  out = nil  nN = 0  nP = 0  nAmb = 0  nOther = 0
  foreach( key masters
    let( ((e masters[key]) (alias nil) (pinmap nil) (parmap nil) (npins 0) (roles nil))
      kind = cond(
        ( e->nterm < 3 nil )
        ( e->vdd && !e->gnd "PMOS" )
        ( e->gnd && !e->vdd "NMOS" )
        ( t "AMBIGUOUS" ) )
      cond(
        ( kind == "NMOS" nN = nN + 1  alias = sprintf(nil "N%d" nN) )
        ( kind == "PMOS" nP = nP + 1  alias = sprintf(nil "P%d" nP) )
        ( kind == "AMBIGUOUS" nAmb = nAmb + 1 )
        ( t nOther = nOther + 1 ) )
      when( alias
        ;; pin roles from the master's terminals
        let( ((m dbOpenCellViewByType(e->lib e->cell e->view "" "r")))
          when( m
            foreach( term m~>terminals
              when( PR_pinRole(term~>name)
                pinmap = cons(list(PR_pinRole(term~>name) term~>name) pinmap) ) )
            dbClose(m) ) )
        ;; size parameters from the master's CDF
        cdf = cdfGetCellCDF(ddGetObj(e->lib e->cell))
        when( cdf
          foreach( p cdf~>parameters
            when( PR_paramRole(p~>name)
              parmap = cons(list(PR_paramRole(p~>name) p~>name) parmap) ) ) )
        roles = mapcar('car parmap)
        out = cons(list(nil 'alias alias 'kind kind 'lib e->lib 'cell e->cell 'view e->view
                        'pins pinmap 'params parmap 'source e->cv) out)
        printf("DEVMAP: %s (%s) found: pins resolved %d/4, width=%s length=%s mult=%s fingers=%s\n"
               alias kind length(pinmap)
               if(member("width" roles) "yes" "no") if(member("length" roles) "yes" "no")
               if(member("mult" roles) "yes" "no") if(member("fingers" roles) "yes" "no")) ) ) )

  printf("DEVMAP: schematics scanned %d, PDK instances %d, masters %d (NMOS %d, PMOS %d, ambiguous %d, other %d)\n"
         nSch nInst length(masters) nN nP nAmb nOther)
  ;; is the device library on the technology the target library is attached to?
  let( ((dlibs nil))
    foreach( key masters dlibs = cons(masters[key]->lib dlibs) )
    foreach( dl let( ((u nil)) foreach( x dlibs unless( member(x u) u = cons(x u) ) ) u )
      let( ((o ddGetObj(dl)) (tl nil))
        tl = o && (techGetTechLibName(o) || dl)
        printf("DEVMAP: device library uses the target technology: %s\n"
               if(tl == PR_TECH || dl == PR_TECH "yes" "no")) ) ) )
  when( out
    let( ((port outfile(PR_OUT "w")))
      if( port then
        fprintf(port ";; private device map -- do not share\nPR_DEVMAP = '%L\n" out)
        close(port)
        printf("DEVMAP: written %d entries to the private directory\n" length(out))
      else
        printf("DEVMAP: ERROR could not write output file\n") ) ) )
  unless( out printf("DEVMAP: nothing written (no NMOS/PMOS found)\n") )
)
exit()
