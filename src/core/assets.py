"""
Asset and Icon Management for Keuangan Mandiri.
Loads and caches SVG icons as QIcon, QPixmap, or QSvgWidget across all UI views.
"""
import os
import re
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QImage
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


# =========================================================================
# GRAPHIC OBJECT & RESOURCE MANAGEMENT
# =========================================================================
# 1. _ICON_CACHE: Reuses QIcon instances across identical requests (O(1) memory)
# 2. _RENDERER_CACHE: Reuses parsed QSvgRenderer DOM trees to avoid disk I/O
# 3. _PIXMAP_CACHE & QPixmapCache: Native LRU graphic buffer management
# =========================================================================

from PySide6.QtGui import QPixmapCache

# Configure Qt native graphics cache limit to 32 MB (in KB)
QPixmapCache.setCacheLimit(32768)

_PIXMAP_CACHE: dict[tuple, QPixmap] = {}
_ICON_CACHE: dict[tuple, QIcon] = {}
_RENDERER_CACHE: dict[str, QSvgRenderer] = {}
# Cropped icon content (alpha-trimmed) at probe resolution, per SVG file
_CONTENT_CACHE: dict[str, QImage | None] = {}


# A pixel counts as opaque when its alpha exceeds this threshold (0-255)
_ALPHA_THRESHOLD = 10
_NONZERO_RE = re.compile(rb'[^\x00-' + bytes([_ALPHA_THRESHOLD]) + rb']')

# Probe render height (px): large enough that scaling down to any UI size stays crisp
_PROBE_MIN_DIM = 600


def _get_content_image(renderer: QSvgRenderer, svg_path: str) -> QImage | None:
    """
    Returns the icon's content as an alpha-trimmed QImage at probe resolution.

    The Figma-exported SVGs sit on a huge canvas (1024x576) and QSvgRenderer's
    bounds-based rendering is unreliable with them (some files paint garbage).
    So instead we render the full canvas once — which always works — measure
    the opaque-pixel bounding box, and crop to it. Cropped result is cached
    per file; all UI sizes are produced by scaling this crop (aspect kept).
    """
    if svg_path in _CONTENT_CACHE:
        return _CONTENT_CACHE[svg_path]

    result = None
    vb = renderer.viewBoxF()
    if vb.isValid() and vb.width() > 0 and vb.height() > 0:
        probe_h = _PROBE_MIN_DIM
        probe_w = max(1, round(_PROBE_MIN_DIM * vb.width() / vb.height()))

        probe = QPixmap(probe_w, probe_h)
        probe.fill(Qt.transparent)
        p = QPainter(probe)
        p.setRenderHint(QPainter.Antialiasing)
        renderer.render(p)
        p.end()

        img = probe.toImage()
        alpha = img.convertToFormat(QImage.Format_Alpha8)
        stride = alpha.bytesPerLine()
        data = bytes(alpha.constBits())
        w, h = alpha.width(), alpha.height()

        min_y, max_y, min_x, max_x = -1, -1, w, -1
        for y in range(h):
            row = data[y * stride: y * stride + w]
            m = _NONZERO_RE.search(row)
            if m is not None:
                if min_y < 0:
                    min_y = y
                max_y = y
                if m.start() < min_x:
                    min_x = m.start()
                mr = _NONZERO_RE.search(row[::-1])
                if mr is not None and (w - 1 - mr.start()) > max_x:
                    max_x = w - 1 - mr.start()

        if min_y >= 0 and max_x >= min_x:
            # Small margin so antialiased edges are not clipped
            pad = 2
            min_x = max(0, min_x - pad)
            min_y = max(0, min_y - pad)
            max_x = min(w - 1, max_x + pad)
            max_y = min(h - 1, max_y + pad)
            result = img.copy(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)

    _CONTENT_CACHE[svg_path] = result
    return result


def get_cached_svg_renderer(svg_path: str) -> QSvgRenderer | None:
    """Retrieves or creates a shared QSvgRenderer instance (avoids redundant XML re-parsing)."""
    if not os.path.exists(svg_path):
        return None
    if svg_path not in _RENDERER_CACHE:
        renderer = QSvgRenderer(svg_path)
        if renderer.isValid():
            _RENDERER_CACHE[svg_path] = renderer
        else:
            return None
    return _RENDERER_CACHE[svg_path]


def get_svg_pixmap(svg_path: str, width: int = 24, height: int = 24, color: str | None = None) -> QPixmap:
    """
    Renders and caches an SVG path to a crisp QPixmap of specified dimensions.
    Uses managed Graphic Cache to prevent memory leaks.
    """
    cache_key = (svg_path, width, height, color)
    if cache_key in _PIXMAP_CACHE:
        return _PIXMAP_CACHE[cache_key]

    if not os.path.exists(svg_path):
        pix = QPixmap(width, height)
        pix.fill(Qt.transparent)
        return pix

    pix = QPixmap(width, height)
    pix.fill(Qt.transparent)

    renderer = get_cached_svg_renderer(svg_path)
    if renderer is not None and renderer.isValid():
        content = _get_content_image(renderer, svg_path)
        if content is not None and not content.isNull():
            # Scale the cropped content to fit the target, PRESERVING the
            # aspect ratio, centered — icons are never stretched.
            scaled = QPixmap.fromImage(content.scaled(
                width, height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            ))
            painter = QPainter(pix)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.drawPixmap(
                (width - scaled.width()) // 2,
                (height - scaled.height()) // 2,
                scaled,
            )
            painter.end()
        else:
            painter = QPainter(pix)
            painter.setRenderHint(QPainter.Antialiasing)
            renderer.render(painter)
            painter.end()

    if color:
        tinted = QPixmap(pix.size())
        tinted.fill(Qt.transparent)
        tint_painter = QPainter(tinted)
        tint_painter.setRenderHint(QPainter.Antialiasing)
        tint_painter.setRenderHint(QPainter.SmoothPixmapTransform)
        tint_painter.drawPixmap(0, 0, pix)
        tint_painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        tint_painter.fillRect(tinted.rect(), QColor(color))
        tint_painter.end()
        pix = tinted

    _PIXMAP_CACHE[cache_key] = pix
    return pix


def get_svg_icon(svg_path: str, width: int = 24, height: int = 24, color: str | None = None) -> QIcon:
    """
    Returns a shared QIcon created from an SVG file.
    Caches QIcon instances to avoid redundant GPU/RAM allocations.
    """
    cache_key = (svg_path, width, height, color)
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key]

    pix = get_svg_pixmap(svg_path, width, height, color)
    icon = QIcon(pix)
    _ICON_CACHE[cache_key] = icon
    return icon


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


def clear_graphic_resource_cache():
    """
    Explicitly frees all cached graphic objects, pixmaps, icons, and SVG renderers.
    Useful during memory optimization or session resets.
    """
    _PIXMAP_CACHE.clear()
    _ICON_CACHE.clear()
    _RENDERER_CACHE.clear()
    _CONTENT_CACHE.clear()
    QPixmapCache.clear()

