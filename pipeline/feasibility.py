"""Is a published set of specifications jointly reachable at all?

A sizing run that meets three of a paper's four numbers and misses the fourth
leaves a question the run itself cannot answer: was that the method's limit, or
the specification's? For a Miller-compensated two-stage amplifier the phase
margin, the unity-gain frequency and the power budget together force a
transconductance per unit current on the output stage, and that quantity has a
physical ceiling in weak inversion, 1/(n kT/q) (Silveira et al., 1996 -- the
same bound the telescopic GBW check uses). Comparing the two is a one-sided
test: it can show a specification is out of reach, never that it is reachable.

Every approximation here is deliberately generous to the paper:
  * the entire supply current is allowed to sit in the output stage, so the
    first stage and the bias branch are free
  * the output node carries the stated load only, with no device capacitance,
    which lowers the required transconductance
  * the non-dominant pole is placed by gm2/C_out, the textbook best case
so the number returned is a LOWER bound on what the specification demands.

    feasibility.py GAIN_DB GBW_HZ PM_DEG POWER_W CL_F VDD_V
"""
import json
import math
import sys

N_SUB = 1.3                      # subthreshold slope factor, typical bulk CMOS
UT = 1.380649e-23 * 300.0 / 1.602176634e-19       # kT/q at 300 K


def bound(gbw_Hz, pm_deg, power_W, cl_F, vdd_V, n=N_SUB, ut=UT):
    if not (0 < pm_deg < 90):
        raise ValueError("phase margin must be between 0 and 90 degrees")
    wu = 2 * math.pi * gbw_Hz
    # two-pole loop: PM = 90 - atan(wu / w2)
    # PM = 90 - atan(wu / w2)  =>  wu / w2 = tan(90 - PM)
    ratio = 1.0 / math.tan(math.radians(90.0 - pm_deg))  # w2 / wu
    w2 = ratio * wu
    gm2 = w2 * cl_F                                      # best case: load only
    i_total = power_W / vdd_V
    need = gm2 / i_total                                 # all the current to stage 2
    ceiling = 1.0 / (n * ut)
    return dict(gbw_Hz=gbw_Hz, pm_deg=pm_deg, power_W=power_W, cl_F=cl_F, vdd_V=vdd_V,
                pole_ratio=ratio, w2_rad_s=w2, gm2_required_S=gm2,
                i_total_A=i_total, gm_over_id_required=need,
                gm_over_id_ceiling=ceiling, fraction_of_ceiling=need / ceiling,
                feasible_on_this_test=need < ceiling, n=n, ut_V=ut)


if __name__ == "__main__":
    a = [float(x) for x in sys.argv[1:7]]
    r = bound(a[1], a[2], a[3], a[4], a[5])
    print(json.dumps(r, indent=1))
    print(f"\nrequired gm/ID on the output stage : {r['gm_over_id_required']:.2f} 1/V")
    print(f"weak-inversion ceiling             : {r['gm_over_id_ceiling']:.2f} 1/V")
    print(f"fraction of the ceiling            : {100 * r['fraction_of_ceiling']:.0f}%")
    print("verdict: " + ("not excluded by this bound, but it leaves "
                         f"{100 * (1 - r['fraction_of_ceiling']):.0f}% of the physical range"
                         if r["feasible_on_this_test"] else
                         "EXCLUDED: the specification needs more gm/ID than a MOSFET can give"))
