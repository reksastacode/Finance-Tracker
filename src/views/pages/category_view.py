"""
Category View.
Displays category cards for Expense and Income, handles tab-switching events,
category creation, editing, and deletion.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QGridLayout, QScrollArea, QDialog, QLineEdit
)
from PySide6.QtCore import Qt, Slot, Signal
from src.core.constants import AppColors, TransactionType
from src.viewmodels.category_viewmodel import CategoryViewModel
from src.views.components.header import HeaderWidget

class CategoryDialog(QDialog):
    """Modal dialog for creating or updating a category."""
    def __init__(self, cat_type: str, edit_data: dict = None, parent=None):
        super().__init__(parent)
        self.cat_type = cat_type
        self.edit_data = edit_data
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(460, 340)
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
        box_layout.setContentsMargins(24, 20, 24, 20)
        box_layout.setSpacing(14)

        # Title
        title_text = "EDIT KATEGORI" if self.edit_data else "TAMBAH KATEGORI"
        sub_text = f"Kelola kategori {self.cat_type.lower()} baru untuk keuanganmu"

        lbl_title = QLabel(title_text)
        lbl_title.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {AppColors.TEXT_PRIMARY};")
        lbl_sub = QLabel(sub_text)
        lbl_sub.setStyleSheet(f"font-size: 11px; color: {AppColors.TEXT_SECONDARY};")

        box_layout.addWidget(lbl_title)
        box_layout.addWidget(lbl_sub)

        # Fields
        box_layout.addWidget(QLabel("Nama Kategori", styleSheet="font-size: 12px; font-weight: 600; color: #4A5568;"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Masukan kategori yang akan dimasukan")
        if self.edit_data:
            self.name_input.setText(self.edit_data.get("name", ""))
        box_layout.addWidget(self.name_input)

        box_layout.addWidget(QLabel("Deskripsi (Opsional)", styleSheet="font-size: 12px; font-weight: 600; color: #4A5568;"))
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Tambahkan deskripsi untuk kategori (opsional)")
        if self.edit_data:
            self.desc_input.setText(self.edit_data.get("description", ""))
        box_layout.addWidget(self.desc_input)

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

        save_btn = QPushButton("Simpan Kategori")
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


class CategoryCard(QFrame):
    edit_clicked = Signal(dict)
    delete_clicked = Signal(str)

    def __init__(self, cat_data: dict, parent=None):
        super().__init__(parent)
        self.cat_data = cat_data
        self._setup_ui()

    def _setup_ui(self):
        self.setProperty("class", "card")
        self.setFixedHeight(140)
        self.setStyleSheet(f"""
            CategoryCard {{
                background-color: {AppColors.CARD_BG};
                border: 1px solid {AppColors.BORDER_CARD};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        # Name
        name_lbl = QLabel(self.cat_data.get("name", ""))
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {AppColors.TEXT_PRIMARY};")
        layout.addWidget(name_lbl)

        # Dashed line
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("border-top: 1px dashed #CBD5E0; max-height: 1px;")
        layout.addWidget(sep)

        # Description
        desc_lbl = QLabel(self.cat_data.get("description", ""))
        desc_lbl.setWordWrap(True)
        desc_lbl.setAlignment(Qt.AlignCenter)
        desc_lbl.setStyleSheet(f"font-size: 11px; color: {AppColors.TEXT_SECONDARY};")
        layout.addWidget(desc_lbl)

        layout.addStretch()

        # Action buttons (Edit & Delete)
        act_layout = QHBoxLayout()
        act_layout.setSpacing(8)
        act_layout.addStretch()

        edit_btn = QPushButton("✏️")
        edit_btn.setFixedSize(28, 26)
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFB74D;
                border-radius: 6px;
                border: none;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #FFA726;
            }
        """)
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.cat_data))

        del_btn = QPushButton("🗑️")
        del_btn.setFixedSize(28, 26)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet("""
            QPushButton {
                background-color: #E57373;
                border-radius: 6px;
                border: none;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #EF5350;
            }
        """)
        del_btn.clicked.connect(lambda: self.delete_clicked.emit(self.cat_data.get("id", "")))

        act_layout.addWidget(edit_btn)
        act_layout.addWidget(del_btn)
        layout.addLayout(act_layout)


class CategoryView(QWidget):
    def __init__(self, viewmodel: CategoryViewModel, parent=None):
        super().__init__(parent)
        self.vm = viewmodel
        self._current_tab = TransactionType.PENGELUARAN
        self._setup_ui()
        self._bind_viewmodel()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # 1. Header
        self.header = HeaderWidget("KATEGORI", "Kelola kategori pengeluaranmu di sini")
        main_layout.addWidget(self.header)

        # 2. Tabs & Add Button Bar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        self.btn_pengeluaran = QPushButton("Kategori Pengeluaran")
        self.btn_pengeluaran.setCursor(Qt.PointingHandCursor)
        self.btn_pengeluaran.setCheckable(True)
        self.btn_pengeluaran.setChecked(True)
        self.btn_pengeluaran.setFixedHeight(36)
        self._style_tab_btn(self.btn_pengeluaran, True)
        self.btn_pengeluaran.clicked.connect(lambda: self._on_tab_selected(TransactionType.PENGELUARAN))

        self.btn_pemasukan = QPushButton("Kategori Pemasukan")
        self.btn_pemasukan.setCursor(Qt.PointingHandCursor)
        self.btn_pemasukan.setCheckable(True)
        self.btn_pemasukan.setChecked(False)
        self.btn_pemasukan.setFixedHeight(36)
        self._style_tab_btn(self.btn_pemasukan, False)
        self.btn_pemasukan.clicked.connect(lambda: self._on_tab_selected(TransactionType.PEMASUKAN))

        top_bar.addWidget(self.btn_pengeluaran)
        top_bar.addWidget(self.btn_pemasukan)
        top_bar.addStretch()

        # Add Category Button
        add_btn = QPushButton("+ Tambah Kategori")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setFixedHeight(36)
        add_btn.setStyleSheet(f"""
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
        add_btn.clicked.connect(self._on_add_category_clicked)
        top_bar.addWidget(add_btn)

        main_layout.addLayout(top_bar)

        # 3. Grid Container with ScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(14)

        scroll.setWidget(self.grid_container)
        main_layout.addWidget(scroll)

    def _style_tab_btn(self, btn: QPushButton, is_active: bool):
        if is_active:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #B5C9B0;
                    color: #1A202C;
                    font-weight: 700;
                    border-radius: 8px;
                    padding: 0 16px;
                    border: none;
                }}
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #E6E2D8;
                    color: #718096;
                    font-weight: 600;
                    border-radius: 8px;
                    padding: 0 16px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #DDD8CC;
                }
            """)

    def _bind_viewmodel(self):
        self.vm.categories_updated.connect(self._on_categories_updated)

    def showEvent(self, event):
        super().showEvent(event)
        self.vm.refresh()

    def _on_tab_selected(self, tab_type: str):
        self._current_tab = tab_type
        is_pengeluaran = (tab_type == TransactionType.PENGELUARAN)
        self.btn_pengeluaran.setChecked(is_pengeluaran)
        self.btn_pemasukan.setChecked(not is_pengeluaran)
        self._style_tab_btn(self.btn_pengeluaran, is_pengeluaran)
        self._style_tab_btn(self.btn_pemasukan, not is_pengeluaran)

        sub = "Kelola kategori pengeluaranmu di sini" if is_pengeluaran else "Kelola kategori pemasukanmu di sini"
        self.header.set_title("KATEGORI", sub)

        self.vm.set_active_tab(tab_type)

    @Slot(list, str)
    def _on_categories_updated(self, categories: list, tab_type: str):
        # Clear grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cols = 4
        for idx, cat in enumerate(categories):
            row = idx // cols
            col = idx % cols
            card = CategoryCard(cat)
            card.edit_clicked.connect(self._on_edit_category_clicked)
            card.delete_clicked.connect(self.vm.delete_category)
            self.grid_layout.addWidget(card, row, col)

    def _on_add_category_clicked(self):
        dlg = CategoryDialog(self._current_tab, parent=self)
        if dlg.exec() == QDialog.Accepted:
            name = dlg.name_input.text()
            desc = dlg.desc_input.text()
            self.vm.add_category(name, self._current_tab, desc)

    def _on_edit_category_clicked(self, cat_data: dict):
        dlg = CategoryDialog(self._current_tab, edit_data=cat_data, parent=self)
        if dlg.exec() == QDialog.Accepted:
            name = dlg.name_input.text()
            desc = dlg.desc_input.text()
            self.vm.update_category(cat_data["id"], name, desc)
