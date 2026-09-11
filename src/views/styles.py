"""
Application Stylesheet (QSS) for Keuangan Mandiri.
Implements modern UI styling based on the design PDF palette.
"""
from src.core.constants import AppColors

MAIN_STYLESHEET = f"""
/* Global Reset & Base */
QWidget {{
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif;
    color: {AppColors.TEXT_PRIMARY};
    font-size: 13px;
}}

QMainWindow, QStackedWidget {{
    background-color: {AppColors.BACKGROUND};
}}

/* All labels by default must have transparent background and no borders */
QLabel {{
    background: transparent;
    border: none;
}}

/* ScrollArea */
QScrollArea {{
    background: transparent;
    border: none;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: #CBD5E0;
    min-height: 20px;
    border-radius: 3px;
}}

QScrollBar::handle:vertical:hover {{
    background: #A0AEC0;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* Cards & Panels */
QFrame.card {{
    background-color: {AppColors.CARD_BG};
    border-radius: 12px;
    border: 1px solid {AppColors.BORDER_CARD};
}}

QFrame.sidebar, SidebarWidget {{
    background-color: #A8BFA3;
    border-top-right-radius: 24px;
    border-bottom-right-radius: 24px;
    border: none;
}}

/* Buttons */
QPushButton {{
    font-weight: 600;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
}}

QPushButton.primary-btn {{
    background-color: {AppColors.PRIMARY_BUTTON};
    color: #FFFFFF;
    border: none;
}}

QPushButton.primary-btn:hover {{
    background-color: {AppColors.PRIMARY_BUTTON_HOVER};
}}

QPushButton.primary-btn:pressed {{
    background-color: {AppColors.PRIMARY_BUTTON_PRESSED};
}}

QPushButton.secondary-btn {{
    background-color: #E2E8F0;
    color: {AppColors.TEXT_PRIMARY};
    border: none;
}}

QPushButton.secondary-btn:hover {{
    background-color: #CBD5E0;
}}

QPushButton.pill-btn {{
    background-color: #EAE6DF;
    color: {AppColors.TEXT_PRIMARY};
    border-radius: 16px;
    padding: 6px 14px;
    border: none;
    font-weight: 600;
}}

QPushButton.pill-btn:checked, QPushButton.pill-btn.active {{
    background-color: {AppColors.PRIMARY_BUTTON};
    color: #FFFFFF;
}}

QPushButton.icon-action-btn {{
    background-color: transparent;
    border-radius: 6px;
    padding: 4px;
}}

QPushButton.icon-action-btn:hover {{
    background-color: #EDF2F7;
}}

/* Form Inputs */
QLineEdit, QTextEdit, QPlainTextEdit, QDateEdit, QComboBox {{
    background-color: #FFFFFF;
    border: 1.5px solid {AppColors.BORDER_LIGHT};
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 13px;
    color: {AppColors.TEXT_PRIMARY};
    selection-background-color: {AppColors.PRIMARY_BUTTON};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QDateEdit:focus, QComboBox:focus {{
    border: 1.5px solid {AppColors.PRIMARY_BUTTON};
    background-color: #FFFFFF;
}}

QComboBox {{
    padding-right: 28px;
    padding-left: 10px;
    min-height: 24px;
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: none;
}}

QComboBox QAbstractItemView {{
    background-color: #FFFFFF;
    border: 1px solid {AppColors.BORDER_LIGHT};
    border-radius: 8px;
    selection-background-color: {AppColors.PEMASUKAN_LIGHT};
    selection-color: {AppColors.TEXT_PRIMARY};
    padding: 4px;
}}

/* Labels */
QLabel.heading-1 {{
    font-size: 20px;
    font-weight: 700;
    color: {AppColors.TEXT_PRIMARY};
    background: transparent;
}}

QLabel.heading-2 {{
    font-size: 16px;
    font-weight: 700;
    color: {AppColors.TEXT_PRIMARY};
    background: transparent;
}}

QLabel.subtitle {{
    font-size: 12px;
    color: {AppColors.TEXT_SECONDARY};
    background: transparent;
}}

QLabel.field-label {{
    font-size: 12px;
    font-weight: 600;
    color: {AppColors.TEXT_PRIMARY};
    margin-bottom: 2px;
    background: transparent;
}}

/* Table Widget */
QTableWidget {{
    background-color: #FFFFFF;
    border: 1px solid {AppColors.BORDER_CARD};
    border-radius: 12px;
    gridline-color: #F0EDE6;
    font-size: 12px;
}}

QTableWidget::item {{
    padding: 10px 8px;
    border-bottom: 1px solid #F0EDE6;
}}

QTableWidget::item:selected {{
    background-color: {AppColors.PEMASUKAN_LIGHT};
    color: {AppColors.TEXT_PRIMARY};
}}

QHeaderView::section {{
    background-color: #F4F1EB;
    color: {AppColors.TEXT_SECONDARY};
    font-weight: 600;
    font-size: 12px;
    border: none;
    border-bottom: 1.5px solid {AppColors.BORDER_CARD};
    padding: 8px 6px;
}}

/* Progress Bar */
QProgressBar {{
    background-color: #EDF2F7;
    border-radius: 5px;
    text-align: center;
    font-size: 11px;
    font-weight: 600;
    color: {AppColors.TEXT_PRIMARY};
    height: 10px;
}}

QProgressBar::chunk {{
    background-color: {AppColors.PEMASUKAN};
    border-radius: 5px;
}}
"""
