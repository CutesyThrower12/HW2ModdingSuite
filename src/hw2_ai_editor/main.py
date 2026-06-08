"""
hw2_ai_editor — main.py
========================
Full PySide6 application for editing Halo Wars 2 AI strategy XML files.
Aesthetic: HW2 Modding Suite dark navy, cyan/blue accents, crisp data panels.
"""

import sys
import os
import json
from typing import Optional, List

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QLabel, QPushButton, QLineEdit, QSpinBox,
    QCheckBox, QComboBox, QTextEdit, QScrollArea, QFrame, QFileDialog,
    QGroupBox, QFormLayout, QMessageBox, QListWidget, QListWidgetItem,
    QSizePolicy, QToolTip, QDialog, QDialogButtonBox, QStatusBar, QGridLayout,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QPlainTextEdit, QStyle
)
from PySide6.QtCore import Qt, QSize, Signal, QThread, QTimer
from PySide6.QtGui import (
    QFont, QColor, QPalette, QIcon, QPixmap, QFontDatabase,
    QSyntaxHighlighter, QTextCharFormat, QCursor, QGuiApplication
)

from .core.models import (
    AITable, AISettings, LeaderPower,
    BuildingDirective, TechDirective, MissionDirective, SquadEntry
)
from .core.parser import parse_file
from .core.exporter import export_xml
from .core.validator import validate, ValidationIssue
from .core.knowledge import STRATEGY_INFO, FIELD_TOOLTIPS, STRATEGY_PHASE_GUIDE


# ============================================================
# THEME
# ============================================================

DARK_BG       = "#07101A"
PANEL_BG      = "#0D1725"
CARD_BG       = "#111F31"
CARD_SOFT     = "#0A1420"
BORDER        = "#2A415C"
ACCENT        = "#5DE8FF"
ACCENT_DARK   = "#2F80ED"
TEXT_BRIGHT   = "#F4F8FF"
TEXT_MID      = "#AAB8CA"
TEXT_DIM      = "#718196"
ERROR_RED     = "#FF5F7A"
WARN_AMBER    = "#FFD166"
OK_GREEN      = "#58F29A"
INFO_BLUE     = "#75D8FF"

MONO_FONT     = "Cascadia Mono"
UI_FONT       = "Segoe UI"


def runtime_path(*parts: str) -> str:
    base_dir = getattr(sys, "_MEIPASS", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    return os.path.join(base_dir, *parts)


STYLESHEET = f"""
QMainWindow, QDialog {{
    background: {DARK_BG};
    color: {TEXT_BRIGHT};
}}
QWidget {{
    background: {DARK_BG};
    color: {TEXT_BRIGHT};
    font-family: '{UI_FONT}';
    font-size: 13px;
}}
QLabel {{
    background: transparent;
}}
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 8px;
    background: {PANEL_BG};
    top: -1px;
}}
QTabBar::tab {{
    background: {CARD_BG};
    color: {TEXT_MID};
    border: 1px solid {BORDER};
    border-bottom: none;
    padding: 11px 22px;
    margin-right: 5px;
    font-size: 12px;
    border-top-left-radius: 7px;
    border-top-right-radius: 7px;
}}
QTabBar::tab:selected {{
    background: {PANEL_BG};
    color: {ACCENT};
    border-top: 2px solid {ACCENT};
    font-weight: bold;
}}
QTabBar::tab:hover {{
    color: {TEXT_BRIGHT};
}}
QPushButton {{
    background: #17283D;
    color: {TEXT_BRIGHT};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 9px 16px;
    font-weight: bold;
    font-size: 12px;
    min-height: 18px;
}}
QPushButton:hover {{
    background: #203754;
    border-color: {ACCENT_DARK};
    color: {TEXT_BRIGHT};
}}
QPushButton:pressed {{
    background: #102037;
    color: {TEXT_BRIGHT};
}}
QPushButton#primary {{
    background: {ACCENT_DARK};
    color: white;
    border: none;
    font-size: 13px;
}}
QPushButton#primary:hover {{
    background: #3F8EFF;
}}
QPushButton#danger {{
    color: {ERROR_RED};
    border-color: {ERROR_RED};
}}
QPushButton#danger:hover {{
    background: {ERROR_RED};
    color: white;
}}
QLineEdit, QSpinBox, QComboBox {{
    background: {CARD_SOFT};
    color: {TEXT_BRIGHT};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 9px 11px;
    min-height: 26px;
    selection-background-color: {ACCENT_DARK};
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border-color: {ACCENT};
}}
QComboBox::drop-down {{
    border: none;
    width: 26px;
}}
QComboBox QAbstractItemView {{
    background: {CARD_BG};
    color: {TEXT_BRIGHT};
    border: 1px solid {BORDER};
    selection-background-color: {ACCENT_DARK};
}}
QGroupBox {{
    background: {PANEL_BG};
    border: 1px solid {BORDER};
    border-radius: 8px;
    margin-top: 18px;
    padding-top: 16px;
    font-size: 12px;
    color: {TEXT_MID};
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px;
    top: -2px;
    padding: 0 8px;
    background: transparent;
    color: {ACCENT};
}}
QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollBar:vertical {{
    background: {DARK_BG};
    width: 10px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: #31465E;
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {ACCENT_DARK};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QTextEdit, QPlainTextEdit {{
    background: #050A10;
    color: {TEXT_BRIGHT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 10px;
    font-family: '{MONO_FONT}';
    font-size: 12px;
    selection-background-color: {ACCENT_DARK};
}}
QListWidget {{
    background: {CARD_SOFT};
    color: {TEXT_BRIGHT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    outline: none;
}}
QListWidget::item {{
    padding: 9px 11px;
    border-bottom: 1px solid {DARK_BG};
}}
QListWidget::item:selected {{
    background: {ACCENT_DARK};
    color: {TEXT_BRIGHT};
}}
QListWidget::item:hover {{
    background: {BORDER};
}}
QTreeWidget {{
    background: {CARD_SOFT};
    color: {TEXT_BRIGHT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    outline: none;
}}
QTreeWidget::item {{
    padding: 7px 8px;
}}
QTreeWidget::item:selected {{
    background: {ACCENT_DARK};
}}
QTreeWidget::item:hover {{
    background: {BORDER};
}}
QHeaderView::section {{
    background: {PANEL_BG};
    color: {ACCENT};
    border: 1px solid {BORDER};
    padding: 8px;
    font-size: 12px;
}}
QLabel#header {{
    color: {ACCENT};
    font-size: 24px;
    font-weight: bold;
}}
QLabel#subheader {{
    color: {TEXT_MID};
    font-size: 13px;
}}
QLabel#section {{
    color: {ACCENT};
    font-size: 12px;
    font-weight: bold;
    border-bottom: 1px solid {BORDER};
    padding-bottom: 7px;
}}
QLabel#error {{
    color: {ERROR_RED};
    font-size: 12px;
}}
QLabel#warning {{
    color: {WARN_AMBER};
    font-size: 12px;
}}
QLabel#ok {{
    color: {OK_GREEN};
    font-size: 12px;
}}
QLabel#info {{
    color: {INFO_BLUE};
    font-size: 12px;
}}
QFrame#separator {{
    background: {BORDER};
    max-height: 1px;
}}
QFrame#card {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 8px;
}}
QStatusBar {{
    background: {PANEL_BG};
    color: {TEXT_MID};
    border-top: 1px solid {BORDER};
    font-size: 12px;
}}
QCheckBox {{
    spacing: 10px;
    color: {TEXT_BRIGHT};
    font-size: 13px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {BORDER};
    background: {CARD_SOFT};
    border-radius: 3px;
}}
QCheckBox::indicator:checked {{
    background: {ACCENT_DARK};
    border-color: {ACCENT};
}}
QToolTip {{
    background: {PANEL_BG};
    color: {TEXT_BRIGHT};
    border: 1px solid {ACCENT_DARK};
    padding: 8px;
    font-size: 12px;
    max-width: 350px;
}}
"""


# ============================================================
# HELPER WIDGETS
# ============================================================

def make_label(text: str, style: str = "") -> QLabel:
    lbl = QLabel(text)
    if style:
        lbl.setObjectName(style)
    return lbl


def make_separator() -> QFrame:
    f = QFrame()
    f.setObjectName("separator")
    f.setFrameShape(QFrame.HLine)
    f.setFixedHeight(1)
    return f


def make_tip_button(tooltip: str) -> QPushButton:
    btn = QPushButton("?")
    btn.setFixedSize(26, 26)
    btn.setToolTip(tooltip)
    btn.setStyleSheet(f"""
        QPushButton {{
            background: transparent;
            color: {TEXT_DIM};
            border: 1px solid {TEXT_DIM};
            border-radius: 13px;
            font-size: 11px;
            padding: 0;
        }}
        QPushButton:hover {{
            color: {ACCENT};
            border-color: {ACCENT};
        }}
    """)
    return btn


def labeled_field(label: str, widget: QWidget, tooltip: str = "") -> QHBoxLayout:
    row = QHBoxLayout()
    lbl = QLabel(label + ":")
    lbl.setFixedWidth(220)
    lbl.setStyleSheet(f"color: {TEXT_MID}; font-size: 13px; background: transparent;")
    row.addWidget(lbl)
    row.addWidget(widget, 1)
    if tooltip:
        tip = make_tip_button(tooltip)
        row.addWidget(tip)
    return row


# ============================================================
# SETTINGS PANEL
# ============================================================

class SettingsPanel(QWidget):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(make_label("SETTINGS", "section"))

        self.faction = QLineEdit()
        self.faction.setPlaceholderText("e.g. Covenant, UNSC, Banished")
        self.faction.setToolTip(FIELD_TOOLTIPS["Faction"])

        self.game_mode = QLineEdit("Deathmatch")
        self.game_mode.setToolTip(FIELD_TOOLTIPS["GameMode"])

        self.strategy_type = QComboBox()
        self.strategy_type.addItems(["Boom", "FastTech", "MapControl", "Rush", "Turtle", "Custom..."])
        self.strategy_type.setEditable(False)
        self.strategy_type.setToolTip(FIELD_TOOLTIPS["StrategyType"])

        self.commander = QLineEdit()
        self.commander.setPlaceholderText("e.g. Atriox, Ravakteus, Cutter")
        self.commander.setToolTip(FIELD_TOOLTIPS["Commander"])

        self.map_name = QLineEdit()
        self.map_name.setPlaceholderText("Leave blank for all maps")

        self.rally_thresh = QSpinBox()
        self.rally_thresh.setRange(1, 200)
        self.rally_thresh.setValue(10)
        self.rally_thresh.setToolTip(FIELD_TOOLTIPS["RallyPointMovementPopulationThreshold"])

        self.reserved = QCheckBox("Reserved")
        self.reserved.setToolTip(FIELD_TOOLTIPS["Reserved"])
        self.auto_ai = QCheckBox("Auto AI")
        self.auto_ai.setToolTip(FIELD_TOOLTIPS["AutoAI"])

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(14)

        def add_row(label, widget, tip=""):
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {TEXT_MID}; font-size: 13px; background: transparent;")
            if tip:
                widget.setToolTip(tip)
            form.addRow(lbl, widget)

        add_row("Faction", self.faction, FIELD_TOOLTIPS["Faction"])
        add_row("GameMode", self.game_mode, FIELD_TOOLTIPS["GameMode"])
        add_row("StrategyType", self.strategy_type, FIELD_TOOLTIPS["StrategyType"])
        add_row("Commander", self.commander, FIELD_TOOLTIPS["Commander"])
        add_row("Map Name", self.map_name)
        add_row("Rally Threshold", self.rally_thresh,
                FIELD_TOOLTIPS["RallyPointMovementPopulationThreshold"])

        flags_row = QHBoxLayout()
        flags_row.addWidget(self.reserved)
        flags_row.addWidget(self.auto_ai)
        flags_row.addStretch()
        form.addRow("", flags_row)

        layout.addLayout(form)
        layout.addStretch()

    def load(self, s: AISettings):
        self.faction.setText(s.faction)
        self.game_mode.setText(s.game_mode)
        idx = self.strategy_type.findText(s.strategy_type)
        if idx >= 0:
            self.strategy_type.setCurrentIndex(idx)
        else:
            self.strategy_type.addItem(s.strategy_type)
            self.strategy_type.setCurrentIndex(self.strategy_type.count() - 1)
        self.commander.setText(s.commander)
        self.map_name.setText(s.map_name)
        self.rally_thresh.setValue(s.rally_point_movement_population_threshold)
        self.reserved.setChecked(s.reserved)
        self.auto_ai.setChecked(s.auto_ai)

    def get_settings(self) -> AISettings:
        s = AISettings()
        s.faction = self.faction.text().strip()
        s.game_mode = self.game_mode.text().strip()
        s.strategy_type = self.strategy_type.currentText().strip()
        s.commander = self.commander.text().strip()
        s.map_name = self.map_name.text().strip()
        s.rally_point_movement_population_threshold = self.rally_thresh.value()
        s.reserved = self.reserved.isChecked()
        s.auto_ai = self.auto_ai.isChecked()
        return s


# ============================================================
# LEADER POWER PANEL
# ============================================================

class LeaderPowerCard(QFrame):
    delete_requested = Signal(object)
    duplicate_requested = Signal(object)
    move_up_requested = Signal(object)
    move_down_requested = Signal(object)

    def __init__(self, lp: LeaderPower, parent=None):
        super().__init__(parent)
        self.lp = lp
        self.setObjectName("card")
        self.setMinimumWidth(560)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header row
        hdr = QHBoxLayout()
        self.name_edit = QLineEdit(lp.power_type)
        self.name_edit.setFont(QFont(MONO_FONT, 11))
        self.name_edit.setPlaceholderText("LeaderPowerType")
        self.name_edit.setToolTip(FIELD_TOOLTIPS["LeaderPowerType"])
        hdr.addWidget(self.name_edit, 1)

        style = self.style()

        up_btn = QPushButton()
        up_btn.setIcon(style.standardIcon(QStyle.SP_ArrowUp))
        up_btn.setFixedSize(34, 34)
        up_btn.setToolTip("Move power up")
        up_btn.clicked.connect(lambda: self.move_up_requested.emit(self))
        hdr.addWidget(up_btn)

        dn_btn = QPushButton()
        dn_btn.setIcon(style.standardIcon(QStyle.SP_ArrowDown))
        dn_btn.setFixedSize(34, 34)
        dn_btn.setToolTip("Move power down")
        dn_btn.clicked.connect(lambda: self.move_down_requested.emit(self))
        hdr.addWidget(dn_btn)

        dup_btn = QPushButton()
        dup_btn.setIcon(style.standardIcon(QStyle.SP_FileDialogNewFolder))
        dup_btn.setFixedSize(34, 34)
        dup_btn.setToolTip("Duplicate power")
        dup_btn.clicked.connect(lambda: self.duplicate_requested.emit(self))
        hdr.addWidget(dup_btn)

        del_btn = QPushButton()
        del_btn.setIcon(style.standardIcon(QStyle.SP_TrashIcon))
        del_btn.setFixedSize(34, 34)
        del_btn.setObjectName("danger")
        del_btn.setToolTip("Delete power")
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self))
        hdr.addWidget(del_btn)
        layout.addLayout(hdr)

        # Fields
        fields = QFormLayout()
        fields.setHorizontalSpacing(14)
        fields.setVerticalSpacing(9)

        self.target_type = QLineEdit(lp.target_type or "")
        self.target_type.setPlaceholderText("_Unit, _Enemy, _Base …")
        self.target_type.setToolTip(FIELD_TOOLTIPS["TargetType"])

        self.missions = QLineEdit(", ".join(str(m) for m in lp.assigned_mission_ids))
        self.missions.setPlaceholderText("1, 2, 3  (comma-separated)")
        self.missions.setToolTip(FIELD_TOOLTIPS["AssignedMissionID"])

        self.uses = QLineEdit(str(lp.number_of_times_to_be_used) if lp.number_of_times_to_be_used is not None else "")
        self.uses.setPlaceholderText("10000 = unlimited")
        self.uses.setToolTip(FIELD_TOOLTIPS["NumberOfTimesToBeUsed"])

        self.heal = QLineEdit(str(lp.minimum_heal_points_to_heal) if lp.minimum_heal_points_to_heal is not None else "")
        self.heal.setPlaceholderText("optional — healing powers only")
        self.heal.setToolTip(FIELD_TOOLTIPS["MinimumHealPointsToHeal"])

        self.pop = QLineEdit(str(lp.minimum_target_pop_to_cast) if lp.minimum_target_pop_to_cast is not None else "")
        self.pop.setPlaceholderText("optional — offensive powers only")
        self.pop.setToolTip(FIELD_TOOLTIPS["MinimumTargetPopToCast"])

        def mk_lbl(t):
            l = QLabel(t)
            l.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px; background: transparent;")
            return l

        fields.addRow(mk_lbl("TargetType"), self.target_type)
        fields.addRow(mk_lbl("MissionIDs"), self.missions)
        fields.addRow(mk_lbl("Uses"), self.uses)
        fields.addRow(mk_lbl("MinHeal"), self.heal)
        fields.addRow(mk_lbl("MinPop"), self.pop)
        layout.addLayout(fields)

    def get_power(self) -> LeaderPower:
        lp = LeaderPower()
        lp.power_type = self.name_edit.text().strip()
        lp.target_type = self.target_type.text().strip() or None
        raw = self.missions.text().strip()
        lp.assigned_mission_ids = [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]
        u = self.uses.text().strip()
        lp.number_of_times_to_be_used = int(u) if u.isdigit() else None
        h = self.heal.text().strip()
        lp.minimum_heal_points_to_heal = int(h) if h.isdigit() else None
        p = self.pop.text().strip()
        lp.minimum_target_pop_to_cast = int(p) if p.isdigit() else None
        return lp


class LeaderPowerPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(14)

        hdr = QHBoxLayout()
        hdr.addWidget(make_label("LEADER POWERS", "section"), 1)
        add_btn = QPushButton("+ Add Power")
        add_btn.setObjectName("primary")
        add_btn.clicked.connect(lambda: self._add_power())
        hdr.addWidget(add_btn)
        outer.addLayout(hdr)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.container = QWidget()
        self.container.setMinimumWidth(620)
        self.cards_layout = QVBoxLayout(self.container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(14)
        self.cards_layout.addStretch()
        self.scroll.setWidget(self.container)
        outer.addWidget(self.scroll, 1)

        self.cards: List[LeaderPowerCard] = []

    def _add_power(self, lp: Optional[LeaderPower] = None):
        if lp is None:
            lp = LeaderPower(power_type="NewPower")
        card = LeaderPowerCard(lp)
        card.delete_requested.connect(self._remove_card)
        card.duplicate_requested.connect(self._duplicate_card)
        card.move_up_requested.connect(self._move_up_card)
        card.move_down_requested.connect(self._move_down_card)
        self.cards.append(card)
        self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
        card.show()
        self.container.adjustSize()
        self.scroll.ensureWidgetVisible(card)

    def _remove_card(self, card: LeaderPowerCard):
        if card in self.cards:
            self.cards.remove(card)
        card.setParent(None)
        card.deleteLater()

    def _move_up_card(self, card: LeaderPowerCard):
        if card not in self.cards:
            return
        idx = self.cards.index(card)
        if idx <= 0:
            return
        self.cards[idx - 1], self.cards[idx] = self.cards[idx], self.cards[idx - 1]
        self._rebuild_cards()
        self.scroll.ensureWidgetVisible(card)

    def _move_down_card(self, card: LeaderPowerCard):
        if card not in self.cards:
            return
        idx = self.cards.index(card)
        if idx >= len(self.cards) - 1:
            return
        self.cards[idx], self.cards[idx + 1] = self.cards[idx + 1], self.cards[idx]
        self._rebuild_cards()
        self.scroll.ensureWidgetVisible(card)

    def _duplicate_card(self, card: LeaderPowerCard):
        if card not in self.cards:
            return
        idx = self.cards.index(card)
        lp = card.get_power()
        self._add_power_at(idx + 1, lp)

    def _add_power_at(self, index: int, lp: LeaderPower):
        new_card = LeaderPowerCard(lp)
        new_card.delete_requested.connect(self._remove_card)
        new_card.duplicate_requested.connect(self._duplicate_card)
        new_card.move_up_requested.connect(self._move_up_card)
        new_card.move_down_requested.connect(self._move_down_card)
        self.cards.insert(index, new_card)
        self._rebuild_cards()
        self.scroll.ensureWidgetVisible(new_card)

    def _rebuild_cards(self):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                self.cards_layout.removeWidget(widget)
        for card in self.cards:
            self.cards_layout.addWidget(card)
        self.cards_layout.addStretch()

    def load(self, powers: List[LeaderPower]):
        for c in self.cards[:]:
            c.setParent(None)
            c.deleteLater()
        self.cards.clear()
        for lp in powers:
            self._add_power(lp)
        if self.cards:
            self.scroll.ensureWidgetVisible(self.cards[-1])

    def get_powers(self) -> List[LeaderPower]:
        return [c.get_power() for c in self.cards]


# ============================================================
# DIRECTIVE LIST (Buildings / Tech / Missions in doc order)
# ============================================================

class DirectiveListPanel(QWidget):
    """Shows all directives (Building, Tech, Mission) in document order as a tree."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        hdr = QHBoxLayout()
        hdr.addWidget(make_label("DIRECTIVES (Document Order)", "section"), 1)
        add_bldg = QPushButton("+ Building")
        add_tech = QPushButton("+ Tech")
        add_miss = QPushButton("+ Mission")
        add_bldg.clicked.connect(lambda: self._add(BuildingDirective()))
        add_tech.clicked.connect(lambda: self._add(TechDirective()))
        add_miss.clicked.connect(lambda: self._add(MissionDirective()))
        for b in [add_bldg, add_tech, add_miss]:
            hdr.addWidget(b)
        layout.addLayout(hdr)

        # Tree
        self.tree = QTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels(["Type", "Name / Target", "Count / Squads", "Prereq"])
        self.tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tree.setUniformRowHeights(True)
        self.tree.setIndentation(16)
        self.tree.setAlternatingRowColors(False)
        self.tree.itemDoubleClicked.connect(self._edit_item)
        layout.addWidget(self.tree, 1)

        btn_row = QHBoxLayout()
        up_btn = QPushButton("▲ Up")
        dn_btn = QPushButton("▼ Down")
        del_btn = QPushButton("Delete")
        del_btn.setObjectName("danger")
        dup_btn = QPushButton("Duplicate")
        up_btn.clicked.connect(self._move_up)
        dn_btn.clicked.connect(self._move_down)
        del_btn.clicked.connect(self._delete_selected)
        dup_btn.clicked.connect(self._duplicate)
        for b in [up_btn, dn_btn, dup_btn, del_btn]:
            btn_row.addWidget(b)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._directives: List = []

    def _format_prereq(self, d) -> str:
        parts: list[str] = []
        if getattr(d, 'prerequisite_obtained_object_type', None):
            count = getattr(d, 'prerequisite_obtained_object_count', None)
            parts.append(f"Obt:{d.prerequisite_obtained_object_type}{' x'+str(count) if count else ''}")
        if getattr(d, 'prerequisite_sighting_object_type', None):
            count = getattr(d, 'prerequisite_sighting_object_count', None)
            parts.append(f"Sight:{d.prerequisite_sighting_object_type}{' x'+str(count) if count else ''}")
        if getattr(d, 'prerequisite_tech', None):
            parts.append(f"Tech:{d.prerequisite_tech}")
        if getattr(d, 'prerequisite_leader_power', None):
            parts.append(f"Power:{d.prerequisite_leader_power}")
        return "; ".join(parts)

    @staticmethod
    def _unit_label(squad_type: str) -> str:
        """Extract a readable display label from an internal unit string.
        cov_inf_sniper_01       -> sniper
        cov_veh_brutechopper_01 -> brutechopper
        unsc_veh_wolverine_01   -> wolverine
        cov_inf_generic_grunt   -> grunt
        _Vehicle                -> _Vehicle  (wildcards kept as-is)
        """
        if not squad_type or squad_type.startswith("_"):
            return squad_type
        parts = squad_type.split("_")
        # Strip known faction/class prefix tokens
        SKIP = {"cov", "unsc", "van", "ban", "flood", "fore",
                "inf", "veh", "air", "bldg", "hook", "generic"}
        # Strip trailing purely-numeric tokens (01, 02 ...)
        while parts and parts[-1].isdigit():
            parts.pop()
        # Strip leading prefix tokens
        while parts and parts[0].lower() in SKIP:
            parts.pop(0)
        return "_".join(parts) if parts else squad_type

    def _summarize_squad(self, sq) -> str:
        label = self._unit_label(sq.squad_type)
        entry = f"{label} x{sq.number_of_squads}"
        if sq.minimum_number_of_squads is not None:
            entry += f" (min {sq.minimum_number_of_squads})"
        if sq.alternate_squad_types:
            alt_list = [self._unit_label(a) for a in sq.alternate_squad_types]
            entry += f" | alt:{','.join(alt_list)}"
        return entry

    def _directive_row(self, d) -> List[str]:
        if isinstance(d, BuildingDirective):
            prereq = self._format_prereq(d)
            return ["BUILDING", d.building_type, str(d.number_of_building_type_needed), prereq]
        elif isinstance(d, TechDirective):
            prereq = self._format_prereq(d)
            return ["TECH", d.tech_to_research, "", prereq]
        elif isinstance(d, MissionDirective):
            sq_str = ", ".join(self._summarize_squad(s) for s in d.squads[:3])
            if len(d.squads) > 3:
                sq_str += "…"
            prereq = self._format_prereq(d)
            label = f"{d.mission_type}"
            if d.mission_id:
                label += f" [ID:{d.mission_id}]"
            return ["MISSION", label, sq_str, prereq]
        return ["?", "", "", ""]

    def _color_for_type(self, d) -> QColor:
        if isinstance(d, BuildingDirective):
            return QColor("#1a2a1a")
        elif isinstance(d, TechDirective):
            return QColor("#1a1a2a")
        elif isinstance(d, MissionDirective):
            return QColor("#2a1a1a")
        return QColor(CARD_BG)

    def load(self, directives: List):
        self._directives = list(directives)
        self._refresh_tree()

    def _refresh_tree(self):
        current_index = self._selected_index()
        scroll = self.tree.verticalScrollBar()
        scroll_value = scroll.value()

        self.tree.clear()
        for d in self._directives:
            row = self._directive_row(d)
            item = QTreeWidgetItem(row)
            item.setBackground(0, self._color_for_type(d))
            type_color = {
                "BUILDING": QColor(OK_GREEN),
                "TECH": QColor(INFO_BLUE),
                "MISSION": QColor(ACCENT),
            }.get(row[0], QColor(TEXT_MID))
            item.setForeground(0, type_color)
            item.setFont(0, QFont(MONO_FONT, 9))
            item.setFont(1, QFont(MONO_FONT, 9))
            self.tree.addTopLevelItem(item)

        if 0 <= current_index < self.tree.topLevelItemCount():
            self.tree.setCurrentItem(self.tree.topLevelItem(current_index))
        QTimer.singleShot(0, lambda: scroll.setValue(scroll_value))

    def _selected_index(self) -> int:
        items = self.tree.selectedItems()
        if not items:
            return -1
        return self.tree.indexOfTopLevelItem(items[0])

    def _add(self, directive):
        idx = self._selected_index()
        if idx < 0:
            self._directives.append(directive)
        else:
            self._directives.insert(idx + 1, directive)
        self._refresh_tree()
        # Open editor immediately
        self._open_editor(directive, len(self._directives) - 1 if idx < 0 else idx + 1)

    def _move_up(self):
        idx = self._selected_index()
        if idx > 0:
            self._directives[idx], self._directives[idx-1] = self._directives[idx-1], self._directives[idx]
            self._refresh_tree()
            self.tree.setCurrentItem(self.tree.topLevelItem(idx - 1))

    def _move_down(self):
        idx = self._selected_index()
        if 0 <= idx < len(self._directives) - 1:
            self._directives[idx], self._directives[idx+1] = self._directives[idx+1], self._directives[idx]
            self._refresh_tree()
            self.tree.setCurrentItem(self.tree.topLevelItem(idx + 1))

    def _delete_selected(self):
        idx = self._selected_index()
        if idx >= 0:
            self._directives.pop(idx)
            self._refresh_tree()

    def _duplicate(self):
        idx = self._selected_index()
        if idx >= 0:
            import copy
            dup = copy.deepcopy(self._directives[idx])
            self._directives.insert(idx + 1, dup)
            self._refresh_tree()
            if 0 <= idx + 1 < self.tree.topLevelItemCount():
                self.tree.setCurrentItem(self.tree.topLevelItem(idx + 1))

    def _edit_item(self, item, col):
        idx = self.tree.indexOfTopLevelItem(item)
        if 0 <= idx < len(self._directives):
            self._open_editor(self._directives[idx], idx)

    def _open_editor(self, directive, idx: int):
        dlg = DirectiveEditorDialog(directive, self)
        if dlg.exec() == QDialog.Accepted:
            self._directives[idx] = dlg.get_directive()
            self._refresh_tree()

    def get_directives(self) -> List:
        return self._directives


# ============================================================
# DIRECTIVE EDITOR DIALOG
# ============================================================

class DirectiveEditorDialog(QDialog):
    def __init__(self, directive, parent=None):
        super().__init__(parent)
        self._directive = directive
        self.setWindowTitle("Edit Directive")
        self.setMinimumSize(520, 420)
        self.setStyleSheet(STYLESHEET)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        if isinstance(directive, BuildingDirective):
            self._widget = BuildingEditor(directive)
        elif isinstance(directive, TechDirective):
            self._widget = TechEditor(directive)
        elif isinstance(directive, MissionDirective):
            self._widget = MissionEditor(directive)
        else:
            self._widget = QLabel("Unknown directive type")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(self._widget)
        layout.addWidget(scroll, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        if screen:
            available = screen.availableGeometry()
            width = min(820, max(560, available.width() - 120))
            height = min(760, max(480, available.height() - 140))
            self.resize(width, height)
            self.setMaximumSize(max(560, available.width() - 40), max(480, available.height() - 80))
        else:
            self.resize(760, 700)

    def get_directive(self):
        if hasattr(self._widget, 'get_directive'):
            return self._widget.get_directive()
        return self._directive


class _PrereqGroup(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Prerequisites", parent)
        form = QFormLayout(self)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        def mk(tip=""):
            w = QLineEdit()
            if tip:
                w.setToolTip(tip)
            return w

        self.obt_type = mk(FIELD_TOOLTIPS["PrerequisiteObtainedObjectType"])
        self.obt_type.setPlaceholderText("e.g. cov_bldg_supplyDepot_01, _Vehicle")
        self.obt_count = QSpinBox(); self.obt_count.setRange(0, 9999)
        self.sight_type = mk(FIELD_TOOLTIPS["PrerequisiteSightingObjectType"])
        self.sight_type.setPlaceholderText("e.g. unsc_veh_mongoose_01")
        self.sight_count = QSpinBox(); self.sight_count.setRange(0, 9999)
        self.tech = mk(FIELD_TOOLTIPS["PrerequisiteTech"])
        self.tech.setPlaceholderText("e.g. cov_bruteChopper_upgrade4")
        self.power = mk(FIELD_TOOLTIPS["PrerequisiteLeaderPower"])
        self.power.setPlaceholderText("e.g. FieldRecalibration1")

        def lbl(t): l = QLabel(t); l.setStyleSheet(f"color:{TEXT_DIM};font-size:12px;background:transparent;"); return l
        form.addRow(lbl("ObtainedType"), self.obt_type)
        form.addRow(lbl("ObtainedCount"), self.obt_count)
        form.addRow(lbl("SightingType"), self.sight_type)
        form.addRow(lbl("SightingCount"), self.sight_count)
        form.addRow(lbl("Tech"), self.tech)
        form.addRow(lbl("LeaderPower"), self.power)

    def load(self, d):
        self.obt_type.setText(d.prerequisite_obtained_object_type or "")
        self.obt_count.setValue(d.prerequisite_obtained_object_count or 0)
        self.sight_type.setText(d.prerequisite_sighting_object_type or "")
        self.sight_count.setValue(d.prerequisite_sighting_object_count or 0)
        self.tech.setText(d.prerequisite_tech or "")
        self.power.setText(d.prerequisite_leader_power or "")

    def apply(self, d):
        d.prerequisite_obtained_object_type = self.obt_type.text().strip() or None
        d.prerequisite_obtained_object_count = self.obt_count.value() if self.obt_count.value() > 0 else None
        d.prerequisite_sighting_object_type = self.sight_type.text().strip() or None
        d.prerequisite_sighting_object_count = self.sight_count.value() if self.sight_count.value() > 0 else None
        d.prerequisite_tech = self.tech.text().strip() or None
        d.prerequisite_leader_power = self.power.text().strip() or None


class BuildingEditor(QWidget):
    def __init__(self, b: BuildingDirective, parent=None):
        super().__init__(parent)
        self._b = b
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        layout.addWidget(make_label("BUILDING DIRECTIVE", "section"))

        form = QFormLayout()
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        def lbl(t): l = QLabel(t); l.setStyleSheet(f"color:{TEXT_MID};font-size:13px;background:transparent;"); return l

        self.btype = QLineEdit(b.building_type)
        self.btype.setToolTip(FIELD_TOOLTIPS["BuildingType"])
        self.btype.setFont(QFont(MONO_FONT, 11))
        self.count = QSpinBox(); self.count.setRange(1, 999); self.count.setValue(b.number_of_building_type_needed)
        self.count.setToolTip(FIELD_TOOLTIPS["NumberOfBuildingTypeNeeded"])
        self.loc = QLineEdit(b.production_location_type or "")
        self.loc.setPlaceholderText("optional — e.g. _Minibase")
        self.loc.setToolTip(FIELD_TOOLTIPS["ProductionLocationType"])
        self.recycle = QCheckBox("RecycleBuilding")
        self.recycle.setChecked(b.recycle_building)
        self.recycle.setToolTip(FIELD_TOOLTIPS["RecycleBuilding"])

        form.addRow(lbl("BuildingType"), self.btype)
        form.addRow(lbl("NumberNeeded"), self.count)
        form.addRow(lbl("ProductionLocation"), self.loc)
        form.addRow("", self.recycle)
        layout.addLayout(form)

        self.prereq = _PrereqGroup()
        self.prereq.load(b)
        layout.addWidget(self.prereq)

    def get_directive(self) -> BuildingDirective:
        b = BuildingDirective()
        b.building_type = self.btype.text().strip()
        b.number_of_building_type_needed = self.count.value()
        b.production_location_type = self.loc.text().strip() or None
        b.recycle_building = self.recycle.isChecked()
        self.prereq.apply(b)
        return b


class TechEditor(QWidget):
    def __init__(self, t: TechDirective, parent=None):
        super().__init__(parent)
        self._t = t
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        layout.addWidget(make_label("TECH DIRECTIVE", "section"))

        form = QFormLayout(); form.setHorizontalSpacing(14); form.setVerticalSpacing(10)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        def lbl(s): l = QLabel(s); l.setStyleSheet(f"color:{TEXT_MID};font-size:13px;background:transparent;"); return l

        self.tech = QLineEdit(t.tech_to_research)
        self.tech.setFont(QFont(MONO_FONT, 11))
        self.tech.setToolTip(FIELD_TOOLTIPS["TechToResearch"])
        form.addRow(lbl("TechToResearch"), self.tech)
        layout.addLayout(form)

        self.prereq = _PrereqGroup()
        self.prereq.load(t)
        layout.addWidget(self.prereq)

    def get_directive(self) -> TechDirective:
        t = TechDirective()
        t.tech_to_research = self.tech.text().strip()
        self.prereq.apply(t)
        return t


class MissionEditor(QWidget):
    def __init__(self, m: MissionDirective, parent=None):
        super().__init__(parent)
        self._m = m
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        layout.addWidget(make_label("MISSION DIRECTIVE", "section"))

        form = QFormLayout(); form.setHorizontalSpacing(14); form.setVerticalSpacing(10)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        def lbl(s): l = QLabel(s); l.setStyleSheet(f"color:{TEXT_MID};font-size:13px;background:transparent;"); return l

        self.mtype = QComboBox()
        self.mtype.addItems(["Attack", "Defend", "Reserves", "Forage", "Scout", "BaseScout"])
        self.mtype.setEditable(True)
        idx = self.mtype.findText(m.mission_type)
        if idx >= 0: self.mtype.setCurrentIndex(idx)
        else: self.mtype.setEditText(m.mission_type)
        self.mtype.setToolTip(FIELD_TOOLTIPS["MissionType"])

        self.mid = QLineEdit(str(m.mission_id) if m.mission_id is not None else "")
        self.mid.setPlaceholderText("optional — links to LeaderPower AssignedMissionID")
        self.mid.setToolTip(FIELD_TOOLTIPS["MissionID"])

        self.targets = QLineEdit(", ".join(m.target_types))
        self.targets.setPlaceholderText("_Base, hook_bldg_EnergyCapturePoint_01 …")
        self.targets.setToolTip(FIELD_TOOLTIPS["TargetType"])

        self.target_bases = QLineEdit(", ".join(m.target_base_types))
        self.target_bases.setPlaceholderText("Start, Expansion, Mini …")
        self.target_bases.setToolTip(FIELD_TOOLTIPS["TargetBaseType"])

        self.repeats = QSpinBox(); self.repeats.setRange(-1, 9999); self.repeats.setValue(m.number_of_times_to_repeat_mission)
        self.repeats.setToolTip(FIELD_TOOLTIPS["NumberOfTimesToRepeatMission"])
        self.replace = QSpinBox(); self.replace.setRange(-1, 9999); self.replace.setValue(m.number_of_times_to_replace_squads)
        self.replace.setToolTip(FIELD_TOOLTIPS["NumberOfTimesToReplaceSquads"])
        self.wait = QLineEdit(str(m.time_to_wait_at_target) if m.time_to_wait_at_target is not None else "")
        self.wait.setPlaceholderText("seconds at target (optional)")
        self.wait.setToolTip(FIELD_TOOLTIPS["TimeToWaitAtTarget"])
        self.squad_replace_time = QLineEdit(str(m.time_until_squads_are_replaced) if m.time_until_squads_are_replaced is not None else "")
        self.squad_replace_time.setPlaceholderText("seconds before replacing squads (MapControl Scout: 30)")
        self.squad_replace_time.setToolTip(FIELD_TOOLTIPS["TimeUntilSquadsAreReplaced"])

        form.addRow(lbl("MissionType"), self.mtype)
        form.addRow(lbl("MissionID"), self.mid)
        form.addRow(lbl("Targets"), self.targets)
        form.addRow(lbl("TargetBases"), self.target_bases)
        form.addRow(lbl("Repeat"), self.repeats)
        form.addRow(lbl("Replace"), self.replace)
        form.addRow(lbl("WaitAtTarget"), self.wait)
        form.addRow(lbl("SquadReplaceTime"), self.squad_replace_time)
        layout.addLayout(form)

        # Flags
        flags_box = QGroupBox("Mission Flags")
        flags_layout = QGridLayout(flags_box)
        flags_layout.setHorizontalSpacing(18)
        flags_layout.setVerticalSpacing(8)
        def ck(label, tip=""):
            c = QCheckBox(label)
            c.setToolTip(tip)
            c.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            return c
        self.focus = ck("Focus fire", FIELD_TOOLTIPS["FocusFireOnTarget"])
        self.stream = ck("Stream replacements", FIELD_TOOLTIPS["StreamReplaceSquads"])
        self.take = ck("Take from others", FIELD_TOOLTIPS["TakeSquadsFromOtherMissions"])
        self.no_take = ck("Keep squads here", FIELD_TOOLTIPS["DontTakeSquadsFromThisMission"])
        self.rally = ck("Return to rally", FIELD_TOOLTIPS["ReturnToRallyPoint"])
        self.closest = ck("Closest random first", FIELD_TOOLTIPS["TargetClosestObjectsToRandomEnemyFirst"])
        self.skip = ck("Skip existing target", FIELD_TOOLTIPS["SkipTargetIfPreviousTargetExists"])
        self.init_after = ck("After previous complete", FIELD_TOOLTIPS["InitializeAfterPreviousMissionsComplete"])

        self.focus.setChecked(m.focus_fire_on_target)
        self.stream.setChecked(m.stream_replace_squads)
        self.take.setChecked(m.take_squads_from_other_missions)
        self.no_take.setChecked(m.dont_take_squads_from_this_mission)
        self.rally.setChecked(m.return_to_rally_point)
        self.closest.setChecked(m.target_closest_objects_to_random_enemy_first)
        self.skip.setChecked(m.skip_target_if_previous_target_exists)
        self.init_after.setChecked(m.initialize_after_previous_missions_complete)

        flag_widgets = [
            self.focus, self.stream,
            self.take, self.no_take,
            self.rally, self.closest,
            self.skip, self.init_after,
        ]
        for idx, widget in enumerate(flag_widgets):
            flags_layout.addWidget(widget, idx // 2, idx % 2)
        layout.addWidget(flags_box)

        # Squads
        sq_box = QGroupBox("Squads")
        sq_layout = QVBoxLayout(sq_box)
        sq_layout.setSpacing(10)
        self.squads_edit = QPlainTextEdit()
        self.squads_edit.setFont(QFont(MONO_FONT, 11))
        self.squads_edit.setFixedHeight(130)
        self.squads_edit.setToolTip(
            "One squad per line. Format:\n"
            "  squad_type, count[, min_count][, alt:AlternateType]\n"
            "Example:  cov_inf_generic_grunt, 13, 8"
        )
        # Populate
        lines = []
        for sq in m.squads:
            parts = [sq.squad_type, str(sq.number_of_squads)]
            if sq.minimum_number_of_squads is not None:
                parts.append(str(sq.minimum_number_of_squads))
            for alt in sq.alternate_squad_types:
                parts.append(f"alt:{alt}")
            lines.append(", ".join(parts))
        self.squads_edit.setPlainText("\n".join(lines))
        sq_hint = QLabel("Format: squad_type, count[, min_count][, alt:AlternateSqType]")
        sq_hint.setStyleSheet(f"color:{TEXT_DIM};font-size:12px;background:transparent;")
        sq_layout.addWidget(self.squads_edit)
        sq_layout.addWidget(sq_hint)
        layout.addWidget(sq_box)

        self.prereq = _PrereqGroup()
        self.prereq.load(m)
        layout.addWidget(self.prereq)

    def get_directive(self) -> MissionDirective:
        m = MissionDirective()
        m.mission_type = self.mtype.currentText().strip()
        mid_txt = self.mid.text().strip()
        m.mission_id = int(mid_txt) if mid_txt.isdigit() else None
        m.target_types = [t.strip() for t in self.targets.text().split(",") if t.strip()]
        m.target_base_types = [t.strip() for t in self.target_bases.text().split(",") if t.strip()]
        m.number_of_times_to_repeat_mission = self.repeats.value()
        m.number_of_times_to_replace_squads = self.replace.value()
        w = self.wait.text().strip()
        m.time_to_wait_at_target = int(w) if w.isdigit() else None
        sr = self.squad_replace_time.text().strip()
        m.time_until_squads_are_replaced = int(sr) if sr.isdigit() else None
        m.focus_fire_on_target = self.focus.isChecked()
        m.stream_replace_squads = self.stream.isChecked()
        m.take_squads_from_other_missions = self.take.isChecked()
        m.dont_take_squads_from_this_mission = self.no_take.isChecked()
        m.return_to_rally_point = self.rally.isChecked()
        m.target_closest_objects_to_random_enemy_first = self.closest.isChecked()
        m.skip_target_if_previous_target_exists = self.skip.isChecked()
        m.initialize_after_previous_missions_complete = self.init_after.isChecked()
        # Parse squads
        for line in self.squads_edit.toPlainText().splitlines():
            parts = [p.strip() for p in line.split(",") if p.strip()]
            if not parts:
                continue
            sq = SquadEntry(squad_type=parts[0])
            if len(parts) >= 2 and parts[1].isdigit():
                sq.number_of_squads = int(parts[1])
            if len(parts) >= 3 and parts[2].isdigit():
                sq.minimum_number_of_squads = int(parts[2])
            for p in parts[3:]:
                if p.startswith("alt:"):
                    sq.alternate_squad_types.append(p[4:])
            m.squads.append(sq)
        self.prereq.apply(m)
        return m


# ============================================================
# VALIDATION PANEL
# ============================================================

class ValidationPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        hdr = QHBoxLayout()
        hdr.addWidget(make_label("VALIDATION", "section"), 1)
        self.run_btn = QPushButton("▶ Run Validation")
        self.run_btn.setObjectName("primary")
        hdr.addWidget(self.run_btn)
        layout.addLayout(hdr)

        self.issue_list = QListWidget()
        layout.addWidget(self.issue_list, 1)

        self.summary = QLabel("Run validation to check your AI file.")
        self.summary.setStyleSheet(f"color:{TEXT_MID};font-size:13px;background:transparent;padding:8px 0;")
        layout.addWidget(self.summary)

    def show_issues(self, issues: List[ValidationIssue]):
        self.issue_list.clear()
        counts = {"ERROR": 0, "WARNING": 0, "INFO": 0}
        for issue in issues:
            counts[issue.severity] += 1
            icon = {"ERROR": "✕", "WARNING": "⚠", "INFO": "ℹ"}.get(issue.severity, "•")
            color = {"ERROR": ERROR_RED, "WARNING": WARN_AMBER, "INFO": INFO_BLUE}.get(issue.severity, TEXT_MID)
            item = QListWidgetItem(f"{icon}  [{issue.code}]  {issue.message}")
            item.setForeground(QColor(color))
            self.issue_list.addItem(item)

        if not issues:
            item = QListWidgetItem("✓  No issues found — file looks good!")
            item.setForeground(QColor(OK_GREEN))
            self.issue_list.addItem(item)
            self.summary.setText("✓ Validation passed.")
            self.summary.setObjectName("ok")
        else:
            self.summary.setText(
                f"Found {counts['ERROR']} error(s), {counts['WARNING']} warning(s), {counts['INFO']} info(s)."
            )


# ============================================================
# STRATEGY KNOWLEDGE PANEL
# ============================================================

class KnowledgePanel(QWidget):
    def __init__(self, strategy: str, parent=None):
        super().__init__(parent)
        self.strategy = strategy
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        info = STRATEGY_INFO.get(strategy, {})

        layout.addWidget(make_label(f"{strategy.upper()} — STRATEGY GUIDE", "section"))

        tagline = QLabel(info.get("tagline", ""))
        tagline.setStyleSheet(f"color:{ACCENT};font-size:14px;font-style:italic;background:transparent;")
        tagline.setWordWrap(True)
        layout.addWidget(tagline)

        desc = QLabel(info.get("description", ""))
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color:{TEXT_MID};font-size:13px;background:transparent;")
        layout.addWidget(desc)

        layout.addWidget(make_separator())

        # Phase guide
        phases = STRATEGY_PHASE_GUIDE.get(strategy, [])
        if phases:
            layout.addWidget(make_label("BUILD PHASES", "section"))
            for ph in phases:
                ph_frame = QFrame()
                ph_frame.setObjectName("card")
                ph_layout = QHBoxLayout(ph_frame)
                ph_layout.setContentsMargins(16, 14, 16, 14)
                ph_layout.setSpacing(16)
                ph_lbl = QLabel(ph["phase"])
                ph_lbl.setFixedWidth(210)
                ph_lbl.setStyleSheet(f"color:{ACCENT};font-weight:bold;font-size:13px;background:transparent;")
                ph_desc = QLabel(ph["description"])
                ph_desc.setStyleSheet(f"color:{TEXT_MID};font-size:13px;background:transparent;")
                ph_desc.setWordWrap(True)
                ph_layout.addWidget(ph_lbl)
                ph_layout.addWidget(ph_desc, 1)
                layout.addWidget(ph_frame)

        layout.addWidget(make_separator())

        # Tips
        tips = info.get("tuning_tips", [])
        if tips:
            layout.addWidget(make_label("TUNING TIPS", "section"))
            for tip in tips:
                tip_lbl = QLabel(f"▸  {tip}")
                tip_lbl.setWordWrap(True)
                tip_lbl.setStyleSheet(f"color:{OK_GREEN};font-size:13px;padding:4px 0;background:transparent;")
                layout.addWidget(tip_lbl)

        layout.addWidget(make_separator())

        # Mistakes
        mistakes = info.get("common_mistakes", [])
        if mistakes:
            layout.addWidget(make_label("COMMON MISTAKES", "section"))
            for m in mistakes:
                m_lbl = QLabel(f"✕  {m}")
                m_lbl.setWordWrap(True)
                m_lbl.setStyleSheet(f"color:{ERROR_RED};font-size:13px;padding:4px 0;background:transparent;")
                layout.addWidget(m_lbl)

        layout.addStretch()


# ============================================================
# XML PREVIEW PANEL
# ============================================================

class XMLPreviewPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        hdr = QHBoxLayout()
        hdr.addWidget(make_label("XML PREVIEW", "section"), 1)
        self.refresh_btn = QPushButton("↻ Refresh")
        self.copy_btn = QPushButton("⧉ Copy")
        hdr.addWidget(self.refresh_btn)
        hdr.addWidget(self.copy_btn)
        layout.addLayout(hdr)

        self.editor = QPlainTextEdit()
        self.editor.setFont(QFont(MONO_FONT, 11))
        self.editor.setReadOnly(False)
        layout.addWidget(self.editor, 1)

    def set_xml(self, xml: str):
        self.editor.setPlainText(xml)

    def get_xml(self) -> str:
        return self.editor.toPlainText()


# ============================================================
# LEADER WIZARD DIALOG
# ============================================================

class LeaderWizardDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Leader Pathing Wizard")
        self.setMinimumWidth(640)
        self.setMinimumHeight(500)
        self.setStyleSheet(STYLESHEET)

        layout = QVBoxLayout(self)
        layout.addWidget(make_label("LEADER PATHING WIZARD", "header"))
        layout.addWidget(make_label(
            "Answer the questions below to generate a recommended AI strategy skeleton.",
            "subheader"
        ))
        layout.addWidget(make_separator())

        form = QFormLayout()
        form.setSpacing(10)
        def lbl(t): l = QLabel(t); l.setStyleSheet(f"color:{TEXT_MID};"); return l

        self.faction = QLineEdit(); self.faction.setPlaceholderText("e.g. Covenant, UNSC, Banished")
        self.commander = QLineEdit(); self.commander.setPlaceholderText("e.g. Ravakteus")
        self.strategy = QComboBox(); self.strategy.addItems(["Boom","FastTech","MapControl","Rush","Turtle"])

        self.early_unit = QLineEdit(); self.early_unit.setPlaceholderText("e.g. cov_inf_generic_grunt")
        self.raider = QLineEdit(); self.raider.setPlaceholderText("e.g. cov_veh_brutechopper_01")
        self.mid_unit = QLineEdit(); self.mid_unit.setPlaceholderText("e.g. van_veh_siegeMarauder_01")
        self.late_unit = QLineEdit(); self.late_unit.setPlaceholderText("e.g. cov_veh_scarab_01")
        self.hero_unit = QLineEdit(); self.hero_unit.setPlaceholderText("e.g. van_veh_siegeBreakerChariot_01 (optional)")
        self.eco_bldg = QLineEdit(); self.eco_bldg.setText("cov_bldg_supplyDepot_01")
        self.tech_bldg = QLineEdit(); self.tech_bldg.setText("cov_bldg_reactor_01")
        self.combat_bldg = QLineEdit(); self.combat_bldg.setText("cov_bldg_lightfactory_01")

        form.addRow(lbl("Faction"), self.faction)
        form.addRow(lbl("Commander"), self.commander)
        form.addRow(lbl("Strategy"), self.strategy)
        form.addRow(lbl("Early Infantry"), self.early_unit)
        form.addRow(lbl("Raider / Scout Unit"), self.raider)
        form.addRow(lbl("Mid-Game Vehicle"), self.mid_unit)
        form.addRow(lbl("Late-Game Siege Unit"), self.late_unit)
        form.addRow(lbl("Hero / Elite Unit"), self.hero_unit)
        form.addRow(lbl("Eco Building"), self.eco_bldg)
        form.addRow(lbl("Tech Building"), self.tech_bldg)
        form.addRow(lbl("Combat Building"), self.combat_bldg)
        layout.addLayout(form)

        layout.addWidget(make_separator())

        self.output = QPlainTextEdit()
        self.output.setFont(QFont(MONO_FONT, 9))
        self.output.setFixedHeight(150)
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

        buttons = QDialogButtonBox()
        gen_btn = buttons.addButton("Generate Skeleton", QDialogButtonBox.AcceptRole)
        buttons.addButton("Close", QDialogButtonBox.RejectRole)
        gen_btn.clicked.connect(self._generate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _generate(self):
        strategy = self.strategy.currentText()
        info = STRATEGY_INFO.get(strategy, {})
        tips = info.get("tuning_tips", [])

        summary = (
            f"=== Generated Profile: {self.commander.text() or 'Unknown'} ({strategy}) ===\n\n"
            f"Faction:      {self.faction.text()}\n"
            f"Strategy:     {strategy}\n"
            f"Early unit:   {self.early_unit.text()}\n"
            f"Raider:       {self.raider.text()}\n"
            f"Mid vehicle:  {self.mid_unit.text()}\n"
            f"Late siege:   {self.late_unit.text()}\n"
            f"Hero/Elite:   {self.hero_unit.text() or 'None'}\n\n"
            f"--- Strategy Notes ---\n"
        )
        for tip in tips[:4]:
            summary += f"• {tip}\n"
        summary += (
            f"\n--- What to do next ---\n"
            f"1. Use File → New to create a blank AI table.\n"
            f"2. Fill in Settings with the values above.\n"
            f"3. Add Leader Powers matching your leader's power list.\n"
            f"4. Add directives following the '{strategy}' build phases in the Strategy Guide tab.\n"
            f"5. Swap unit strings above into Mission squads and Reserves.\n"
            f"6. Run Validation before exporting.\n"
        )
        self.output.setPlainText(summary)
        self.accept()


# ============================================================
# MAIN WINDOW
# ============================================================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HW2 AI Strategy Editor")
        icon_path = runtime_path("assets", "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.resize(1520, 940)
        self.setStyleSheet(STYLESHEET)

        self._table: Optional[AITable] = None
        self._current_file: Optional[str] = None

        self._build_menu()
        self._build_ui()
        self._build_status()

        self.status("Ready. Use File → Open to load an AI file, or File → New to start fresh.")

    # ------------------------------------------------------------------
    def _build_menu(self):
        mb = self.menuBar()
        mb.setStyleSheet(f"""
            QMenuBar {{ background:{PANEL_BG}; color:{TEXT_BRIGHT}; border-bottom:1px solid {BORDER}; }}
            QMenuBar::item {{ padding:9px 16px; border-radius:6px; font-size:13px; }}
            QMenuBar::item:selected {{ background:#17283D; color:{TEXT_BRIGHT}; }}
            QMenu {{ background:{CARD_BG}; color:{TEXT_BRIGHT}; border:1px solid {BORDER}; padding:4px; }}
            QMenu::item {{ padding:9px 24px; border-radius:5px; font-size:13px; }}
            QMenu::item:selected {{ background:{ACCENT_DARK}; }}
        """)

        file_menu = mb.addMenu("File")
        file_menu.addAction("New", self._new_file)
        file_menu.addAction("Open…", self._open_file)
        file_menu.addSeparator()
        file_menu.addAction("Save", self._save_file)
        file_menu.addAction("Save As…", self._save_as)
        file_menu.addAction("Export XML…", self._export_xml)
        file_menu.addSeparator()
        file_menu.addAction("Quit", self.close)

        tools_menu = mb.addMenu("Tools")
        tools_menu.addAction("Leader Wizard…", self._open_wizard)
        tools_menu.addAction("Run Validation", self._run_validation)
        tools_menu.addAction("Refresh XML Preview", self._refresh_preview)

    # ------------------------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Left sidebar
        sidebar = self._build_sidebar()
        root.addWidget(sidebar)

        # Main splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet(f"QSplitter::handle {{ background:{BORDER}; }}")

        # Editor area (tabs)
        editor_area = QWidget()
        editor_layout = QVBoxLayout(editor_area)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)

        # File header bar
        self._file_bar = self._build_file_bar()
        editor_layout.addWidget(self._file_bar)

        self.main_tabs = QTabWidget()
        editor_layout.addWidget(self.main_tabs, 1)

        # Tab 1: Settings
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setFrameShape(QFrame.NoFrame)
        self.settings_panel = SettingsPanel()
        settings_scroll.setWidget(self.settings_panel)
        self.main_tabs.addTab(settings_scroll, "Settings")

        # Tab 2: Leader Powers
        self.lp_panel = LeaderPowerPanel()
        self.main_tabs.addTab(self.lp_panel, "Leader Powers")

        # Tab 3: Directives
        self.directive_panel = DirectiveListPanel()
        self.main_tabs.addTab(self.directive_panel, "Directives")

        # Tab 4: Validation
        self.validation_panel = ValidationPanel()
        self.validation_panel.run_btn.clicked.connect(self._run_validation)
        self.main_tabs.addTab(self.validation_panel, "Validation")

        # Tab 5: XML Preview
        self.xml_panel = XMLPreviewPanel()
        self.xml_panel.refresh_btn.clicked.connect(self._refresh_preview)
        self.xml_panel.copy_btn.clicked.connect(self._copy_xml)
        self.main_tabs.addTab(self.xml_panel, "XML Preview")

        # Tab 6+: Strategy Guides
        for strat in ["Boom", "FastTech", "MapControl", "Rush", "Turtle"]:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            panel = KnowledgePanel(strat)
            scroll.setWidget(panel)
            self.main_tabs.addTab(scroll, f"⚑ {strat}")

        splitter.addWidget(editor_area)
        splitter.setSizes([900])
        root.addWidget(splitter, 1)

    def _build_sidebar(self) -> QWidget:
        w = QWidget()
        w.setFixedWidth(292)
        w.setStyleSheet(f"background:{PANEL_BG}; border-right:1px solid {BORDER};")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(20, 22, 20, 16)
        layout.setSpacing(14)

        title = QLabel("HW2 AI Editor")
        title.setStyleSheet(f"""
            color: {ACCENT};
            font-size: 24px;
            font-weight: bold;
            font-family: '{MONO_FONT}';
            background: transparent;
        """)
        layout.addWidget(title)

        sub = QLabel("Halo Wars 2 strategy workspace")
        sub.setWordWrap(True)
        sub.setStyleSheet(f"color:{TEXT_MID};font-size:13px;background:transparent;")
        layout.addWidget(sub)

        layout.addWidget(make_separator())

        # Quick actions
        layout.addWidget(make_label("QUICK ACTIONS", "section"))

        for label, slot in [
            ("Open File", self._open_file),
            ("New File", self._new_file),
            ("Save", self._save_file),
            ("Export XML", self._export_xml),
            ("Validate", self._run_validation),
            ("Leader Wizard", self._open_wizard),
        ]:
            btn = QPushButton(label)
            btn.setMinimumHeight(40)
            btn.clicked.connect(slot)
            layout.addWidget(btn)

        layout.addWidget(make_separator())
        layout.addWidget(make_label("CURRENT FILE", "section"))
        self.file_label = QLabel("No file loaded")
        self.file_label.setWordWrap(True)
        self.file_label.setStyleSheet(f"color:{TEXT_MID};font-size:12px;font-family:'{MONO_FONT}';background:transparent;padding:2px 0;")
        layout.addWidget(self.file_label)

        layout.addWidget(make_separator())
        layout.addWidget(make_label("STATUS", "section"))
        self.status_label = QLabel("Ready")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(f"color:{TEXT_MID};font-size:13px;background:transparent;padding:2px 0;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        version = QLabel("v1.0.0")
        version.setStyleSheet(f"color:{TEXT_DIM};font-size:12px;background:transparent;")
        layout.addWidget(version)
        return w

    def _build_file_bar(self) -> QWidget:
        w = QWidget()
        w.setFixedHeight(58)
        w.setStyleSheet(f"background:{CARD_SOFT};border-bottom:1px solid {BORDER};")
        layout = QHBoxLayout(w)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(12)
        label = QLabel("Active file")
        label.setStyleSheet(f"color:{ACCENT};font-size:12px;font-weight:bold;background:transparent;")
        layout.addWidget(label)
        self.file_path_label = QLabel("No file loaded")
        self.file_path_label.setStyleSheet(f"color:{TEXT_MID};font-family:'{MONO_FONT}';font-size:12px;background:transparent;")
        layout.addWidget(self.file_path_label)
        layout.addStretch()
        return w

    def _build_status(self):
        sb = QStatusBar()
        self.setStatusBar(sb)
        sb.showMessage("Ready")

    # ------------------------------------------------------------------
    def status(self, msg: str):
        self.statusBar().showMessage(msg)
        self.status_label.setText(msg[:80])

    def _set_table(self, table: AITable):
        self._table = table
        self.settings_panel.load(table.settings)
        self.lp_panel.load(table.leader_powers)
        self.directive_panel.load(table.directives)
        self.status(f"Loaded: {table.settings.commander} / {table.settings.strategy_type} / {table.settings.faction}")

    def _collect_table(self) -> AITable:
        table = AITable()
        table.settings = self.settings_panel.get_settings()
        table.leader_powers = self.lp_panel.get_powers()
        table.directives = self.directive_panel.get_directives()
        return table

    # ------------------------------------------------------------------
    def _new_file(self):
        table = AITable()
        table.settings = AISettings(
            faction="", commander="", strategy_type="Boom",
            game_mode="Deathmatch"
        )
        self._current_file = None
        self.file_label.setText("New file (unsaved)")
        self.file_path_label.setText("New file — unsaved")
        self._set_table(table)

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open AI File", "",
            "HW2 AI Files (*.ai *.xml);;All Files (*)"
        )
        if not path:
            return
        try:
            table = parse_file(path)
            self._current_file = path
            fname = os.path.basename(path)
            self.file_label.setText(fname)
            self.file_path_label.setText(path)
            self._set_table(table)
            self.status(f"Opened: {fname}")
        except Exception as e:
            QMessageBox.critical(self, "Open Error", f"Failed to parse file:\n{e}")

    def _save_file(self):
        if self._current_file:
            self._write_file(self._current_file)
        else:
            self._save_as()

    def _save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save AI File", "",
            "HW2 AI Files (*.ai);;XML Files (*.xml);;All Files (*)"
        )
        if path:
            self._current_file = path
            self.file_label.setText(os.path.basename(path))
            self.file_path_label.setText(path)
            self._write_file(path)

    def _write_file(self, path: str):
        try:
            table = self._collect_table()
            xml = export_xml(table)
            with open(path, "w", encoding="us-ascii", errors="replace") as f:
                f.write(xml)
            self.status(f"Saved: {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))

    def _export_xml(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export XML", "",
            "XML Files (*.xml);;HW2 AI Files (*.ai);;All Files (*)"
        )
        if path:
            try:
                table = self._collect_table()
                xml = export_xml(table)
                with open(path, "w", encoding="us-ascii", errors="replace") as f:
                    f.write(xml)
                self.status(f"Exported: {os.path.basename(path)}")
                QMessageBox.information(self, "Export Complete", f"XML exported to:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def _run_validation(self):
        table = self._collect_table()
        issues = validate(table)
        self.validation_panel.show_issues(issues)
        self.main_tabs.setCurrentWidget(self.validation_panel)
        self.status(f"Validation complete — {len(issues)} issue(s) found.")

    def _refresh_preview(self):
        try:
            table = self._collect_table()
            xml = export_xml(table)
            self.xml_panel.set_xml(xml)
            self.main_tabs.setCurrentWidget(self.xml_panel)
        except Exception as e:
            self.xml_panel.set_xml(f"<!-- Error generating XML:\n{e} -->")

    def _copy_xml(self):
        xml = self.xml_panel.get_xml()
        QApplication.clipboard().setText(xml)
        self.status("XML copied to clipboard.")

    def _open_wizard(self):
        dlg = LeaderWizardDialog(self)
        dlg.exec()


# ============================================================
# ENTRY POINT
# ============================================================

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("HW2 AI Strategy Editor")
    app.setApplicationVersion("1.0.0")

    # Load monospace font fallback
    app.setFont(QFont(UI_FONT, 11))

    window = MainWindow()
    window.show()
    QTimer.singleShot(0, window.raise_)
    QTimer.singleShot(0, window.activateWindow)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
