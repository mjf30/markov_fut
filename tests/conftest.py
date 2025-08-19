import sys, pathlib
src = pathlib.Path(__file__).resolve().parents[1] / 'src'
p = str(src)
if p not in sys.path:
    sys.path.insert(0, p)
