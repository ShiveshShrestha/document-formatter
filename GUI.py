import json
import html
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFont, QPixmap, QImage, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QMenu,
    QProgressBar,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

baseDir = os.path.dirname(os.path.abspath(__file__))
iconDir = os.path.join(baseDir, "Assets", "Icons")



def icon_path(name):
    return os.path.join(iconDir, name)



def make_icon(name):
    return QIcon(icon_path(name))


CONTENT_ICON_MAP = {
    "Quick Actions": "quick-actions.svg",
    "Workflow": "workflow.svg",
    "Workflow": "workflow.svg",
    "Margins": "margins.svg",
    "Font": "font.svg",
    "Export Format": "export.svg",
    "Output Images": "figures.svg",
    "Caption Options": "tag.svg",
    "Manual Captions": "captions.svg",
    "Cover Page": "cover.svg",
    "Table of Contents": "toc.svg",
    "Code Page": "code.svg",
    "Place Output After Code": "code-output.svg",
    "Watermark": "watermark.svg",
    "Watermark Coverage": "shield.svg",
    "Report Generation": "progress.svg",
}

METRIC_ICON_MAP = {
    "Layout": "layout.svg",
    "Content": "figures.svg",
    "Generate": "generate.svg",
    "Sample PDF": "preview.svg",
    "Check Project": "health.svg",
    "Custom Table": "captions.svg",
}

ACTION_ICON_MAP = {
    "Project Check": "health.svg",
    "Generation Summary": "summary.svg",
    "Report History": "history.svg",
    "Manage Captions": "captions.svg",
}

TOOL_BUTTON_ICON_MAP = {
    "Refresh Images": "refresh.svg",
    "Save Captions": "save.svg",
    "Clear Captions": "clear.svg",
    "Choose Contents File": "folder-open.svg",
    "Choose Code Folder": "folder-open.svg",
    "Choose Image Folder": "folder-open.svg",
    "Choose Save Location": "save.svg",
    "Add Logo": "logo-upload.svg",
    "Preview Report": "preview.svg",
    "Generate Report": "proceed.svg",
}


CAPTION_MODE_CUSTOM_OUTPUT = "Manual captions"
CAPTION_MODE_MATCH_FILENAME = "Use file names"
CAPTION_MODE_NONE = "No captions"

TOC_MODE_MANUAL = "Enter manually"
TOC_MODE_BROWSE = "Import from file"

finalPdfPath = os.path.join(baseDir, "Final_Report.pdf")
previewPdfPath = os.path.join(baseDir, "Preview_Report.pdf")
summaryPath = os.path.join(baseDir, "Generation_Summary.txt")
codeDir = os.path.join(baseDir, "Default_Code_Folder")
imageDir = os.path.join(baseDir, "Default_Output_Snapshot_Folder")
jsonDir = os.path.join(baseDir, "JsonFile")
captionsPath = os.path.join(jsonDir, "output_captions.json")
historyPath = os.path.join(baseDir, "Generated_Project_History.json")
logoFlagPath = os.path.join(jsonDir, "custom_logo_selected.json")

for directory in (codeDir, imageDir, jsonDir):
    os.makedirs(directory, exist_ok=True)


def required_font_files(font_family):
    if str(font_family).lower() == "arial":
        names = ("arial.ttf", "arialbd.ttf")
    else:
        names = ("times.ttf", "timesbd.ttf")
    return [(name, os.path.join(baseDir, "Fonts", name)) for name in names]


DEFAULT_COLLEGE_NAME = ""
DEFAULT_COLLEGE_ADDRESS = ""

PLACEHOLDERS = {
    "college_name": "Enter college name",
    "college_address": "Enter college address",
    "student_name": "Enter student name",
    "roll": "Enter roll number",
    "section": "Enter section",
    "semester": "Enter semester",
    "teacher_name": "Enter teacher name",
    "project_title": "Enter project title",
    "toc": "1. Introduction\n2. System Design\n3. Results",
    "code_line_height": "e.g., 40 points",
    "code_file_ext": "e.g., py",
    "watermark_name": "Enter watermark text",
}



class ToggleSwitch(QPushButton):



    def __init__(self, parent=None, checked=False):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setFixedSize(92, 44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggled.connect(self.apply_style)
        self.apply_style()


    def apply_style(self):
        if self.isChecked():
            self.setText("ON   ●")
            self.setStyleSheet(
                """
                QPushButton {
                    background-color: #2f80ed;
                    color: #ffffff;
                    border-radius: 0px;
                    padding: 0px 13px;
                    text-align: right;
                    font-size: 13px;
                    font-weight: 900;
                    border: 1px solid #1d6fe8;
                }
                QPushButton:hover {
                    background-color: #1d6fe8;
                }
            """
            )
        else:
            self.setText("●   OFF")
            self.setStyleSheet(
                """
                QPushButton {
                    background-color: #eef5fb;
                    color: #64748b;
                    border-radius: 0px;
                    padding: 0px 13px;
                    text-align: left;
                    font-size: 13px;
                    font-weight: 900;
                    border: 1px solid #c9d8e8;
                }
                QPushButton:hover {
                    background-color: #e2edf7;
                    border: 1px solid #adc4dd;
                }
            """
            )



class ModernComboBox(QPushButton):



    def __init__(self, items=None, parent=None):
        super().__init__(parent)
        self._items = []
        self._current_text = ""
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(52)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setObjectName("modernDropdown")
        self.clicked.connect(self.show_dropdown_menu)
        if items:
            self.addItems(items)
        self.apply_style()


    def addItems(self, items):
        for item in items:
            item = str(item)
            if item not in self._items:
                self._items.append(item)
        if not self._current_text and self._items:
            self._current_text = self._items[0]
        self.refresh_text()


    def currentText(self):
        return self._current_text


    def setCurrentText(self, text):
        text = str(text)
        if text not in self._items:
            self._items.append(text)
        self._current_text = text
        self.refresh_text()
        callback = getattr(self, "on_change", None)
        if callable(callback):
            callback()


    def refresh_text(self):
        self.setText(f"{self._current_text}    ▾")


    def show_dropdown_menu(self):
        menu = QMenu(self)
        menu.setFixedWidth(max(self.width(), 220))
        menu.setStyleSheet(
            """
            QMenu {
                background: #FFFFFF;
                color: #142338;
                border: 1px solid #BFD4E8;
                border-radius: 4px;
                padding: 4px;
                font-size: 12px;
                font-weight: 400;
            }
            QMenu::item {
                min-height: 24px;
                padding: 5px 18px;
                border-radius: 2px;
            }
            QMenu::item:selected {
                background: #EAF6FF;
                color: #1267C4;
            }
        """
        )
        for item in self._items:
            action = menu.addAction(item)
            action.triggered.connect(lambda checked=False, value=item: self.setCurrentText(value))
        menu.exec(self.mapToGlobal(self.rect().bottomLeft()))


    def apply_style(self):
        self.setStyleSheet(
            """
            QPushButton#modernDropdown {
                background: #FFFFFF;
                color: #111111;
                border: 1px solid #D5E2EC;
                border-radius: 0px;
                padding: 9px 12px;
                text-align: left;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton#modernDropdown:hover {
                border: 1px solid #0078D4;
                background: #FFFFFF;
            }
            QPushButton#modernDropdown:pressed {
                border: 1px solid #005FB8;
                background: #F7FBFF;
            }
        """
        )



class SidebarButton(QPushButton):

    def __init__(self, icon_name, label):
        super().__init__(label)
        self.icon_name = icon_name
        self.label_text = label
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(58)
        self.setIcon(make_icon(icon_name))
        self.setIconSize(QSize(32, 32))
        self.setObjectName("sidebarButton")


    def set_compact(self, compact):
        self.setText("" if compact else self.label_text)
        self.setIconSize(QSize(34, 34) if compact else QSize(32, 32))
        self.setToolTip(self.label_text)



class PdfPreviewDialog(QDialog):

    def __init__(self, pdf_path, title, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.pdf_doc = None
        self.current_page = 0
        self.zoom = 1.05

        self.setWindowTitle(title)
        self.resize(1040, 880)
        self.setStyleSheet("QDialog { background: #E8F5FC; }")

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        toolbar = QFrame()
        toolbar.setObjectName("previewToolbar")
        toolbar.setStyleSheet(
            """
            QFrame#previewToolbar {
                background: #FFFFFF;
                border: 1px solid #D8E5F1;
                border-radius: 20px;
            }
        """
        )
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 10, 16, 10)

        self.page_label = QLabel("Page 1 of 1")
        self.page_label.setStyleSheet("color: #1B2A3B; font-size: 14px; font-weight: 800;")
        toolbar_layout.addWidget(self.page_label)
        toolbar_layout.addStretch()

        self.prev_btn = self.small_button("Previous")
        self.next_btn = self.small_button("Next")
        self.zoom_out_btn = self.small_button("Zoom Out")
        self.zoom_in_btn = self.small_button("Zoom In")
        self.open_btn = self.primary_small_button("Open in System Viewer")

        for btn in [
            self.prev_btn,
            self.next_btn,
            self.zoom_out_btn,
            self.zoom_in_btn,
            self.open_btn,
        ]:
            toolbar_layout.addWidget(btn)

        root.addWidget(toolbar)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setStyleSheet(
            """
            QScrollArea {
                background: #D7EBFA;
                border: none;
                border-radius: 20px;
            }
            QScrollBar:vertical {
                background: #E9F4FD;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #95BFE1;
                border-radius: 6px;
                min-height: 44px;
            }
            QScrollBar:horizontal {
                background: #E9F4FD;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background: #95BFE1;
                border-radius: 6px;
                min-width: 44px;
            }
        """
        )
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background: #D7EBFA; padding: 22px;")
        self.scroll_area.setWidget(self.image_label)
        root.addWidget(self.scroll_area, stretch=1)

        self.prev_btn.clicked.connect(self.previous_page)
        self.next_btn.clicked.connect(self.next_page)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.open_btn.clicked.connect(lambda: open_pdf_with_system_viewer(self.pdf_path, self))

        self.load_pdf()


    def small_button(self, text):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(38)
        btn.setStyleSheet(
            """
            QPushButton {
                background: #E5F3FF;
                color: #1267C4;
                border: none;
                border-radius: 0px;
                padding: 8px 14px;
                font-size: 13px;
                font-weight: 800;
            }
            QPushButton:hover { background: #D5ECFF; }
        """
        )
        return btn


    def primary_small_button(self, text):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(38)
        btn.setStyleSheet(
            """
            QPushButton {
                background: #2F80ED;
                color: white;
                border: none;
                border-radius: 0px;
                padding: 8px 15px;
                font-size: 13px;
                font-weight: 900;
            }
            QPushButton:hover { background: #1D6FD8; }
        """
        )
        return btn


    def load_pdf(self):
        if not os.path.exists(self.pdf_path):
            QMessageBox.warning(self, "Preview Unavailable", f"PDF file not found:\n{self.pdf_path}")
            self.close()
            return

        try:
            import fitz
        except Exception:
            QMessageBox.warning(
                self,
                "Preview Component Missing",
                "Install PyMuPDF to view PDF pages in the app:\n\npip install pymupdf\n\nThe PDF will open in your default viewer.",
            )
            open_pdf_with_system_viewer(self.pdf_path, self)
            self.close()
            return

        try:
            self.pdf_doc = fitz.open(self.pdf_path)
        except Exception as exc:
            QMessageBox.critical(self, "Preview Failed", f"Could not load the PDF.\n{exc}")
            self.close()
            return

        if len(self.pdf_doc) == 0:
            QMessageBox.warning(self, "Preview Unavailable", "The PDF contains no pages.")
            self.close()
            return

        self.render_page()


    def render_page(self):
        if not self.pdf_doc:
            return

        try:
            import fitz

            page = self.pdf_doc.load_page(self.current_page)
            matrix = fitz.Matrix(self.zoom, self.zoom)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            image = QImage(
                pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888
            )
            pixmap = QPixmap.fromImage(image.copy())
            self.image_label.setPixmap(pixmap)
            self.image_label.resize(pixmap.size())
            self.page_label.setText(f"Page {self.current_page + 1} of {len(self.pdf_doc)}")
        except Exception as exc:
            QMessageBox.critical(self, "Preview Failed", f"Could not display this page.\n{exc}")


    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.render_page()


    def next_page(self):
        if self.pdf_doc and self.current_page < len(self.pdf_doc) - 1:
            self.current_page += 1
            self.render_page()


    def zoom_out(self):
        self.zoom = max(0.5, self.zoom - 0.15)
        self.render_page()


    def zoom_in(self):
        self.zoom = min(2.5, self.zoom + 0.15)
        self.render_page()


    def closeEvent(self, event):
        try:
            if self.pdf_doc:
                self.pdf_doc.close()
        except Exception:
            pass
        event.accept()



class TextReportDialog(QDialog):

    def __init__(
        self,
        title,
        subtitle,
        report_text,
        parent=None,
        icon_name="document.svg",
        extra_action_text=None,
        extra_action_callback=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(780, 620)
        self.setStyleSheet(
            """
            QDialog {
                background: #E8F5FC;
                color: #142338;
                font-family: "Microsoft YaHei UI", "Segoe UI Variable Text", "Segoe UI", "Aptos", "Arial";
            }
            QFrame#dialogCard {
                background: #FFFFFF;
                border: 1px solid #D8E5F1;
                border-radius: 8px;
            }
            QLabel#dialogTitle {
                color: #142338;
                font-size: 24px;
                font-weight: 900;
            }
            QLabel#dialogSubtitle {
                color: #58708A;
                font-size: 13px;
                font-weight: 650;
            }
            QTextEdit#dialogText {
                background: #F8FCFF;
                color: #142338;
                border: 1px solid #D8E5F1;
                border-radius: 8px;
                padding: 14px;
                font-family: "Microsoft YaHei UI", "Segoe UI Variable Text", "Segoe UI", "Aptos", "Arial";
                font-size: 12px;
                line-height: 150%;
            }
            QPushButton#dialogPrimary {
                background: #2F80ED;
                color: #FFFFFF;
                border: none;
                border-radius: 0px;
                padding: 11px 18px;
                font-size: 13px;
                font-weight: 800;
            }
            QPushButton#dialogPrimary:hover {
                background: #1D6FE8;
            }
            QPushButton#dialogSecondary {
                background: #EEF7FF;
                color: #2F80ED;
                border: 1px solid #D8E5F1;
                border-radius: 0px;
                padding: 11px 18px;
                font-size: 13px;
                font-weight: 800;
            }
            QPushButton#dialogSecondary:hover {
                background: #E3F2FF;
            }
        """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 22, 22, 22)

        card = QFrame()
        card.setObjectName("dialogCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 20)
        card_layout.setSpacing(14)

        header = QHBoxLayout()
        icon = QLabel()
        icon.setFixedSize(54, 54)
        icon.setPixmap(make_icon(icon_name).pixmap(48, 48))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_box = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("dialogTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("dialogSubtitle")
        subtitle_label.setWordWrap(True)
        title_box.addWidget(title_label)
        title_box.addWidget(subtitle_label)

        header.addWidget(icon)
        header.addLayout(title_box, stretch=1)
        card_layout.addLayout(header)

        self.text_box = QTextEdit()
        self.text_box.setObjectName("dialogText")
        self.text_box.setReadOnly(True)
        if self.report_needs_error_highlight(report_text):
            self.text_box.setHtml(self.highlight_report_text(report_text))
        else:
            self.text_box.setPlainText(report_text)
        card_layout.addWidget(self.text_box, stretch=1)

        actions = QHBoxLayout()
        actions.addStretch()

        if extra_action_text and extra_action_callback:
            extra_btn = QPushButton(extra_action_text)
            extra_btn.setObjectName("dialogSecondary")


            def _run_extra_action():
                try:
                    extra_action_callback(self)
                except TypeError:
                    extra_action_callback()

            extra_btn.clicked.connect(_run_extra_action)
            actions.addWidget(extra_btn)

        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("dialogSecondary")
        copy_btn.clicked.connect(
            lambda: QApplication.clipboard().setText(self.text_box.toPlainText())
        )

        close_btn = QPushButton("Close")
        close_btn.setObjectName("dialogPrimary")
        close_btn.clicked.connect(self.accept)

        actions.addWidget(copy_btn)
        actions.addWidget(close_btn)
        card_layout.addLayout(actions)

        root.addWidget(card)


    def report_needs_error_highlight(self, text):
        lowered = str(text).lower()
        return any(
            word in lowered
            for word in [
                "error",
                "failed",
                "failure",
                "issues",
                "warning",
                "unmatched",
                "not identified",
            ]
        )


    def highlight_report_text(self, text):
        rows = []
        for raw_line in str(text).splitlines():
            line = html.escape(raw_line)
            lower = raw_line.lower()
            if any(
                word in lower
                for word in [
                    "error",
                    "failed",
                    "failure",
                    "issues",
                    "warning",
                    "unmatched",
                    "not identified",
                ]
            ):
                rows.append(f'<div style="color:#B42318; font-weight:700;">{line}</div>')
            else:
                rows.append(f'<div style="color:#142338;">{line}</div>')
        return (
            '<div style="font-family: Microsoft YaHei UI, Segoe UI, Arial; font-size:12px; line-height:1.55;">'
            + "".join(rows)
            + "</div>"
        )



class ThemedMessageDialog(QDialog):

    def __init__(self, title, message, parent=None, icon_name="document.svg", confirm=False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(560, 360)
        self.setStyleSheet(
            """
            QDialog {
                background: #E8F5FC;
                color: #142338;
                font-family: "Microsoft YaHei UI", "Segoe UI Variable Text", "Segoe UI", "Aptos", "Arial";
            }
            QFrame#messageCard {
                background: #FFFFFF;
                border: 1px solid #D8E5F1;
                border-radius: 8px;
            }
            QLabel#messageTitle {
                color: #111111;
                font-size: 22px;
                font-weight: 700;
            }
            QLabel#messageBody {
                color: #34495E;
                font-size: 13px;
                font-weight: 400;
                line-height: 150%;
            }
            QPushButton#messagePrimary {
                background: #0067C0;
                color: #FFFFFF;
                border: none;
                border-radius: 0px;
                padding: 10px 22px;
                font-size: 13px;
                font-weight: 600;
                min-width: 110px;
            }
            QPushButton#messagePrimary:hover { background: #005A9E; }
            QPushButton#messageSecondary {
                background: #E8F4FC;
                color: #0067C0;
                border: 1px solid #D5EAF8;
                border-radius: 0px;
                padding: 10px 22px;
                font-size: 13px;
                font-weight: 500;
                min-width: 110px;
            }
            QPushButton#messageSecondary:hover { background: #DDF0FB; }
        """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        card = QFrame()
        card.setObjectName("messageCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        header = QHBoxLayout()
        icon = QLabel()
        icon.setFixedSize(48, 48)
        icon.setPixmap(make_icon(icon_name).pixmap(42, 42))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        is_error = any(
            word in title.lower()
            for word in ("error", "failed", "missing", "required", "unavailable")
        )
        title_label = QLabel(title)
        title_label.setObjectName("messageTitle")
        title_label.setWordWrap(True)
        if is_error:
            title_label.setStyleSheet("color: #B42318;")
        header.addWidget(icon)
        header.addWidget(title_label, stretch=1)
        layout.addLayout(header)

        body = QLabel(str(message))
        body.setObjectName("messageBody")
        body.setWordWrap(True)
        if is_error:
            body.setStyleSheet("color: #B42318;")
        body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(body, stretch=1)

        actions = QHBoxLayout()
        actions.addStretch()
        if confirm:
            cancel_btn = QPushButton("Cancel")
            cancel_btn.setObjectName("messageSecondary")
            cancel_btn.clicked.connect(self.reject)
            actions.addWidget(cancel_btn)
            ok_text = "Continue"
        else:
            ok_text = "OK"
        ok_btn = QPushButton(ok_text)
        ok_btn.setObjectName("messagePrimary")
        ok_btn.clicked.connect(self.accept)
        actions.addWidget(ok_btn)
        layout.addLayout(actions)
        root.addWidget(card)



def open_pdf_with_system_viewer(pdf_path, parent=None):
    try:
        if sys.platform.startswith("win"):
            os.startfile(pdf_path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", pdf_path])
        else:
            subprocess.Popen(["xdg-open", pdf_path])
    except Exception as exc:
        QMessageBox.critical(parent, "Preview Failed", f"Could not open the PDF viewer.\n{exc}")



class DocumentFormatterWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Document Formatter")
        self.resize(1280, 820)
        self.setMinimumSize(980, 700)

        self.generation_queue = queue.Queue()
        self.preview_queue = queue.Queue()
        self.generation_running = False
        self.preview_running = False
        self.preview_dialogs = []
        self.sidebar_buttons = []
        self.sidebar_compact = False

        self.init_ui()
        self.apply_styles()
        self.select_page(0)

        self.timer = QTimer(self)
        self.timer.setInterval(130)
        self.timer.timeout.connect(self.tick_progress)


    def show_themed_message(self, title, message, icon_name="document.svg"):
        ThemedMessageDialog(title, message, self, icon_name, confirm=False).exec()


    def show_themed_error(self, title, message):
        ThemedMessageDialog(title, message, self, "shield.svg", confirm=False).exec()


    def show_themed_confirm(self, title, message):
        return (
            ThemedMessageDialog(title, message, self, "generate.svg", confirm=True).exec()
            == QDialog.DialogCode.Accepted
        )


    def build_app_menu(self):
        menu_bar = self.menuBar()
        menu_bar.setObjectName("appMenuBar")

        file_menu = menu_bar.addMenu("File")
        file_menu.addAction("Save Settings", self.save_configuration_action)
        file_menu.addAction("Import Settings", self.import_configuration_action)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        folders_menu = menu_bar.addMenu("Folders")
        folders_menu.addAction("Open Code Folder", self.open_code_folder_action)
        folders_menu.addAction("Open Image Folder", self.open_output_folder_action)
        folders_menu.addAction("Open Report Folder", self.open_final_folder_action)

        run_menu = menu_bar.addMenu("Run")
        run_menu.addAction("Preview Report", self.preview_action)
        run_menu.addAction("Generate Report", self.proceed_action)

        tools_menu = menu_bar.addMenu("Tools")
        tools_menu.addAction("Project Check", self.run_health_check_action)
        tools_menu.addAction("View Generation Summary", self.show_generation_summary_action)


    #build main window
    def init_ui(self):
        central = QWidget()
        central.setObjectName("app")
        self.setCentralWidget(central)
        self.build_app_menu()

        app_layout = QHBoxLayout(central)
        app_layout.setContentsMargins(22, 22, 22, 22)
        app_layout.setSpacing(20)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(275)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(18, 18, 18, 18)
        sidebar_layout.setSpacing(10)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(12)
        brand_row.setContentsMargins(0, 0, 0, 0)
        self.logo_circle = QLabel()
        self.logo_circle.setObjectName("logoCircle")
        self.logo_circle.setFixedSize(48, 48)
        self.logo_circle.setPixmap(make_icon("app.svg").pixmap(46, 46))
        self.logo_circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.brand_label = QLabel("Document\nFormatter")
        self.brand_label.setWordWrap(False)
        self.brand_label.setObjectName("brand")
        self.collapse_btn = QPushButton()
        self.collapse_btn.setObjectName("collapseButton")
        self.collapse_btn.setFixedSize(38, 38)
        self.collapse_btn.setIcon(make_icon("chevron-left.svg"))
        self.collapse_btn.setIconSize(QSize(20, 20))
        self.collapse_btn.setText("")
        self.collapse_btn.clicked.connect(self.toggle_sidebar)
        brand_row.addWidget(self.logo_circle)
        brand_row.addWidget(self.brand_label, stretch=1)
        brand_row.addWidget(self.collapse_btn)
        sidebar_layout.addLayout(brand_row)

        self.tagline = QLabel("Create clear, consistent reports")
        self.tagline.setObjectName("tagline")
        sidebar_layout.addWidget(self.tagline)

        menu_label = QLabel("NAVIGATION")
        menu_label.setObjectName("menuLabel")
        sidebar_layout.addWidget(menu_label)

        nav_items = [
            ("dashboard.svg", "Dashboard"),
            ("layout.svg", "Layout"),
            ("document.svg", "Cover & Contents"),
            ("code.svg", "Code"),
            ("figures.svg", "Output Images"),
            ("watermark.svg", "Watermark"),
            ("generate.svg", "Generate"),
        ]

        for index, (icon, label) in enumerate(nav_items):
            btn = SidebarButton(icon, label)
            btn.clicked.connect(lambda checked=False, i=index: self.select_page(i))
            self.sidebar_buttons.append(btn)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        app_layout.addWidget(self.sidebar)

        self.main_panel = QFrame()
        self.main_panel.setObjectName("mainPanel")
        main_layout = QVBoxLayout(self.main_panel)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.header = QFrame()
        self.header.setObjectName("topHeader")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(28, 22, 28, 14)

        self.page_icon = QLabel()
        self.page_icon.setObjectName("pageIcon")
        self.page_icon.setFixedSize(62, 62)
        self.page_icon.setPixmap(make_icon("dashboard.svg").pixmap(48, 48))
        self.page_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.page_icon)

        title_block = QVBoxLayout()
        self.page_title = QLabel("Dashboard")
        self.page_title.setObjectName("pageTitle")
        self.page_subtitle = QLabel("Set up, preview, and generate your report.")
        self.page_subtitle.setObjectName("pageSubtitle")
        title_block.addWidget(self.page_title)
        title_block.addWidget(self.page_subtitle)

        self.quick_preview_btn = QPushButton("Preview Report")
        self.quick_preview_btn.setObjectName("secondaryButton")
        self.quick_preview_btn.setMinimumHeight(50)
        self.quick_preview_btn.setIcon(make_icon("preview.svg"))
        self.quick_preview_btn.setIconSize(QSize(22, 22))
        self.quick_preview_btn.clicked.connect(self.preview_action)

        self.quick_proceed_btn = QPushButton("Generate Report")
        self.quick_proceed_btn.setObjectName("primaryButton")
        self.quick_proceed_btn.setMinimumHeight(50)
        self.quick_proceed_btn.setIcon(make_icon("proceed.svg"))
        self.quick_proceed_btn.setIconSize(QSize(22, 22))
        self.quick_proceed_btn.clicked.connect(self.handle_primary_header_action)

        header_layout.addLayout(title_block)
        header_layout.addStretch()
        header_layout.addWidget(self.quick_preview_btn)
        header_layout.addWidget(self.quick_proceed_btn)

        main_layout.addWidget(self.header)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack, stretch=1)

        app_layout.addWidget(self.main_panel, stretch=1)

        self.build_pages()


    def toggle_sidebar(self):
        self.sidebar_compact = not self.sidebar_compact
        compact = self.sidebar_compact
        self.sidebar.setFixedWidth(86 if compact else 275)
        self.brand_label.setVisible(not compact)
        self.tagline.setVisible(not compact)
        self.collapse_btn.setIcon(make_icon("chevron-right.svg" if compact else "chevron-left.svg"))
        for btn in self.sidebar_buttons:
            btn.set_compact(compact)


    def make_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("contentScroll")
        body = QWidget()
        body.setObjectName("pageBody")
        layout = QVBoxLayout(body)
        layout.setContentsMargins(28, 18, 28, 30)
        layout.setSpacing(16)
        scroll.setWidget(body)
        self.stack.addWidget(scroll)
        return layout


    def card(self, layout, title, subtitle=None):
        frame = QFrame()
        frame.setObjectName("card")
        card_layout = QVBoxLayout(frame)
        card_layout.setContentsMargins(22, 18, 22, 20)
        card_layout.setSpacing(13)

        icon_name = CONTENT_ICON_MAP.get(title)
        if icon_name:
            header = QHBoxLayout()
            header.setSpacing(10)
            icon_label = QLabel()
            icon_label.setObjectName("contentSectionIcon")
            icon_label.setFixedSize(34, 34)
            icon_label.setPixmap(make_icon(icon_name).pixmap(28, 28))
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label = QLabel(title)
            label.setObjectName("sectionTitle")
            header.addWidget(icon_label)
            header.addWidget(label)
            header.addStretch()
            card_layout.addLayout(header)
        else:
            label = QLabel(title)
            label.setObjectName("sectionTitle")
            card_layout.addWidget(label)

        if subtitle:
            sub = QLabel(subtitle)
            sub.setObjectName("sectionSubtitle")
            sub.setWordWrap(True)
            card_layout.addWidget(sub)
        layout.addWidget(frame)
        return frame, card_layout


    def build_pages(self):
        self.build_dashboard_page()
        self.build_layout_page()
        self.build_cover_toc_page()
        self.build_code_page()
        self.build_figures_page()
        self.build_watermark_page()
        self.build_generate_page()
        self.update_section_enabled_states()


    def metric_card(self, title, value, hint):
        frame = QFrame()
        frame.setObjectName("metricCard")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(18, 16, 18, 16)
        icon_name = METRIC_ICON_MAP.get(value) or METRIC_ICON_MAP.get(title)
        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        if icon_name:
            icon_label = QLabel()
            icon_label.setObjectName("metricIcon")
            icon_label.setFixedSize(36, 36)
            icon_label.setPixmap(make_icon(icon_name).pixmap(28, 28))
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            top_row.addWidget(icon_label)
        value_label = QLabel(value)
        value_label.setObjectName("metricValue")
        top_row.addWidget(value_label)
        top_row.addStretch()
        title_label = QLabel(title)
        title_label.setObjectName("metricTitle")
        hint_label = QLabel(hint)
        hint_label.setObjectName("metricHint")
        hint_label.setWordWrap(True)
        lay.addLayout(top_row)
        lay.addWidget(title_label)
        lay.addWidget(hint_label)
        return frame


    def tool_button(self, text, callback, primary=False):
        button = QPushButton(text)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setObjectName("primaryButtonLarge" if primary else "secondaryButtonLarge")
        button.setMinimumHeight(46)
        icon_name = TOOL_BUTTON_ICON_MAP.get(text)
        if icon_name:
            button.setIcon(make_icon(icon_name))
            button.setIconSize(QSize(20, 20))
        button.clicked.connect(callback)
        return button


    def dashboard_action_button(self, title, description, callback):
        button = QPushButton(f"{title}\n{description}")
        button.setObjectName("dashboardActionButton")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setMinimumHeight(78)
        icon_name = ACTION_ICON_MAP.get(title)
        if icon_name:
            button.setIcon(make_icon(icon_name))
            button.setIconSize(QSize(24, 24))
        button.clicked.connect(callback)
        return button


    def build_dashboard_page(self):
        layout = self.make_page()

        hero = QFrame()
        hero.setObjectName("dashboardHero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(30, 28, 30, 28)
        hero_layout.setSpacing(24)

        hero_text = QVBoxLayout()
        hero_text.setSpacing(10)

        eyebrow = QLabel("REPORT GENERATOR")
        eyebrow.setObjectName("dashboardEyebrow")

        h1 = QLabel("Create a clear, professional report")
        h1.setObjectName("dashboardHeroTitle")
        h1.setWordWrap(True)

        h2 = QLabel(
            "Set the layout and content, review a preview, and export the final PDF."
        )
        h2.setObjectName("dashboardHeroSubtitle")
        h2.setWordWrap(True)

        hero_text.addWidget(eyebrow)
        hero_text.addWidget(h1)
        hero_text.addWidget(h2)

        hero_actions = QVBoxLayout()
        hero_actions.setSpacing(10)
        start_btn = QPushButton("Start")
        start_btn.setObjectName("dashboardPrimaryButton")
        start_btn.setMinimumHeight(44)
        start_btn.setIcon(make_icon("next.svg"))
        start_btn.setIconSize(QSize(20, 20))
        start_btn.clicked.connect(lambda: self.select_page(1))

        preview_btn = QPushButton("Preview Report")
        preview_btn.setObjectName("dashboardSecondaryButton")
        preview_btn.setMinimumHeight(42)
        preview_btn.clicked.connect(self.preview_action)

        dashboard_proceed_btn = QPushButton("Generate Report")
        dashboard_proceed_btn.setObjectName("dashboardPrimaryButton")
        dashboard_proceed_btn.setMinimumHeight(44)
        dashboard_proceed_btn.setIcon(make_icon("proceed.svg"))
        dashboard_proceed_btn.setIconSize(QSize(20, 20))
        dashboard_proceed_btn.clicked.connect(self.proceed_action)

        hero_actions.addStretch()
        hero_actions.addWidget(start_btn)
        hero_actions.addWidget(preview_btn)
        hero_actions.addWidget(dashboard_proceed_btn)
        hero_actions.addStretch()

        hero_layout.addLayout(hero_text, stretch=1)
        hero_layout.addLayout(hero_actions)
        layout.addWidget(hero)

        quick_card, quick_layout = self.card(
            layout,
            "Quick Actions",
            "Access common report tools.",
        )

        actions_grid = QGridLayout()
        actions_grid.setSpacing(12)

        self.dashboard_health_btn = self.dashboard_action_button(
            "Project Check",
            "Check folders, files, and report settings.",
            self.run_health_check_action,
        )
        self.dashboard_summary_btn = self.dashboard_action_button(
            "Generation Summary",
            "View details from the latest generated report.",
            self.show_generation_summary_action,
        )
        self.dashboard_history_btn = self.dashboard_action_button(
            "Report History",
            "View previously generated reports.",
            self.show_generated_project_history_action,
        )
        captions_btn = self.dashboard_action_button(
            "Manage Captions",
            "Review captions for output images.",
            lambda: self.select_page(4),
        )

        actions_grid.addWidget(self.dashboard_health_btn, 0, 0)
        actions_grid.addWidget(self.dashboard_summary_btn, 0, 1)
        actions_grid.addWidget(self.dashboard_history_btn, 1, 0)
        actions_grid.addWidget(captions_btn, 1, 1)
        quick_layout.addLayout(actions_grid)

        overview_grid = QGridLayout()
        overview_grid.setSpacing(12)
        overview_grid.addWidget(
            self.metric_card("Step 1", "Layout", "Set margins, font, and export format."), 0, 0
        )
        overview_grid.addWidget(
            self.metric_card(
                "Step 2",
                "Content",
                "Add cover details, contents, code, images, and watermark.",
            ),
            0,
            1,
        )
        overview_grid.addWidget(
            self.metric_card(
                "Step 3", "Generate", "Review a preview, then export the final PDF."
            ),
            0,
            2,
        )
        layout.addLayout(overview_grid)

        _, workflow_layout = self.card(
            layout,
            "Workflow",
            "Complete these steps in order.",
        )
        steps = QLabel(
            "1. Set the layout.\n2. Add report content.\n3. Run Project Check.\n4. Preview the report.\n5. Generate the final PDF."
        )
        steps.setObjectName("bodyText")
        steps.setWordWrap(True)
        workflow_layout.addWidget(steps)

        layout.addStretch()


    def build_layout_page(self):
        layout = self.make_page()
        _, margin_layout = self.card(
            layout, "Margins", "Use the default margins or enter values in points. 72 points = 1 inch."
        )
        grid = QGridLayout()
        grid.setSpacing(14)
        self.margin_top = self.compact_input("Top", "10")
        self.margin_bottom = self.compact_input("Bottom", "20")
        self.margin_left = self.compact_input("Left", "30")
        self.margin_right = self.compact_input("Right", "40")
        grid.addWidget(self.margin_top["container"], 0, 0)
        grid.addWidget(self.margin_bottom["container"], 0, 1)
        grid.addWidget(self.margin_left["container"], 0, 2)
        grid.addWidget(self.margin_right["container"], 0, 3)
        margin_layout.addLayout(grid)
        self.default_margin = self.switch_row(margin_layout, "Use default margins", True)
        _, font_layout = self.card(
            layout, "Font", "Select the font used in the report."
        )
        self.font_combo = ModernComboBox(["Times New Roman", "Arial"])
        font_layout.addWidget(self.font_combo)
        _, export_layout = self.card(layout, "Export Format", "PDF is the available export format.")
        self.export_combo = ModernComboBox(["PDF"])
        export_layout.addWidget(self.export_combo)
        layout.addStretch()


    def build_figures_page(self):
        layout = self.make_page()
        _, fig_layout = self.card(
            layout,
            "Output Images",
            "Choose the folder that contains output images and set the caption options.",
        )

        self.output_after_code = self.switch_row(fig_layout, "Place Output After Code", False)
        self.output_after_code.toggled.connect(self.on_output_after_code_toggled)

        self.output_folder_path = imageDir
        self.output_folder_row = QFrame()
        self.output_folder_row.setObjectName("folderSelectRow")
        output_folder_layout = QHBoxLayout(self.output_folder_row)
        output_folder_layout.setContentsMargins(18, 0, 0, 0)
        output_folder_layout.setSpacing(12)
        self.output_folder_label = QLabel(f"Image folder: {self.output_folder_path}")
        self.output_folder_label.setObjectName("bodyText")
        self.output_folder_label.setWordWrap(True)
        self.browse_output_folder_btn = self.tool_button(
            "Choose Image Folder", self.browse_output_folder_action
        )
        output_folder_layout.addWidget(self.output_folder_label, stretch=1)
        output_folder_layout.addWidget(self.browse_output_folder_btn)
        fig_layout.addWidget(self.output_folder_row)

        self.include_figure = self.switch_row(fig_layout, "Show figure numbers", False)

        caption_mode_label = QLabel("Caption Style")
        caption_mode_label.setObjectName("fieldLabel")
        fig_layout.addWidget(caption_mode_label)
        self.caption_mode_combo = ModernComboBox(
            [
                CAPTION_MODE_NONE,
                CAPTION_MODE_CUSTOM_OUTPUT,
                CAPTION_MODE_MATCH_FILENAME,
            ]
        )
        self.caption_mode_combo.on_change = self.update_caption_table_visibility
        fig_layout.addWidget(self.caption_mode_combo)

        note = QLabel(
            "Images are added directly from the selected folder."
        )
        note.setObjectName("bodyText")
        note.setWordWrap(True)
        fig_layout.addWidget(note)

        self.generate_output_pages = self.switch_row(fig_layout, "Include output images", False)
        self.generate_output_pages.toggled.connect(self.on_generate_output_pages_toggled)

        self.caption_card, caption_layout = self.card(
            layout,
            "Manual Captions",
            "Enter a caption for each image. Captions are saved before preview and generation.",
        )

        self.caption_table = QFrame()
        self.caption_table.setObjectName("captionTableFrame")
        self.caption_table_layout = QVBoxLayout(self.caption_table)
        self.caption_table_layout.setContentsMargins(0, 0, 0, 0)
        self.caption_table_layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("captionHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 0, 18, 0)
        header_layout.setSpacing(0)

        output_header = QLabel("Image File")
        output_header.setObjectName("captionHeaderLabel")
        output_header.setFixedWidth(230)

        divider = QFrame()
        divider.setObjectName("captionDivider")
        divider.setFixedWidth(1)

        caption_header = QLabel("Caption")
        caption_header.setObjectName("captionHeaderLabel")
        caption_header.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout.addWidget(output_header)
        header_layout.addWidget(divider)
        header_layout.addWidget(caption_header, stretch=1)
        self.caption_table_layout.addWidget(header)

        self.caption_rows_container = QWidget()
        self.caption_rows_container.setObjectName("captionRowsContainer")
        self.caption_rows_layout = QVBoxLayout(self.caption_rows_container)
        self.caption_rows_layout.setContentsMargins(0, 0, 0, 0)
        self.caption_rows_layout.setSpacing(0)

        self.caption_scroll = QScrollArea()
        self.caption_scroll.setObjectName("captionScroll")
        self.caption_scroll.setWidgetResizable(True)
        self.caption_scroll.setMinimumHeight(300)
        self.caption_scroll.setWidget(self.caption_rows_container)
        self.caption_table_layout.addWidget(self.caption_scroll)

        self.caption_rows = []
        caption_layout.addWidget(self.caption_table)

        caption_actions = QHBoxLayout()
        self.refresh_captions_btn = self.tool_button(
            "Refresh Images", self.refresh_caption_table
        )
        self.save_captions_btn = self.tool_button("Save Captions", self.save_output_captions)
        self.clear_captions_btn = self.tool_button("Clear Captions", self.clear_output_captions)
        self.clear_captions_btn.setIcon(make_icon("clear.svg"))
        self.clear_captions_btn.setIconSize(QSize(20, 20))
        caption_actions.addWidget(self.refresh_captions_btn)
        caption_actions.addWidget(self.save_captions_btn)
        caption_actions.addWidget(self.clear_captions_btn)
        caption_layout.addLayout(caption_actions)
        self.caption_save_status = QLabel("")
        self.caption_save_status.setObjectName("bodyText")
        self.caption_save_status.setWordWrap(True)
        self.caption_save_status.setStyleSheet(
            "color: #027A48; font-size: 12px; font-weight: 600;"
        )
        caption_layout.addWidget(self.caption_save_status)
        self.refresh_caption_table(show_message=False)
        self.update_caption_table_visibility()
        layout.addStretch()


    def build_cover_toc_page(self):
        layout = self.make_page()
        _, cover_layout = self.card(
            layout, "Cover Page", "Enter the information shown on the cover page."
        )
        self.college_name = self.input_row(
            cover_layout, "College Name", PLACEHOLDERS["college_name"]
        )
        self.college_name.setText(DEFAULT_COLLEGE_NAME)
        self.college_address = self.input_row(
            cover_layout, "Address", PLACEHOLDERS["college_address"]
        )
        self.college_address.setText(DEFAULT_COLLEGE_ADDRESS)
        self.student_name = self.input_row(
            cover_layout, "Student Name", PLACEHOLDERS["student_name"]
        )
        self.roll = self.input_row(cover_layout, "Roll Number", PLACEHOLDERS["roll"])
        self.section_entry = self.input_row(cover_layout, "Section", PLACEHOLDERS["section"])
        self.semester = self.input_row(cover_layout, "Semester", PLACEHOLDERS["semester"])
        self.teacher_name = self.input_row(
            cover_layout, "Teacher Name", PLACEHOLDERS["teacher_name"]
        )
        self.project_title = self.input_row(
            cover_layout, "Project Title", PLACEHOLDERS["project_title"]
        )
        self.logo_selected = os.path.exists(os.path.join(baseDir, "logo.png"))
        logo_actions = QHBoxLayout()
        self.logo_status_label = QLabel(
            "Current logo: logo.png"
            if self.logo_selected
            else "No logo selected."
        )
        self.logo_status_label.setObjectName("bodyText")
        self.logo_status_label.setWordWrap(True)
        self.add_logo_btn = self.tool_button("Add Logo", self.add_logo_action)
        self.add_logo_btn.setIcon(make_icon("logo-upload.svg"))
        self.add_logo_btn.setIconSize(QSize(20, 20))
        logo_actions.addWidget(self.logo_status_label, stretch=1)
        logo_actions.addWidget(self.add_logo_btn)
        cover_layout.addLayout(logo_actions)
        self.cover_validation_status = QLabel("")
        self.cover_validation_status.setObjectName("bodyText")
        self.cover_validation_status.setWordWrap(True)
        self.cover_validation_status.setStyleSheet(
            "color: #64748b; font-size: 12px; font-weight: 500;"
        )
        cover_layout.addWidget(self.cover_validation_status)
        self.generate_cover = self.switch_row(cover_layout, "Include cover page", False)
        self.generate_cover.toggled.connect(self.on_generate_cover_toggled)

        for cover_widget in [
            self.college_name,
            self.college_address,
            self.student_name,
            self.roll,
            self.section_entry,
            self.semester,
            self.teacher_name,
            self.project_title,
        ]:
            cover_widget.textChanged.connect(self.update_cover_generate_state)
        self.update_cover_generate_state()

        _, toc_layout = self.card(
            layout, "Table of Contents", "Create the table of contents manually or import a TXT or DOCX file."
        )

        toc_mode_label = QLabel("Contents Source")
        toc_mode_label.setObjectName("fieldLabel")
        toc_layout.addWidget(toc_mode_label)
        self.toc_mode_combo = ModernComboBox([TOC_MODE_MANUAL, TOC_MODE_BROWSE])
        self.toc_mode_combo.on_change = self.update_toc_mode_visibility
        toc_layout.addWidget(self.toc_mode_combo)

        self.toc_manual_container = QFrame()
        self.toc_manual_container.setObjectName("tocManualContainer")
        manual_layout = QVBoxLayout(self.toc_manual_container)
        manual_layout.setContentsMargins(0, 0, 0, 0)
        manual_layout.setSpacing(8)
        self.toc_text = QTextEdit()
        self.toc_text.setObjectName("textArea")
        self.toc_text.setMinimumHeight(190)
        self.toc_text.setPlaceholderText(PLACEHOLDERS["toc"])
        manual_layout.addWidget(self.toc_text)
        self.toc_manual_status = QLabel("")
        self.toc_manual_status.setObjectName("bodyText")
        self.toc_manual_status.setWordWrap(True)
        self.toc_manual_status.setStyleSheet("color: #64748b; font-size: 12px; font-weight: 500;")
        manual_layout.addWidget(self.toc_manual_status)
        self.toc_text.textChanged.connect(self.update_toc_generate_state)
        toc_layout.addWidget(self.toc_manual_container)

        self.toc_browse_container = QFrame()
        self.toc_browse_container.setObjectName("tocBrowseContainer")
        browse_layout = QVBoxLayout(self.toc_browse_container)
        browse_layout.setContentsMargins(0, 0, 0, 0)
        browse_layout.setSpacing(10)

        browse_row = QHBoxLayout()
        self.toc_file_label = QLabel("No file selected.")
        self.toc_file_label.setObjectName("bodyText")
        self.toc_file_label.setWordWrap(True)
        self.toc_file_path = ""
        self.browse_toc_btn = self.tool_button("Choose Contents File", self.browse_toc_file_action)
        browse_row.addWidget(self.toc_file_label, stretch=1)
        browse_row.addWidget(self.browse_toc_btn)
        browse_layout.addLayout(browse_row)

        toc_layout.addWidget(self.toc_browse_container)

        self.keep_toc_label_row = QFrame()
        self.keep_toc_label_row.setObjectName("switchRow")
        keep_row = QHBoxLayout(self.keep_toc_label_row)
        keep_row.setContentsMargins(18, 13, 18, 13)
        keep_label = QLabel("Keep existing numbering")
        keep_label.setObjectName("fieldLabel")
        self.keep_toc_label = ToggleSwitch(checked=True)
        self.keep_toc_label.toggled.connect(self.update_toc_generate_state)
        keep_row.addWidget(keep_label)
        keep_row.addStretch()
        keep_row.addWidget(self.keep_toc_label)
        toc_layout.addWidget(self.keep_toc_label_row)

        hint = QLabel(
            "Keep labels such as 1), 2.1), or Lab 1. Entries without labels are numbered automatically."
        )
        hint.setObjectName("bodyText")
        hint.setWordWrap(True)
        toc_layout.addWidget(hint)

        self.toc_label_status = QLabel("")
        self.toc_label_status.setObjectName("bodyText")
        self.toc_label_status.setWordWrap(True)
        self.toc_label_status.setStyleSheet("color: #64748b; font-size: 12px; font-weight: 500;")
        toc_layout.addWidget(self.toc_label_status)

        self.generate_toc = self.switch_row(toc_layout, "Include table of contents", False)
        self.generate_toc.toggled.connect(self.on_generate_toc_toggled)
        self.update_toc_mode_visibility()
        self.update_toc_generate_state()
        layout.addStretch()


    def build_code_page(self):
        layout = self.make_page()
        _, code_layout = self.card(
            layout, "Code Page", "Choose the source-code folder and set the line height."
        )
        self.code_line_height = self.input_row(
            code_layout, "Line Height (points)", PLACEHOLDERS["code_line_height"]
        )
        self.code_line_height_status = QLabel("")
        self.code_line_height_status.setObjectName("bodyText")
        self.code_line_height_status.setWordWrap(True)
        code_layout.addWidget(self.code_line_height_status)

        self.code_file_ext = QLineEdit()
        self.code_file_ext.setVisible(False)
        self.code_file_ext.setText("")

        self.code_folder_path = codeDir
        self.code_folder_row = QFrame()
        self.code_folder_row.setObjectName("folderSelectRow")
        code_folder_layout = QHBoxLayout(self.code_folder_row)
        code_folder_layout.setContentsMargins(18, 0, 0, 0)
        code_folder_layout.setSpacing(12)
        self.code_folder_label = QLabel(f"Code folder: {self.code_folder_path}")
        self.code_folder_label.setObjectName("bodyText")
        self.code_folder_label.setWordWrap(True)
        self.browse_code_folder_btn = self.tool_button(
            "Choose Code Folder", self.browse_code_folder_action
        )
        code_folder_layout.addWidget(self.code_folder_label, stretch=1)
        code_folder_layout.addWidget(self.browse_code_folder_btn)
        code_layout.addWidget(self.code_folder_row)

        self.code_file_status = QLabel(
            "Scans supported source-code and text files in this folder and its subfolders."
        )
        self.code_file_status.setObjectName("bodyText")
        self.code_file_status.setWordWrap(True)
        self.code_file_status.setStyleSheet("color: #64748b; font-size: 12px; font-weight: 500;")
        code_layout.addWidget(self.code_file_status)
        self.generate_code_page = self.switch_row(code_layout, "Include code pages", False)
        self.generate_code_page.toggled.connect(self.on_generate_code_toggled)
        self.code_line_height.textChanged.connect(self.update_code_generate_state)
        self.update_code_generate_state()
        layout.addStretch()


    def build_watermark_page(self):
        layout = self.make_page()
        _, wm_layout = self.card(
            layout,
            "Watermark",
            "Add a watermark to report pages.",
        )
        self.watermark_name = self.input_row(wm_layout, "Watermark Text", PLACEHOLDERS["watermark_name"])
        self.watermark_validation_status = QLabel("")
        self.watermark_validation_status.setObjectName("bodyText")
        self.watermark_validation_status.setWordWrap(True)
        self.watermark_validation_status.setStyleSheet(
            "color: #64748b; font-size: 12px; font-weight: 500;"
        )
        wm_layout.addWidget(self.watermark_validation_status)
        self.generate_watermark = self.switch_row(wm_layout, "Include watermark", False)
        self.generate_watermark.toggled.connect(self.on_generate_watermark_toggled)
        self.watermark_name.textChanged.connect(self.update_watermark_generate_state)
        self.update_watermark_generate_state()
        _, note_layout = self.card(layout, "Watermark Coverage", "Applied to report pages except the cover and table of contents.")
        note = QLabel(
            "The cover page and table of contents are not watermarked."
        )
        note.setObjectName("bodyText")
        note.setWordWrap(True)
        note_layout.addWidget(note)
        layout.addStretch()


    def build_generate_page(self):
        layout = self.make_page()
        _, progress_layout = self.card(
            layout,
            "Report Generation",
            "Preview the report or generate the final PDF.",
        )
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("status")
        progress_layout.addWidget(self.status_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMinimumHeight(13)
        self.progress_bar.setObjectName("progress")
        progress_layout.addWidget(self.progress_bar)
        actions = QHBoxLayout()
        self.preview_btn = QPushButton("Preview Report")
        self.preview_btn.setObjectName("secondaryButtonLarge")
        self.preview_btn.setMinimumHeight(52)
        self.preview_btn.setIcon(make_icon("preview.svg"))
        self.preview_btn.setIconSize(QSize(22, 22))
        self.preview_btn.clicked.connect(self.preview_action)
        self.proceed_btn = QPushButton("Generate Report")
        self.proceed_btn.setObjectName("primaryButtonLarge")
        self.proceed_btn.setMinimumHeight(52)
        self.proceed_btn.setIcon(make_icon("proceed.svg"))
        self.proceed_btn.setIconSize(QSize(22, 22))
        self.proceed_btn.clicked.connect(self.proceed_action)
        actions.addWidget(self.preview_btn)
        actions.addWidget(self.proceed_btn)
        progress_layout.addLayout(actions)

        self.log_box = QTextEdit()
        self.log_box.setObjectName("logBox")
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(230)
        self.log_box.setPlainText("Progress messages will appear here.\n")
        progress_layout.addWidget(self.log_box)

        _, save_layout = self.card(
            layout,
            "Save Location",
            "Choose the file name and location for the final report.",
        )
        self.final_report_path = finalPdfPath
        self.final_report_row = QFrame()
        self.final_report_row.setObjectName("folderSelectRow")
        final_report_layout = QHBoxLayout(self.final_report_row)
        final_report_layout.setContentsMargins(18, 0, 0, 0)
        final_report_layout.setSpacing(12)
        self.final_report_path_label = QLabel(f"Save as: {self.selected_final_report_path()}")
        self.final_report_path_label.setObjectName("bodyText")
        self.final_report_path_label.setWordWrap(True)
        self.browse_final_report_btn = self.tool_button(
            "Choose Save Location", self.browse_final_report_path_action
        )
        final_report_layout.addWidget(self.final_report_path_label, stretch=1)
        final_report_layout.addWidget(self.browse_final_report_btn)
        save_layout.addWidget(self.final_report_row)
        layout.addStretch()


    def compact_input(self, label, value):
        box = QFrame()
        box.setObjectName("compactInputBox")
        lay = QVBoxLayout(box)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(7)
        lab = QLabel(label)
        lab.setObjectName("miniLabel")
        entry = QLineEdit(value)
        entry.setObjectName("compactInput")
        entry.setMinimumHeight(38)
        lay.addWidget(lab)
        lay.addWidget(entry)
        return {"container": box, "entry": entry}


    def switch_row(self, layout, text, default=False):
        row_widget = QFrame()
        row_widget.setObjectName("switchRow")
        row = QHBoxLayout(row_widget)
        row.setContentsMargins(18, 13, 18, 13)
        row.setSpacing(12)
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        switch = ToggleSwitch(checked=default)
        row.addWidget(label)
        row.addStretch()
        row.addWidget(switch)
        layout.addWidget(row_widget)
        return switch


    def input_row(self, layout, label, placeholder=""):
        row = QHBoxLayout()
        row.setSpacing(14)
        lab = QLabel(label)
        lab.setObjectName("fieldLabel")
        lab.setFixedWidth(155)
        entry = QLineEdit()
        entry.setPlaceholderText(placeholder)
        entry.setMinimumHeight(44)
        entry.setObjectName("input")
        row.addWidget(lab)
        row.addWidget(entry)
        layout.addLayout(row)
        return entry


    def select_page(self, index):
        titles = [
            ("dashboard.svg", "Dashboard", "Create and manage your report."),
            ("layout.svg", "Layout", "Set margins, font, and export format."),
            ("document.svg", "Cover & Contents", "Configure the cover page and table of contents."),
            ("code.svg", "Code", "Select source files and code-page settings."),
            ("figures.svg", "Output Images", "Select images and caption options."),
            ("watermark.svg", "Watermark", "Set watermark text and coverage."),
            ("generate.svg", "Generate", "Preview or generate the final PDF."),
        ]
        self.stack.setCurrentIndex(index)
        self.page_icon.setPixmap(make_icon(titles[index][0]).pixmap(48, 48))
        self.page_title.setText(titles[index][1])
        self.page_subtitle.setText(titles[index][2])
        if hasattr(self, "quick_proceed_btn"):
            self.quick_proceed_btn.setText("Start" if index == 0 else "Generate Report")
        for i, btn in enumerate(self.sidebar_buttons):
            btn.setChecked(i == index)


    def apply_styles(self):
        self.setStyleSheet(
            """

            QMenuBar#appMenuBar {
                background: #F6FBFE;
                color: #202020;
                border-bottom: 1px solid #DCE7EF;
                padding: 3px 8px;
                font-size: 12px;
                font-weight: 400;
            }
            QMenuBar#appMenuBar::item {
                background: transparent;
                border-radius: 6px;
                padding: 5px 10px;
                margin: 1px;
            }
            QMenuBar#appMenuBar::item:selected {
                background: #E5F2FB;
                color: #0067C0;
            }
            QMenu {
                background: #FFFFFF;
                color: #142338;
                border: 1px solid #BFD4E8;
                border-radius: 10px;
                padding: 6px;
                font-size: 13px;
                font-weight: 650;
            }
            QMenu::item {
                min-height: 30px;
                padding: 8px 24px;
                border-radius: 8px;
            }
            QMenu::item:selected {
                background: #EAF6FF;
                color: #1267C4;
            }
            QMenu::separator {
                height: 1px;
                background: #E1ECF6;
                margin: 6px 8px;
            }

            QTableWidget#captionTable {
                background: #FFFFFF;
                alternate-background-color: #F7FBFF;
                color: #111111;
                border: 1px solid #D5E2EC;
                border-radius: 8px;
                gridline-color: transparent;
                selection-background-color: #DDEEFF;
                selection-color: #005FB8;
                font-size: 13px;
                font-weight: 500;
            }
            QTableWidget#captionTable::item {
                padding: 10px;
                border-bottom: 1px solid #E6EEF7;
            }
            QTableWidget#captionTable::item:selected {
                background: #D9ECFF;
                color: #0B4C94;
            }
            QHeaderView::section {
                background: #F1F7FC;
                color: #202020;
                border: none;
                border-right: 1px solid #D5E2EC;
                border-bottom: 1px solid #D5E2EC;
                padding: 10px;
                font-size: 13px;
                font-weight: 600;
            }


            QPushButton#heroPrimaryButtonFlat {
                background: #0067C0;
                color: #FFFFFF;
                border: none;
                border-radius: 0px;
                font-size: 13px;
                font-weight: 600;
                padding: 8px 18px;
            }
            QPushButton#heroPrimaryButtonFlat:hover {
                background: #005A9E;
            }

            QFrame#captionTableFrame {
                background: #FFFFFF;
                border: 1px solid #D5E2EC;
                border-radius: 0px;
            }
            QFrame#captionHeader {
                background: #F1F7FC;
                border-bottom: 1px solid #D5E2EC;
                min-height: 44px;
            }
            QLabel#captionHeaderLabel {
                color: #111111;
                font-size: 13px;
                font-weight: 600;
                padding: 0px 12px;
            }
            QFrame#captionDivider {
                background: #D5E2EC;
                min-width: 1px;
                max-width: 1px;
            }
            QScrollArea#captionScroll {
                background: #FFFFFF;
                border: none;
            }
            QWidget#captionRowsContainer {
                background: #FFFFFF;
            }
            QFrame#captionRow {
                background: #FFFFFF;
                border-bottom: 1px solid #E6EEF7;
                min-height: 46px;
            }
            QLabel#captionFileLabel {
                color: #111111;
                font-size: 13px;
                font-weight: 500;
                padding: 0px 12px;
            }
            QLineEdit#captionEntry {
                background: transparent;
                color: #111111;
                border: none;
                padding: 8px 12px;
                font-size: 13px;
                font-weight: 400;
            }
            QLineEdit#captionEntry:focus {
                background: #F7FBFF;
                border: none;
            }


            QFrame#dashboardHero {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #EAF6FF, stop:1 #FFFFFF);
                border: 1px solid #D8E8F4;
                border-radius: 8px;
            }
            QLabel#dashboardEyebrow {
                color: #0067C0;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1.1px;
            }
            QLabel#dashboardHeroTitle {
                color: #111111;
                font-size: 27px;
                font-weight: 600;
                line-height: 120%;
            }
            QLabel#dashboardHeroSubtitle {
                color: #4F5F6F;
                font-size: 13px;
                font-weight: 400;
                line-height: 150%;
            }
            QPushButton#dashboardPrimaryButton {
                background: #0067C0;
                color: #FFFFFF;
                border: none;
                border-radius: 0px;
                font-size: 13px;
                font-weight: 600;
                padding: 8px 22px;
                min-width: 150px;
            }
            QPushButton#dashboardPrimaryButton:hover {
                background: #005A9E;
            }
            QPushButton#dashboardSecondaryButton {
                background: #E8F4FC;
                color: #0067C0;
                border: 1px solid #D5EAF8;
                border-radius: 0px;
                font-size: 13px;
                font-weight: 500;
                padding: 8px 22px;
                min-width: 150px;
            }
            QPushButton#dashboardSecondaryButton:hover {
                background: #DDF0FB;
            }
            QPushButton#dashboardActionButton {
                icon-size: 24px;
                background: #FFFFFF;
                color: #111111;
                border: 1px solid #DDE8F0;
                border-radius: 0px;
                text-align: left;
                padding: 12px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton#dashboardActionButton:hover {
                background: #F4FAFF;
                border: 1px solid #BBDDF3;
                color: #005FB8;
            }


            QLabel#contentSectionIcon {
                background: #EEF7FF;
                border: 1px solid #D8E8F4;
                border-radius: 0px;
                qproperty-alignment: AlignCenter;
            }
            QLabel#metricIcon {
                background: #EEF7FF;
                border: 1px solid #D8E8F4;
                border-radius: 0px;
                qproperty-alignment: AlignCenter;
            }

            QWidget#app {
                background: #E8F5FC;
                color: #1F1F1F;
                font-family: "Microsoft YaHei UI", "Segoe UI Variable Text", "Segoe UI", "Aptos", "Arial";
            }
            QFrame#sidebar {
                background: #E4F3FB;
                border: none;
                border-radius: 0px;
            }
            QLabel#logoCircle {
                background: transparent;
                border: none;
                qproperty-alignment: AlignCenter;
            }
            QLabel#brand {
                color: #111111;
                font-size: 22px;
                font-weight: 600;
                line-height: 118%;
            }
            QLabel#tagline {
                color: #4F5F6F;
                font-size: 12px;
                font-weight: 500;
                padding-left: 4px;
            }
            QPushButton#collapseButton {
                background: transparent;
                color: #0067C0;
                border: none;
                border-radius: 0px;
                font-size: 18px;
                font-weight: 700;
            }
            QPushButton#collapseButton:hover {
                background: #D8EDF8;
            }

            QLabel#menuLabel {
                color: #91A3B6;
                font-size: 10px;
                font-weight: 900;
                letter-spacing: 1.5px;
                padding-left: 8px;
                padding-top: 8px;
            }
            QPushButton#sidebarButton {
                icon-size: 26px;
                background: transparent;
                color: #202020;
                border: none;
                border-radius: 0px;
                text-align: left;
                padding: 10px 12px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton#sidebarButton:hover {
                background: #D8EDF8;
                color: #005FB8;
            }
            QPushButton#sidebarButton:checked {
                background: #D7EBF8;
                color: #0067C0;
                border-left: 4px solid #0078D4;
                font-weight: 700;
            }

            QFrame#mainPanel {
                background: #F6FBFE;
                border: none;
                border-radius: 0px;
            }
            QFrame#topHeader { background: transparent; }
            QLabel#pageIcon {
                background: #FFFFFF;
                border: 1px solid #D8E5F1;
                border-radius: 20px;
                qproperty-alignment: AlignCenter;
            }
            QLabel#pageTitle {
                color: #111111;
                font-size: 30px;
                font-weight: 600;
            }
            QLabel#pageSubtitle {
                color: #4F5F6F;
                font-size: 13px;
                font-weight: 500;
            }
            QScrollArea#contentScroll {
                background: transparent;
                border: none;
            }
            QWidget#pageBody { background: transparent; }
            QScrollBar:vertical {
                background: transparent;
                width: 10px;
                border-radius: 5px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #A7C8E5;
                border-radius: 5px;
                min-height: 48px;
            }
            QScrollBar::handle:vertical:hover { background: #77AEDD; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QFrame#hero {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #EAF6FF, stop:1 #FFFFFF);
                border: 1px solid #D8E8F4;
                border-radius: 8px;
            }
            QLabel#heroTitle {
                color: #111111;
                font-size: 24px;
                font-weight: 600;
            }
            QLabel#heroSubtitle {
                color: #4F5F6F;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton#heroPrimaryButton, QPushButton#heroSecondaryButton {
                border-radius: 0px;
                padding: 8px 18px;
                font-size: 14px;
                font-weight: 900;
                min-width: 150px;
            }
            QPushButton#heroPrimaryButton {
                background: #FFFFFF;
                color: #1267C4;
                border: none;
            }
            QPushButton#heroPrimaryButton:hover { background: #EAF6FF; }
            QPushButton#heroSecondaryButton {
                background: rgba(255,255,255,0.30);
                color: #FFFFFF;
                border: 1px solid rgba(255,255,255,0.48);
            }
            QPushButton#heroSecondaryButton:hover { background: rgba(255,255,255,0.42); }
            QFrame#metricCard {
                background: #FFFFFF;
                border: 1px solid #E0E7ED;
                border-radius: 8px;
            }
            QLabel#metricValue { color: #2F80ED; font-size: 32px; font-weight: 900; }
            QLabel#metricTitle { color: #1C2A3A; font-size: 15px; font-weight: 900; }
            QLabel#metricHint { color: #58708A; font-size: 12px; font-weight: 650; }
            QFrame#card {
                background: #FFFFFF;
                border: 1px solid #E0E7ED;
                border-radius: 8px;
            }
            QLabel#sectionTitle {
                color: #111111;
                font-size: 20px;
                font-weight: 600;
            }
            
            QLabel#largeIcon {
                font-size: 34px;
                font-weight: 900;
            }

            QLabel#sectionSubtitle {
                color: #4F5F6F;
                font-size: 12px;
                font-weight: 500;
                line-height: 145%;
            }
            QLabel#fieldLabel {
                color: #202020;
                font-size: 13px;
                font-weight: 600;
            }
            QLabel#miniLabel { color: #6B7F94; font-size: 12px; font-weight: 750; }
            QLabel#bodyText {
                color: #3F4B5A;
                font-size: 13px;
                font-weight: 500;
                line-height: 155%;
            }
            QFrame#compactInputBox, QFrame#switchRow {
                background: rgba(255,255,255,0.68);
                border: 1px solid #D8E5F1;
                border-radius: 0px;
            }
            QLineEdit#compactInput,
            QLineEdit#input {
                background: #FFFFFF;
                color: #111111;
                border: 1px solid #D5E2EC;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                font-weight: 500;
            }
            QLineEdit#compactInput:focus,
            QLineEdit#input:focus {
                border: 1px solid #0078D4;
                background: #FFFFFF;
            }
            QTextEdit#textArea,
            QTextEdit#logBox {
                background: #FFFFFF;
                color: #111111;
                border: 1px solid #D5E2EC;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                font-weight: 500;
            }
            QTextEdit#logBox {
                font-family: "Microsoft YaHei UI", "Segoe UI Variable Text", "Segoe UI", "Aptos", "Arial";
                font-size: 12px;
                color: #263B52;
            }
            QLabel#status { color: #142338; font-size: 15px; font-weight: 850; }
            QProgressBar#progress {
                background: #DCEAF5;
                border: none;
                border-radius: 4px;
            }
            QProgressBar#progress::chunk {
                background: #0067C0;
                border-radius: 4px;
            }
            QPushButton#primaryButton, QPushButton#primaryButtonLarge,
            QPushButton#secondaryButton, QPushButton#secondaryButtonLarge {
                border: none;
                border-radius: 0px;
                font-size: 16px;
                font-weight: 900;
                padding: 8px 20px;
            }
            QPushButton#primaryButton, QPushButton#primaryButtonLarge {
                background: #2F80ED;
                color: white;
            }
            QPushButton#primaryButton:hover, QPushButton#primaryButtonLarge:hover { background: #1D6FD8; }
            QPushButton#secondaryButton, QPushButton#secondaryButtonLarge {
                background: #E5F3FF;
                color: #1267C4;
            }
            QPushButton#secondaryButton:hover, QPushButton#secondaryButtonLarge:hover { background: #D5ECFF; }
            /* dashboard-hero-visible-overrides */

            QPushButton#heroSecondaryButton {
                background: #E8F4FC;
                color: #0067C0;
                border: 1px solid #D5EAF8;
                border-radius: 0px;
                font-size: 13px;
                font-weight: 600;
                padding: 8px 18px;
                min-width: 150px;
            }
            QPushButton#heroSecondaryButton:hover {
                background: #DDF0FB;
                border: 1px solid #BBDDF3;
            }

            QLabel:disabled {
                color: #8A9AAA;
            }
            QFrame#compactInputBox:disabled,
            QFrame#switchRow:disabled,
            QFrame#tocManualContainer:disabled,
            QFrame#tocBrowseContainer:disabled,
            QFrame#captionTableFrame:disabled,
            QFrame#captionRow:disabled,
            QFrame#folderSelectRow:disabled {
                background: #F1F4F7;
                border: 1px solid #D2DCE6;
            }
            QLineEdit#compactInput:disabled,
            QLineEdit#input:disabled,
            QLineEdit#captionEntry:disabled {
                background: #EEF2F6;
                color: #8A9AAA;
                border: 1px solid #D2DCE6;
            }
            QTextEdit#textArea:disabled {
                background: #EEF2F6;
                color: #8A9AAA;
                border: 1px solid #D2DCE6;
            }
            QScrollArea#captionScroll:disabled,
            QWidget#captionRowsContainer:disabled {
                background: #F1F4F7;
            }

            QPushButton#modernDropdown:disabled {
                background: #EEF2F6;
                color: #8A9AAA;
                border: 1px solid #D2DCE6;
            }
            QPushButton:disabled {
                background: #D7E1EC;
                color: #7F93A7;
                border: 1px solid #C7D3DF;
            }
        """
        )


    def selected_code_folder(self):
        path = getattr(self, "code_folder_path", "") or codeDir
        return os.path.abspath(os.path.expanduser(path))


    def selected_output_folder(self):
        path = getattr(self, "output_folder_path", "") or imageDir
        return os.path.abspath(os.path.expanduser(path))


    def selected_final_report_path(self):
        path = getattr(self, "final_report_path", "") or finalPdfPath
        path = os.path.abspath(os.path.expanduser(str(path)))
        if not path.lower().endswith(".pdf"):
            path += ".pdf"
        return path


    def update_final_report_path_label(self):
        if hasattr(self, "final_report_path_label"):
            self.final_report_path_label.setText(
                f"Save as: {self.selected_final_report_path()}"
            )


    def browse_final_report_path_action(self):
        start_path = self.selected_final_report_path()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Final PDF As", start_path, "PDF Files (*.pdf)"
        )
        if file_path:
            if not file_path.lower().endswith(".pdf"):
                file_path += ".pdf"
            self.final_report_path = file_path
            self.update_final_report_path_label()
            self.append_log(f"Save location selected: {file_path}")


    def update_code_folder_label(self):
        if hasattr(self, "code_folder_label"):
            self.code_folder_label.setText(f"Code folder: {self.selected_code_folder()}")


    def update_output_folder_label(self):
        if hasattr(self, "output_folder_label"):
            self.output_folder_label.setText(f"Image folder: {self.selected_output_folder()}")


    #select folder of code files
    def browse_code_folder_action(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Code Folder", self.selected_code_folder()
        )
        if folder:
            self.code_folder_path = folder
            self.update_code_folder_label()
            self.update_code_generate_state()
            self.append_log(f"Code folder selected: {folder}")


    #select folder of output images
    def browse_output_folder_action(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Image Folder", self.selected_output_folder()
        )
        if folder:
            self.output_folder_path = folder
            self.update_output_folder_label()
            self.refresh_caption_table(show_message=False)
            self.update_section_enabled_states()
            self.append_log(f"Image folder selected: {folder}")


    def output_image_files(self):
        folder = (
            self.selected_output_folder()
            if hasattr(self, "selected_output_folder")
            else imageDir
        )
        if not os.path.isdir(folder):
            return []
        valid_ext = (".png", ".jpg", ".jpeg", ".bmp", ".webp")
        return sorted(
            [f for f in os.listdir(folder) if f.lower().endswith(valid_ext)], key=str.lower
        )


    def update_caption_table_visibility(self):
        is_custom = (
            hasattr(self, "caption_mode_combo")
            and self.caption_mode_combo.currentText() == CAPTION_MODE_CUSTOM_OUTPUT
        )
        output_enabled = (
            hasattr(self, "generate_output_pages") and self.generate_output_pages.isChecked()
        )
        if hasattr(self, "caption_card"):
            self.caption_card.setVisible(is_custom)
            self.caption_card.setEnabled(output_enabled)
        if hasattr(self, "caption_table"):
            self.caption_table.setEnabled(is_custom and output_enabled)
        if hasattr(self, "caption_rows"):
            for _, caption_entry in self.caption_rows:
                caption_entry.setEnabled(is_custom and output_enabled)


    #for collecting file names and their captions
    def current_caption_mapping(self):
        captions = {}
        if (
            hasattr(self, "caption_mode_combo")
            and self.caption_mode_combo.currentText() != CAPTION_MODE_CUSTOM_OUTPUT
        ):
            return captions
        if hasattr(self, "caption_rows"):
            for file_name, caption_entry in self.caption_rows:
                caption = caption_entry.text().strip()
                if file_name and caption:
                    captions[file_name] = caption
                    captions[os.path.splitext(file_name)[0]] = caption
            return captions

        if not hasattr(self, "caption_table"):
            return captions
        try:
            for row in range(self.caption_table.rowCount()):
                file_item = self.caption_table.item(row, 0)
                caption_item = self.caption_table.item(row, 1)
                if not file_item:
                    continue
                file_name = file_item.text().strip()
                caption = caption_item.text().strip() if caption_item else ""
                if file_name and caption:
                    captions[file_name] = caption
                    captions[os.path.splitext(file_name)[0]] = caption
        except Exception:
            pass
        return captions


    def clear_caption_rows(self):
        if not hasattr(self, "caption_rows_layout"):
            return
        while self.caption_rows_layout.count():
            item = self.caption_rows_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.caption_rows = []


    def create_caption_row(self, file_name, caption):
        row_frame = QFrame()
        row_frame.setObjectName("captionRow")
        row_layout = QHBoxLayout(row_frame)
        row_layout.setContentsMargins(18, 0, 18, 0)
        row_layout.setSpacing(0)

        file_label = QLabel(file_name)
        file_label.setObjectName("captionFileLabel")
        file_label.setFixedWidth(230)
        file_label.setToolTip(file_name)

        divider = QFrame()
        divider.setObjectName("captionDivider")
        divider.setFixedWidth(1)

        caption_entry = QLineEdit()
        caption_entry.setObjectName("captionEntry")
        caption_entry.setText(caption)
        caption_entry.setPlaceholderText("Enter caption")

        row_layout.addWidget(file_label)
        row_layout.addWidget(divider)
        row_layout.addWidget(caption_entry, stretch=1)

        self.caption_rows_layout.addWidget(row_frame)
        self.caption_rows.append((file_name, caption_entry))


    def refresh_caption_table(self, show_message=True):
        if not hasattr(self, "caption_rows_layout"):
            return
        previous = self.current_caption_mapping()
        saved = self.load_saved_output_captions()
        files = self.output_image_files()
        self.clear_caption_rows()

        for file_name in files:
            stem = os.path.splitext(file_name)[0]
            caption = (
                previous.get(file_name)
                or previous.get(stem)
                or saved.get(file_name)
                or saved.get(stem)
                or ""
            )
            self.create_caption_row(file_name, caption)

        if not files:
            empty_row = QFrame()
            empty_row.setObjectName("captionRow")
            empty_layout = QHBoxLayout(empty_row)
            empty_layout.setContentsMargins(18, 0, 18, 0)
            empty_label = QLabel("No output images found in the selected folder.")
            empty_label.setObjectName("captionFileLabel")
            empty_layout.addWidget(empty_label)
            self.caption_rows_layout.addWidget(empty_row)

        if show_message:
            self.show_themed_message(
                "Images Refreshed",
                f"Found {len(files)} output image(s).",
                "refresh.svg",
            )


    def load_saved_output_captions(self):

        try:
            if not os.path.exists(captionsPath):
                return {}
            with open(captionsPath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return {}
            cleaned = {}
            for key, value in data.items():
                key = str(key).strip()
                value = str(value).strip()
                if key and value:
                    cleaned[key] = value
            return cleaned
        except Exception:
            return {}


    def save_output_captions(self, show_message=True):
        try:
            os.makedirs(jsonDir, exist_ok=True)
            captions = self.current_caption_mapping()
            with open(captionsPath, "w", encoding="utf-8") as f:
                json.dump(captions, f, indent=4)
            if hasattr(self, "caption_save_status"):
                self.caption_save_status.setText("Captions have been saved successfully.")
            if show_message:
                self.show_themed_message(
                    "Captions Saved", f"Saved {len(captions)} caption(s). Captions are also saved automatically before previewing or generating the report.", "save.svg"
                )
        except Exception as exc:
            self.show_themed_error("Caption Save Failed", f"Could not save captions.\n{exc}")


    def open_code_folder(self):
        self.open_folder(
            self.selected_code_folder() if hasattr(self, "selected_code_folder") else codeDir
        )


    def open_output_folder(self):
        self.open_folder(
            self.selected_output_folder()
            if hasattr(self, "selected_output_folder")
            else imageDir
        )


    def is_auto_code_file(self, path):
        skip_extensions = {
            ".class",
            ".exe",
            ".dll",
            ".jar",
            ".war",
            ".ear",
            ".o",
            ".obj",
            ".bin",
            ".png",
            ".jpg",
            ".jpeg",
            ".bmp",
            ".gif",
            ".webp",
            ".ico",
            ".svg",
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
            ".zip",
            ".rar",
            ".7z",
            ".tar",
            ".gz",
            ".mp3",
            ".mp4",
            ".avi",
            ".mov",
        }
        name = os.path.basename(path)
        if name.startswith(".") or not os.path.isfile(path):
            return False
        if os.path.splitext(name)[1].lower() in skip_extensions:
            return False
        try:
            with open(path, "rb") as file:
                chunk = file.read(4096)
            if b"\x00" in chunk:
                return False
            if not chunk:
                return True
            try:
                chunk.decode("utf-8")
            except UnicodeDecodeError:
                chunk.decode("latin-1")
            return True
        except Exception:
            return False


    def discover_auto_code_files(self):
        code_folder = (
            self.selected_code_folder() if hasattr(self, "selected_code_folder") else codeDir
        )
        if not os.path.isdir(code_folder):
            return []
        files = []
        for root, dirs, names in os.walk(code_folder):
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".") and d not in {"__pycache__", "node_modules", ".git"}
            ]
            dirs.sort(key=self.natural_key_for_health_check)
            for name in sorted(names, key=self.natural_key_for_health_check):
                full_path = os.path.join(root, name)
                if self.is_auto_code_file(full_path):
                    files.append(os.path.relpath(full_path, code_folder).replace(os.sep, "/"))
        return sorted(files, key=self.natural_key_for_health_check)


    def project_health_text(self):
        image_exts = (".png", ".jpg", ".jpeg", ".bmp", ".webp")
        code_files_all = []
        code_files_matching = []
        output_files = []
        action_items = []
        code_folder = (
            self.selected_code_folder() if hasattr(self, "selected_code_folder") else codeDir
        )
        output_folder = (
            self.selected_output_folder()
            if hasattr(self, "selected_output_folder")
            else imageDir
        )

        if os.path.isdir(code_folder):
            for root, dirs, names in os.walk(code_folder):
                dirs[:] = [
                    d
                    for d in dirs
                    if not d.startswith(".") and d not in {"__pycache__", "node_modules", ".git"}
                ]
                dirs.sort(key=self.natural_key_for_health_check)
                for name in sorted(names, key=self.natural_key_for_health_check):
                    full_path = os.path.join(root, name)
                    if os.path.isfile(full_path):
                        code_files_all.append(
                            os.path.relpath(full_path, code_folder).replace(os.sep, "/")
                        )
            code_files_matching = self.discover_auto_code_files()
        else:
            action_items.append("Select a valid code folder.")

        if os.path.isdir(output_folder):
            output_files = sorted(
                [f for f in os.listdir(output_folder) if f.lower().endswith(image_exts)],
                key=self.natural_key_for_health_check,
            )
        else:
            action_items.append("Select a valid image folder.")

        code_stems = {os.path.splitext(os.path.basename(f))[0].lower() for f in code_files_matching}
        output_stems = {os.path.splitext(f)[0].lower() for f in output_files}
        matched_names = len(code_stems & output_stems)
        unmatched_code = sorted(
            [
                f
                for f in code_files_matching
                if os.path.splitext(os.path.basename(f))[0].lower() not in output_stems
            ],
            key=self.natural_key_for_health_check,
        )
        unmatched_output = sorted(
            [f for f in output_files if os.path.splitext(f)[0].lower() not in code_stems],
            key=self.natural_key_for_health_check,
        )

        if self.generate_code_page.isChecked() and not code_files_matching:
            action_items.append(
                "Code pages are enabled, but no supported source-code or text files were found."
            )
        if self.generate_output_pages.isChecked() and not output_files:
            action_items.append(
                "Output images are enabled, but no supported images were found."
            )
        if self.generate_cover.isChecked() and not os.path.exists(
            os.path.join(baseDir, "logo.png")
        ):
            action_items.append(
                "The cover page is enabled, but no logo is available. Add a logo or disable the cover page."
            )
        if self.generate_toc.isChecked() and not self.toc_text.toPlainText().strip():
            action_items.append("The table of contents is enabled, but no entries were provided.")
        if self.output_after_code.isChecked() and unmatched_code:
            action_items.append(
                "Some code files do not have matching output images, so output cannot be placed directly after those files."
            )
        if self.output_after_code.isChecked() and unmatched_output:
            action_items.append(
                "Some output images do not match a code file name, so they will be placed later in the report."
            )

        has_content = any(
            (
                self.generate_cover.isChecked(),
                self.generate_toc.isChecked(),
                self.generate_code_page.isChecked(),
                self.generate_output_pages.isChecked(),
            )
        )
        if not has_content:
            action_items.append("Enable at least one report section.")

        missing_fonts = [
            name for name, font_path in required_font_files(self.font_combo.currentText())
            if not os.path.isfile(font_path)
        ]
        if missing_fonts:
            action_items.append(
                "Place the following font file(s) in the Fonts folder: "
                + ", ".join(missing_fonts)
            )

        enabled_parts = []
        disabled_parts = []
        section_states = [
            ("Cover page", self.generate_cover.isChecked()),
            ("Table of contents", self.generate_toc.isChecked()),
            ("Code pages", self.generate_code_page.isChecked()),
            ("Output images", self.generate_output_pages.isChecked()),
            ("Watermark", self.generate_watermark.isChecked()),
            ("Place Output After Code", self.output_after_code.isChecked()),
        ]
        for label, enabled in section_states:
            (enabled_parts if enabled else disabled_parts).append(label)

        status = "Ready" if not action_items else "Action required"
        status_note = (
            "No setup issues were found."
            if not action_items
            else "Review the items below before generating the report."
        )

        lines = [
            "PROJECT CHECK",
            "=" * 60,
            f"Status: {status}",
            f"Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "Summary",
            "-" * 60,
            status_note,
            "",
            "Folders",
            "-" * 60,
            f"Code folder   : {code_folder}",
            f"Image folder  : {output_folder}",
            "",
            "Files",
            "-" * 60,
            f"Readable code files      : {len(code_files_matching)}",
            f"Total files in code area : {len(code_files_all)}",
            f"Output images             : {len(output_files)}",
            f"Matching code/output names: {matched_names}",
            "",
            "Report Sections",
            "-" * 60,
            f"Enabled : {', '.join(enabled_parts) if enabled_parts else 'None'}",
            f"Disabled: {', '.join(disabled_parts) if disabled_parts else 'None'}",
        ]

        if action_items:
            lines.extend(["", "Required Actions", "-" * 60])
            lines.extend([f"{index}. {item}" for index, item in enumerate(action_items, start=1)])
        else:
            lines.extend(
                [
                    "",
                    "Required Actions",
                    "-" * 60,
                    "No action is required.",
                ]
            )

        lines.extend(["", "File Matching", "-" * 60])
        if self.output_after_code.isChecked():
            lines.append("Code files and output images are matched by file name.")
            lines.append("Example: Lab10.java matches Lab10.png or Lab10.jpg.")
        else:
            lines.append(
                "Output placement after code is disabled, so matching file names is optional."
            )

        if unmatched_code:
            lines.append("")
            lines.append(f"Code files without matching output images ({len(unmatched_code)}):")
            lines.extend([f"- {name}" for name in unmatched_code[:20]])
            if len(unmatched_code) > 20:
                lines.append(f"- ... and {len(unmatched_code) - 20} more")

        if unmatched_output:
            lines.append("")
            lines.append(
                f"Output images without matching code files ({len(unmatched_output)}):"
            )
            lines.extend([f"- {name}" for name in unmatched_output[:20]])
            if len(unmatched_output) > 20:
                lines.append(f"- ... and {len(unmatched_output) - 20} more")

        return "\n".join(lines)


    #check project folders and files
    def run_project_health_check(self):
        report = self.project_health_text()
        self.select_page(0)
        self.append_log(report)
        TextReportDialog(
            "Project Check",
            "Review folders, files, and report settings.",
            report,
            self,
            "dashboard.svg",
        ).exec()


    def read_generation_summary(self):
        if not os.path.exists(summaryPath):
            return (
                "No generation summary is available.\n\n"
                "Generate a report to view its location, page count, file size, selected sections, and file-matching details."
            )
        try:
            with open(summaryPath, "r", encoding="utf-8") as f:
                text = f.read().strip()
        except Exception as exc:
            return f"Could not read the generation summary.\n\nDetails: {exc}"

        if not text:
            return "The generation summary is empty. Generate the report again."
        return text


    def show_last_generation_summary(self):
        TextReportDialog(
            "Generation Summary",
            "Details from the latest generated report.",
            self.read_generation_summary(),
            self,
            "document.svg",
        ).exec()


    def collect_gui_settings(self):
        return {
            "_document_formatter_config_version": 2,
            "_config_type": "Document Formatter Report Configuration",
            "Margins": {
                "top": self.margin_top["entry"].text(),
                "bottom": self.margin_bottom["entry"].text(),
                "left": self.margin_left["entry"].text(),
                "right": self.margin_right["entry"].text(),
                "use_default": self.default_margin.isChecked(),
            },
            "Typography": {
                "font_family": self.font_combo.currentText(),
            },
            "Export": {
                "format": self.export_combo.currentText(),
                "final_pdf_path": self.selected_final_report_path(),
            },
            "Figures": {
                "include_figure_labels": self.include_figure.isChecked(),
                "generate_output_pages": self.generate_output_pages.isChecked(),
                "output_caption_mode": self.caption_mode_combo.currentText(),
                "output_folder_path": self.selected_output_folder(),
            },
            "CoverPage": {
                "generate_cover_page": self.generate_cover.isChecked(),
                "CollegeName": self.college_name.text(),
                "Address": self.college_address.text(),
                "StudentName": self.student_name.text(),
                "Roll": self.roll.text(),
                "Section": self.section_entry.text(),
                "Semester": self.semester.text(),
                "TeacherName": self.teacher_name.text(),
                "ProjectTitle": self.project_title.text(),
                "logo_selected": getattr(self, "logo_selected", False),
            },
            "TableOfContent": {
                "generate_table_of_content": self.generate_toc.isChecked(),
                "toc_text": self.toc_text.toPlainText(),
                "toc_source_mode": (
                    self.toc_mode_combo.currentText()
                    if hasattr(self, "toc_mode_combo")
                    else TOC_MODE_MANUAL
                ),
                "toc_file_path": getattr(self, "toc_file_path", ""),
                "keep_existing_label": (
                    self.keep_toc_label.isChecked() if hasattr(self, "keep_toc_label") else True
                ),
            },
            "CodePage": {
                "generate_code_page": self.generate_code_page.isChecked(),
                "line_height": self.code_line_height.text(),
                "code_folder_path": self.selected_code_folder(),
                "output_after_code": self.output_after_code.isChecked()
                and self.generate_output_pages.isChecked(),
            },
            "Watermark": {
                "generate_watermark": self.generate_watermark.isChecked(),
                "name": self.watermark_name.text(),
            },
            "OutputCaptions": self.current_caption_mapping(),
        }


    def collect_runtime_configuration(self):

        config_data = self.collect_gui_settings()
        caption_mode = self.caption_mode_combo.currentText()

        config_data["Margins"] = {
            "top": self.safe_int(self.margin_top["entry"].text(), 72),
            "bottom": self.safe_int(self.margin_bottom["entry"].text(), 72),
            "left": self.safe_int(self.margin_left["entry"].text(), 90),
            "right": self.safe_int(self.margin_right["entry"].text(), 60),
            "use_default": self.default_margin.isChecked(),
        }
        config_data["Figures"].update(
            {
                "use_custom_output_captions": caption_mode == CAPTION_MODE_CUSTOM_OUTPUT,
                "match_output_name_with_file_name": caption_mode == CAPTION_MODE_MATCH_FILENAME,
                "dont_caption_output": caption_mode == CAPTION_MODE_NONE,
            }
        )
        return config_data


    def list_to_dict_if_pairs(self, value):
        if isinstance(value, list):
            if all(isinstance(item, (list, tuple)) and len(item) == 2 for item in value):
                return {str(key): val for key, val in value}
            if all(isinstance(item, dict) for item in value):
                merged = {}
                for item in value:
                    merged.update(item)
                return merged
        return value


    def normalized_config_key(self, key):
        return re.sub(r"[^a-z0-9]", "", str(key).lower())


    def normalize_section(self, data, *names):
        data = self.list_to_dict_if_pairs(data)
        if not isinstance(data, dict):
            return {}

        lookup = {self.normalized_config_key(key): value for key, value in data.items()}

        for name in names:
            wanted = self.normalized_config_key(name)
            if wanted in lookup:
                value = self.list_to_dict_if_pairs(lookup[wanted])
                return value if isinstance(value, dict) else value

        return {}


    def normalize_imported_configuration(self, data):
        data = self.list_to_dict_if_pairs(data)

        if not isinstance(data, dict):
            raise ValueError(
                "The selected JSON file is not a valid settings file. "
                "Choose a file created with File > Save Settings or JsonFile/config_data.json."
            )


        margins = self.normalize_section(data, "Margins", "margins", "Margin")
        typography = self.normalize_section(data, "Typography", "typography", "Font", "font")
        export = self.normalize_section(data, "Export", "export")
        figures = self.normalize_section(data, "Figures", "figures", "Figure", "figure")
        cover = self.normalize_section(
            data, "CoverPage", "cover_page", "coverPage", "FrontPage", "front_page"
        )
        toc = self.normalize_section(
            data, "TableOfContent", "Table_Of_Content", "table_of_content", "toc", "TOC"
        )
        code = self.normalize_section(data, "CodePage", "code_page", "code", "Code")
        watermark = self.normalize_section(data, "Watermark", "watermark")
        captions = self.normalize_section(data, "OutputCaptions", "output_captions", "captions")


        flat_keys = set(data.keys())
        if not margins and {"top", "bottom", "left", "right"}.issubset(flat_keys):
            margins = {
                "top": data.get("top"),
                "bottom": data.get("bottom"),
                "left": data.get("left"),
                "right": data.get("right"),
                "use_default": data.get(
                    "use_default", data.get("default_margin", self.default_margin.isChecked())
                ),
            }

        if not typography and ("font_family" in data or "font" in data):
            typography = {"font_family": data.get("font_family", data.get("font"))}

        if not export and (
            "format" in data
            or "export_format" in data
            or "final_pdf_path" in data
            or "output_pdf_path" in data
        ):
            export = {
                "format": data.get("format", data.get("export_format", "PDF")),
                "final_pdf_path": data.get(
                    "final_pdf_path",
                    data.get("output_pdf_path", data.get("save_pdf_path", finalPdfPath)),
                ),
            }



        if isinstance(margins, list):
            margins = {
                "top": margins[0] if len(margins) > 0 else self.margin_top["entry"].text(),
                "bottom": margins[1] if len(margins) > 1 else self.margin_bottom["entry"].text(),
                "left": margins[2] if len(margins) > 2 else self.margin_left["entry"].text(),
                "right": margins[3] if len(margins) > 3 else self.margin_right["entry"].text(),
                "use_default": margins[4] if len(margins) > 4 else self.default_margin.isChecked(),
            }

        if isinstance(typography, list):
            typography = {
                "font_family": typography[0] if typography else self.font_combo.currentText()
            }

        if isinstance(export, list):
            export = {"format": export[0] if export else self.export_combo.currentText()}

        if isinstance(figures, list):
            figures = {
                "include_figure_labels": (
                    figures[0] if len(figures) > 0 else self.include_figure.isChecked()
                ),
                "output_caption_mode": (
                    figures[2] if len(figures) > 2 else self.caption_mode_combo.currentText()
                ),
                "generate_output_pages": (
                    figures[3] if len(figures) > 3 else self.generate_output_pages.isChecked()
                ),
            }

        if isinstance(cover, list):
            keys = [
                "StudentName",
                "Roll",
                "Section",
                "Semester",
                "TeacherName",
                "ProjectTitle",
                "generate_cover_page",
                "CollegeName",
                "Address",
            ]
            cover = {key: cover[index] for index, key in enumerate(keys) if index < len(cover)}

        if isinstance(toc, list):
            toc = {
                "toc_text": "\n".join(str(item) for item in toc),
                "generate_table_of_content": False,
            }

        if isinstance(code, list):
            code = {
                "line_height": code[0] if len(code) > 0 else self.code_line_height.text(),
                "file_extension": code[1] if len(code) > 1 else self.code_file_ext.text(),
                "generate_code_page": code[2] if len(code) > 2 else False,
                "output_after_code": code[3] if len(code) > 3 else False,
            }

        if isinstance(watermark, list):
            watermark = {
                "name": watermark[0] if len(watermark) > 0 else self.watermark_name.text(),
                "generate_watermark": watermark[1] if len(watermark) > 1 else False,
            }

        if isinstance(captions, list):
            captions = self.list_to_dict_if_pairs(captions)

        return {
            "Margins": margins if isinstance(margins, dict) else {},
            "Typography": typography if isinstance(typography, dict) else {},
            "Export": export if isinstance(export, dict) else {},
            "Figures": figures if isinstance(figures, dict) else {},
            "CoverPage": cover if isinstance(cover, dict) else {},
            "TableOfContent": toc if isinstance(toc, dict) else {},
            "CodePage": code if isinstance(code, dict) else {},
            "Watermark": watermark if isinstance(watermark, dict) else {},
            "OutputCaptions": captions if isinstance(captions, dict) else {},
        }


    def set_dropdown_value(self, dropdown, value):
        if value in [None, ""]:
            return
        try:
            dropdown.setCurrentText(str(value))
        except Exception:
            try:
                dropdown.setText(str(value))
            except Exception:
                pass


    def config_get_first(self, section, names, default=None):
        if not isinstance(section, dict):
            return default
        normalized_lookup = {
            re.sub(r"[^a-z0-9]", "", str(key).lower()): value for key, value in section.items()
        }
        for name in names:
            key = re.sub(r"[^a-z0-9]", "", str(name).lower())
            if key in normalized_lookup:
                return normalized_lookup[key]
        return default


    def normalize_output_caption_mode(self, value=None, figures=None):

        valid_modes = {
            CAPTION_MODE_NONE,
            CAPTION_MODE_CUSTOM_OUTPUT,
            CAPTION_MODE_MATCH_FILENAME,
        }
        mode = str(value or "").strip()
        if mode in valid_modes:
            return mode

        figures = figures if isinstance(figures, dict) else {}
        if bool(self.config_get_first(figures, ["dont_caption_output"], False)):
            return CAPTION_MODE_NONE
        if bool(self.config_get_first(figures, ["match_output_name_with_file_name"], False)):
            return CAPTION_MODE_MATCH_FILENAME
        if bool(self.config_get_first(figures, ["use_custom_output_captions"], False)):
            return CAPTION_MODE_CUSTOM_OUTPUT
        return CAPTION_MODE_NONE


    def set_text_from_config(self, widget, section, names):
        value = self.config_get_first(section, names, None)
        if value is not None:
            widget.setText(str(value))


    def set_switch_from_config(self, switch, section, names, default=False, respect_enabled=True):
        value = self.config_get_first(section, names, default)
        checked = bool(value)
        if respect_enabled:
            switch.setChecked(checked and switch.isEnabled())
        else:
            switch.setChecked(checked)


    def apply_gui_settings(self, data):
        data = self.normalize_imported_configuration(data)

        self._importing_configuration = True
        try:
            margins = data.get("Margins", {})
            self.set_text_from_config(self.margin_top["entry"], margins, ["top"])
            self.set_text_from_config(self.margin_bottom["entry"], margins, ["bottom"])
            self.set_text_from_config(self.margin_left["entry"], margins, ["left"])
            self.set_text_from_config(self.margin_right["entry"], margins, ["right"])
            self.default_margin.setChecked(
                bool(
                    self.config_get_first(
                        margins, ["use_default", "default_margin"], self.default_margin.isChecked()
                    )
                )
            )

            typography = data.get("Typography", {})
            self.set_dropdown_value(
                self.font_combo, self.config_get_first(typography, ["font_family", "font"], None)
            )

            export = data.get("Export", {})
            self.set_dropdown_value(
                self.export_combo, self.config_get_first(export, ["format", "export_format"], None)
            )
            final_pdf_path = self.config_get_first(
                export, ["final_pdf_path", "output_pdf_path", "save_pdf_path"], None
            )
            if final_pdf_path:
                self.final_report_path = str(final_pdf_path)
                self.update_final_report_path_label()

            figures = data.get("Figures", {})
            self.include_figure.setChecked(
                bool(
                    self.config_get_first(
                        figures, ["include_figure_labels"], self.include_figure.isChecked()
                    )
                )
            )
            if hasattr(self, "generate_output_pages"):
                self.generate_output_pages.setChecked(
                    bool(
                        self.config_get_first(
                            figures,
                            ["generate_output_pages"],
                            self.generate_output_pages.isChecked(),
                        )
                    )
                )

            output_folder_path = self.config_get_first(
                figures, ["output_folder_path", "input_image_folder", "input_folder"], None
            )
            if output_folder_path:
                self.output_folder_path = str(output_folder_path)
                self.update_output_folder_label()

            caption_mode = self.normalize_output_caption_mode(
                self.config_get_first(figures, ["output_caption_mode"], None),
                figures,
            )
            self.set_dropdown_value(self.caption_mode_combo, caption_mode)
            self.update_caption_table_visibility()

            cover = data.get("CoverPage", {})
            self.set_text_from_config(
                self.college_name, cover, ["CollegeName", "college_name", "College"]
            )
            self.set_text_from_config(
                self.college_address, cover, ["Address", "address", "CollegeAddress"]
            )
            self.set_text_from_config(self.student_name, cover, ["StudentName", "student_name"])
            self.set_text_from_config(self.roll, cover, ["Roll", "roll"])
            self.set_text_from_config(self.section_entry, cover, ["Section", "section"])
            self.set_text_from_config(self.semester, cover, ["Semester", "semester"])
            self.set_text_from_config(self.teacher_name, cover, ["TeacherName", "teacher_name"])
            self.set_text_from_config(self.project_title, cover, ["ProjectTitle", "project_title"])

            imported_logo_selected = bool(self.config_get_first(cover, ["logo_selected"], False))
            self.logo_selected = imported_logo_selected or os.path.exists(
                os.path.join(baseDir, "logo.png")
            )
            if self.logo_selected:
                os.makedirs(jsonDir, exist_ok=True)
                with open(logoFlagPath, "w", encoding="utf-8") as f:
                    json.dump(
                        {"selected": True, "source": "imported configuration or existing logo.png"},
                        f,
                        indent=4,
                    )
            if hasattr(self, "logo_status_label"):
                self.logo_status_label.setText(
                    "Current logo: logo.png"
                    if self.logo_selected
                    else "No logo selected."
                )
            self.update_cover_generate_state()
            self.generate_cover.setChecked(
                bool(self.config_get_first(cover, ["generate_cover_page"], False))
                and self.generate_cover.isEnabled()
            )

            toc = data.get("TableOfContent", {})
            toc_text_value = self.config_get_first(toc, ["toc_text", "questions", "content"], None)
            if toc_text_value is not None:
                self.toc_text.setPlainText(str(toc_text_value))

            if hasattr(self, "toc_mode_combo"):
                self.set_dropdown_value(
                    self.toc_mode_combo,
                    self.config_get_first(toc, ["toc_source_mode", "source_mode"], TOC_MODE_MANUAL),
                )

            if hasattr(self, "keep_toc_label"):
                self.keep_toc_label.setChecked(
                    bool(
                        self.config_get_first(
                            toc, ["keep_existing_label"], self.keep_toc_label.isChecked()
                        )
                    )
                )

            if hasattr(self, "toc_file_label"):
                self.toc_file_path = str(
                    self.config_get_first(toc, ["toc_file_path", "file_path"], "") or ""
                )
                self.toc_file_label.setText(
                    f"Selected file: {self.toc_file_path}"
                    if self.toc_file_path
                    else "No file selected."
                )

            self.update_toc_mode_visibility()
            requested_toc = bool(
                self.config_get_first(toc, ["generate_table_of_content", "generate_toc"], False)
            )
            self.generate_toc.setChecked(requested_toc and self.generate_toc.isEnabled())

            code = data.get("CodePage", {})
            self.set_text_from_config(self.code_line_height, code, ["line_height", "lineHeight"])
            self.set_text_from_config(
                self.code_file_ext, code, ["file_extension", "file_ext", "extension"]
            )
            code_folder_path = self.config_get_first(
                code, ["code_folder_path", "input_code_folder", "input_folder"], None
            )
            if code_folder_path:
                self.code_folder_path = str(code_folder_path)
                self.update_code_folder_label()
            self.generate_code_page.setChecked(
                bool(self.config_get_first(code, ["generate_code_page"], False))
                and self.generate_code_page.isEnabled()
            )
            self.update_code_generate_state()
            self.update_section_enabled_states()
            self.output_after_code.setChecked(
                bool(self.config_get_first(code, ["output_after_code"], False))
                and self.output_after_code.isEnabled()
            )

            watermark = data.get("Watermark", {})
            self.set_text_from_config(self.watermark_name, watermark, ["name", "watermark_name"])
            self.update_watermark_generate_state()
            self.generate_watermark.setChecked(
                bool(self.config_get_first(watermark, ["generate_watermark"], False))
                and self.generate_watermark.isEnabled()
            )

            imported_captions = (
                data.get("OutputCaptions", {})
                if isinstance(data.get("OutputCaptions", {}), dict)
                else {}
            )
            os.makedirs(jsonDir, exist_ok=True)
            with open(captionsPath, "w", encoding="utf-8") as f:
                json.dump(imported_captions, f, indent=4)
            self.refresh_caption_table(show_message=False)


            self.update_cover_generate_state()
            self.update_toc_generate_state()
            self.update_code_generate_state()
            self.update_watermark_generate_state()
            self.update_caption_table_visibility()
        finally:
            self._importing_configuration = False


    def add_logo_action(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Logo", baseDir, "Image Files (*.png *.jpg *.jpeg *.webp *.bmp)"
            )
            if not file_path:
                return

            target_path = os.path.join(baseDir, "logo.png")

            try:
                from PIL import Image

                image = Image.open(file_path).convert("RGBA")
                image.save(target_path)
            except Exception:
                shutil.copyfile(file_path, target_path)

            if hasattr(self, "logo_status_label"):
                self.logo_status_label.setText(f"Current logo: {os.path.basename(file_path)}")
            self.show_themed_message(
                "Logo Added",
                "The selected logo will be used on the cover page.",
                "logo-upload.svg",
            )
        except Exception as exc:
            self.show_themed_error("Logo Upload Failed", f"Could not add the logo.\n{exc}")


    def clear_output_captions(self):
        try:
            if (
                hasattr(self, "caption_mode_combo")
                and self.caption_mode_combo.currentText() != CAPTION_MODE_CUSTOM_OUTPUT
            ):
                self.show_themed_message(
                    "Manual Captions Not Selected",
                    "Select Manual captions before clearing captions.",
                    "captions.svg",
                )
                return
            if hasattr(self, "caption_rows"):
                for _, caption_entry in self.caption_rows:
                    caption_entry.clear()

            if os.path.exists(captionsPath):
                os.remove(captionsPath)

            self.show_themed_message(
                "Captions Cleared", "Manual captions have been cleared.", "clear.svg"
            )
        except Exception as exc:
            self.show_themed_error("Caption Clear Failed", f"Could not clear captions.\n{exc}")


    def record_generated_project_history(self, pdf_path):
        try:
            history = []
            if os.path.exists(historyPath):
                with open(historyPath, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                    if isinstance(existing, list):
                        history = existing

            pdf_size = os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0
            summary_text = ""
            if os.path.exists(summaryPath):
                with open(summaryPath, "r", encoding="utf-8") as f:
                    summary_text = f.read().strip()

            entry = {
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "pdf_path": pdf_path,
                "pdf_size_mb": round(pdf_size / (1024 * 1024), 2) if pdf_size else 0,
                "project_title": (
                    self.project_title.text().strip() if hasattr(self, "project_title") else ""
                ),
                "student_name": (
                    self.student_name.text().strip() if hasattr(self, "student_name") else ""
                ),
                "summary": summary_text,
            }

            history.insert(0, entry)
            history = history[:50]

            with open(historyPath, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=4)
        except Exception:
            pass


    def generated_project_history_text(self):
        if not os.path.exists(historyPath):
            return (
                "No report history is available.\n\n"
                "Generated reports will appear here with the date, project title, student name, location, and file size."
            )

        try:
            with open(historyPath, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception as exc:
            return f"Could not read report history.\n\nDetails: {exc}"

        if not history:
            return "No report history is available. Generate a report first."

        lines = [
            "REPORT HISTORY",
            "=" * 60,
            f"Showing {len(history)} saved report(s). Newest first.",
            "",
        ]
        for index, item in enumerate(history, start=1):
            generated_at = item.get("generated_at", "Date unavailable")
            project_title = item.get("project_title") or "Not provided"
            student_name = item.get("student_name") or "Not provided"
            pdf_path = item.get("pdf_path") or "Unavailable"
            pdf_size = item.get("pdf_size_mb", 0)

            lines.extend(
                [
                    f"Report {index}",
                    "-" * 60,
                    f"Generated: {generated_at}",
                    f"Project: {project_title}",
                    f"Student: {student_name}",
                    f"File size: {pdf_size} MB",
                    f"Location: {pdf_path}",
                ]
            )

            summary = str(item.get("summary", "")).strip()
            if summary:
                summary_lines = [line.strip() for line in summary.splitlines() if line.strip()]
                important = []
                for line in summary_lines:
                    lower = line.lower()
                    if any(
                        key in lower
                        for key in [
                            "status",
                            "pages",
                            "file size",
                            "code files",
                            "output images",
                            "output after code",
                            "watermark",
                        ]
                    ):
                        important.append(line)
                    if len(important) >= 5:
                        break
                if important:
                    lines.append("Details:")
                    lines.extend([f"  - {line}" for line in important])

            lines.append("")
        return "\n".join(lines)


    def clear_generated_project_history_action(self, dialog=None):
        if not self.show_themed_confirm(
            "Clear Report History", "Clear all saved report history?"
        ):
            return
        try:
            if os.path.exists(historyPath):
                os.remove(historyPath)
            if dialog is not None and hasattr(dialog, "text_box"):
                dialog.text_box.setPlainText(self.generated_project_history_text())
            self.show_themed_message(
                "Report History Cleared", "Report history has been cleared.", "history.svg"
            )
        except Exception as exc:
            self.show_themed_error(
                "History Clear Failed", f"Could not clear report history.\n{exc}"
            )


    def show_generated_project_history_action(self):
        TextReportDialog(
            "Report History",
            "Previously generated reports.",
            self.generated_project_history_text(),
            self,
            "history.svg",
            extra_action_text="Clear History",
            extra_action_callback=self.clear_generated_project_history_action,
        ).exec()


    #save current settings
    def save_configuration_action(self):
        try:
            default_path = os.path.join(baseDir, "saved_report_configuration.json")
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Settings", default_path, "JSON Files (*.json)"
            )
            if not file_path:
                return
            if not file_path.lower().endswith(".json"):
                file_path += ".json"

            config_data = self.collect_runtime_configuration()


            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)



            os.makedirs(jsonDir, exist_ok=True)
            with open(os.path.join(jsonDir, "config_data.json"), "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)
            with open(
                os.path.join(jsonDir, "last_saved_configuration.json"), "w", encoding="utf-8"
            ) as f:
                json.dump(config_data, f, indent=4)

            self.show_themed_message(
                "Settings Saved", f"Settings saved to:\n{file_path}", "save.svg"
            )
        except Exception as exc:
            self.show_themed_error("Save Failed", f"Could not save settings.\n{exc}")


    def dict_section(self, data, key):
        if not isinstance(data, dict):
            return {}
        value = data.get(key, {})
        return value if isinstance(value, dict) else {}


    def restore_imported_configuration_directly(self, raw_data):

        expected_sections = {
            "Margins",
            "Typography",
            "Export",
            "Figures",
            "CoverPage",
            "TableOfContent",
            "CodePage",
            "Watermark",
            "OutputCaptions",
        }
        if isinstance(raw_data, dict) and any(section in raw_data for section in expected_sections):
            data = raw_data
        else:
            data = self.normalize_imported_configuration(raw_data)

        margins = data.get("Margins", {}) if isinstance(data.get("Margins", {}), dict) else {}
        typography = (
            data.get("Typography", {}) if isinstance(data.get("Typography", {}), dict) else {}
        )
        export = data.get("Export", {}) if isinstance(data.get("Export", {}), dict) else {}
        figures = data.get("Figures", {}) if isinstance(data.get("Figures", {}), dict) else {}
        cover = data.get("CoverPage", {}) if isinstance(data.get("CoverPage", {}), dict) else {}
        toc = (
            data.get("TableOfContent", {})
            if isinstance(data.get("TableOfContent", {}), dict)
            else {}
        )
        code = data.get("CodePage", {}) if isinstance(data.get("CodePage", {}), dict) else {}
        watermark = data.get("Watermark", {}) if isinstance(data.get("Watermark", {}), dict) else {}
        output_captions = (
            data.get("OutputCaptions", {})
            if isinstance(data.get("OutputCaptions", {}), dict)
            else {}
        )


        self.margin_top["entry"].setText(str(margins.get("top", "")))
        self.margin_bottom["entry"].setText(str(margins.get("bottom", "")))
        self.margin_left["entry"].setText(str(margins.get("left", "")))
        self.margin_right["entry"].setText(str(margins.get("right", "")))
        self.default_margin.setChecked(bool(margins.get("use_default", True)))
        self.set_dropdown_value(self.font_combo, typography.get("font_family", "Times New Roman"))
        self.set_dropdown_value(self.export_combo, export.get("format", "PDF"))
        self.final_report_path = str(
            export.get(
                "final_pdf_path",
                export.get("output_pdf_path", getattr(self, "final_report_path", finalPdfPath)),
            )
            or finalPdfPath
        )
        self.update_final_report_path_label()


        self.include_figure.setChecked(bool(figures.get("include_figure_labels", False)))
        if hasattr(self, "generate_output_pages"):
            self.generate_output_pages.setChecked(bool(figures.get("generate_output_pages", False)))
        self.output_folder_path = str(
            figures.get("output_folder_path", getattr(self, "output_folder_path", imageDir))
            or imageDir
        )
        self.update_output_folder_label()
        caption_mode = self.normalize_output_caption_mode(
            figures.get("output_caption_mode", CAPTION_MODE_NONE), figures
        )
        self.set_dropdown_value(self.caption_mode_combo, caption_mode)
        self.update_caption_table_visibility()


        self.college_name.setText(str(cover.get("CollegeName", DEFAULT_COLLEGE_NAME)))
        self.college_address.setText(str(cover.get("Address", DEFAULT_COLLEGE_ADDRESS)))
        self.student_name.setText(str(cover.get("StudentName", "")))
        self.roll.setText(str(cover.get("Roll", "")))
        self.section_entry.setText(str(cover.get("Section", "")))
        self.semester.setText(str(cover.get("Semester", "")))
        self.teacher_name.setText(str(cover.get("TeacherName", "")))
        self.project_title.setText(str(cover.get("ProjectTitle", "")))


        self.logo_selected = bool(cover.get("logo_selected", False)) or os.path.exists(
            os.path.join(baseDir, "logo.png")
        )
        if hasattr(self, "logo_status_label"):
            self.logo_status_label.setText(
                "Current logo: logo.png"
                if self.logo_selected
                else "No logo selected."
            )
        self.update_cover_generate_state()
        self.generate_cover.setChecked(
            bool(cover.get("generate_cover_page", False)) and self.generate_cover.isEnabled()
        )


        self.toc_text.setPlainText(str(toc.get("toc_text", "")))
        if hasattr(self, "toc_mode_combo"):
            self.set_dropdown_value(
                self.toc_mode_combo, toc.get("toc_source_mode", TOC_MODE_MANUAL)
            )
        if hasattr(self, "toc_file_label"):
            self.toc_file_path = str(toc.get("toc_file_path", "") or "")
            self.toc_file_label.setText(
                f"Selected file: {self.toc_file_path}" if self.toc_file_path else "No file selected."
            )
        if hasattr(self, "keep_toc_label"):
            self.keep_toc_label.setChecked(bool(toc.get("keep_existing_label", False)))
        self.update_toc_mode_visibility()
        self.generate_toc.setChecked(
            bool(toc.get("generate_table_of_content", False)) and self.generate_toc.isEnabled()
        )


        self.code_line_height.setText(str(code.get("line_height", "")))
        self.code_file_ext.setText(str(code.get("file_extension", "")))
        self.code_folder_path = str(
            code.get("code_folder_path", getattr(self, "code_folder_path", codeDir))
            or codeDir
        )
        self.update_code_folder_label()
        self.generate_code_page.setChecked(
            bool(code.get("generate_code_page", False)) and self.generate_code_page.isEnabled()
        )
        self.update_code_generate_state()
        self.update_section_enabled_states()
        self.output_after_code.setChecked(
            bool(code.get("output_after_code", False)) and self.output_after_code.isEnabled()
        )


        self.watermark_name.setText(str(watermark.get("name", "")))
        self.update_watermark_generate_state()
        self.generate_watermark.setChecked(
            bool(watermark.get("generate_watermark", False)) and self.generate_watermark.isEnabled()
        )


        os.makedirs(jsonDir, exist_ok=True)
        with open(captionsPath, "w", encoding="utf-8") as f:
            json.dump(output_captions, f, indent=4)
        self.refresh_caption_table(show_message=False)
        self.update_caption_table_visibility()


        with open(
            os.path.join(jsonDir, "last_imported_configuration.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(data, f, indent=4)
        with open(
            os.path.join(jsonDir, "last_imported_raw_configuration.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(raw_data, f, indent=4)

        QApplication.processEvents()

        return {
            "student": self.student_name.text(),
            "project": self.project_title.text(),
            "roll": self.roll.text(),
            "section": self.section_entry.text(),
            "semester": self.semester.text(),
            "teacher": self.teacher_name.text(),
            "toc_mode": (
                self.toc_mode_combo.currentText() if hasattr(self, "toc_mode_combo") else ""
            ),
            "code_folder": self.selected_code_folder(),
            "output_folder": self.selected_output_folder(),
            "watermark": self.watermark_name.text(),
        }


    def coerce_imported_configuration_root(self, data):
        section_names = {
            "Margins",
            "Typography",
            "Export",
            "Figures",
            "CoverPage",
            "TableOfContent",
            "CodePage",
            "Watermark",
            "OutputCaptions",
        }

        if isinstance(data, dict):
            return data

        if isinstance(data, list):

            if all(isinstance(item, (list, tuple)) and len(item) == 2 for item in data):
                return {str(key): value for key, value in data}


            if len(data) == 1 and isinstance(data[0], dict):
                return data[0]


            merged = {}
            for item in data:
                if isinstance(item, dict):
                    if any(key in item for key in section_names):
                        return item
                    merged.update(item)
            if merged:
                return merged

        raise ValueError(
            "The selected file does not contain report settings. "
            "Choose a JSON file created with File > Save Settings."
        )


    def config_section_names(self):
        return {
            "Margins",
            "Typography",
            "Export",
            "Figures",
            "CoverPage",
            "TableOfContent",
            "CodePage",
            "Watermark",
            "OutputCaptions",
        }


    def config_section_alias_groups(self):
        return [
            ("Margins", "margins", "Margin"),
            ("Typography", "typography", "Font", "font"),
            ("Export", "export"),
            ("Figures", "figures", "Figure", "figure"),
            ("CoverPage", "cover_page", "coverPage", "FrontPage", "front_page"),
            ("TableOfContent", "Table_Of_Content", "table_of_content", "toc", "TOC"),
            ("CodePage", "code_page", "code", "Code"),
            ("Watermark", "watermark"),
            ("OutputCaptions", "output_captions", "captions"),
        ]


    def raw_config_section_count(self, value):
        if not isinstance(value, dict):
            return 0
        count = 0
        for aliases in self.config_section_alias_groups():
            section = self.normalize_section(value, *aliases)
            if isinstance(section, dict) and len(section) > 0:
                count += 1
            elif isinstance(section, list) and len(section) > 0:
                count += 1
        return count


    def has_report_config_marker(self, value):
        if not isinstance(value, dict):
            return False
        marker = value.get("_config_type", "")
        return self.normalized_config_key(marker) == self.normalized_config_key(
            "Document Formatter Report Configuration"
        )


    def is_report_configuration_payload(self, value):
        return isinstance(value, dict) and (
            self.has_report_config_marker(value) or self.raw_config_section_count(value) > 0
        )


    def extract_configuration_payload(self, raw_data):

        try:
            root = self.coerce_imported_configuration_root(raw_data)
        except Exception:
            root = raw_data

        if self.is_report_configuration_payload(root):
            return root

        found = self.find_config_object_in_json(raw_data)
        if found and self.is_report_configuration_payload(found):
            return found

        raise ValueError(
            "This JSON file does not contain report settings. "
            "Save the settings first, then import that JSON file. "
            "Report history files cannot restore the form."
        )


    def score_config_candidate(self, value):
        if not isinstance(value, dict):
            return 0

        return self.raw_config_section_count(value)


    def config_user_value_score(self, value):

        if not isinstance(value, dict):
            return 0

        score = 0
        cover = value.get("CoverPage", {}) if isinstance(value.get("CoverPage", {}), dict) else {}
        for key in [
            "CollegeName",
            "Address",
            "StudentName",
            "Roll",
            "Section",
            "Semester",
            "TeacherName",
            "ProjectTitle",
        ]:
            if str(cover.get(key, "")).strip():
                score += 10

        toc = (
            value.get("TableOfContent", {})
            if isinstance(value.get("TableOfContent", {}), dict)
            else {}
        )
        if str(toc.get("toc_text", "")).strip():
            score += 8
        if str(toc.get("toc_file_path", "")).strip():
            score += 5
        if bool(toc.get("generate_table_of_content", False)):
            score += 2

        code = value.get("CodePage", {}) if isinstance(value.get("CodePage", {}), dict) else {}
        if str(code.get("line_height", "")).strip():
            score += 4
        if str(code.get("code_folder_path", "")).strip():
            score += 2
        if bool(code.get("generate_code_page", False)):
            score += 2
        if bool(code.get("output_after_code", False)):
            score += 1

        watermark = (
            value.get("Watermark", {}) if isinstance(value.get("Watermark", {}), dict) else {}
        )
        if str(watermark.get("name", "")).strip():
            score += 8
        if bool(watermark.get("generate_watermark", False)):
            score += 2

        figures = value.get("Figures", {}) if isinstance(value.get("Figures", {}), dict) else {}
        for key in ["output_caption_mode", "output_folder_path"]:
            if str(figures.get(key, "")).strip():
                score += 2
        if bool(figures.get("include_figure_labels", False)):
            score += 1
        if bool(figures.get("generate_output_pages", False)):
            score += 1

        captions = (
            value.get("OutputCaptions", {})
            if isinstance(value.get("OutputCaptions", {}), dict)
            else {}
        )
        score += min(10, len([v for v in captions.values() if str(v).strip()]))

        margins = value.get("Margins", {}) if isinstance(value.get("Margins", {}), dict) else {}
        for key in ["top", "bottom", "left", "right"]:
            if str(margins.get(key, "")).strip():
                score += 1

        typography = (
            value.get("Typography", {}) if isinstance(value.get("Typography", {}), dict) else {}
        )
        if str(typography.get("font_family", "")).strip():
            score += 1

        return score


    def find_config_object_in_json(self, data):

        best = None
        best_section_score = 0
        best_user_score = -1


        def visit(value):
            nonlocal best, best_section_score, best_user_score
            if isinstance(value, dict):
                if self.is_report_configuration_payload(value):
                    canonical = self.normalize_imported_configuration(value)
                    section_score = self.score_config_candidate(canonical)
                    user_score = self.config_user_value_score(canonical)
                    if (self.has_report_config_marker(value) or section_score > 0) and (
                        user_score > best_user_score
                        or (user_score == best_user_score and section_score > best_section_score)
                    ):
                        best = value
                        best_section_score = section_score
                        best_user_score = user_score
                for child in value.values():
                    visit(child)
            elif isinstance(value, list):
                if all(isinstance(item, (list, tuple)) and len(item) == 2 for item in value):
                    try:
                        candidate = {str(key): val for key, val in value}
                        visit(candidate)
                    except Exception:
                        pass
                for child in value:
                    visit(child)

        visit(data)
        return best if best_section_score > 0 else None


    def load_json_file_safely(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)


    def file_priority_for_config(self, file_path, selected_path=None):
        name = os.path.basename(file_path).lower()
        priority = 0
        if selected_path and os.path.normcase(os.path.abspath(file_path)) == os.path.normcase(
            os.path.abspath(selected_path)
        ):
            priority += 20
        if name == "saved_report_configuration.json":
            priority += 15
        if name == "last_saved_configuration.json":
            priority += 12
        if name == "last_imported_configuration.json":
            priority += 8
        if name == "config_data.json":
            priority -= 10
        return priority


    def find_configuration_from_paths(self, paths, selected_path=None):
        checked = []
        best_config = None
        best_path = None
        best_rank = None

        for path in paths:
            if not path or not os.path.exists(path):
                continue
            checked.append(path)
            try:
                data = self.load_json_file_safely(path)
                found = self.find_config_object_in_json(data)
                if not found:
                    continue

                user_score = self.config_user_value_score(found)
                section_score = self.score_config_candidate(found)
                priority = self.file_priority_for_config(path, selected_path)
                rank = (user_score, priority, section_score)

                if best_rank is None or rank > best_rank:
                    best_config = found
                    best_path = path
                    best_rank = rank
            except Exception:
                continue


        if best_config is not None and best_rank and best_rank[0] > 0:
            return best_config, best_path, checked

        return None, None, checked


    def candidate_configuration_paths(self, selected_path=None):
        paths = []
        folders_to_scan = []

        if selected_path:
            paths.append(selected_path)
            folders_to_scan.append(os.path.dirname(selected_path))

        folders_to_scan.extend(
            [
                baseDir,
                os.path.join(baseDir, "JsonFile"),
            ]
        )

        fixed_names = [
            "saved_report_configuration.json",
            "last_saved_configuration.json",
            "last_imported_configuration.json",
            "config_data.json",
        ]

        for folder in folders_to_scan:
            if not folder:
                continue
            for name in fixed_names:
                paths.append(os.path.join(folder, name))


            if os.path.isdir(folder):
                try:
                    for name in os.listdir(folder):
                        if name.lower().endswith(".json"):
                            paths.append(os.path.join(folder, name))
                except Exception:
                    pass

        unique = []
        seen = set()
        for path in paths:
            norm = os.path.normcase(os.path.abspath(path))
            if norm not in seen:
                seen.add(norm)
                unique.append(path)
        return unique


    def import_configuration_from_path_or_nearby(self, selected_path=None):




        if selected_path:
            raw_data = self.load_json_file_safely(selected_path)
            payload = self.extract_configuration_payload(raw_data)
            config = self.normalize_imported_configuration(payload)
            restored = self.import_exact_saved_configuration(config)
            return restored, selected_path

        paths = self.candidate_configuration_paths(selected_path)
        config, source_path, checked = self.find_configuration_from_paths(paths, selected_path)
        if not config:
            checked_text = "\n".join(checked[:12]) if checked else "No settings files were found."
            raise ValueError(
                "No saved report settings were found.\n\n"
                "The available JSON files were empty or did not contain report settings.\n\n"
                "Complete the form, use File > Save Settings, and import the saved file.\n\n"
                "Checked:\n" + checked_text
            )
        restored = self.import_exact_saved_configuration(
            self.normalize_imported_configuration(config)
        )
        return restored, source_path


    def import_exact_saved_configuration(self, data):
        if not isinstance(data, dict) or not any(
            section in data for section in self.config_section_names()
        ):
            found = self.find_config_object_in_json(data)
            if found:
                data = found

        required_sections = [
            "Margins",
            "Typography",
            "Export",
            "Figures",
            "CoverPage",
            "TableOfContent",
            "CodePage",
            "Watermark",
            "OutputCaptions",
        ]
        if not any(section in data for section in required_sections):
            raise ValueError("This JSON file does not contain the required report settings.")


        def section(name):
            value = data.get(name, {})
            return value if isinstance(value, dict) else {}

        margins = section("Margins")
        typography = section("Typography")
        export = section("Export")
        figures = section("Figures")
        cover = section("CoverPage")
        toc = section("TableOfContent")
        code = section("CodePage")
        watermark = section("Watermark")
        captions = section("OutputCaptions")

        self._importing_configuration = True
        try:

            self.margin_top["entry"].setText(str(margins.get("top", "")))
            self.margin_bottom["entry"].setText(str(margins.get("bottom", "")))
            self.margin_left["entry"].setText(str(margins.get("left", "")))
            self.margin_right["entry"].setText(str(margins.get("right", "")))
            self.default_margin.setChecked(bool(margins.get("use_default", True)))

            self.set_dropdown_value(
                self.font_combo, typography.get("font_family", "Times New Roman")
            )
            self.set_dropdown_value(self.export_combo, export.get("format", "PDF"))
            self.final_report_path = str(
                export.get(
                    "final_pdf_path",
                    export.get("output_pdf_path", getattr(self, "final_report_path", finalPdfPath)),
                )
                or finalPdfPath
            )
            self.update_final_report_path_label()


            self.include_figure.setChecked(bool(figures.get("include_figure_labels", False)))
            if hasattr(self, "generate_output_pages"):
                self.generate_output_pages.setChecked(
                    bool(figures.get("generate_output_pages", False))
                )
            self.output_folder_path = str(
                figures.get(
                    "output_folder_path", getattr(self, "output_folder_path", imageDir)
                )
                or imageDir
            )
            self.update_output_folder_label()
            caption_mode = self.normalize_output_caption_mode(
                figures.get("output_caption_mode", CAPTION_MODE_NONE), figures
            )
            self.set_dropdown_value(self.caption_mode_combo, caption_mode)


            self.college_name.setText(str(cover.get("CollegeName", DEFAULT_COLLEGE_NAME)))
            self.college_address.setText(str(cover.get("Address", DEFAULT_COLLEGE_ADDRESS)))
            self.student_name.setText(str(cover.get("StudentName", "")))
            self.roll.setText(str(cover.get("Roll", "")))
            self.section_entry.setText(str(cover.get("Section", "")))
            self.semester.setText(str(cover.get("Semester", "")))
            self.teacher_name.setText(str(cover.get("TeacherName", "")))
            self.project_title.setText(str(cover.get("ProjectTitle", "")))

            self.logo_selected = bool(cover.get("logo_selected", False)) or os.path.exists(
                os.path.join(baseDir, "logo.png")
            )
            if hasattr(self, "logo_status_label"):
                self.logo_status_label.setText(
                    "Current logo: logo.png"
                    if self.logo_selected
                    else "No logo selected."
                )
            self.update_cover_generate_state()
            self.generate_cover.setChecked(
                bool(cover.get("generate_cover_page", False)) and self.generate_cover.isEnabled()
            )


            self.toc_text.setPlainText(str(toc.get("toc_text", "")))
            if hasattr(self, "toc_mode_combo"):
                self.set_dropdown_value(
                    self.toc_mode_combo, toc.get("toc_source_mode", TOC_MODE_MANUAL)
                )
            self.toc_file_path = str(toc.get("toc_file_path", "") or "")
            if hasattr(self, "toc_file_label"):
                self.toc_file_label.setText(
                    f"Selected file: {self.toc_file_path}"
                    if self.toc_file_path
                    else "No file selected."
                )
            if hasattr(self, "keep_toc_label"):
                self.keep_toc_label.setChecked(bool(toc.get("keep_existing_label", False)))


            self.code_line_height.setText(str(code.get("line_height", "")))
            self.code_file_ext.setText(str(code.get("file_extension", "")))
            self.code_folder_path = str(
                code.get("code_folder_path", getattr(self, "code_folder_path", codeDir))
                or codeDir
            )
            self.update_code_folder_label()


            self.watermark_name.setText(str(watermark.get("name", "")))


            os.makedirs(jsonDir, exist_ok=True)
            with open(captionsPath, "w", encoding="utf-8") as f:
                json.dump(captions if isinstance(captions, dict) else {}, f, indent=4)


            self.update_cover_generate_state()
            self.update_toc_mode_visibility()
            self.update_code_generate_state()
            self.update_watermark_generate_state()
            self.update_caption_table_visibility()
            self.refresh_caption_table(show_message=False)


            self.generate_cover.setChecked(
                bool(cover.get("generate_cover_page", False)) and self.generate_cover.isEnabled()
            )
            self.generate_toc.setChecked(
                bool(toc.get("generate_table_of_content", False)) and self.generate_toc.isEnabled()
            )
            self.generate_code_page.setChecked(
                bool(code.get("generate_code_page", False)) and self.generate_code_page.isEnabled()
            )
            self.generate_watermark.setChecked(
                bool(watermark.get("generate_watermark", False))
                and self.generate_watermark.isEnabled()
            )
            self.update_section_enabled_states()
            self.output_after_code.setChecked(
                bool(code.get("output_after_code", False)) and self.output_after_code.isEnabled()
            )


            with open(
                os.path.join(jsonDir, "last_imported_configuration.json"), "w", encoding="utf-8"
            ) as f:
                json.dump(data, f, indent=4)

            self.repaint()
            for widget in [
                self.margin_top["entry"],
                self.margin_bottom["entry"],
                self.margin_left["entry"],
                self.margin_right["entry"],
                self.college_name,
                self.college_address,
                self.student_name,
                self.roll,
                self.section_entry,
                self.semester,
                self.teacher_name,
                self.project_title,
                self.toc_text,
                self.code_line_height,
                self.watermark_name,
            ]:
                try:
                    widget.repaint()
                except Exception:
                    pass
            QApplication.processEvents()

            return {
                "student": self.student_name.text(),
                "project": self.project_title.text(),
                "roll": self.roll.text(),
                "section": self.section_entry.text(),
                "semester": self.semester.text(),
                "teacher": self.teacher_name.text(),
                "code_folder": self.selected_code_folder(),
                "output_folder": self.selected_output_folder(),
                "save_pdf": self.selected_final_report_path(),
                "watermark": self.watermark_name.text(),
                "toc_mode": (
                    self.toc_mode_combo.currentText() if hasattr(self, "toc_mode_combo") else ""
                ),
            }
        finally:
            self._importing_configuration = False


    def load_placed_configuration_action(self):
        try:
            restored, source_path = self.import_configuration_from_path_or_nearby(None)
            message = (
                f"Settings loaded from:\n{source_path}\n\n"
                f"Student: {restored.get('student') or '-'}\n"
                f"Project: {restored.get('project') or '-'}\n"
                f"Code folder: {restored.get('code_folder') or '-'}\n"
                f"Image folder: {restored.get('output_folder') or '-'}\n"
                f"Save as: {restored.get('save_pdf') or self.selected_final_report_path()}\n"
                f"Watermark: {restored.get('watermark') or '-'}"
            )
            self.show_themed_message("Settings Loaded", message, "document.svg")
        except Exception as exc:
            self.show_themed_error("Load Failed", f"Could not load settings.\n{exc}")


    #load saved settings
    def import_configuration_action(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Import Settings", baseDir, "JSON Files (*.json)"
            )
            if not file_path:
                return

            restored, source_path = self.import_configuration_from_path_or_nearby(file_path)

            message = (
                f"Settings imported successfully.\n\n"
                f"Loaded from: {source_path}\n\n"
                f"Student: {restored.get('student') or '-'}\n"
                f"Roll: {restored.get('roll') or '-'}\n"
                f"Section: {restored.get('section') or '-'}\n"
                f"Semester: {restored.get('semester') or '-'}\n"
                f"Teacher: {restored.get('teacher') or '-'}\n"
                f"Project: {restored.get('project') or '-'}\n"
                f"Contents source: {restored.get('toc_mode') or '-'}\n"
                f"Code folder: {restored.get('code_folder') or '-'}\n"
                f"Image folder: {restored.get('output_folder') or '-'}\n"
                f"Save as: {restored.get('save_pdf') or self.selected_final_report_path()}\n"
                f"Watermark: {restored.get('watermark') or '-'}"
            )
            self.show_themed_message("Settings Imported", message, "document.svg")
        except Exception as exc:
            self.show_themed_error(
                "Import Failed",
                f"Could not import settings.\n{exc}\n\n"
                "Select a JSON file created with File > Save Settings.",
            )


    def safe_int(self, value, fallback):
        try:
            return int(str(value).strip())
        except Exception:
            return fallback


    def clean_value(self, widget):
        return widget.text().strip()


    def update_toc_mode_visibility(self):
        is_browse = (
            hasattr(self, "toc_mode_combo") and self.toc_mode_combo.currentText() == TOC_MODE_BROWSE
        )
        if hasattr(self, "toc_manual_container"):
            self.toc_manual_container.setVisible(not is_browse)
        if hasattr(self, "toc_browse_container"):
            self.toc_browse_container.setVisible(is_browse)
        self.update_toc_generate_state()


    def browse_toc_file_action(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Browse Table of Content",
            baseDir,
            "TOC Files (*.txt *.docx);;Text Files (*.txt);;Word Documents (*.docx)",
        )
        if not file_path:
            return
        self.toc_file_path = file_path
        if hasattr(self, "toc_file_label"):
            self.toc_file_label.setText(f"Selected file: {file_path}")
        self.validate_toc_file_labels()


    def format_docx_number(self, value, fmt):
        value = int(value)
        fmt = str(fmt or "decimal")
        if fmt == "lowerLetter":
            result = ""
            n = value
            while n > 0:
                n -= 1
                result = chr(ord("a") + (n % 26)) + result
                n //= 26
            return result or "a"
        if fmt == "upperLetter":
            return self.format_docx_number(value, "lowerLetter").upper()
        if fmt == "lowerRoman":
            pairs = [
                (1000, "m"),
                (900, "cm"),
                (500, "d"),
                (400, "cd"),
                (100, "c"),
                (90, "xc"),
                (50, "l"),
                (40, "xl"),
                (10, "x"),
                (9, "ix"),
                (5, "v"),
                (4, "iv"),
                (1, "i"),
            ]
            result = ""
            n = value
            for number, roman in pairs:
                while n >= number:
                    result += roman
                    n -= number
            return result or "i"
        if fmt == "upperRoman":
            return self.format_docx_number(value, "lowerRoman").upper()
        return str(value)


    def read_docx_toc_lines(self, file_path):
        try:
            from zipfile import ZipFile
            from lxml import etree

            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            with ZipFile(file_path) as z:
                document_xml = etree.fromstring(z.read("word/document.xml"))
                numbering_xml = (
                    etree.fromstring(z.read("word/numbering.xml"))
                    if "word/numbering.xml" in z.namelist()
                    else None
                )

            num_to_abs = {}
            level_info = {}
            if numbering_xml is not None:
                for num in numbering_xml.xpath("//w:num", namespaces=ns):
                    num_id = num.get("{%s}numId" % ns["w"])
                    abs_node = num.find("w:abstractNumId", ns)
                    if abs_node is not None:
                        num_to_abs[num_id] = abs_node.get("{%s}val" % ns["w"])
                for abs_num in numbering_xml.xpath("//w:abstractNum", namespaces=ns):
                    abs_id = abs_num.get("{%s}abstractNumId" % ns["w"])
                    for lvl in abs_num.findall("w:lvl", ns):
                        ilvl = int(lvl.get("{%s}ilvl" % ns["w"], "0"))
                        fmt_node = lvl.find("w:numFmt", ns)
                        text_node = lvl.find("w:lvlText", ns)
                        start_node = lvl.find("w:start", ns)
                        level_info[(abs_id, ilvl)] = {
                            "fmt": (
                                fmt_node.get("{%s}val" % ns["w"])
                                if fmt_node is not None
                                else "decimal"
                            ),
                            "text": (
                                text_node.get("{%s}val" % ns["w"])
                                if text_node is not None
                                else f"%{ilvl+1}."
                            ),
                            "start": (
                                int(start_node.get("{%s}val" % ns["w"]))
                                if start_node is not None
                                else 1
                            ),
                        }

            counters = {}
            numbered_lines = []
            plain_lines = []
            for p in document_xml.xpath("//w:body/w:p", namespaces=ns):
                text = "".join(p.xpath(".//w:t/text()", namespaces=ns)).strip()
                if not text:
                    continue
                num_pr = p.find("w:pPr/w:numPr", ns)
                if num_pr is None:
                    plain_lines.append(text)
                    continue
                num_id_node = num_pr.find("w:numId", ns)
                ilvl_node = num_pr.find("w:ilvl", ns)
                if num_id_node is None:
                    plain_lines.append(text)
                    continue
                num_id = num_id_node.get("{%s}val" % ns["w"])
                ilvl = int(ilvl_node.get("{%s}val" % ns["w"])) if ilvl_node is not None else 0
                abs_id = num_to_abs.get(num_id)
                counter = counters.setdefault(num_id, {})
                info = level_info.get(
                    (abs_id, ilvl), {"fmt": "decimal", "text": f"%{ilvl+1}.", "start": 1}
                )
                counter[ilvl] = counter.get(ilvl, info.get("start", 1) - 1) + 1
                for deeper in list(counter.keys()):
                    if deeper > ilvl:
                        del counter[deeper]
                label = info.get("text", f"%{ilvl+1}.")
                for level in range(ilvl + 1):
                    level_data = level_info.get((abs_id, level), {"fmt": "decimal", "start": 1})
                    number = counter.get(level, level_data.get("start", 1))
                    label = label.replace(
                        f"%{level+1}",
                        self.format_docx_number(number, level_data.get("fmt", "decimal")),
                    )
                label = label.strip().rstrip(".")
                numbered_lines.append(f"{label}. {text}")

            if numbered_lines:
                return numbered_lines
            return plain_lines
        except Exception:
            try:
                from docx import Document

                document = Document(file_path)
                return [p.text.strip() for p in document.paragraphs if p.text.strip()]
            except Exception as exc:
                raise ValueError(f"Could not read DOCX table-of-content file.\n{exc}") from exc


    def toc_line_has_existing_label(self, line):
        return self.detect_toc_label(line) is not None


    def toc_label_validation_errors(self):
        mode = (
            self.toc_mode_combo.currentText()
            if hasattr(self, "toc_mode_combo")
            else TOC_MODE_MANUAL
        )
        if mode != TOC_MODE_BROWSE:
            return []
        file_path = getattr(self, "toc_file_path", "")
        if not file_path:
            return ["Please browse and select a table-of-content file first."]
        if not os.path.exists(file_path):
            return [f"Selected file does not exist: {file_path}"]

        try:
            lines = self.read_toc_source_lines()
        except Exception as exc:
            return [str(exc)]

        non_empty_lines = [str(line).strip() for line in lines if str(line).strip()]
        if not non_empty_lines:
            return ["The selected TOC file does not contain readable entries."]

        return []


    def validate_toc_file_labels(self, *args, show_message=False):
        mode = (
            self.toc_mode_combo.currentText()
            if hasattr(self, "toc_mode_combo")
            else TOC_MODE_MANUAL
        )
        is_browse = mode == TOC_MODE_BROWSE

        if not hasattr(self, "toc_label_status"):
            return True

        if not is_browse:
            keep_existing = hasattr(self, "keep_toc_label") and self.keep_toc_label.isChecked()
            if keep_existing:
                self.toc_label_status.setText(
                    "Existing numbering will be kept where possible. Other entries will be numbered automatically."
                )
            else:
                self.toc_label_status.setText(
                    "All entries will be numbered automatically."
                )
            self.toc_label_status.setStyleSheet(
                "color: #0067C0; font-size: 12px; font-weight: 500;"
            )
            return True

        file_path = getattr(self, "toc_file_path", "")
        if not file_path or not os.path.exists(file_path):
            self.toc_label_status.setText(
                "Select a valid TOC file. Entries without numbering will be numbered automatically."
            )
            self.toc_label_status.setStyleSheet(
                "color: #B42318; font-size: 12px; font-weight: 600;"
            )
            if show_message:
                self.show_themed_error(
                    "TOC File Required",
                    "Select a valid table-of-contents file.",
                )
            return False

        errors = self.toc_label_validation_errors()
        if errors:
            self.toc_label_status.setText("TOC validation failed: " + errors[0])
            self.toc_label_status.setStyleSheet(
                "color: #B42318; font-size: 12px; font-weight: 600;"
            )
            if show_message:
                self.show_themed_error("TOC Validation Failed", errors[0])
            return False

        keep_existing = hasattr(self, "keep_toc_label") and self.keep_toc_label.isChecked()
        if keep_existing:
            self.toc_label_status.setText(
                "TOC file selected. Existing numbering will be kept where possible."
            )
        else:
            self.toc_label_status.setText(
                "TOC file selected. Entries will be numbered automatically."
            )
        self.toc_label_status.setStyleSheet("color: #0067C0; font-size: 12px; font-weight: 500;")
        return True


    def read_toc_source_lines(self):
        mode = (
            self.toc_mode_combo.currentText()
            if hasattr(self, "toc_mode_combo")
            else TOC_MODE_MANUAL
        )
        if mode == TOC_MODE_MANUAL:
            return self.toc_text.toPlainText().splitlines()

        file_path = getattr(self, "toc_file_path", "")
        if not file_path:
            raise ValueError("Select a table-of-contents file.")
        if not os.path.exists(file_path):
            raise ValueError(f"The selected table-of-contents file was not found:\n{file_path}")

        lower = file_path.lower()
        if lower.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read().splitlines()
        if lower.endswith(".docx"):
            return self.read_docx_toc_lines(file_path)
        raise ValueError("Unsupported file type. Choose a TXT or DOCX file.")


    def normalize_toc_label(self, label):
        label = re.sub(r"\s+", " ", str(label).strip())
        label = label.rstrip(".:-)] ").strip()
        lab_match = re.match(r"^(lab)\s*(.+)$", label, flags=re.IGNORECASE)
        if lab_match:
            rest = lab_match.group(2).strip().rstrip(".:-)] ").strip()
            return f"Lab {rest}" if rest else "Lab"
        return label


    def detect_toc_label(self, line):
        line = str(line).strip()
        if not line:
            return None


        punctuation_match = re.match(
            r"^(?P<label>(?:lab\s*)?(?:\d+(?:\.\d+)*|[A-Za-z]))\s*[:\)\]\-–—]\s*(?P<question>.+)$",
            line,
            flags=re.IGNORECASE,
        )
        if punctuation_match:
            return (
                self.normalize_toc_label(punctuation_match.group("label")),
                punctuation_match.group("question").strip(),
            )


        dot_match = re.match(
            r"^(?P<label>(?:lab\s*)?(?:\d+(?:\.\d+)*|[A-Za-z]))\.\s+(?P<question>.+)$",
            line,
            flags=re.IGNORECASE,
        )
        if dot_match:
            return (
                self.normalize_toc_label(dot_match.group("label")),
                dot_match.group("question").strip(),
            )

        return None


    def parse_toc_line(self, line, serial, keep_existing_label):
        line = str(line).strip()
        if not line:
            return None

        detected = self.detect_toc_label(line)
        if detected:
            existing_label, question = detected
            label = existing_label if keep_existing_label else str(serial)
            return label, question

        return str(serial), line


    def build_toc_dict(self):
        keep_existing = hasattr(self, "keep_toc_label") and self.keep_toc_label.isChecked()
        mode = (
            self.toc_mode_combo.currentText()
            if hasattr(self, "toc_mode_combo")
            else TOC_MODE_MANUAL
        )
        if mode == TOC_MODE_BROWSE:
            errors = self.toc_label_validation_errors()
            if errors:
                raise ValueError(errors[0])
        lines = self.read_toc_source_lines()
        toc_dict = {}
        serial = 1
        for line in lines:
            parsed = self.parse_toc_line(line, serial, keep_existing)
            if not parsed:
                continue
            label, question = parsed
            if question:
                toc_dict[label] = question
                serial += 1
        if not toc_dict:
            raise ValueError("No valid table-of-contents entries were found.")
        toc_dict["font_family"] = self.font_combo.currentText()
        return toc_dict


    def confirmation_settings_text(self):
        output_pages_enabled = self.generate_output_pages.isChecked()
        lines = [
            "Review the report settings before generation:",
            "",
            "Page order: Cover > Contents > Code > Output",
            "",
            f"Cover page: {'Yes' if self.generate_cover.isChecked() else 'No'}",
            f"Table of contents: {'Yes' if self.generate_toc.isChecked() else 'No'}",
            f"TOC source: {self.toc_mode_combo.currentText() if hasattr(self, 'toc_mode_combo') else 'Manual'}",
            f"Code pages: {'Yes' if self.generate_code_page.isChecked() else 'No'}",
            f"Output images: {'Yes' if output_pages_enabled else 'No'}",
        ]
        if output_pages_enabled:
            lines.extend(
                [
                    f"Image folder: {self.selected_output_folder()}",
                    f"Caption style: {self.caption_mode_combo.currentText()}",
                    f"Show figure numbers: {'Yes' if self.include_figure.isChecked() else 'No'}",
                ]
            )
        if output_pages_enabled:
            lines.append(
                f"Place output after code: {'Yes' if self.output_after_code.isChecked() else 'No'}"
            )
        lines.extend(
            [
                f"Watermark: {'Yes' if self.generate_watermark.isChecked() else 'No'}",
                f"Save as: {self.selected_final_report_path()}",
                "",
                "Generate the final PDF?",
            ]
        )
        return "\n".join(lines)


    def confirm_proceed_settings(self):
        return self.show_themed_confirm(
            "Confirm Report Generation", self.confirmation_settings_text()
        )


    def set_widgets_enabled(self, widgets, enabled):
        for widget in widgets:
            if widget is not None:
                try:
                    widget.setEnabled(enabled)
                except Exception:
                    pass


    def update_section_enabled_states(self, *args):
        cover_enabled = hasattr(self, "generate_cover") and self.generate_cover.isChecked()
        self.set_widgets_enabled(
            [
                getattr(self, "college_name", None),
                getattr(self, "college_address", None),
                getattr(self, "student_name", None),
                getattr(self, "roll", None),
                getattr(self, "section_entry", None),
                getattr(self, "semester", None),
                getattr(self, "teacher_name", None),
                getattr(self, "project_title", None),
                getattr(self, "add_logo_btn", None),
            ],
            cover_enabled,
        )

        toc_enabled = hasattr(self, "generate_toc") and self.generate_toc.isChecked()
        self.set_widgets_enabled(
            [
                getattr(self, "toc_mode_combo", None),
                getattr(self, "toc_manual_container", None),
                getattr(self, "toc_browse_container", None),
                getattr(self, "keep_toc_label_row", None),
                getattr(self, "keep_toc_label", None),
            ],
            toc_enabled,
        )

        code_enabled = hasattr(self, "generate_code_page") and self.generate_code_page.isChecked()
        self.set_widgets_enabled(
            [
                getattr(self, "code_line_height", None),
                getattr(self, "code_file_ext", None),
                getattr(self, "code_folder_row", None),
                getattr(self, "code_folder_label", None),
                getattr(self, "browse_code_folder_btn", None),
            ],
            code_enabled,
        )

        output_enabled = (
            hasattr(self, "generate_output_pages") and self.generate_output_pages.isChecked()
        )
        self.set_widgets_enabled(
            [
                getattr(self, "output_folder_row", None),
                getattr(self, "output_folder_label", None),
                getattr(self, "browse_output_folder_btn", None),
                getattr(self, "include_figure", None),
                getattr(self, "caption_mode_combo", None),
                getattr(self, "caption_card", None),
                getattr(self, "caption_table", None),
                getattr(self, "caption_scroll", None),
                getattr(self, "refresh_captions_btn", None),
                getattr(self, "save_captions_btn", None),
                getattr(self, "clear_captions_btn", None),
            ],
            output_enabled,
        )

        output_after_code_enabled = output_enabled and code_enabled
        if hasattr(self, "output_after_code"):
            self.output_after_code.setEnabled(output_after_code_enabled)
            if not output_after_code_enabled and self.output_after_code.isChecked():
                self.output_after_code.setChecked(False)
        self.set_widgets_enabled(
            [getattr(self, "output_order_card", None)], output_after_code_enabled
        )

        watermark_enabled = (
            hasattr(self, "generate_watermark") and self.generate_watermark.isChecked()
        )
        self.set_widgets_enabled(
            [
                getattr(self, "watermark_name", None),
            ],
            watermark_enabled,
        )

        if hasattr(self, "caption_card"):
            self.update_caption_table_visibility()


    def nonempty_text(self, widget):
        try:
            return widget.text().strip()
        except Exception:
            return ""


    def cover_validation_errors(self):
        labels_and_widgets = [
            ("College Name", self.college_name),
            ("Address", self.college_address),
            ("Student Name", self.student_name),
            ("Roll", self.roll),
            ("Section", self.section_entry),
            ("Semester", self.semester),
            ("Teacher Name", self.teacher_name),
            ("Project Title", self.project_title),
        ]
        missing = [label for label, widget in labels_and_widgets if not self.nonempty_text(widget)]
        if missing:
            return ["Complete the following cover fields: " + ", ".join(missing)]
        if not (
            getattr(self, "logo_selected", False)
            or os.path.exists(os.path.join(baseDir, "logo.png"))
        ):
            return ["Logo is not selected. Click Add Logo before enabling cover page generation."]
        return []


    def update_cover_generate_state(self, *args):
        if not hasattr(self, "generate_cover"):
            return
        self.logo_selected = getattr(self, "logo_selected", False) or os.path.exists(
            os.path.join(baseDir, "logo.png")
        )
        if hasattr(self, "logo_status_label") and self.logo_selected:
            self.logo_status_label.setText("Current logo: logo.png")
        errors = self.cover_validation_errors()
        if errors:
            self.cover_validation_status.setText(errors[0])
            self.cover_validation_status.setStyleSheet(
                "color: #B42318; font-size: 12px; font-weight: 600;"
            )
        else:
            self.cover_validation_status.setText("Cover page details are complete.")
            self.cover_validation_status.setStyleSheet(
                "color: #027A48; font-size: 12px; font-weight: 600;"
            )


    def on_generate_cover_toggled(self, checked):
        self.update_section_enabled_states()
        self.update_cover_generate_state()


    def toc_manual_text(self):
        return self.toc_text.toPlainText().strip() if hasattr(self, "toc_text") else ""


    def update_toc_generate_state(self, *args):
        if not hasattr(self, "generate_toc"):
            return True
        mode = (
            self.toc_mode_combo.currentText()
            if hasattr(self, "toc_mode_combo")
            else TOC_MODE_MANUAL
        )
        if mode == TOC_MODE_MANUAL:
            if not self.toc_manual_text():
                if hasattr(self, "toc_manual_status"):
                    self.toc_manual_status.setText(
                        "Enter table-of-contents entries before generation."
                    )
                    self.toc_manual_status.setStyleSheet(
                        "color: #B42318; font-size: 12px; font-weight: 600;"
                    )
            else:
                if hasattr(self, "toc_manual_status"):
                    self.toc_manual_status.setText(
                        "Table-of-contents entries are ready."
                    )
                    self.toc_manual_status.setStyleSheet(
                        "color: #027A48; font-size: 12px; font-weight: 600;"
                    )
            self.validate_toc_file_labels()
            return bool(self.toc_manual_text())
        return self.validate_toc_file_labels()


    def on_generate_toc_toggled(self, checked):
        self.update_section_enabled_states()
        self.update_toc_generate_state()


    def count_code_files_for_extension(self):
        code_folder = (
            self.selected_code_folder() if hasattr(self, "selected_code_folder") else codeDir
        )
        if not os.path.isdir(code_folder):
            return 0, 0
        total = 0
        for root, dirs, files in os.walk(code_folder):
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".") and d not in {"__pycache__", "node_modules", ".git"}
            ]
            total += sum(1 for name in files if os.path.isfile(os.path.join(root, name)))
        matched = len(self.discover_auto_code_files())
        return matched, total


    def update_code_generate_state(self, *args):
        if not hasattr(self, "generate_code_page"):
            return
        line_height = self.code_line_height.text().strip()
        if self.generate_code_page.isChecked():
            self.code_line_height_status.setVisible(True)
            if not line_height:
                self.code_line_height_status.setText("Line height has not been entered.")
                self.code_line_height_status.setStyleSheet(
                    "color: #B42318; font-size: 12px; font-weight: 600;"
                )
            else:
                try:
                    line_height_value = int(line_height)
                except ValueError:
                    line_height_value = None
                if line_height_value is None:
                    self.code_line_height_status.setText("Line height must be a whole number.")
                    self.code_line_height_status.setStyleSheet(
                        "color: #B42318; font-size: 12px; font-weight: 600;"
                    )
                elif not 10 <= line_height_value <= 120:
                    self.code_line_height_status.setText(
                        "Line height must be between 10 and 120 points."
                    )
                    self.code_line_height_status.setStyleSheet(
                        "color: #B42318; font-size: 12px; font-weight: 600;"
                    )
                else:
                    self.code_line_height_status.setText(
                        f"Line height is {line_height_value} points as per user input."
                    )
                    self.code_line_height_status.setStyleSheet(
                        "color: #027A48; font-size: 12px; font-weight: 600;"
                    )
        else:
            self.code_line_height_status.clear()
            self.code_line_height_status.setVisible(False)
        matched, total = self.count_code_files_for_extension()
        if matched:
            self.code_file_status.setText(
                f"Found {matched} supported source-code or text file(s) out of {total} file(s)."
            )
            self.code_file_status.setStyleSheet(
                "color: #0067C0; font-size: 12px; font-weight: 500;"
            )
        else:
            self.code_file_status.setText(
                f"No supported source-code or text files found. Total files: {total}."
            )
            self.code_file_status.setStyleSheet(
                "color: #64748b; font-size: 12px; font-weight: 500;"
            )
        self.update_section_enabled_states()


    def on_generate_output_pages_toggled(self, checked):
        if (
            not checked
            and hasattr(self, "output_after_code")
            and self.output_after_code.isChecked()
        ):
            self.output_after_code.setChecked(False)
        self.update_section_enabled_states()


    def on_output_after_code_toggled(self, checked):
        if not checked:
            return
        if not self.generate_output_pages.isChecked():
            self.output_after_code.setChecked(False)
            self.show_themed_error(
                "Output Placement Unavailable",
                "Include output images before placing them after code.",
            )
            return
        if not self.generate_code_page.isChecked():
            self.output_after_code.setChecked(False)
            self.show_themed_error(
                "Output Placement Unavailable",
                "Include code pages before placing output images after code.",
            )
            return
        if not self.code_line_height.text().strip():
            self.output_after_code.setChecked(False)
            self.show_themed_error(
                "Output Placement Unavailable", "Enter the line height before placing output images after code."
            )


    def on_generate_code_toggled(self, checked):
        self.update_section_enabled_states()
        self.update_code_generate_state()


    def update_watermark_generate_state(self, *args):
        if not hasattr(self, "generate_watermark"):
            return
        if not self.watermark_name.text().strip():
            self.watermark_validation_status.setText("Enter watermark text.")
            self.watermark_validation_status.setStyleSheet(
                "color: #B42318; font-size: 12px; font-weight: 600;"
            )
        else:
            self.watermark_validation_status.setText("Watermark text is ready.")
            self.watermark_validation_status.setStyleSheet(
                "color: #027A48; font-size: 12px; font-weight: 600;"
            )
        self.update_section_enabled_states()


    def on_generate_watermark_toggled(self, checked):
        self.update_section_enabled_states()
        self.update_watermark_generate_state()


    def validate_enabled_sections_before_write(self):
        has_content = any(
            (
                self.generate_cover.isChecked(),
                self.generate_toc.isChecked(),
                self.generate_code_page.isChecked(),
                self.generate_output_pages.isChecked(),
            )
        )
        if not has_content:
            raise ValueError("Enable at least one report section.")

        missing_fonts = [
            name for name, font_path in required_font_files(self.font_combo.currentText())
            if not os.path.isfile(font_path)
        ]
        if missing_fonts:
            raise ValueError(
                "Place the following font file(s) in the Fonts folder: "
                + ", ".join(missing_fonts)
            )

        if not self.default_margin.isChecked():
            margin_values = {}
            for name, field in (
                ("top", self.margin_top["entry"]),
                ("bottom", self.margin_bottom["entry"]),
                ("left", self.margin_left["entry"]),
                ("right", self.margin_right["entry"]),
            ):
                value = field.text().strip()
                try:
                    margin_values[name] = int(value)
                except ValueError:
                    raise ValueError(f"Enter a whole number for the {name} margin.")
                if margin_values[name] < 0:
                    raise ValueError(f"The {name} margin cannot be negative.")
            if margin_values["left"] + margin_values["right"] >= 575:
                raise ValueError("The left and right margins leave no usable page width.")
            if margin_values["top"] + margin_values["bottom"] >= 822:
                raise ValueError("The top and bottom margins leave no usable page height.")

        if self.generate_cover.isChecked():
            errors = self.cover_validation_errors()
            if errors:
                raise ValueError(errors[0])
        if self.generate_toc.isChecked() and not self.update_toc_generate_state():
            raise ValueError("The table of contents is not ready.")
        if self.generate_code_page.isChecked():
            line_height_text = self.code_line_height.text().strip()
            try:
                line_height = int(line_height_text)
            except ValueError:
                raise ValueError("Enter a whole number for the code line height.")
            if not 10 <= line_height <= 120:
                raise ValueError("Code line height must be between 10 and 120 points.")
            code_folder = self.selected_code_folder()
            if not os.path.isdir(code_folder):
                raise ValueError("Select a valid code folder.")
            if not self.discover_auto_code_files():
                raise ValueError("The selected code folder contains no supported source-code or text files.")

        if self.generate_output_pages.isChecked():
            output_folder = self.selected_output_folder()
            if not os.path.isdir(output_folder):
                raise ValueError("Select a valid output image folder.")
            image_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".webp")
            output_images = [
                name for name in os.listdir(output_folder)
                if name.lower().endswith(image_extensions)
            ]
            if not output_images:
                raise ValueError("The selected output folder contains no supported images.")

        if self.output_after_code.isChecked() and (
            not self.generate_output_pages.isChecked() or not self.generate_code_page.isChecked()
        ):
            raise ValueError("Placing output after code requires both code pages and output images.")

        final_pdf_path = self.selected_final_report_path()
        final_pdf_dir = os.path.dirname(final_pdf_path)
        if not final_pdf_path.lower().endswith(".pdf"):
            raise ValueError("The report file name must end with .pdf.")
        if final_pdf_dir and not os.path.isdir(final_pdf_dir):
            try:
                os.makedirs(final_pdf_dir, exist_ok=True)
            except Exception as exc:
                raise ValueError(
                    f"Could not create the selected save folder: {final_pdf_dir}\n{exc}"
                )
        if self.generate_watermark.isChecked() and not self.watermark_name.text().strip():
            raise ValueError("Enter watermark text.")


    def write_configuration_files(self):
        self.validate_enabled_sections_before_write()
        folder = os.path.join(baseDir, "JsonFile")
        os.makedirs(folder, exist_ok=True)
        config_data = self.collect_runtime_configuration()
        with open(os.path.join(folder, "config_data.json"), "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)
        if self.generate_cover.isChecked():
            frontpage_data = {
                "CollegeName": self.clean_value(self.college_name),
                "Address": self.clean_value(self.college_address),
                "StudentName": self.clean_value(self.student_name),
                "Roll": self.clean_value(self.roll),
                "Section": self.clean_value(self.section_entry),
                "Semester": self.clean_value(self.semester),
                "TeacherName": self.clean_value(self.teacher_name),
                "ProjectTitle": self.clean_value(self.project_title),
                "logo_selected": getattr(self, "logo_selected", False),
                "font_family": self.font_combo.currentText(),
            }
            with open(os.path.join(folder, "frontpage.json"), "w", encoding="utf-8") as f:
                json.dump(frontpage_data, f, indent=4)
        if self.generate_toc.isChecked():
            if (
                hasattr(self, "toc_mode_combo")
                and self.toc_mode_combo.currentText() == TOC_MODE_BROWSE
            ):
                if not self.validate_toc_file_labels(show_message=True):
                    raise ValueError("TOC validation failed. Select a valid TOC file.")
            toc_dict = self.build_toc_dict()
            with open(os.path.join(folder, "table_of_content.json"), "w", encoding="utf-8") as f:
                json.dump(toc_dict, f, indent=4)
        if self.generate_code_page.isChecked():
            code_page_data = {
                "line_height": self.code_line_height.text().strip(),
                "code_folder_path": self.selected_code_folder(),
                "output_after_code": self.output_after_code.isChecked()
                and self.generate_output_pages.isChecked(),
            }
            with open(os.path.join(folder, "code_page.json"), "w", encoding="utf-8") as f:
                json.dump(code_page_data, f, indent=4)
        if self.generate_watermark.isChecked():
            watermark_data = {"name": self.watermark_name.text().strip()}
            with open(os.path.join(folder, "watermark.json"), "w", encoding="utf-8") as f:
                json.dump(watermark_data, f, indent=4)
        self.save_output_captions(show_message=False)


    def append_log(self, text):
        self.log_box.append(text)


    def clear_log(self):
        self.log_box.clear()
        self.log_box.append("Progress messages will appear here.")


    def set_controls_busy(self, busy):
        button_names = [
            "save_config_btn",
            "import_config_btn",
            "quick_preview_btn",
            "quick_proceed_btn",
            "preview_btn",
            "proceed_btn",
            "health_check_btn",
            "open_code_btn",
            "open_output_btn",
            "summary_btn",
            "open_final_folder_btn",
            "browse_final_report_btn",
        ]

        for button_name in button_names:
            button = getattr(self, button_name, None)
            if button is not None:
                button.setDisabled(busy)


    def run_subprocess_worker(self, script_name, output_queue, success_payload):
        try:
            script_path = os.path.join(baseDir, script_name)
            process = subprocess.Popen(
                [sys.executable, "-u", script_path],
                cwd=baseDir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
            for line in process.stdout:
                clean_line = line.rstrip()
                if clean_line:
                    output_queue.put(("log", clean_line))
            return_code = process.wait()
            if return_code == 0:
                output_queue.put(("success", success_payload))
            else:
                output_queue.put(("error", f"{script_name} failed with exit code {return_code}."))
        except Exception as exc:
            output_queue.put(("error", str(exc)))


    def tick_progress(self):
        active = self.generation_running or self.preview_running
        if active:
            value = self.progress_bar.value()
            self.progress_bar.setValue(8 if value >= 95 else value + 3)
        if self.generation_running:
            self.process_queue(self.generation_queue, "generation")
        if self.preview_running:
            self.process_queue(self.preview_queue, "preview")
        if not self.generation_running and not self.preview_running:
            self.timer.stop()


    def process_queue(self, active_queue, mode):
        try:
            while True:
                message_type, payload = active_queue.get_nowait()
                if message_type == "log":
                    self.status_label.setStyleSheet("")
                    self.status_label.setText(payload)
                    self.append_log(payload)
                elif message_type == "success":
                    if mode == "generation":
                        self.generation_running = False
                        self.status_label.setStyleSheet("")
                        self.status_label.setText("Final report created.")
                        self.append_log(f"Final report saved: {payload}")
                        self.record_generated_project_history(payload)
                        self.progress_bar.setValue(100)
                        self.set_controls_busy(False)
                        self.show_themed_message(
                            "Report Created", f"The final PDF was saved to:\n{payload}", "generate.svg"
                        )
                        self.show_pdf_preview(payload, "Final Report")
                    else:
                        self.preview_running = False
                        self.status_label.setStyleSheet("")
                        self.status_label.setText("Preview created.")
                        self.append_log(f"Preview saved: {payload}")
                        self.progress_bar.setValue(100)
                        self.set_controls_busy(False)
                        self.show_pdf_preview(payload, "Report Preview")
                elif message_type == "error":
                    if mode == "generation":
                        self.generation_running = False
                        title = "Report Generation Failed"
                    else:
                        self.preview_running = False
                        title = "Preview Failed"
                    self.status_label.setStyleSheet("color: #B42318;")
                    self.status_label.setText(title)
                    self.append_log(payload)
                    self.progress_bar.setValue(0)
                    self.set_controls_busy(False)
                    self.show_themed_error(title, payload)
        except queue.Empty:
            pass


    def get_code_extension_for_health_check(self):
        value = ""
        try:
            value = self.code_file_ext.text().strip()
        except Exception:
            value = ""
        if value.startswith("."):
            value = value[1:]
        return value.lower()


    def natural_key_for_health_check(self, name):

        parts = []
        current = ""
        for char in str(name):
            if char.isdigit():
                if current and not current[-1].isdigit():
                    parts.append((1, current.lower()))
                    current = ""
                current += char
            else:
                if current and current[-1].isdigit():
                    parts.append((0, int(current)))
                    current = ""
                current += char
        if current:
            if current.isdigit():
                parts.append((0, int(current)))
            else:
                parts.append((1, current.lower()))
        return tuple(parts)


    def run_health_check_action(self):
        try:
            report = self.project_health_text()
            health_path = os.path.join(baseDir, "Project_Health_Check.txt")
            with open(health_path, "w", encoding="utf-8") as f:
                f.write(report)
            self.append_log(report)
            TextReportDialog(
                "Project Check", f"Saved to {health_path}", report, self, "dashboard.svg"
            ).exec()
        except Exception as exc:
            self.show_themed_error(
                "Project Check Failed", f"Could not complete the project check.\n{exc}"
            )


    def open_code_folder_action(self):
        self.open_folder(
            self.selected_code_folder() if hasattr(self, "selected_code_folder") else codeDir
        )


    def open_output_folder_action(self):
        self.open_folder(
            self.selected_output_folder()
            if hasattr(self, "selected_output_folder")
            else imageDir
        )


    def open_final_folder_action(self):
        self.open_folder(os.path.dirname(self.selected_final_report_path()) or baseDir)


    def open_folder(self, folder_path):
        try:
            os.makedirs(folder_path, exist_ok=True)
            if sys.platform.startswith("win"):
                os.startfile(folder_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder_path])
            else:
                subprocess.Popen(["xdg-open", folder_path])
        except Exception as exc:
            self.show_themed_error("Open Folder Failed", f"Could not open the folder.\n{exc}")


    def show_generation_summary_action(self):
        TextReportDialog(
            "Generation Summary",
            "Details from the latest generated report.",
            self.read_generation_summary(),
            self,
            "document.svg",
        ).exec()


    def handle_primary_header_action(self):
        if self.stack.currentIndex() == 0:
            self.select_page(1)
        else:
            self.proceed_action()


    #start report generation
    def proceed_action(self):
        if self.generation_running or self.preview_running:
            return
        try:
            self.write_configuration_files()
        except Exception as exc:
            self.show_themed_error("Settings Error", f"Could not save the current settings.\n{exc}")
            return
        if not self.confirm_proceed_settings():
            return
        self.select_page(6)
        self.generation_running = True
        self.clear_log()
        self.set_controls_busy(True)
        self.progress_bar.setValue(5)
        self.status_label.setStyleSheet("")
        self.status_label.setText("Generating final report...")
        final_pdf_path = self.selected_final_report_path()
        threading.Thread(
            target=self.run_subprocess_worker,
            args=("OutputGenerator.py", self.generation_queue, final_pdf_path),
            daemon=True,
        ).start()
        self.timer.start()


    #make report preview
    def preview_action(self):
        if self.generation_running or self.preview_running:
            return
        try:
            self.write_configuration_files()
        except Exception as exc:
            self.show_themed_error("Settings Error", f"Could not save the current settings.\n{exc}")
            return
        self.select_page(6)
        self.preview_running = True
        self.clear_log()
        self.set_controls_busy(True)
        self.progress_bar.setValue(5)
        self.status_label.setStyleSheet("")
        self.status_label.setText("Creating report preview...")
        threading.Thread(
            target=self.run_subprocess_worker,
            args=("PreviewGenerator.py", self.preview_queue, previewPdfPath),
            daemon=True,
        ).start()
        self.timer.start()


    def show_pdf_preview(self, pdf_path, title):
        dialog = PdfPreviewDialog(pdf_path, title, self)
        self.preview_dialogs.append(dialog)
        dialog.show()



def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Microsoft YaHei UI", 10))
    app.setStyleSheet(
        """
        QMessageBox {
            background: #E8F5FC;
            color: #142338;
            font-family: "Microsoft YaHei UI", "Segoe UI", "Arial";
        }
        QMessageBox QLabel { color: #B42318; font-size: 13px; }
        QMessageBox QPushButton {
            background: #0067C0;
            color: white;
            border: none;
            border-radius: 0px;
            padding: 8px 18px;
            min-width: 90px;
        }
    """
    )
    window = DocumentFormatterWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
