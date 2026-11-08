"""
Settings Dialog.

Central place for local storage preferences: data folder, history page size,
chart period, cache, attachment limits, encryption, and encrypted backups.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFrame, QHBoxLayout, QLabel,
    QMessageBox, QPushButton, QScrollArea, QSpinBox, QVBoxLayout, QWidget,
    QSizePolicy,
)

from src.core.constants import AppColors
from src.core.event_bus import event_bus


class SettingsDialog(QDialog):
    """Modal dialog used by the sidebar gear button."""

    preferences_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._db = None
        self._config = None
        self._loading = True
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(690, 640)
        self._setup_ui()
        self._load_values()
        self._loading = False

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        card = QFrame()
        card.setObjectName("settingsCard")
        card.setStyleSheet(f"""
            QFrame#settingsCard {{
                background-color: #FFFFFF;
                border: 1px solid {AppColors.BORDER_CARD};
                border-radius: 16px;
            }}
            QFrame#settingsCard QLabel {{
                background: transparent;
                border: none;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel("PENGATURAN")
        title.setStyleSheet(f"font-size: 17px; font-weight: 800; color: {AppColors.TEXT_PRIMARY};")
        subtitle = QLabel("Penyimpanan lokal, cache, keamanan, dan cadangan data")
        subtitle.setStyleSheet(f"font-size: 11px; color: {AppColors.TEXT_SECONDARY};")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header.addLayout(title_col)
        header.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #A0AEC0;
                font-size: 14px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                color: #2D3748;
            }
        """)
        close_btn.clicked.connect(self.reject)
        header.addWidget(close_btn)
        card_layout.addLayout(header)

        # Scrollable body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollArea > QWidget > QWidget { background: transparent; }
        """)
        body = QWidget()
        body.setObjectName("settingsScrollBody")
        body.setStyleSheet("QWidget#settingsScrollBody { background: transparent; }")
        self.body_layout = QVBoxLayout(body)
        self.body_layout.setContentsMargins(0, 2, 4, 2)
        self.body_layout.setSpacing(10)

        self._build_storage_section()
        self._build_preferences_section()
        self._build_cache_section()
        self._build_security_section()
        self._build_backup_section()
        self.body_layout.addStretch()

        scroll.setWidget(body)
        card_layout.addWidget(scroll, 1)

        # Footer
        footer = QHBoxLayout()
        footer.addStretch()

        cancel_btn = self._secondary_button("Tutup")
        cancel_btn.clicked.connect(self.reject)
        footer.addWidget(cancel_btn)

        save_btn = self._primary_button("Simpan Pengaturan")
        save_btn.clicked.connect(self._save_preferences)
        footer.addWidget(save_btn)
        card_layout.addLayout(footer)

        main_layout.addWidget(card)

    def _section(self, title: str, subtitle: str = "") -> QVBoxLayout:
        frame = QFrame()
        frame.setObjectName("settingsSection")
        frame.setStyleSheet("""
            QFrame#settingsSection {
                background-color: #FBFAF7;
                border: 1px solid #EAE6DF;
                border-radius: 10px;
            }
            QFrame#settingsSection QLabel {
                background: transparent;
                border: none;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(7)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 12px; font-weight: 800; color: {AppColors.TEXT_PRIMARY};")
        layout.addWidget(title_lbl)
        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setWordWrap(True)
            sub_lbl.setStyleSheet(f"font-size: 10px; color: {AppColors.TEXT_SECONDARY};")
            layout.addWidget(sub_lbl)

        self.body_layout.addWidget(frame)
        return layout

    @staticmethod
    def _primary_button(text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(34)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AppColors.PRIMARY_BUTTON};
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                font-size: 11px;
                font-weight: 700;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background-color: {AppColors.PRIMARY_BUTTON_HOVER};
            }}
        """)
        return btn

    @staticmethod
    def _secondary_button(text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(34)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #FAF8F5;
                color: #4A5568;
                border: 1px solid #CBD5E0;
                border-radius: 8px;
                font-size: 11px;
                font-weight: 700;
                padding: 0 14px;
            }
            QPushButton:hover {
                background-color: #EDF2F7;
                border-color: #A0AEC0;
            }
        """)
        return btn

    # ------------------------------------------------------------------
    # Sections
    # ------------------------------------------------------------------
    def _build_storage_section(self):
        layout = self._section(
            "LOKASI PENYIMPANAN",
            "Semua data aplikasi disimpan di folder data proyek agar mudah dibawa dan dicadangkan.",
        )
        self.storage_lbl = QLabel("")
        self.storage_lbl.setMinimumWidth(0)
        self.storage_lbl.setWordWrap(True)
        self.storage_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.storage_lbl.setStyleSheet(f"font-size: 10px; color: {AppColors.TEXT_SECONDARY};")
        layout.addWidget(self.storage_lbl)

        row = QHBoxLayout()
        open_data = self._secondary_button("Buka Folder Data")
        open_data.clicked.connect(self._open_data_folder)
        row.addWidget(open_data)

        open_backups = self._secondary_button("Buka Folder Backup")
        open_backups.clicked.connect(self._open_backup_folder)
        row.addWidget(open_backups)
        row.addStretch()
        layout.addLayout(row)

    def _build_preferences_section(self):
        layout = self._section(
            "TAMPILAN & RIWAYAT",
            "Atur jumlah baris riwayat per halaman dan periode grafik dashboard.",
        )
        row = QHBoxLayout()
        row.setSpacing(12)

        page_col = QVBoxLayout()
        page_col.setSpacing(3)
        page_col.addWidget(QLabel("Baris per halaman", styleSheet="font-size: 10px; font-weight: 600; color: #4A5568;"))
        self.page_size_combo = QComboBox()
        for size in (25, 50, 100, 200):
            self.page_size_combo.addItem(f"{size} transaksi", size)
        self.page_size_combo.setFixedHeight(32)
        page_col.addWidget(self.page_size_combo)
        row.addLayout(page_col, 1)

        period_col = QVBoxLayout()
        period_col.setSpacing(3)
        period_col.addWidget(QLabel("Periode grafik", styleSheet="font-size: 10px; font-weight: 600; color: #4A5568;"))
        self.chart_period_combo = QComboBox()
        self.chart_period_combo.addItems(["Minggu ini", "Bulan ini", "Tahun ini"])
        self.chart_period_combo.setFixedHeight(32)
        period_col.addWidget(self.chart_period_combo)
        row.addLayout(period_col, 1)

        layout.addLayout(row)

        attach_row = QHBoxLayout()
        attach_row.setSpacing(10)
        attach_lbl = QLabel("Ukuran maksimum lampiran")
        attach_lbl.setStyleSheet(f"font-size: 10px; font-weight: 600; color: #4A5568;")
        attach_row.addWidget(attach_lbl)
        self.attachment_mb_spin = QSpinBox()
        self.attachment_mb_spin.setRange(1, 100)
        self.attachment_mb_spin.setSuffix(" MB")
        self.attachment_mb_spin.setFixedWidth(110)
        self.attachment_mb_spin.setFixedHeight(32)
        attach_row.addWidget(self.attachment_mb_spin)
        attach_row.addStretch()
        layout.addLayout(attach_row)

    def _build_cache_section(self):
        layout = self._section(
            "CACHE",
            "Cache mempercepat dashboard. Data cache terenkripsi dan otomatis dibuang saat data berubah.",
        )
        row = QHBoxLayout()
        self.cache_enabled_check = QCheckBox("Aktifkan cache")
        self.cache_enabled_check.setStyleSheet("font-size: 11px; font-weight: 600; color: #2D3748;")
        row.addWidget(self.cache_enabled_check)

        ttl_lbl = QLabel("Kedaluwarsa")
        ttl_lbl.setStyleSheet(f"font-size: 10px; color: {AppColors.TEXT_SECONDARY};")
        row.addSpacing(8)
        row.addWidget(ttl_lbl)
        self.cache_ttl_spin = QSpinBox()
        self.cache_ttl_spin.setRange(0, 86400)
        self.cache_ttl_spin.setSuffix(" detik")
        self.cache_ttl_spin.setFixedWidth(130)
        self.cache_ttl_spin.setFixedHeight(32)
        row.addWidget(self.cache_ttl_spin)
        row.addStretch()
        layout.addLayout(row)

        stats_row = QHBoxLayout()
        self.cache_stats_lbl = QLabel("")
        self.cache_stats_lbl.setMinimumWidth(0)
        self.cache_stats_lbl.setWordWrap(True)
        self.cache_stats_lbl.setStyleSheet(f"font-size: 10px; color: {AppColors.TEXT_SECONDARY};")
        stats_row.addWidget(self.cache_stats_lbl)
        stats_row.addStretch()
        clear_btn = self._secondary_button("Bersihkan Cache")
        clear_btn.clicked.connect(self._clear_cache)
        stats_row.addWidget(clear_btn)
        layout.addLayout(stats_row)

    def _build_security_section(self):
        layout = self._section(
            "KEAMANAN DATA",
            "Catatan transaksi, catatan target, deskripsi kategori, nama lampiran, cache, dan backup "
            "dienkripsi dengan kunci yang dilindungi Windows DPAPI.",
        )
        row = QHBoxLayout()
        self.encryption_check = QCheckBox("Enkripsi data sensitif")
        self.encryption_check.setStyleSheet("font-size: 11px; font-weight: 600; color: #2D3748;")
        self.encryption_check.toggled.connect(self._on_encryption_toggled)
        row.addWidget(self.encryption_check)
        row.addStretch()
        self.key_backend_lbl = QLabel("")
        self.key_backend_lbl.setMinimumWidth(0)
        self.key_backend_lbl.setStyleSheet(f"font-size: 10px; color: {AppColors.TEXT_SECONDARY};")
        row.addWidget(self.key_backend_lbl)
        layout.addLayout(row)

    def _build_backup_section(self):
        layout = self._section(
            "BACKUP & PEMULIHAN",
            "Backup berisi database, lampiran, dan konfigurasi dalam satu file .kmbak terenkripsi. "
            "Backup otomatis dibuat sebelum restorasi.",
        )
        row = QHBoxLayout()
        self.backup_combo = QComboBox()
        self.backup_combo.setMinimumWidth(120)
        self.backup_combo.setMinimumContentsLength(8)
        self.backup_combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.backup_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.backup_combo.setMinimumHeight(32)
        row.addWidget(self.backup_combo, 1)

        create_btn = self._primary_button("Buat Backup")
        create_btn.clicked.connect(self._create_backup)
        row.addWidget(create_btn)

        restore_btn = self._secondary_button("Pulihkan")
        restore_btn.clicked.connect(self._restore_backup)
        row.addWidget(restore_btn)
        layout.addLayout(row)

        self.backup_stats_lbl = QLabel("")
        self.backup_stats_lbl.setMinimumWidth(0)
        self.backup_stats_lbl.setWordWrap(True)
        self.backup_stats_lbl.setStyleSheet(f"font-size: 10px; color: {AppColors.TEXT_SECONDARY};")
        layout.addWidget(self.backup_stats_lbl)

    # ------------------------------------------------------------------
    # Lazy services
    # ------------------------------------------------------------------
    def _database(self):
        if self._db is None:
            from src.core.mock_data import mock_store

            self._db = mock_store.db
        return self._db

    def _config_manager(self):
        if self._config is None:
            from src.storage.config import get_config

            self._config = get_config()
        return self._config

    def _refresh_stats(self):
        from src.storage.attachments import get_attachment_service
        from src.storage.backup import get_backup_manager
        from src.storage.cache import get_cache
        from src.storage.file_store import human_size
        from src.storage.paths import storage_paths

        cache_stats = get_cache().stats()
        self.cache_stats_lbl.setText(
            f"{cache_stats['entries']} entri, {cache_stats['size_human']} di {cache_stats['directory']}"
        )
        attachment_stats = get_attachment_service().stats()
        self.storage_lbl.setText(
            f"Data: {storage_paths.base_dir}\n"
            f"Database: {storage_paths.db_path}\n"
            f"Lampiran: {attachment_stats['count']} file "
            f"({human_size(attachment_stats['size_bytes'])})"
        )

        backups = get_backup_manager().list_backups()
        self.backup_combo.clear()
        for item in backups:
            self.backup_combo.addItem(
                f"{item['name']}  •  {item['size_human']}",
                item["path"],
            )
        self.backup_stats_lbl.setText(
            f"{len(backups)} backup tersedia."
            if backups else "Belum ada backup. Buat backup pertama Anda sekarang."
        )
        if not backups:
            self.backup_combo.addItem("Belum ada backup", "")

        try:
            from src.storage.crypto import get_crypto

            backend = get_crypto().key_backend
            self.key_backend_lbl.setText(
                "Kunci: Windows DPAPI" if backend == "dpapi" else "Kunci: file lokal"
            )
        except Exception:
            self.key_backend_lbl.setText("Kunci: tidak tersedia")

    def _load_values(self):
        config = self._config_manager()
        page_size = int(config.get("ui.page_size", 50))
        index = self.page_size_combo.findData(page_size)
        self.page_size_combo.setCurrentIndex(index if index >= 0 else 1)
        self.chart_period_combo.setCurrentText(config.get("ui.chart_period", "Minggu ini"))

        self.cache_enabled_check.setChecked(bool(config.get("cache.enabled", True)))
        self.cache_ttl_spin.setValue(int(config.get("cache.ttl_seconds", 300)))
        self.attachment_mb_spin.setValue(int(config.get("storage.max_attachment_mb", 10)))

        try:
            self.encryption_check.blockSignals(True)
            self.encryption_check.setChecked(bool(self._database().encryption_enabled))
        finally:
            self.encryption_check.blockSignals(False)

        self._refresh_stats()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _open_data_folder(self):
        from src.storage.paths import storage_paths

        storage_paths.ensure()
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(storage_paths.base_dir)))

    def _open_backup_folder(self):
        from src.storage.paths import storage_paths

        storage_paths.ensure()
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(storage_paths.backups_dir)))

    def _clear_cache(self):
        from src.storage.cache import get_cache

        get_cache().clear()
        self._refresh_stats()
        event_bus.toast_requested.emit("Cache berhasil dibersihkan.", "success")

    def _on_encryption_toggled(self, checked: bool):
        if self._loading:
            return
        action = "mengenkripsi" if checked else "mendekripsi"
        answer = QMessageBox.question(
            self,
            "Ubah Enkripsi Data",
            f"Semua data sensitif akan {action} ulang. Proses ini tidak dapat dibatalkan "
            "kecuali dari file backup. Lanjutkan?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            self.encryption_check.blockSignals(True)
            self.encryption_check.setChecked(not checked)
            self.encryption_check.blockSignals(False)
            return

        success = self._database().set_encryption_enabled(checked)
        if success:
            from src.storage.cache import get_cache

            get_cache().clear()
            event_bus.toast_requested.emit(
                "Enkripsi data berhasil diperbarui.", "success"
            )
            event_bus.data_changed.emit()
        else:
            self.encryption_check.blockSignals(True)
            self.encryption_check.setChecked(not checked)
            self.encryption_check.blockSignals(False)
            QMessageBox.warning(
                self, "Enkripsi Data",
                "Perubahan enkripsi gagal. Periksa izin file dan coba lagi.",
            )
        self._refresh_stats()

    def _create_backup(self):
        from src.storage.backup import BackupError, get_backup_manager

        try:
            path = get_backup_manager().create_backup("manual")
        except BackupError as exc:
            QMessageBox.warning(self, "Backup Gagal", str(exc))
            return
        self._refresh_stats()
        event_bus.toast_requested.emit(f"Backup dibuat: {path.name}", "success")

    def _restore_backup(self):
        path = self.backup_combo.currentData()
        if not path:
            QMessageBox.information(
                self, "Pulihkan Backup", "Belum ada file backup yang dapat dipulihkan."
            )
            return
        answer = QMessageBox.question(
            self,
            "Pulihkan Backup",
            "Semua data saat ini akan diganti dengan isi backup. "
            "Backup pengaman akan dibuat otomatis sebelum proses ini. Lanjutkan?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        from src.core.mock_data import mock_store
        from src.storage.backup import BackupError, get_backup_manager

        try:
            result = get_backup_manager().restore_backup(path)
        except BackupError as exc:
            QMessageBox.warning(self, "Pemulihan Gagal", str(exc))
            return

        mock_store.reload_from_database()
        try:
            from src.storage.cache import get_cache

            get_cache().clear()
        except Exception:
            pass
        self._refresh_stats()
        event_bus.data_changed.emit()
        event_bus.toast_requested.emit(
            f"Backup dipulihkan ({result['restored_attachments']} lampiran).", "success"
        )

    def _save_preferences(self):
        page_size = int(self.page_size_combo.currentData() or 50)
        chart_period = self.chart_period_combo.currentText()
        cache_enabled = self.cache_enabled_check.isChecked()
        cache_ttl = int(self.cache_ttl_spin.value())
        max_attachment_mb = int(self.attachment_mb_spin.value())

        self._config_manager().update({
            "ui.page_size": page_size,
            "ui.chart_period": chart_period,
            "cache.enabled": cache_enabled,
            "cache.ttl_seconds": cache_ttl,
            "storage.max_attachment_mb": max_attachment_mb,
        })

        # Update live singletons without requiring a restart.
        try:
            from src.storage.cache import get_cache

            cache = get_cache()
            cache.ttl_seconds = cache_ttl if cache_enabled else 0
            cache.clear()
        except Exception:
            pass
        try:
            from src.storage.attachments import get_attachment_service

            get_attachment_service().max_size_bytes = max_attachment_mb * 1024 * 1024
        except Exception:
            pass

        preferences = {
            "page_size": page_size,
            "chart_period": chart_period,
        }
        self.preferences_changed.emit(preferences)
        event_bus.toast_requested.emit("Pengaturan berhasil disimpan.", "success")
        self.accept()
