"""Render sample icons with the project's assets.py to inspect distortion."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QPainter, QColor

app = QApplication([])

from src.core.assets import get_svg_pixmap, _get_content_image, AppIcons
from src.core.assets import get_cached_svg_renderer

SAMPLES = [
    ("dashboard_menu", AppIcons.DASHBOARD_MENU, 22, 22),
    ("saldo", AppIcons.DASHBOARD_SALDO, 24, 24),
    ("pemasukan", AppIcons.DASHBOARD_PEMASUKAN, 24, 24),
    ("kalender", AppIcons.DASHBOARD_KALENDER, 24, 24),
    ("tx_tanggal", AppIcons.TX_TANGGAL, 20, 20),
    ("target_menu", AppIcons.TARGET_MENU, 22, 22),
]

out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon_debug")
os.makedirs(out_dir, exist_ok=True)

# Grid sheet on dark background so white/green icons are visible
CELL = 80
sheet = QPixmap(CELL * len(SAMPLES), CELL + 30)
sheet.fill(QColor("#3a4a38"))
p = QPainter(sheet)

for i, (name, path, w, h) in enumerate(SAMPLES):
    print(f"--- {name}: {os.path.basename(path)}")
    print(f"    content size: {_get_content_image(r, path).size() if (r := get_cached_svg_renderer(path)) else None}")
    r = get_cached_svg_renderer(path)
    print(f"    viewBox: {r.viewBoxF() if r else None}  defaultSize: {r.defaultSize() if r else None}")
    pix = get_svg_pixmap(path, w, h, color="#FFFFFF")
    # report where the opaque pixels actually are inside the pixmap
    img = pix.toImage()
    minx, miny, maxx, maxy = w, h, -1, -1
    for y in range(h):
        for x in range(w):
            if img.pixelColor(x, y).alpha() > 10:
                minx, miny = min(minx, x), min(miny, y)
                maxx, maxy = max(maxx, x), max(maxy, y)
    print(f"    opaque bbox in {w}x{h} pixmap: ({minx},{miny})-({maxx},{maxy})  -> drawn size {maxx-minx+1}x{maxy-miny+1}")
    x0 = i * CELL + (CELL - w) // 2
    y0 = (CELL - h) // 2
    p.drawPixmap(x0, y0, pix)

p.end()
sheet.save(os.path.join(out_dir, "sheet.png"))
print("saved:", os.path.join(out_dir, "sheet.png"))
