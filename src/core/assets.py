"""
Asset and Icon Management for Keuangan Mandiri.
Loads and caches SVG icons as QIcon, QPixmap, or QSvgWidget across all UI views.
"""
import os
import re
from PySide6.QtCore import Qt, QSize, QRectF
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QLabel

# Resolve base project asset directory
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_CURRENT_DIR))
ASSETS_DIR = os.path.join(_PROJECT_ROOT, "assets")

class AppIcons:
    # 1. DASHBOARD
    DASHBOARD_MENU = os.path.join(ASSETS_DIR, "1. DASHBOARD", "Menu Dashboard Icon (Dashboard Menu).svg")
    DASHBOARD_SALDO = os.path.join(ASSETS_DIR, "1. DASHBOARD", "Saldo Icon (Dashboard Menu).svg")
    DASHBOARD_PEMASUKAN = os.path.join(ASSETS_DIR, "1. DASHBOARD", "Total Pemasukan Icon (Dashboard Menu).svg")
    DASHBOARD_PENGELUARAN = os.path.join(ASSETS_DIR, "1. DASHBOARD", "Total Pengeluaran Icon (Dashboard Menu).svg")
    DASHBOARD_TOTAL_TARGET = os.path.join(ASSETS_DIR, "1. DASHBOARD", "Total Target Icon (Dashboard Menu).svg")
    DASHBOARD_TARGET_CARD = os.path.join(ASSETS_DIR, "1. DASHBOARD", "Target Keuangan Icon (Dashboard Menu).svg")
    DASHBOARD_RECENT_TX = os.path.join(ASSETS_DIR, "1. DASHBOARD", "Riwayat Transaksi Terbaru Icon (Dashboard Menu).svg")
    DASHBOARD_KALENDER = os.path.join(ASSETS_DIR, "1. DASHBOARD", "Kalender Icon (Dashboard Menu).svg")

    # 2. INPUT TRANSAKSI
    INPUT_TRANSAKSI_MENU = os.path.join(ASSETS_DIR, "2. INPUT TRANSAKSI", "Menu Input Transakasi Icon (Input Transaksi Menu).svg")
    TX_PEMASUKAN = os.path.join(ASSETS_DIR, "2. INPUT TRANSAKSI", "Jenis Transaksi Pemasukan Icon (Input Transaksi Menu).svg")
    TX_PENGELUARAN = os.path.join(ASSETS_DIR, "2. INPUT TRANSAKSI", "Jenis Transaksi Pengeluaran Icon (Input Transaksi Menu).svg")
    TX_TANGGAL = os.path.join(ASSETS_DIR, "2. INPUT TRANSAKSI", "Tanggal Icon (Input Transaksi Menu).svg")

    # 3. KATEGORI
    KATEGORI_MENU = os.path.join(ASSETS_DIR, "3. KATEGORI", "Menu Kategori Icon (Kategori Menu).svg")
    CAT_EDIT = os.path.join(ASSETS_DIR, "3. KATEGORI", "Edit Icon (Kategori Menu).svg")
    CAT_DELETE = os.path.join(ASSETS_DIR, "3. KATEGORI", "Hapus Icon (Kategori Menu).svg")

    # 4. RIWAYAT
    RIWAYAT_MENU = os.path.join(ASSETS_DIR, "4. RIWAYAT", "Menu Riwayat Icon (Riwayat Menu).svg")
    HIST_FILTER = os.path.join(ASSETS_DIR, "4. RIWAYAT", "Filter Icon (Riwayat Menu).svg")
    HIST_PEMASUKAN = os.path.join(ASSETS_DIR, "4. RIWAYAT", "Total Pemasukan Icon (Riwayat Menu).svg")
    HIST_PENGELUARAN = os.path.join(ASSETS_DIR, "4. RIWAYAT", "Total Pengeluaran Icon (Riwayat Menu).svg")
    HIST_SALDO_BERSIH = os.path.join(ASSETS_DIR, "4. RIWAYAT", "Saldo Bersih Icon (Riwayat Menu).svg")
    HIST_JUMLAH_TX = os.path.join(ASSETS_DIR, "4. RIWAYAT", "Jumlah Transaksi Icon (Riwayat Menu).svg")
    HIST_TANGGAL = os.path.join(ASSETS_DIR, "4. RIWAYAT", "Tanggal Icon (Riwayat Menu).svg")

    # 5. TARGET KEUANGAN
    TARGET_MENU = os.path.join(ASSETS_DIR, "5. TARGET KEUANGAN", "Menu Target Keuangan Icon_ Target Icon (Target Keuangan Menu).svg")
    TARGET_TOTAL = os.path.join(ASSETS_DIR, "5. TARGET KEUANGAN", "Total Target  Keuangan Icon (Target Keuangan Menu).svg")
    TARGET_TERKUMPUL = os.path.join(ASSETS_DIR, "5. TARGET KEUANGAN", "Terkumpul Icon (Target Keuangan Menu).svg")
    TARGET_PROGRESS = os.path.join(ASSETS_DIR, "5. TARGET KEUANGAN", "Seluruh Progress Icon (Target Keuangan Menu).svg")
    TARGET_TIPS = os.path.join(ASSETS_DIR, "5. TARGET KEUANGAN", "Tips Menabung Icon (Target Keuangan Menu).svg")
    TARGET_ISI = os.path.join(ASSETS_DIR, "5. TARGET KEUANGAN", "Isi Target Icon (Isi Target Keuangan Menu).svg")
    TARGET_SALDO_TERSEDIA = os.path.join(ASSETS_DIR, "5. TARGET KEUANGAN", "Saldo Tersedia Icon (Isi Target Keuangan Menu).svg")
    TARGET_NOMINAL = os.path.join(ASSETS_DIR, "5. TARGET KEUANGAN", "Nominal yg ... Icon (Isi Target Keuangan Menu).svg")
    TARGET_PRIORITY_TINGGI = os.path.join(ASSETS_DIR, "5. TARGET KEUANGAN", "Prioritas Target Tinggi (Tambah Target Keuangan Menu).svg")
    TARGET_PRIORITY_SEDANG = os.path.join(ASSETS_DIR, "5. TARGET KEUANGAN", "Prioritas Target Sedang (Tambah Target Keuangan Menu).svg")
    TARGET_PRIORITY_RENDAH = os.path.join(ASSETS_DIR, "5. TARGET KEUANGAN", "Prioritas Target Rendah (Tambah Target Keuangan Menu).svg")
    TARGET_TANGGAL = os.path.join(ASSETS_DIR, "5. TARGET KEUANGAN", "Tanggal Icon (Tambah Target Keuangan Menu).svg")
    TARGET_AKTIVITAS = os.path.join(ASSETS_DIR, "5. TARGET KEUANGAN", "Aktivitas Terbaru Icon (Target Keuangan Menu).svg")


_PIXMAP_CACHE = {}
_BOUNDS_CACHE = {}

# These SVG files from Figma/Inkscape export have a large canvas (1024x576)
# with the icon element positioned away from the origin. We detect the icon
# bounding box from the first <clipPath> rect/path so we can crop precisely.
_TRANSFORM_RE = re.compile(
    r'transform="matrix\(1,\s*0,\s*0,\s*1,\s*([\d.]+),\s*([\d.]+)\)"'
)
_RECT_CLIP_RE = re.compile(
    r'<clipPath[^>]*>\s*<rect[^/]*width="(\d+)"[^/]*height="(\d+)"',
    re.DOTALL
)
_RECT_CLIP_RE2 = re.compile(
    r'<clipPath[^>]*>\s*<rect[^/]*height="(\d+)"[^/]*width="(\d+)"',
    re.DOTALL
)
_SIMPLE_RECT_RE = re.compile(
    r'M\s+([\d.]+)\s+([\d.]+)\s+L\s+([\d.]+)\s+([\d.]+)\s+L\s+([\d.]+)\s+([\d.]+)\s+L\s+([\d.]+)\s+([\d.]+)'
)


def _get_icon_bounds(svg_path: str) -> QRectF | None:
    """
    Detects the actual icon bounding box for Figma-exported SVGs.
    These SVGs have a large canvas (1024x576) with the icon positioned via a
    group transform. We extract the transform offset (tx, ty) and the largest
    clipPath <rect> size to compute the global icon bounds: (tx, ty, w, h).
    Returns None if the SVG appears to already fit within a normal viewBox.
    """
    if svg_path in _BOUNDS_CACHE:
        return _BOUNDS_CACHE[svg_path]

    result = None
    try:
        with open(svg_path, encoding="utf-8") as f:
            content = f.read()

        # Check if viewBox is small — no crop needed
        vb_m = re.search(r'viewBox="([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)"', content)
        if vb_m:
            vx, vy, vw, vh = (float(v) for v in vb_m.groups())
            if vw <= 600 and vh <= 600:
                _BOUNDS_CACHE[svg_path] = None
                return None

        # Strategy 1: Find first group-level transform (the icon offset) + largest rect clipPath
        # The Figma pattern is: <g transform="matrix(1, 0, 0, 1, tx, ty)"> ... icon at local (0,0)
        tm = _TRANSFORM_RE.search(content)
        if tm:
            tx, ty = float(tm.group(1)), float(tm.group(2))
            # Now find the largest <rect> clipPath to get icon dimensions
            best_w, best_h = 0, 0
            for rm in _RECT_CLIP_RE.finditer(content):
                w, h = int(rm.group(1)), int(rm.group(2))
                if w * h > best_w * best_h:
                    best_w, best_h = w, h
            for rm in _RECT_CLIP_RE2.finditer(content):
                w, h = int(rm.group(2)), int(rm.group(1))
                if w * h > best_w * best_h:
                    best_w, best_h = w, h

            if best_w > 100 and best_h > 100:
                result = QRectF(tx, ty, best_w, best_h)
                _BOUNDS_CACHE[svg_path] = result
                return result

        # Strategy 2: Find the largest rect-shaped path in clipPaths (global coords)
        # Pattern: M x y L x2 y L x2 y2 L x y2
        best_bounds = None
        best_area = 0.0
        for m in _SIMPLE_RECT_RE.finditer(content[:6000]):
            pts = [float(v) for v in m.groups()]
            xs = [pts[0], pts[2], pts[4], pts[6]]
            ys = [pts[1], pts[3], pts[5], pts[7]]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            w = max_x - min_x
            h = max_y - min_y
            area = w * h
            if w > 200 and h > 200 and area > best_area:
                best_area = area
                best_bounds = QRectF(min_x, min_y, w, h)

        result = best_bounds

    except Exception:
        pass

    _BOUNDS_CACHE[svg_path] = result
    return result


def get_svg_pixmap(svg_path: str, width: int = 24, height: int = 24) -> QPixmap:
    """
    Renders and caches an SVG path to a crisp QPixmap of specified dimensions.
    Automatically crops large-canvas SVGs (e.g. Figma exports at 1366x768)
    to render only the icon content area.
    """
    cache_key = (svg_path, width, height)
    if cache_key in _PIXMAP_CACHE:
        return _PIXMAP_CACHE[cache_key]

    if not os.path.exists(svg_path):
        pix = QPixmap(width, height)
        pix.fill(Qt.transparent)
        return pix

    pix = QPixmap(width, height)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)

    renderer = QSvgRenderer(svg_path)
    if renderer.isValid():
        bounds = _get_icon_bounds(svg_path)
        if bounds is not None:
            # Render only the icon region (crop from big canvas)
            # We compute the scale and offset needed to map bounds -> (0,0,w,h)
            vb = renderer.viewBoxF()
            # Scale factor from SVG coordinates to pixmap pixels
            scale_x = width / bounds.width()
            scale_y = height / bounds.height()
            # Translate so icon top-left goes to (0,0) then scale to target size
            painter.translate(-bounds.x() * scale_x, -bounds.y() * scale_y)
            painter.scale(scale_x, scale_y)
            renderer.render(painter, vb)
        else:
            renderer.render(painter)

    painter.end()

    _PIXMAP_CACHE[cache_key] = pix
    return pix


def get_svg_icon(svg_path: str, width: int = 24, height: int = 24) -> QIcon:
    """Returns a QIcon created from an SVG file."""
    pix = get_svg_pixmap(svg_path, width, height)
    return QIcon(pix)


def create_svg_label(svg_path: str, width: int = 24, height: int = 24, parent=None) -> QLabel:
    """Returns a QLabel displaying the rendered SVG pixmap."""
    lbl = QLabel(parent)
    lbl.setFixedSize(width, height)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet("background: transparent; border: none;")
    pix = get_svg_pixmap(svg_path, width, height)
    lbl.setPixmap(pix)
    lbl.setScaledContents(True)
    return lbl
