"""Run sizing_local.py with the Spectre back end, on the PDK machine.

    python3 pipeline/cadence/run_sizing.py inner|final|dry RUN [K]

(A tiny wrapper: some site python3 wrappers mangle quoted arguments, so the
back-end switch is set here rather than on the command line.)
"""
import os
import runpy
import sys

os.environ["PR_BACKEND"] = "spectre"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = ["sizing_local.py"] + sys.argv[1:]
runpy.run_path(os.path.join(HERE, "..", "sizing_local.py"), run_name="__main__")
