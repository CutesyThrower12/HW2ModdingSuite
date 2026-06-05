import copy
import html
import os
import sys
import xml.etree.ElementTree as ET

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QColorDialog,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


ATTRS = [
    "objects",
    "corpse",
    "selection",
    "minimap",
    "ui",
    "captureeffects",
    "obscuringunit",
    "effects",
    "lights",
]

DEFAULT_SKIRMISH = [
    ("gaia", "175 175 175", "88 88 88", "175 175 175", "175 175 175", "175 175 175", "175 175 175", "175 175 175", "175 175 175", "175 175 175", "white"),
    ("creeps", "175 175 175", "88 88 88", "255 132 255", "255 132 255", "175 175 175", "175 175 175", "175 175 175", "175 175 175", "175 175 175", "white"),
    ("unsc_red", "160 60 60", "160 60 60", "159 29 29", "209 80 80", "48 244 230", "230 20 20", "253 96 96", "165 28 28", "165 28 28", "red"),
    ("unsc_3v3red", "170 25 25", "170 25 25", "170 25 25", "255 38 38", "48 244 230", "230 20 20", "255 38 38", "170 20 20", "170 20 20", "red"),
    ("unsc_yellow", "250 220 65", "250 220 65", "171 150 44", "255 224 66", "48 244 230", "230 20 20", "255 224 66", "100 87 18", "100 87 18", "red"),
    ("unsc_orange", "220 100 30", "220 100 30", "134 49 0", "255 116 36", "48 244 230", "230 20 20", "255 116 36", "141 61 15", "141 61 15", "red"),
    ("unsc_blue", "60 90 160", "60 90 160", "38 57 102", "94 143 255", "48 244 230", "50 170 255", "94 143 255", "16 52 136", "16 52 136", "blue"),
    ("unsc_3v3navy", "30 50 160", "30 50 160", "19 32 102", "48 79 255", "48 244 230", "50 170 255", "48 79 255", "30 50 160", "30 50 160", "blue"),
    ("unsc_cyan", "80 170 250", "80 170 250", "21 127 153", "82 174 255", "48 244 230", "50 170 255", "82 174 255", "33 98 157", "33 98 157", "blue"),
    ("unsc_green", "30 130 80", "30 130 80", "18 130 74", "59 255 157", "48 244 230", "50 170 255", "59 255 157", "30 130 80", "30 130 80", "blue"),
    ("ban_red", "160 60 60", "160 60 60", "159 29 29", "209 80 80", "48 244 230", "230 20 20", "253 96 96", "165 28 28", "165 28 28", "red"),
    ("ban_3v3red", "210 30 30", "210 30 3", "210 30 30", "255 36 36", "48 244 230", "230 20 20", "255 36 36", "170 24 24", "170 24 24", "red"),
    ("ban_yellow", "240 220 45", "166 152 31", "171 157 32", "255 234 48", "48 244 230", "230 20 20", "255 234 48", "100 87 18", "100 87 18", "red"),
    ("ban_orange", "250 145 20", "250 145 20", "134 49 0", "255 149 20", "48 244 230", "230 20 20", "255 149 20", "141 61 15", "141 61 15", "red"),
    ("ban_blue", "60 90 160", "60 90 160", "14 41 102", "94 143 255", "48 244 230", "50 170 255", "94 143 255", "16 52 136", "16 52 136", "blue"),
    ("ban_3v3navy", "30 50 160", "30 50 160", "19 32 102", "48 79 255", "48 244 230", "50 170 255", "48 79 255", "30 50 160", "30 50 160", "blue"),
    ("ban_cyan", "80 170 250", "80 170 250", "33 70 102", "82 174 255", "48 244 230", "50 170 255", "82 174 255", "33 98 157", "33 98 157", "blue"),
    ("ban_green", "30 130 80", "30 130 80", "23 102 63", "59 255 157", "48 244 230", "50 170 255", "59 255 157", "30 130 80", "30 130 80", "blue"),
    ("flood", "255 0 255", "255 0 255", "255 0 255", "255 0 255", "255 0 255", "255 0 255", "255 0 255", "255 0 255", "255 0 255", "flood"),
]

SPC_LINES = [
    '        <color name="0" objects="175 175 175" corpse="88 88 88" selection="175 175 175" minimap="175 175 175" ui="48 244 230" captureeffects="175 175 175" obscuringunit="175 175 175" effects="175 175 175" lights="175 175 175" />',
    '        <color name="1" objects="43 77 60" corpse="35 55 12" selection="12 89 30" minimap="9 200 60" ui="48 244 230" captureeffects="50 170 255" obscuringunit="21 153 21" effects="50 90 50" lights="60 80 40 128" />',
    '        <color name="2" objects="180 150 40" corpse="248 227 33" selection="181 147 25" minimap="255 212 56" ui="48 244 230" captureeffects="50 170 255" obscuringunit="255 212 56" effects="180 150 40" lights="240 200 20" />',
    '        <color name="3" objects="48 121 189" corpse="48 121 189" selection="26 110 189" minimap="64 163 255" ui="48 244 230" captureeffects="50 170 255" obscuringunit="64 163 255" effects="48 121 189" lights="0 163 255" />',
    '        <color name="4" objects="225 35 35" corpse="225 35 35" selection="159 29 29" minimap="255 41 41" ui="48 244 230" captureeffects="50 170 255" obscuringunit="255 41 41" effects="225 35 35" lights="200 60 0" />',
    '        <color name="5" objects="220 220 220" corpse="25 25 15" selection="220 220 220" minimap="220 220 220" ui="48 244 230" captureeffects="50 170 255" obscuringunit="220 220 220" effects="220 220 220" lights="50 50 30" />',
    '        <color name="6" objects="185 160 125" corpse="93 50 63" selection="185 160 125" minimap="229 199 156" ui="48 244 230" captureeffects="50 170 255" obscuringunit="229 199 156" effects="185 160 125" lights="185 160 125" />',
    '        <color name="7" objects="255 0 178" corpse="83 48 172" selection="255 36 189" minimap="255 36 189" ui="48 244 230" captureeffects="230 20 20" obscuringunit="255 36 189" effects="255 0 178" lights="255 0 178" />',
    '        <color name="8" objects="35 100 225" corpse="35 100 225" selection="35 100 225" minimap="41 116 255" ui="48 244 230" captureeffects="230 20 20" obscuringunit="41 116 255" effects="35 100 225" lights="255 106 0" />',
    '        <color name="9" objects="215 50 30" corpse="105 10 0" selection="159 29 29" minimap="255 58 36" ui="48 244 230" captureeffects="230 20 20" obscuringunit="255 58 36" effects="215 50 30" lights="255 0 0" />',
    '        <color name="10" objects="40 50 20" corpse="20 25 10" selection="40 50 20" minimap="40 50 20" ui="48 244 230" captureeffects="230 20 20" obscuringunit="40 50 20" effects="40 50 20" lights="40 50 20" />',
    '        <color name="11" objects="255 215 50" corpse="128 107 25" selection="255 211 36" minimap="255 215 50" ui="48 244 230" captureeffects="230 20 20" obscuringunit="255 215 50" effects="255 215 50" lights="255 215 50" />',
    '        <color name="12" objects="215 190 175" corpse="108 95 87" selection="215 200 175" minimap="215 200 175" ui="48 244 230" captureeffects="230 20 20" obscuringunit="215 200 175" effects="215 190 175" lights="215 200 175" />',
    '        <color name="13" objects="225 35 35" corpse="225 35 35" selection="159 29 29" minimap="255 41 41" ui="48 244 230" captureeffects="50 170 255" obscuringunit="255 41 41" effects="225 35 35" lights="200 60 0" />',
    '        <color name="14" objects="175 175 175" corpse="88 88 88" selection="175 175 175" minimap="175 175 175" ui="48 244 230" captureeffects="175 175 175" obscuringunit="175 175 175" effects="175 175 175" lights="175 175 175" />',
    '        <color name="15" objects="255 0 255" corpse="255 0 255" selection="255 0 255" minimap="255 0 255" ui="255 0 255" captureeffects="255 0 255" obscuringunit="255 0 255" effects="255 0 255" lights="255 0 255" enum="flood" />',
    '        <color name="16" objects="250 145 20" corpse="250 145 20" selection="134 49 0" minimap="255 149 20" ui="48 244 230" captureeffects="230 20 20" obscuringunit="255 149 20" effects="141 61 15" lights="141 61 15" />',
    '        <color name="17" objects="175 175 175" corpse="88 88 88" selection="175 175 175" minimap="175 175 175" ui="48 244 230" captureeffects="175 175 175" obscuringunit="175 175 175" effects="175 175 175" lights="175 175 175" />',
    '        <color name="18" objects="175 175 175" corpse="88 88 88" selection="175 175 175" minimap="175 175 175" ui="48 244 230" captureeffects="175 175 175" obscuringunit="175 175 175" effects="175 175 175" lights="175 175 175" />',
    '        <color name="19" objects="175 175 175" corpse="88 88 88" selection="175 175 175" minimap="175 175 175" ui="48 244 230" captureeffects="175 175 175" obscuringunit="175 175 175" effects="175 175 175" lights="175 175 175" />',
    '        <color name="20" objects="175 175 175" corpse="88 88 88" selection="175 175 175" minimap="175 175 175" ui="48 244 230" captureeffects="175 175 175" obscuringunit="175 175 175" effects="175 175 175" lights="175 175 175" />',
]

APP_STYLESHEET = """
QMainWindow, QWidget {
    background: #0B1018;
    color: #EEF4FF;
    font-family: Segoe UI;
    font-size: 12px;
}
QFrame#Header, QFrame#Panel {
    background: #111A27;
    border: 1px solid #273449;
    border-radius: 8px;
}
QFrame#Swatch {
    border: 1px solid #405064;
    border-radius: 5px;
}
QFrame#CivCard {
    background: #0D1420;
    border: 1px solid #273449;
    border-radius: 8px;
}
QFrame#SlotSwatch {
    border: 1px solid #405064;
    border-radius: 4px;
}
QLabel {
    background: transparent;
}
QListWidget {
    background: #0D1420;
    border: 1px solid #273449;
    border-radius: 8px;
    padding: 6px;
}
QListWidget::item {
    padding: 8px;
    border-radius: 6px;
}
QListWidget::item:selected {
    background: #1B3559;
}
QLineEdit, QSpinBox, QComboBox, QTextEdit {
    background: #080D14;
    border: 1px solid #2C394C;
    border-radius: 6px;
    padding: 6px 8px;
    color: #F5F8FF;
    selection-background-color: #2F80ED;
}
QComboBox {
    min-height: 30px;
}
QComboBox QAbstractItemView {
    background: #0D1420;
    border: 1px solid #34445A;
    color: #EEF4FF;
    selection-background-color: #1B3559;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus {
    border-color: #54A6FF;
}
QPushButton {
    background: #1C2635;
    border: 1px solid #34445A;
    border-radius: 6px;
    color: #EEF4FF;
    padding: 7px 12px;
    font-weight: 600;
}
QPushButton:hover {
    background: #243249;
    border-color: #4E6480;
}
QPushButton#PrimaryButton {
    background: #2F80ED;
    border-color: #5EA3FF;
}
QPushButton#DangerButton {
    background: #49202A;
    border-color: #8B4050;
}
QTabWidget::pane {
    border: 1px solid #273449;
    border-radius: 8px;
    top: -1px;
}
QTabBar::tab {
    background: #111A27;
    border: 1px solid #273449;
    border-bottom: none;
    padding: 8px 16px;
    margin-right: 4px;
    border-top-left-radius: 7px;
    border-top-right-radius: 7px;
}
QTabBar::tab:selected {
    background: #1A2638;
    color: white;
}
QScrollArea {
    border: none;
}
QScrollBar:vertical {
    background: #0D1420;
    width: 12px;
}
QScrollBar::handle:vertical {
    background: #35445A;
    border-radius: 5px;
    min-height: 28px;
}
QLabel#Title {
    font-size: 24px;
    font-weight: 800;
}
QLabel#Kicker {
    color: #75D8FF;
    font-weight: 800;
}
QLabel#Muted {
    color: #AAB8CA;
}
"""


def resource_path(relative: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


def parse_rgb(value: str) -> list[int]:
    parts = []
    for chunk in (value or "0 0 0").replace(",", " ").split()[:3]:
        try:
            parts.append(max(0, min(255, int(float(chunk)))))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return parts


def rgb_text(rgb: list[int]) -> str:
    return f"{int(rgb[0])} {int(rgb[1])} {int(rgb[2])}"


def color_style(rgb: list[int]) -> str:
    return (
        f"background: rgb({int(rgb[0])}, {int(rgb[1])}, {int(rgb[2])}); "
        "border: 1px solid #405064; border-radius: 5px;"
    )


def make_color(name: str, rgb=(175, 175, 175), enum_value: str = "") -> dict:
    return {
        "name": name,
        "attrs": {attr: [int(rgb[0]), int(rgb[1]), int(rgb[2])] for attr in ATTRS},
        "enum": enum_value,
    }


def default_model() -> tuple[list[dict], dict[str, list[int]]]:
    colors = []
    for row in DEFAULT_SKIRMISH:
        name, *values, enum_value = row
        attrs = {attr: parse_rgb(values[i]) for i, attr in enumerate(ATTRS)}
        colors.append({"name": name, "attrs": attrs, "enum": enum_value})

    def idx(name: str) -> int:
        return next((i for i, color in enumerate(colors) if color["name"] == name), 0)

    civs = {
        "UNSC": [idx("unsc_red"), idx("unsc_3v3red"), idx("unsc_yellow"), idx("unsc_orange"), idx("unsc_blue"), idx("unsc_3v3navy"), idx("unsc_cyan"), idx("unsc_green"), idx("gaia"), idx("creeps"), idx("flood")],
        "Covenant": [idx("ban_red"), idx("ban_3v3red"), idx("ban_yellow"), idx("ban_orange"), idx("ban_blue"), idx("ban_3v3navy"), idx("ban_cyan"), idx("ban_green"), idx("gaia"), idx("creeps"), idx("flood")],
        "Flood": [idx("flood")] * 11,
    }
    return colors, civs


def player_num(slot_index: int) -> int:
    if slot_index < 8:
        return slot_index + 1
    if slot_index == 8:
        return 0
    return slot_index


def build_xml(colors: list[dict], civs: dict[str, list[int]]) -> str:
    lines = ['<?xml version="1.0" encoding="us-ascii"?>', "<playerColors>", "    <skirmish>"]
    for color in colors:
        name = html.escape(color.get("name", ""), quote=True)
        attrs = color.get("attrs", {})
        attr_text = " ".join(f'{attr}="{rgb_text(attrs.get(attr, [0, 0, 0]))}"' for attr in ATTRS)
        enum_value = html.escape(color.get("enum", ""), quote=True)
        enum_text = f' enum="{enum_value}"' if enum_value else ""
        lines.append(f'        <color name="{name}" {attr_text}{enum_text} />')

    for civ_name, slots in civs.items():
        lines.append("        <civ>")
        for i, assigned in enumerate(slots):
            color_name = colors[assigned]["name"] if 0 <= assigned < len(colors) else ""
            suffix = f"{html.escape(civ_name)}</civ>" if i == len(slots) - 1 else ""
            lines.append(f'            <player num="{player_num(i)}" colorName="{html.escape(color_name, quote=True)}" />{suffix}')
    lines.extend(["    </skirmish>", "    <spc>"])
    lines.extend(SPC_LINES)
    lines.extend([
        "        <civ>",
        '            <player num="0" colorName="0" />',
        '            <player num="1" colorName="1" />',
        '            <player num="2" colorName="2" />',
        '            <player num="3" colorName="3" />',
        '            <player num="4" colorName="4" />',
        '            <player num="5" colorName="5" />',
        '            <player num="6" colorName="6" />',
        '            <player num="7" colorName="13" />',
        '            <player num="8" colorName="14" />UNSC</civ>',
        "        <civ>",
        '            <player num="0" colorName="0" />',
        '            <player num="1" colorName="9" />',
        '            <player num="2" colorName="7" />',
        '            <player num="3" colorName="16" />',
        '            <player num="4" colorName="10" />',
        '            <player num="5" colorName="11" />',
        '            <player num="6" colorName="12" />',
        '            <player num="7" colorName="13" />',
        '            <player num="8" colorName="14" />Covenant</civ>',
        "        <civ>",
        '            <player num="0" colorName="15" />',
        '            <player num="1" colorName="15" />',
        '            <player num="2" colorName="15" />',
        '            <player num="3" colorName="15" />',
        '            <player num="4" colorName="15" />',
        '            <player num="5" colorName="15" />',
        '            <player num="6" colorName="15" />',
        '            <player num="7" colorName="15" />',
        '            <player num="8" colorName="15" />Flood</civ>',
        "    </spc>",
        "</playerColors>",
    ])
    return "\n".join(lines)


def import_xml(path: str) -> tuple[list[dict], dict[str, list[int]]]:
    root = ET.parse(path).getroot()
    skirmish = root.find("skirmish")
    if skirmish is None:
        raise ValueError("No <skirmish> block found.")

    colors = []
    for node in skirmish.findall("color"):
        attrs = {attr: parse_rgb(node.get(attr, "0 0 0")) for attr in ATTRS}
        colors.append({"name": node.get("name", ""), "attrs": attrs, "enum": node.get("enum", "")})
    if not colors:
        raise ValueError("No skirmish colors found.")

    civs: dict[str, list[int]] = {}
    fallback_names = ["UNSC", "Covenant", "Flood"]
    for index, civ in enumerate(skirmish.findall("civ")):
        civ_name = (fallback_names[index] if index < len(fallback_names) else f"Civ {index + 1}")
        players = civ.findall("player")
        slots = []
        for player in players:
            color_name = player.get("colorName", "")
            slots.append(next((i for i, color in enumerate(colors) if color.get("name") == color_name), 0))
        while len(slots) < 11:
            slots.append(0)
        civs[civ_name] = slots[:11]
    if not civs:
        _, civs = default_model()
    return colors, civs


class PlayerColorsEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Halo Wars 2 Player Colors Editor")
        icon_path = resource_path(os.path.join("assets", "icon.ico"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.resize(1260, 820)
        self.setMinimumSize(1040, 700)
        self.setStyleSheet(APP_STYLESHEET)

        self.colors, self.civs = default_model()
        self.selected_index = 0
        self.attr_rows: dict[str, tuple[QFrame, QSpinBox, QSpinBox, QSpinBox]] = {}
        self.civ_combos: list[tuple[str, int, QFrame, QComboBox]] = []

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(12)
        root_layout.addWidget(self.build_header())

        self.tabs = QTabWidget()
        self.tabs.addTab(self.build_editor_tab(), "Colors")
        self.tabs.addTab(self.build_civs_tab(), "Skirmish Order")
        self.tabs.addTab(self.build_xml_tab(), "XML Preview")
        root_layout.addWidget(self.tabs, 1)
        self.setCentralWidget(root)

        self.reload_color_list()
        self.select_color(0)
        self.refresh_civ_combos()
        self.refresh_xml_preview()
        self.raise_()
        self.activateWindow()

    def build_header(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Header")
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(18, 14, 18, 14)

        title_stack = QVBoxLayout()
        kicker = QLabel("PLAYER COLOR WORKSTATION")
        kicker.setObjectName("Kicker")
        title = QLabel("Halo Wars 2 Player Colors")
        title.setObjectName("Title")
        subtitle = QLabel("Edit skirmish palettes, team order, imports, and exports with live previews.")
        subtitle.setObjectName("Muted")
        title_stack.addWidget(kicker)
        title_stack.addWidget(title)
        title_stack.addWidget(subtitle)
        layout.addLayout(title_stack, 1)

        for text, handler, primary in [
            ("Import XML", self.import_file, False),
            ("Export playercolors.xml", self.export_file, True),
            ("Reset Vanilla", self.reset_vanilla, False),
        ]:
            button = QPushButton(text)
            if primary:
                button.setObjectName("PrimaryButton")
            button.clicked.connect(handler)
            layout.addWidget(button)
        return panel

    def build_editor_tab(self) -> QWidget:
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        left = QFrame()
        left.setObjectName("Panel")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.addWidget(QLabel("Color Definitions"))

        actions = QHBoxLayout()
        for text, handler in [("Add", self.add_color), ("Duplicate", self.duplicate_color), ("Up", self.move_up), ("Down", self.move_down)]:
            button = QPushButton(text)
            button.clicked.connect(handler)
            actions.addWidget(button)
        remove = QPushButton("Remove")
        remove.setObjectName("DangerButton")
        remove.clicked.connect(self.remove_color)
        actions.addWidget(remove)
        left_layout.addLayout(actions)

        self.color_list = QListWidget()
        self.color_list.currentRowChanged.connect(self.select_color)
        left_layout.addWidget(self.color_list, 1)
        layout.addWidget(left, 0)

        right = QFrame()
        right.setObjectName("Panel")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(12)

        self.big_preview = QFrame()
        self.big_preview.setObjectName("Swatch")
        self.big_preview.setFixedHeight(72)
        right_layout.addWidget(self.big_preview)

        form = QGridLayout()
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(10)
        form.addWidget(QLabel("Name"), 0, 0)
        self.name_field = QLineEdit()
        self.name_field.textChanged.connect(self.update_name)
        form.addWidget(self.name_field, 0, 1, 1, 4)
        form.addWidget(QLabel("Enum"), 0, 5)
        self.enum_combo = QComboBox()
        self.enum_combo.addItems(["", "red", "blue", "white", "flood"])
        self.enum_combo.currentTextChanged.connect(self.update_enum)
        form.addWidget(self.enum_combo, 0, 6)
        right_layout.addLayout(form)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_body = QWidget()
        self.attr_grid = QGridLayout(scroll_body)
        self.attr_grid.setHorizontalSpacing(10)
        self.attr_grid.setVerticalSpacing(10)
        self.attr_grid.addWidget(QLabel("Attribute"), 0, 0)
        self.attr_grid.addWidget(QLabel("Preview"), 0, 1)
        self.attr_grid.addWidget(QLabel("R"), 0, 2)
        self.attr_grid.addWidget(QLabel("G"), 0, 3)
        self.attr_grid.addWidget(QLabel("B"), 0, 4)
        for row, attr in enumerate(ATTRS, start=1):
            self.add_attr_row(row, attr)
        scroll.setWidget(scroll_body)
        right_layout.addWidget(scroll, 1)
        layout.addWidget(right, 1)
        return tab

    def add_attr_row(self, row: int, attr: str) -> None:
        self.attr_grid.addWidget(QLabel(attr), row, 0)
        swatch = QFrame()
        swatch.setObjectName("Swatch")
        swatch.setFixedSize(58, 28)
        self.attr_grid.addWidget(swatch, row, 1)
        spins = []
        for col in range(2, 5):
            spin = QSpinBox()
            spin.setRange(0, 255)
            spin.valueChanged.connect(lambda _value, a=attr: self.update_attr(a))
            self.attr_grid.addWidget(spin, row, col)
            spins.append(spin)
        pick = QPushButton("Pick")
        pick.clicked.connect(lambda _checked=False, a=attr: self.pick_attr_color(a))
        self.attr_grid.addWidget(pick, row, 5)
        copy = QPushButton("Copy Objects")
        copy.clicked.connect(lambda _checked=False, a=attr: self.copy_objects_to(a))
        self.attr_grid.addWidget(copy, row, 6)
        self.attr_rows[attr] = (swatch, spins[0], spins[1], spins[2])

    def build_civs_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        top_panel = QFrame()
        top_panel.setObjectName("Panel")
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(16, 12, 16, 12)
        copy = QVBoxLayout()
        title = QLabel("Skirmish Color Order")
        title.setObjectName("Kicker")
        hint = QLabel("Assign named colors to each player slot. Swatches update live as you change selections.")
        hint.setObjectName("Muted")
        copy.addWidget(title)
        copy.addWidget(hint)
        top_layout.addLayout(copy, 1)
        layout.addWidget(top_panel)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_body = QWidget()
        self.civs_layout = QHBoxLayout(scroll_body)
        self.civs_layout.setContentsMargins(0, 0, 0, 0)
        self.civs_layout.setSpacing(12)
        scroll.setWidget(scroll_body)
        layout.addWidget(scroll, 1)
        return tab

    def build_xml_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        actions = QHBoxLayout()
        refresh = QPushButton("Refresh Preview")
        refresh.clicked.connect(self.refresh_xml_preview)
        copy = QPushButton("Copy XML")
        copy.clicked.connect(self.copy_xml)
        actions.addWidget(refresh)
        actions.addWidget(copy)
        actions.addStretch(1)
        layout.addLayout(actions)
        self.xml_preview = QTextEdit()
        self.xml_preview.setReadOnly(True)
        self.xml_preview.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(self.xml_preview, 1)
        return tab

    def current_color(self) -> dict | None:
        if 0 <= self.selected_index < len(self.colors):
            return self.colors[self.selected_index]
        return None

    def reload_color_list(self) -> None:
        current = self.selected_index
        self.color_list.blockSignals(True)
        self.color_list.clear()
        for color in self.colors:
            item = QListWidgetItem(color.get("name", ""))
            rgb = color.get("attrs", {}).get("objects", [0, 0, 0])
            item.setBackground(QColor(max(0, rgb[0] // 4), max(0, rgb[1] // 4), max(0, rgb[2] // 4)))
            self.color_list.addItem(item)
        self.color_list.blockSignals(False)
        if self.colors:
            self.color_list.setCurrentRow(max(0, min(current, len(self.colors) - 1)))
        self.refresh_civ_combos()
        self.refresh_xml_preview()

    def select_color(self, index: int) -> None:
        if index < 0 or not self.colors:
            return
        self.selected_index = max(0, min(index, len(self.colors) - 1))
        color = self.current_color()
        if not color:
            return
        self.name_field.blockSignals(True)
        self.name_field.setText(color.get("name", ""))
        self.name_field.blockSignals(False)
        self.enum_combo.blockSignals(True)
        enum_value = color.get("enum", "")
        self.enum_combo.setCurrentText(enum_value if enum_value in ["", "red", "blue", "white", "flood"] else "")
        self.enum_combo.blockSignals(False)
        for attr in ATTRS:
            self.set_attr_widgets(attr, color["attrs"].get(attr, [0, 0, 0]))
        self.big_preview.setStyleSheet(color_style(color["attrs"].get("objects", [0, 0, 0])))

    def set_attr_widgets(self, attr: str, rgb: list[int]) -> None:
        swatch, r_spin, g_spin, b_spin = self.attr_rows[attr]
        for spin, value in [(r_spin, rgb[0]), (g_spin, rgb[1]), (b_spin, rgb[2])]:
            spin.blockSignals(True)
            spin.setValue(int(value))
            spin.blockSignals(False)
        swatch.setStyleSheet(color_style(rgb))

    def update_name(self, text: str) -> None:
        color = self.current_color()
        if not color:
            return
        color["name"] = text.strip()
        item = self.color_list.item(self.selected_index)
        if item:
            item.setText(color["name"])
        self.refresh_civ_combos(keep_values=True)
        self.refresh_xml_preview()

    def update_enum(self, text: str) -> None:
        color = self.current_color()
        if color:
            color["enum"] = text
            self.refresh_xml_preview()

    def update_attr(self, attr: str) -> None:
        color = self.current_color()
        if not color:
            return
        swatch, r_spin, g_spin, b_spin = self.attr_rows[attr]
        rgb = [r_spin.value(), g_spin.value(), b_spin.value()]
        color["attrs"][attr] = rgb
        swatch.setStyleSheet(color_style(rgb))
        if attr == "objects":
            self.big_preview.setStyleSheet(color_style(rgb))
            item = self.color_list.item(self.selected_index)
            if item:
                item.setBackground(QColor(max(0, rgb[0] // 4), max(0, rgb[1] // 4), max(0, rgb[2] // 4)))
        self.refresh_xml_preview()

    def pick_attr_color(self, attr: str) -> None:
        color = self.current_color()
        if not color:
            return
        picked = QColorDialog.getColor(QColor(*color["attrs"].get(attr, [0, 0, 0])), self, f"Pick {attr} color")
        if picked.isValid():
            color["attrs"][attr] = [picked.red(), picked.green(), picked.blue()]
            self.set_attr_widgets(attr, color["attrs"][attr])
            if attr == "objects":
                self.big_preview.setStyleSheet(color_style(color["attrs"][attr]))
                self.reload_color_list()
            self.refresh_xml_preview()

    def copy_objects_to(self, attr: str) -> None:
        color = self.current_color()
        if color:
            color["attrs"][attr] = list(color["attrs"].get("objects", [0, 0, 0]))
            self.set_attr_widgets(attr, color["attrs"][attr])
            self.refresh_xml_preview()

    def add_color(self) -> None:
        self.colors.append(make_color(f"custom_{len(self.colors)}"))
        for slots in self.civs.values():
            while len(slots) < 11:
                slots.append(0)
        self.selected_index = len(self.colors) - 1
        self.reload_color_list()

    def duplicate_color(self) -> None:
        color = self.current_color()
        if not color:
            return
        clone = copy.deepcopy(color)
        clone["name"] = f"{clone.get('name', 'color')}_copy"
        self.colors.insert(self.selected_index + 1, clone)
        self.selected_index += 1
        self.reload_color_list()

    def remove_color(self) -> None:
        if len(self.colors) <= 1:
            QMessageBox.warning(self, "Cannot remove color", "At least one color definition is required.")
            return
        removed = self.selected_index
        self.colors.pop(removed)
        for slots in self.civs.values():
            for i, value in enumerate(slots):
                if value == removed:
                    slots[i] = 0
                elif value > removed:
                    slots[i] = value - 1
        self.selected_index = max(0, min(removed, len(self.colors) - 1))
        self.reload_color_list()

    def move_up(self) -> None:
        if self.selected_index <= 0:
            return
        self.swap_colors(self.selected_index, self.selected_index - 1)

    def move_down(self) -> None:
        if self.selected_index >= len(self.colors) - 1:
            return
        self.swap_colors(self.selected_index, self.selected_index + 1)

    def swap_colors(self, a: int, b: int) -> None:
        self.colors[a], self.colors[b] = self.colors[b], self.colors[a]
        for slots in self.civs.values():
            for i, value in enumerate(slots):
                if value == a:
                    slots[i] = b
                elif value == b:
                    slots[i] = a
        self.selected_index = b
        self.reload_color_list()

    def refresh_civ_combos(self, keep_values: bool = False) -> None:
        if not hasattr(self, "civs_layout"):
            return
        if not keep_values:
            while self.civs_layout.count():
                item = self.civs_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
            self.civ_combos.clear()
            for civ_name, slots in self.civs.items():
                card = QFrame()
                card.setObjectName("CivCard")
                card.setMinimumWidth(360)
                card_layout = QVBoxLayout(card)
                card_layout.setContentsMargins(14, 14, 14, 14)
                card_layout.setSpacing(10)

                header = QHBoxLayout()
                title = QLabel(civ_name)
                title.setObjectName("Kicker")
                count = QLabel("11 slots")
                count.setObjectName("Muted")
                header.addWidget(title)
                header.addStretch(1)
                header.addWidget(count)
                card_layout.addLayout(header)

                for slot_index in range(11):
                    while len(slots) <= slot_index:
                        slots.append(0)
                    row_widget = QWidget()
                    row_layout = QHBoxLayout(row_widget)
                    row_layout.setContentsMargins(0, 0, 0, 0)
                    row_layout.setSpacing(8)

                    label = QLabel(f"Player {player_num(slot_index)}")
                    label.setFixedWidth(64)
                    swatch = QFrame()
                    swatch.setObjectName("SlotSwatch")
                    swatch.setFixedSize(34, 24)
                    combo = QComboBox()
                    combo.setMinimumWidth(190)
                    combo.currentIndexChanged.connect(lambda value, c=civ_name, s=slot_index: self.update_civ_slot(c, s, value))
                    row_layout.addWidget(label)
                    row_layout.addWidget(swatch)
                    row_layout.addWidget(combo, 1)
                    card_layout.addWidget(row_widget)
                    self.civ_combos.append((civ_name, slot_index, swatch, combo))
                self.civs_layout.addWidget(card)
            self.civs_layout.addStretch(1)
        names = [color.get("name", "") for color in self.colors]
        for civ_name, slot_index, swatch, combo in self.civ_combos:
            slots = self.civs.get(civ_name, [])
            value = slots[slot_index] if slot_index < len(slots) else 0
            value = max(0, min(value, len(names) - 1)) if names else 0
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(names)
            if names:
                combo.setCurrentIndex(value)
            combo.blockSignals(False)
            rgb = self.colors[value].get("attrs", {}).get("objects", [0, 0, 0]) if self.colors else [0, 0, 0]
            swatch.setStyleSheet(color_style(rgb))

    def update_civ_slot(self, civ_name: str, slot_index: int, value: int) -> None:
        self.civs[civ_name][slot_index] = max(0, value)
        for combo_civ, combo_slot, swatch, _combo in self.civ_combos:
            if combo_civ == civ_name and combo_slot == slot_index:
                rgb = self.colors[value].get("attrs", {}).get("objects", [0, 0, 0]) if 0 <= value < len(self.colors) else [0, 0, 0]
                swatch.setStyleSheet(color_style(rgb))
                break
        self.refresh_xml_preview()

    def reset_vanilla(self) -> None:
        self.colors, self.civs = default_model()
        self.selected_index = 0
        self.reload_color_list()
        self.select_color(0)

    def import_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import playercolors.xml", "", "XML files (*.xml);;All files (*.*)")
        if not path:
            return
        try:
            self.colors, self.civs = import_xml(path)
            self.selected_index = 0
            self.reload_color_list()
            self.select_color(0)
            QMessageBox.information(self, "Import complete", f"Imported {os.path.basename(path)}.")
        except Exception as exc:
            QMessageBox.critical(self, "Import failed", str(exc))

    def export_file(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export playercolors.xml", "playercolors.xml", "XML files (*.xml);;All files (*.*)")
        if not path:
            return
        try:
            with open(path, "w", encoding="us-ascii") as handle:
                handle.write(build_xml(self.colors, self.civs))
            QMessageBox.information(self, "Export complete", f"Saved {path}.")
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", str(exc))

    def refresh_xml_preview(self) -> None:
        if hasattr(self, "xml_preview"):
            self.xml_preview.setPlainText(build_xml(self.colors, self.civs))

    def copy_xml(self) -> None:
        QApplication.clipboard().setText(build_xml(self.colors, self.civs))
        QMessageBox.information(self, "Copied", "playercolors.xml copied to the clipboard.")


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    window = PlayerColorsEditor()
    window.setWindowFlag(Qt.WindowStaysOnTopHint, True)
    window.show()
    window.raise_()
    window.activateWindow()
    QTimer.singleShot(150, window.raise_)
    QTimer.singleShot(160, window.activateWindow)

    def release_topmost() -> None:
        window.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        window.show()
        window.raise_()
        window.activateWindow()

    QTimer.singleShot(700, release_topmost)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
