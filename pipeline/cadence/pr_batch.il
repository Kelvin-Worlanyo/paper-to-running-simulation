;; pr_batch.il -- steps run in batch Virtuoso (after pr_config.il and pr_common.il).
;; Output lines start with "PR:"; none carries a PDK name or path.

;; netlist a cell with the design environment; netlists go under the private
;; directory (PR_CFG->private_dir/simulation/<cell>/spectre/schematic/netlist)
procedure( PR_netlist(cell)
  let( ((ok nil))
    envSetVal("asimenv.startup" "projectDir" 'string strcat(PR_CFG->private_dir "/simulation"))
    simulator('spectre)
    design(PR_CFG->target_lib cell "schematic")
    ok = errset(createNetlist(?recreateAll t ?display nil))
    printf("PR: netlist %s %s\n" cell if(ok && car(ok) "written" "FAILED")) ) )

;; one NMOS and one PMOS from the device map at the PDK's default parameters, so
;; the netlist shows the default geometry rule (source/drain areas, resistances)
procedure( PR_probe()
  prog( (lib cv foreign n p)
    lib = PR_CFG->target_lib
    PRb_loadMap()
    unless( PRb_entry("N1") && PRb_entry("P1") printf("PR: probe NOT BUILT (device map incomplete)\n") return(nil) )
    foreign = PRb_reset(lib list("PR_PROBE"))
    when( foreign printf("PR: probe NOT BUILT (a foreign PR_PROBE exists)\n") return(nil) )
    cv = PRb_newSchematic(lib "PR_PROBE")
    foreach( spec list(list("N1" "PROBE_N" 0.0:0.0 "n") list("P1" "PROBE_P" 3.0:0.0 "p"))
      let( ((e PRb_entry(car(spec))) (inst nil))
        inst = dbCreateInst(cv dbOpenCellViewByType(e->lib e->cell e->view "" "r") cadr(spec) caddr(spec) "R0")
        foreach( role '("Drain" "Gate" "Source" "Body")
          PRb_label(cv inst PRb_role(e->pins role) strcat(lowerCase(substring(role 1 1)) cadddr(spec))
                    if(member(role '("Gate" "Body")) 'h 'v)) ) ) )
    let( ((chk schCheck(cv)))
      when( car(chk) > 0 printf("PR: probe cell has %d check errors\n" car(chk)) ) )
    dbSave(cv)
    printf("PR: probe cell drawn\n")
    PR_netlist("PR_PROBE")
    return(t) ) )
