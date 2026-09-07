"""Inject realistic 'regenerated atlas' drift and see whether the seam audit catches it.

Each scenario copies the repo, perturbs the sprite atlases the way a re-generated
image would differ, and re-runs the audit.
"""
import shutil, subprocess, sys, json, tempfile, atexit
from pathlib import Path
import numpy as np
from PIL import Image

SRC = Path(__file__).resolve().parent.parent
WORK = Path(tempfile.mkdtemp(prefix="seam-drift-"))
UPPER = "godot/assets/rendered/upper"

atexit.register(lambda: shutil.rmtree(WORK, ignore_errors=True))

def fresh():
    if WORK.exists(): shutil.rmtree(WORK)
    shutil.copytree(SRC, WORK, symlinks=True)

def upper_sheets(root):
    j = json.loads((root/UPPER/"sprites.json").read_text())["models"]
    out = set()
    for m in j.values():
        for c in m["clips"].values():
            out.add(root/UPPER/c["sheet"])
    return sorted(out)

def shift_down(px):
    """Model returns the torso a few px lower in the cell (baseline drift)."""
    for p in upper_sheets(WORK):
        a = np.array(Image.open(p).convert("RGBA"))
        b = np.zeros_like(a); b[px:, :] = a[:-px, :]
        Image.fromarray(b).save(p)

def scale_down(pct):
    """Model returns a slightly smaller character (proportion drift)."""
    for p in upper_sheets(WORK):
        im = Image.open(p).convert("RGBA")
        w, h = im.size
        nw, nh = int(w*(1-pct/100)), int(h*(1-pct/100))
        small = im.resize((nw, nh), Image.NEAREST)
        canvas = Image.new("RGBA", (w, h), (0,0,0,0))
        canvas.paste(small, ((w-nw)//2, h-nh))   # keep feet on the floor
        canvas.save(p)

def erode_alpha(px):
    """Cleaner/anti-alias pass shaves the sprite edge."""
    from PIL import ImageFilter
    for p in upper_sheets(WORK):
        a = np.array(Image.open(p).convert("RGBA"))
        al = Image.fromarray(a[:,:,3])
        for _ in range(px):
            al = al.filter(ImageFilter.MinFilter(3))
        a[:,:,3] = np.array(al)
        Image.fromarray(a).save(p)

def audit():
    r = subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "seam_audit.py"), str(WORK)],
                       capture_output=True, text=True)
    tail = [l for l in r.stdout.strip().splitlines() if "SEAM PASS" in l or "SEAM FAIL" in l or "failures" in l]
    return r.returncode, tail

SCEN = [
    ("baseline (untouched)",            lambda: None),
    ("torso 3px lower in cell",         lambda: shift_down(3)),
    ("torso 6px lower in cell",         lambda: shift_down(6)),
    ("character 4% smaller",            lambda: scale_down(4)),
    ("character 8% smaller",            lambda: scale_down(8)),
    ("alpha edge eroded 2px",           lambda: erode_alpha(2)),
]

print(f"{'scenario':<32} {'verdict':<7} detail")
print("-"*78)
for name, fn in SCEN:
    fresh()
    if fn: fn()
    code, tail = audit()
    verdict = "PASS" if code == 0 else "FAIL"
    detail = "; ".join(t for t in tail if "failures" in t or "FAIL" in t)
    print(f"{name:<32} {verdict:<7} {detail}")
