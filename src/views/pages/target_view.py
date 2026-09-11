"""
Target View.
Manages financial savings targets, progress visualizers, target creation/editing dialogs,
and deposit allocations.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QGridLayout, QScrollArea, QDialog, QLineEdit, QComboBox, QDateEdit
)
from PySide6.QtCore import Qt, QDate, Slot
from src.core.constants import AppColors, TargetPriority
from src.core.event_bus import event_bus
from src.core.utils import format_rupiah, parse_rupiah
from src.viewmodels.target_viewmodel import TargetViewModel
from src.views.components.header import HeaderWidget
from src.views.components.summary_card import SummaryCardWidget
from src.views.components.target_card import TargetCardWidget
from src.views.components.isi_target_dialog import IsiTargetDialog

class TargetFormDialog(QDialog):
    """Dialog for creating or editing a financial target."""
    def __init__(self, edit_data: dict = None, parent=None):
        super().__init__(parent)
        self.edit_data = edit_data
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(520, 520)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        box = QFrame()
        box.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                border: 1px solid {AppColors.BORDER_CARD};
                border-radius: 16px;
            }}
        """)
        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(28, 22, 28, 22)
        box_layout.setSpacing(12)

        # Header
        title_str = "EDIT TARGET KEUANGAN" if self.edit_data else "TAMBAH TARGET KEUANGAN"
        sub_str = "Ubah detail target keuanganmu di sini" if self.edit_data else "Buat target baru untuk membantu mencapai tujuan keuanganmu"

        lbl_t = QLabel(title_str)
        lbl_t.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {AppColors.TEXT_PRIMARY};")
        lbl_s = QLabel(sub_str)
        lbl_s.setStyleSheet(f"font-size: 11px; color: {AppColors.TEXT_SECONDARY};")
        box_layout.addWidget(lbl_t)
        box_layout.addWidget(lbl_s)

        # Name
        box_layout.addWidget(QLabel("Nama Target", styleSheet="font-size: 11px; font-weight: 600; color: #4A5568;"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nama target (misal: Beli Laptop)")
        if self.edit_data:
            self.name_input.setText(self.edit_data.get("name", ""))
        box_layout.addWidget(self.name_input)

        # Nominal
        box_layout.addWidget(QLabel("Target Nominal", styleSheet="font-size: 11px; font-weight: 600; color: #4A5568;"))
        self.nom_input = QLineEdit()
        self.nom_input.setPlaceholderText("Masukkan jumlah target yang ingin dicapai")
        self.nom_input.textChanged.connect(self._on_amount_changed)
        if self.edit_data:
            self.nom_input.setText(self.edit_data.get("target_amount_formatted", ""))
        box_layout.addWidget(self.nom_input)

        # Dates Row (Mulai & Deadline)
        dates_row = QHBoxLayout()
        dates_row.setSpacing(10)

        c1 = QVBoxLayout()
        c1.setSpacing(2)
        c1.addWidget(QLabel("Target Mulai", styleSheet="font-size: 11px; font-weight: 600; color: #4A5568;"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate())
        self.start_date_edit.setDisplayFormat("dd/MM/yyyy")
        c1.addWidget(self.start_date_edit)
        dates_row.addLayout(c1)

        c2 = QVBoxLayout()
        c2.setSpacing(2)
        c2.addWidget(QLabel("Deadline / Tanggal Target", styleSheet="font-size: 11px; font-weight: 600; color: #4A5568;"))
        self.deadline_date_edit = QDateEdit()
        self.deadline_date_edit.setCalendarPopup(True)
        self.deadline_date_edit.setDate(QDate(2027, 12, 25))
        self.deadline_date_edit.setDisplayFormat("dd/MM/yyyy")
        c2.addWidget(self.deadline_date_edit)
        dates_row.addLayout(c2)

        box_layout.addLayout(dates_row)

        # Priority
        box_layout.addWidget(QLabel("Prioritas Target", styleSheet="font-size: 11px; font-weight: 600; color: #4A5568;"))
        self.prio_combo = QComboBox()
        self.prio_combo.addItems([TargetPriority.SEDANG, TargetPriority.TINGGI, TargetPriority.RENDAH])
        if self.edit_data:
            self.prio_combo.setCurrentText(self.edit_data.get("priority", TargetPriority.SEDANG))
        box_layout.addWidget(self.prio_combo)

        # Notes
        box_layout.addWidget(QLabel("Catatan (Opsional)", styleSheet="font-size: 11px; font-weight: 600; color: #4A5568;"))
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Tulis catatan atau rencana untuk mencapai target ini")
        if self.edit_data:
            self.notes_input.setText(self.edit_data.get("notes", ""))
        box_layout.addWidget(self.notes_input)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        batal_btn = QPushButton("Batal")
        batal_btn.setCursor(Qt.PointingHandCursor)
        batal_btn.setStyleSheet("""
            QPushButton {
                background-color: #E2E8F0;
                color: #4A5568;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 700;
                border: none;
            }
            QPushButton:hover {
                background-color: #CBD5E0;
            }
        """)
        batal_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Simpan Target")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AppColors.PRIMARY_BUTTON};
                color: #FFFFFF;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 700;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {AppColors.PRIMARY_BUTTON_HOVER};
            }}
        """)
        save_btn.clicked.connect(self.accept)

        btn_layout.addWidget(batal_btn)
        btn_layout.addWidget(save_btn)
        box_layout.addLayout(btn_layout)

        main_layout.addWidget(box)

    def _on_amount_changed(self, text: str):
        val = parse_rupiah(text)
        if val > 0:
            formatted = format_rupiah(val, with_prefix=True)
            if self.nom_input.text() != formatted:
                self.nom_input.blockSignals(True)
                self.nom_input.setText(formatted)
                self.nom_input.blockSignals(False)


class TargetView(QWidget):
    def __init__(self, viewmodel: TargetViewModel, parent=None):
        super().__init__(parent)
        self.vm = viewmodel
        self.cached_targets = []
        self._setup_ui()
        self._bind_viewmodel()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(16)

        # 1. Header
        self.header = HeaderWidget("Target Keuangan", "Lihat semua catatan pemasukan dan pengeluaranmu di sini!")
        layout.addWidget(self.header)

        # 2. Top Summary KPI Cards Row
        summary_row = QHBoxLayout()
        summary_row.setSpacing(14)

        self.card_total_aktif = SummaryCardWidget("Total Target", "6 Aktif", "🎯", AppColors.TARGET)
        self.card_goal_amount = SummaryCardWidget("Total Target Keuangan", "Rp. 18.111.000", "💰", "#E57373")
        self.card_terkumpul = SummaryCardWidget("Terkumpul", "Rp. 5.100.000", "👛", "#FFB74D")
        self.card_progress_total = SummaryCardWidget("Seluruh Progress", "20% Dari Target", "📈", "#81C784")

        summary_row.addWidget(self.card_total_aktif)
        summary_row.addWidget(self.card_goal_amount)
        summary_row.addWidget(self.card_terkumpul)
        summary_row.addWidget(self.card_progress_total)
        layout.addLayout(summary_row)

        # 3. Action Bar: "TARGET AKTIF" & "+ Tambah Target" Button
        action_bar = QHBoxLayout()
        sec_title = QLabel("TARGET AKTIF")
        sec_title.setStyleSheet(f"font-size: 13px; font-weight: 800; color: {AppColors.TEXT_PRIMARY}; letter-spacing: 0.5px;")
        action_bar.addWidget(sec_title)
        action_bar.addStretch()

        add_target_btn = QPushButton("+ Tambah Target")
        add_target_btn.setCursor(Qt.PointingHandCursor)
        add_target_btn.setFixedHeight(34)
        add_target_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AppColors.PRIMARY_BUTTON};
                color: #FFFFFF;
                font-size: 12px;
                font-weight: 700;
                border-radius: 8px;
                padding: 0 16px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {AppColors.PRIMARY_BUTTON_HOVER};
            }}
        """)
        add_target_btn.clicked.connect(self._on_add_target_clicked)
        action_bar.addWidget(add_target_btn)
        layout.addLayout(action_bar)

        # 4. Target Grid Container
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(14)
        layout.addWidget(self.grid_widget)

        # 5. Bottom Row: Tips Menabung (Left) + Aktivitas Terbaru (Right)
        btm_row = QHBoxLayout()
        btm_row.setSpacing(14)

        # Tips Menabung Card
        tips_box = QFrame()
        tips_box.setStyleSheet(f"""
            QFrame {{
                background-color: {AppColors.CARD_BG};
                border: 1px solid {AppColors.BORDER_CARD};
                border-radius: 12px;
            }}
        """)
        tips_l = QVBoxLayout(tips_box)
        tips_l.setContentsMargins(16, 14, 16, 14)
        tips_l.setSpacing(8)

        t_hdr = QHBoxLayout()
        t_icon = QLabel("💡")
        t_title = QLabel("TIPS MENABUNG")
        t_title.setStyleSheet(f"font-size: 12px; font-weight: 800; color: #F59E0B;")
        t_hdr.addWidget(t_icon)
        t_hdr.addWidget(t_title)
        t_hdr.addStretch()
        tips_l.addLayout(t_hdr)

        tips_text = QLabel("Sedikit demi sedikit, menjadi bukit. Konsisten setiap hari membawa perubahan di masa depan.")
        tips_text.setWordWrap(True)
        tips_text.setStyleSheet(f"font-size: 12px; color: {AppColors.TEXT_PRIMARY}; line-height: 18px;")
        tips_l.addWidget(tips_text)
        tips_l.addStretch()

        btm_row.addWidget(tips_box, 1)

        # Aktivitas Terbaru Card
        self.activity_box = QFrame()
        self.activity_box.setStyleSheet(f"""
            QFrame {{
                background-color: {AppColors.CARD_BG};
                border: 1px solid {AppColors.BORDER_CARD};
                border-radius: 12px;
            }}
        """)
        act_l = QVBoxLayout(self.activity_box)
        act_l.setContentsMargins(16, 14, 16, 14)
        act_l.setSpacing(8)

        act_hdr = QHBoxLayout()
        act_icon = QLabel("🕒")
        act_title = QLabel("Aktivitas Terbaru")
        act_title.setStyleSheet(f"font-size: 12px; font-weight: 800; color: {AppColors.TEXT_PRIMARY};")
        act_hdr.addWidget(act_icon)
        act_hdr.addWidget(act_title)
        act_hdr.addStretch()

        lihat_btn = QPushButton("Lihat Semua")
        lihat_btn.setCursor(Qt.PointingHandCursor)
        lihat_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #8E7CC3;
                color: #FFFFFF;
                font-size: 10px;
                font-weight: 700;
                border-radius: 6px;
                padding: 3px 10px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #7A69B0;
            }}
        """)
        lihat_btn.clicked.connect(lambda: event_bus.navigation_requested.emit(3))
        act_hdr.addWidget(lihat_btn)
        act_l.addLayout(act_hdr)

        self.activity_items_layout = QVBoxLayout()
        self.activity_items_layout.setSpacing(6)
        act_l.addLayout(self.activity_items_layout)

        btm_row.addWidget(self.activity_box, 1)
        layout.addLayout(btm_row)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def _bind_viewmodel(self):
        self.vm.target_summary_updated.connect(self._on_summary_updated)
        self.vm.targets_updated.connect(self._on_targets_updated)
        self.vm.target_allocations_updated.connect(self._on_allocations_updated)

        # Global event for opening Isi Target
        event_bus.open_isi_target_requested.connect(self.open_isi_target_by_id)

    def showEvent(self, event):
        super().showEvent(event)
        self.vm.refresh()

    @Slot(dict)
    def _on_summary_updated(self, summary: dict):
        self.card_total_aktif.update_value(f"{summary.get('total_target_aktif', '0')} Aktif")
        self.card_goal_amount.update_value(summary.get("total_target_keuangan", "Rp 0"))
        self.card_terkumpul.update_value(summary.get("terkumpul", "Rp 0"))
        self.card_progress_total.update_value(f"{summary.get('seluruh_progress', '0%')} Dari Semua Target")

    @Slot(list)
    def _on_targets_updated(self, targets: list):
        self.cached_targets = targets
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cols = 3
        for idx, t in enumerate(targets):
            row = idx // cols
            col = idx % cols
            card = TargetCardWidget(t)
            card.isi_target_clicked.connect(self._on_isi_target_clicked)
            card.edit_target_clicked.connect(self._on_edit_target_clicked)
            card.delete_target_clicked.connect(self.vm.delete_target)
            self.grid_layout.addWidget(card, row, col)

    @Slot(list)
    def _on_allocations_updated(self, allocs: list):
        while self.activity_items_layout.count():
            item = self.activity_items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for a in allocs[:3]:
            row = QFrame()
            row.setStyleSheet("background: transparent; border-bottom: 1px solid #F0EDE6;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 4, 0, 4)
            rl.setSpacing(8)

            icon = QLabel("🎯")
            icon.setStyleSheet(f"color: {AppColors.TARGET}; font-size: 11px;")

            t_col = QVBoxLayout()
            t_col.setSpacing(1)
            name_lbl = QLabel(a["target_name"])
            name_lbl.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {AppColors.TEXT_PRIMARY};")
            cat_lbl = QLabel("Target")
            cat_lbl.setStyleSheet(f"font-size: 9px; color: {AppColors.TEXT_SECONDARY};")
            t_col.addWidget(name_lbl)
            t_col.addWidget(cat_lbl)

            r_col = QVBoxLayout()
            r_col.setSpacing(1)
            amt_lbl = QLabel(a["nominal_formatted"])
            amt_lbl.setAlignment(Qt.AlignRight)
            amt_lbl.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {AppColors.TEXT_SECONDARY};")
            dt_lbl = QLabel(a["date"])
            dt_lbl.setAlignment(Qt.AlignRight)
            dt_lbl.setStyleSheet(f"font-size: 9px; color: {AppColors.TEXT_MUTED};")
            r_col.addWidget(amt_lbl)
            r_col.addWidget(dt_lbl)

            rl.addWidget(icon)
            rl.addLayout(t_col)
            rl.addStretch()
            rl.addLayout(r_col)

            self.activity_items_layout.addWidget(row)

    def _on_isi_target_clicked(self, target_id: str):
        self.open_isi_target_by_id(target_id)

    @Slot(str)
    def open_isi_target_by_id(self, target_id: str):
        target = next((t for t in self.cached_targets if t["id"] == target_id), None)
        if not target:
            return
        dlg = IsiTargetDialog(target, parent=self)
        dlg.deposit_confirmed.connect(self.vm.deposit_funds)
        dlg.exec()

    def _on_add_target_clicked(self):
        dlg = TargetFormDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            name = dlg.name_input.text()
            amt = dlg.nom_input.text()
            start_d = dlg.start_date_edit.date().toString("dd/MM/yyyy")
            deadline_d = dlg.deadline_date_edit.date().toString("dd/MM/yyyy")
            prio = dlg.prio_combo.currentText()
            notes = dlg.notes_input.text()
            self.vm.add_target(name, amt, deadline_d, start_d, prio, notes)

    def _on_edit_target_clicked(self, target_id: str):
        target = next((t for t in self.cached_targets if t["id"] == target_id), None)
        if not target:
            return
        dlg = TargetFormDialog(edit_data=target, parent=self)
        if dlg.exec() == QDialog.Accepted:
            name = dlg.name_input.text()
            amt = dlg.nom_input.text()
            start_d = dlg.start_date_edit.date().toString("dd/MM/yyyy")
            deadline_d = dlg.deadline_date_edit.date().toString("dd/MM/yyyy")
            prio = dlg.prio_combo.currentText()
            notes = dlg.notes_input.text()
            self.vm.update_target(target_id, name, amt, deadline_d, start_d, prio, notes)
