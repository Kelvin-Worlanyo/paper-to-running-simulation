"""Schema check for a circuit record: `validate.py RECORD.json` prints OK or the problems."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import circuit  # noqa: E402

if __name__ == "__main__":
    c = circuit.load(sys.argv[1])
    bad = circuit.schema_problems(c)
    print("OK" if not bad else "\n".join(bad), f"({len(c.get('ckt_netlist', []))} devices)")
