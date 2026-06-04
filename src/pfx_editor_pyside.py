import os
import re
import sys
from dataclasses import dataclass

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


TYPE_RE = re.compile(r"<Type\b[^>]*>\s*(.*?)\s*</Type>", re.IGNORECASE | re.DOTALL)
COLOR_DATA_RE = re.compile(r"<(Colou?rData)\b[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
COLOR_VALUE_RE = re.compile(r"<(Color(?:Vertex\d+)?)\b[^>]*>(\s*-?\d+\s*)</\1>", re.IGNORECASE)
PARTICLE_EFFECT_RE = re.compile(r"<ParticleEffect\b[^>]*\bName=(['\"])(.*?)\1", re.IGNORECASE | re.DOTALL)
EMITTER_RE = re.compile(r"<ParticleEmitter\b([^>]*)>", re.IGNORECASE | re.DOTALL)
ATTR_RE = re.compile(r"\b([A-Za-z_][\w:.-]*)=(['\"])(.*?)\2", re.DOTALL)
TAG_RE = re.compile(r"</?([A-Za-z_][\w:.-]*)\b[^>]*>", re.DOTALL)
PROPERTY_VALUE_RE = re.compile(r"<([A-Za-z_][\w:.-]*)\b[^>]*>([^<>]*)</\1>", re.IGNORECASE)

COLOR_PROPERTY_TAGS = {"PlayerColor", "PlayerColorIntensity", "SunColor", "SunColorIntensity"}
COLOR_VALUE_TAGS = {"Color", "ColorVertex1", "ColorVertex2", "ColorVertex3", "ColorVertex4"}
APP_STYLESHEET = """
QMainWindow, QWidget {
    background: #101216;
    color: #E8EAED;
    font-family: Segoe UI;
    font-size: 12px;
}
QTabWidget::pane {
    border: 1px solid #242933;
    border-radius: 8px;
    top: -1px;
    background: #13161B;
}
QTabBar::tab {
    background: #181C23;
    color: #B8C0CC;
    border: 1px solid #242933;
    border-bottom: none;
    padding: 8px 18px;
    margin-right: 4px;
    border-top-left-radius: 7px;
    border-top-right-radius: 7px;
}
QTabBar::tab:selected {
    background: #202633;
    color: #FFFFFF;
}
QPushButton {
    background: #242B36;
    color: #EEF2F7;
    border: 1px solid #354052;
    border-radius: 6px;
    padding: 7px 12px;
    font-weight: 600;
}
QPushButton:hover {
    background: #2E3848;
    border-color: #4D6078;
}
QPushButton:pressed {
    background: #1C222C;
}
QPushButton#PrimaryButton {
    background: #2D6CDF;
    border-color: #4A86F2;
    color: white;
}
QPushButton#PrimaryButton:hover {
    background: #3A7AF0;
}
QLineEdit, QComboBox, QDoubleSpinBox {
    background: #0D1015;
    border: 1px solid #303746;
    border-radius: 6px;
    padding: 6px 8px;
    color: #F4F7FB;
    selection-background-color: #2D6CDF;
}
QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {
    border-color: #4A86F2;
}
QCheckBox {
    spacing: 8px;
    color: #CAD2DD;
}
QScrollArea {
    border: none;
    background: transparent;
}
QScrollBar:vertical {
    background: #11141A;
    width: 12px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #313947;
    border-radius: 5px;
    min-height: 28px;
}
QScrollBar::handle:vertical:hover {
    background: #48566B;
}
QFrame#ToolbarPanel, QFrame#InfoPanel {
    background: #171B22;
    border: 1px solid #252B36;
    border-radius: 8px;
}
QFrame#ColorGroupCard, QFrame#ColorRowCard, QFrame#PropertyChip {
    background: #171B22;
    border: 1px solid #272F3C;
    border-radius: 8px;
}
QFrame#ColorGroupCard:hover {
    border-color: #3B4A5F;
}
QLabel#TitleLabel {
    color: #FFFFFF;
    font-size: 18px;
    font-weight: 800;
}
QLabel#SubtleLabel {
    color: #99A4B3;
}
QLabel#ChipLabel {
    background: #202633;
    border: 1px solid #30394A;
    border-radius: 6px;
    color: #CBD5E1;
    padding: 4px 8px;
    font-weight: 600;
}
QLabel#EmitterHeader {
    color: #F2D16B;
    font-weight: 800;
    padding-top: 12px;
    padding-bottom: 4px;
}
QLabel {
    background: transparent;
}
QToolButton {
    background: #202633;
    border: 1px solid #30394A;
    border-radius: 6px;
    color: #E8EAED;
    min-width: 24px;
    min-height: 24px;
}
QToolButton:checked, QToolButton:hover {
    background: #2D6CDF;
    border-color: #4A86F2;
}
"""


@dataclass
class ColorEntry:
    index: int
    group_id: int
    label: str
    role: str
    alpha: str
    type_text: str
    effect_name: str
    emitter_name: str
    emitter_active: str
    section_name: str
    line_number: int
    metadata: str
    original_value: int | None
    value_start: int | None
    value_end: int | None
    current_value: int | None

    @property
    def is_editable(self) -> bool:
        return self.original_value is not None


@dataclass
class PropertyEntry:
    index: int
    label: str
    tag_name: str
    category: str
    emitter_name: str
    section_name: str
    line_number: int
    kind: str
    original_value: str
    current_value: str
    value_start: int
    value_end: int
    color_group_id: int | None = None
    source: str = "tag"

    @property
    def is_editable(self) -> bool:
        return self.kind in ("bool", "number")


def int_to_rgb(value: int) -> tuple[int, int, int]:
    rgb = value & 0xFFFFFF
    return (rgb >> 16) & 255, (rgb >> 8) & 255, rgb & 255


def rgb_to_int(r: int, g: int, b: int) -> int:
    rgb = (r << 16) | (g << 8) | b
    if rgb & 0x800000:
        rgb -= 0x1000000
    return rgb


def read_text_file(path: str) -> tuple[str, str]:
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            with open(path, "r", encoding=encoding) as handle:
                return handle.read(), encoding
        except UnicodeDecodeError:
            continue
    with open(path, "r", encoding="latin-1") as handle:
        return handle.read(), "latin-1"


def write_text_file(path: str, text: str, encoding: str) -> None:
    if encoding == "utf-8-sig":
        encoding = "utf-8"
    with open(path, "w", encoding=encoding, newline="") as handle:
        handle.write(text)


def parse_attrs(raw_attrs: str) -> dict[str, str]:
    return {match.group(1): match.group(3) for match in ATTR_RE.finditer(raw_attrs)}


def line_starts_for_text(text: str) -> list[int]:
    return [0] + [match.end() for match in re.finditer("\n", text)]


def line_number_at(line_starts: list[int], position: int) -> int:
    low = 0
    high = len(line_starts)
    while low < high:
        mid = (low + high) // 2
        if line_starts[mid] <= position:
            low = mid + 1
        else:
            high = mid
    return max(1, low)


def find_emitter_contexts(text: str) -> list[tuple[int, int, str, str]]:
    contexts: list[tuple[int, int, str, str]] = []
    for match in EMITTER_RE.finditer(text):
        attrs = parse_attrs(match.group(1))
        end_match = re.search(r"</ParticleEmitter>", text[match.end():], re.IGNORECASE)
        end = match.end() + end_match.end() if end_match else len(text)
        contexts.append((match.start(), end, attrs.get("Name", "Unnamed emitter"), attrs.get("Active", "")))
    return contexts


def context_for_position(
    text: str,
    position: int,
    emitter_contexts: list[tuple[int, int, str, str]],
    line_starts: list[int] | None = None,
) -> tuple[str, str, int, str]:
    emitter_name = "ParticleEffect"
    emitter_active = ""
    emitter_start = 0
    for start, end, name, active in emitter_contexts:
        if start <= position <= end:
            emitter_name = name
            emitter_active = active
            emitter_start = start
            break

    section_name = "ParticleEffect"
    stack: list[str] = []
    for tag in TAG_RE.finditer(text[emitter_start:position]):
        full = tag.group(0)
        name = tag.group(1)
        if full.startswith("</"):
            for index in range(len(stack) - 1, -1, -1):
                if stack[index] == name:
                    del stack[index:]
                    break
        elif not full.endswith("/>"):
            stack.append(name)
    for name in reversed(stack):
        if name not in ("ParticleEmitter", "ParticleEffect"):
            section_name = name
            break

    line_number = line_number_at(line_starts, position) if line_starts is not None else text.count("\n", 0, position) + 1
    return emitter_name, emitter_active, line_number, section_name


def simple_value(block_text: str, tag_name: str) -> str:
    match = re.search(
        rf"<{re.escape(tag_name)}\b[^>]*>\s*(.*?)\s*</{re.escape(tag_name)}>",
        block_text,
        re.IGNORECASE | re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def is_inside_tag(block_text: str, position: int, tag_name: str) -> bool:
    tag = tag_name.lower()
    open_re = re.compile(rf"<{re.escape(tag_name)}\b[^>]*>", re.IGNORECASE)
    close_re = re.compile(rf"</{re.escape(tag_name)}>", re.IGNORECASE)
    last_open = -1
    last_close = -1
    for match in open_re.finditer(block_text, 0, position):
        last_open = match.start()
    for match in close_re.finditer(block_text, 0, position):
        last_close = match.start()
    return last_open > last_close and tag in block_text[last_open:position].lower()


def gradient_info(block_text: str, position: int) -> tuple[str, str]:
    gradient_starts = [match.start() for match in re.finditer(r"<GradientPoint\b[^>]*>", block_text[:position], re.IGNORECASE)]
    point_index = len(gradient_starts)
    if point_index == 0:
        return "Progression color", ""

    point_start = gradient_starts[-1]
    point_close = re.search(r"</GradientPoint>", block_text[position:], re.IGNORECASE)
    point_end = position + point_close.end() if point_close else len(block_text)
    point_text = block_text[point_start:point_end]
    alpha = simple_value(point_text, "Alpha")
    if alpha:
        return f"Progression point {point_index} (alpha {alpha})", alpha
    return f"Progression point {point_index}", ""


def color_info_for_match(block_text: str, position: int, tag_name: str) -> tuple[str, str, str]:
    vertex_match = re.fullmatch(r"ColorVertex(\d+)", tag_name, re.IGNORECASE)
    if vertex_match:
        return f"Vertex {vertex_match.group(1)} color", "vertex", ""
    if is_inside_tag(block_text, position, "ColorProgression"):
        label, alpha = gradient_info(block_text, position)
        return label, "progression", alpha
    if is_inside_tag(block_text, position, "ColorPallette"):
        palette_index = len(list(re.finditer(r"<Color\b", block_text[:position], re.IGNORECASE)))
        return f"Palette color {palette_index}", "palette", ""
    return "Base color", "base", ""


def color_metadata(block_text: str) -> str:
    details = []
    player_color = simple_value(block_text, "PlayerColor")
    player_intensity = simple_value(block_text, "PlayerColorIntensity")
    sun_color = simple_value(block_text, "SunColor")
    sun_intensity = simple_value(block_text, "SunColorIntensity")
    if player_color:
        details.append(f"player color={player_color}")
    if player_intensity:
        details.append(f"player intensity={player_intensity}")
    if sun_color:
        details.append(f"sun color={sun_color}")
    if sun_intensity:
        details.append(f"sun intensity={sun_intensity}")
    return "  |  ".join(details)


def value_kind(value: str) -> str:
    stripped = value.strip()
    if stripped.lower() in ("true", "false"):
        return "bool"
    try:
        float(stripped)
        return "number"
    except ValueError:
        return "text"


def friendly_label(name: str) -> str:
    spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", name)
    return spaced.replace("_", " ")


def color_group_ranges(text: str) -> list[tuple[int, int, int]]:
    return [(match.start(), match.end(), index) for index, match in enumerate(COLOR_DATA_RE.finditer(text), start=1)]


def color_group_for_position(ranges: list[tuple[int, int, int]], position: int) -> int | None:
    for start, end, group_id in ranges:
        if start <= position <= end:
            return group_id
    return None


def find_quick_property_entries(text: str) -> list[PropertyEntry]:
    entries: list[PropertyEntry] = []
    emitter_contexts = find_emitter_contexts(text)
    line_starts = line_starts_for_text(text)

    for emitter_index, emitter_match in enumerate(EMITTER_RE.finditer(text), start=1):
        raw_attrs = emitter_match.group(1)
        attrs = parse_attrs(raw_attrs)
        emitter_name = attrs.get("Name", f"Emitter {emitter_index}")
        for attr_match in ATTR_RE.finditer(raw_attrs):
            attr_name = attr_match.group(1)
            if attr_name.lower() != "active":
                continue
            value = attr_match.group(3)
            kind = value_kind(value)
            if kind != "bool":
                continue
            value_start = emitter_match.start(1) + attr_match.start(3)
            value_end = emitter_match.start(1) + attr_match.end(3)
            entries.append(
                PropertyEntry(
                    index=len(entries) + 1,
                    label="Emitter active",
                    tag_name=attr_name,
                    category="ParticleEmitter",
                    emitter_name=emitter_name,
                    section_name="ParticleEmitter",
                    line_number=line_number_at(line_starts, value_start),
                    kind=kind,
                    original_value=value,
                    current_value=value,
                    value_start=value_start,
                    value_end=value_end,
                    source="attribute",
                )
            )

    for group_id, block_match in enumerate(COLOR_DATA_RE.finditer(text), start=1):
        block_text = block_match.group(0)
        emitter_name, emitter_active, line_number, section_name = context_for_position(
            text,
            block_match.start(),
            emitter_contexts,
            line_starts,
        )
        for tag_name in COLOR_PROPERTY_TAGS:
            match = re.search(
                rf"<{re.escape(tag_name)}\b[^>]*>([^<>]*)</{re.escape(tag_name)}>",
                block_text,
                re.IGNORECASE,
            )
            if not match:
                continue
            raw_value = match.group(1)
            value = raw_value.strip()
            kind = value_kind(value)
            if kind == "text":
                continue
            leading_ws = len(raw_value) - len(raw_value.lstrip())
            trailing_ws = len(raw_value) - len(raw_value.rstrip())
            value_start = block_match.start() + match.start(1) + leading_ws
            value_end = block_match.start() + match.end(1) - trailing_ws
            entries.append(
                PropertyEntry(
                    index=len(entries) + 1,
                    label=friendly_label(tag_name),
                    tag_name=tag_name,
                    category=block_match.group(1),
                    emitter_name=emitter_name,
                    section_name=f"{section_name} / {block_match.group(1)}",
                    line_number=line_number_at(line_starts, value_start),
                    kind=kind,
                    original_value=value,
                    current_value=value,
                    value_start=value_start,
                    value_end=value_end,
                    color_group_id=group_id,
                )
            )
    return entries


def find_color_entries(text: str) -> list[ColorEntry]:
    entries: list[ColorEntry] = []
    effect_match = PARTICLE_EFFECT_RE.search(text)
    effect_name = effect_match.group(2) if effect_match else ""
    emitter_contexts = find_emitter_contexts(text)
    line_starts = line_starts_for_text(text)
    for group_id, block_match in enumerate(COLOR_DATA_RE.finditer(text), start=1):
        block_text = block_match.group(0)
        block_tag = block_match.group(1)
        type_match = TYPE_RE.search(block_text)
        type_text = type_match.group(1).strip() if type_match else block_tag
        metadata = color_metadata(block_text)
        emitter_name, emitter_active, line_number, section_name = context_for_position(
            text,
            block_match.start(),
            emitter_contexts,
            line_starts,
        )
        section_name = f"{section_name} / {block_tag}"

        for color_match in COLOR_VALUE_RE.finditer(block_text):
            raw_value = color_match.group(2)
            try:
                original_value = int(raw_value.strip())
                leading_ws = len(raw_value) - len(raw_value.lstrip())
                trailing_ws = len(raw_value) - len(raw_value.rstrip())
                value_start = block_match.start() + color_match.start(2) + leading_ws
                value_end = block_match.start() + color_match.end(2) - trailing_ws
            except ValueError:
                continue

            absolute_position = block_match.start() + color_match.start()
            label, role, alpha = color_info_for_match(block_text, color_match.start(), color_match.group(1))
            entries.append(
                ColorEntry(
                    index=len(entries) + 1,
                    group_id=group_id,
                    label=label,
                    role=role,
                    alpha=alpha,
                    type_text=type_text,
                    effect_name=effect_name,
                    emitter_name=emitter_name,
                    emitter_active=emitter_active,
                    section_name=section_name,
                    line_number=line_number_at(line_starts, absolute_position),
                    metadata=metadata,
                    original_value=original_value,
                    value_start=value_start,
                    value_end=value_end,
                    current_value=original_value,
                )
            )
    return entries


def apply_color_edits(text: str, entries: list[ColorEntry]) -> tuple[str, int]:
    replacements: list[tuple[int, int, str]] = []
    for entry in entries:
        if not entry.is_editable:
            continue
        if entry.value_start is None or entry.value_end is None:
            continue
        if entry.current_value == entry.original_value:
            continue
        replacements.append((entry.value_start, entry.value_end, str(entry.current_value)))

    for start, end, value in sorted(replacements, reverse=True):
        text = text[:start] + value + text[end:]
    return text, len(replacements)


def apply_property_edits(text: str, entries: list[PropertyEntry]) -> tuple[str, int]:
    replacements: list[tuple[int, int, str]] = []
    for entry in entries:
        if not entry.is_editable:
            continue
        if entry.current_value == entry.original_value:
            continue
        replacements.append((entry.value_start, entry.value_end, entry.current_value))

    for start, end, value in sorted(replacements, reverse=True):
        text = text[:start] + value + text[end:]
    return text, len(replacements)


def apply_particle_edits(
    text: str,
    color_entries: list[ColorEntry],
    property_entries: list[PropertyEntry],
) -> tuple[str, int, int]:
    replacements: list[tuple[int, int, str]] = []
    color_changed = 0
    property_changed = 0

    for entry in color_entries:
        if not entry.is_editable:
            continue
        if entry.value_start is None or entry.value_end is None:
            continue
        if entry.current_value == entry.original_value:
            continue
        replacements.append((entry.value_start, entry.value_end, str(entry.current_value)))
        color_changed += 1

    for entry in property_entries:
        if not entry.is_editable:
            continue
        if entry.current_value == entry.original_value:
            continue
        replacements.append((entry.value_start, entry.value_end, entry.current_value))
        property_changed += 1

    for start, end, value in sorted(replacements, reverse=True):
        text = text[:start] + value + text[end:]
    return text, color_changed, property_changed


def scale_uniform_values_in_text(text: str, multiplier: float) -> tuple[str, int]:
    lines = text.splitlines(keepends=True)
    in_scale_data = False
    result_lines: list[str] = []
    changed = 0

    for line in lines:
        stripped = line.strip()

        if "<ScaleData" in stripped:
            in_scale_data = True

        new_line, did_change = _process_uniform_line(line, in_scale_data, multiplier)
        changed += int(did_change)
        result_lines.append(new_line)

        if "</ScaleData>" in stripped:
            in_scale_data = False

    return "".join(result_lines), changed


def _process_uniform_line(line: str, in_scale_data: bool, multiplier: float) -> tuple[str, bool]:
    if not in_scale_data:
        return line, False

    start_tag = "<UniformValue>"
    end_tag = "</UniformValue>"
    start_idx = line.find(start_tag)
    end_idx = line.find(end_tag)
    if start_idx == -1 or end_idx == -1:
        return line, False

    start_idx += len(start_tag)
    number_str = line[start_idx:end_idx].strip()
    try:
        value = float(number_str)
    except ValueError:
        return line, False

    new_value = value * multiplier
    if number_str.isdigit() or (number_str.startswith("-") and number_str[1:].isdigit()):
        new_number_str = str(int(round(new_value)))
    else:
        new_number_str = f"{new_value:.9g}"

    return line[:start_idx] + new_number_str + line[end_idx:], new_number_str != number_str


def entry_hex(entry: ColorEntry) -> str:
    r, g, b = int_to_rgb(entry.current_value or 0)
    return QColor(r, g, b).name().upper()


def progression_position(entry: ColorEntry, fallback_index: int, fallback_count: int) -> float:
    try:
        return max(0.0, min(1.0, float(entry.alpha)))
    except ValueError:
        if fallback_count <= 1:
            return 0.0
        return fallback_index / (fallback_count - 1)


def gradient_stylesheet(entries: list[ColorEntry]) -> str:
    if not entries:
        return "background: #111; border: 1px solid #333;"
    stops = []
    count = len(entries)
    for index, entry in enumerate(entries):
        percent = progression_position(entry, index, count) * 100.0
        stops.append(f"{entry_hex(entry)} {percent:.1f}%")
    return (
        "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
        + ", ".join(f"stop:{max(0.0, min(1.0, progression_position(entry, i, count))):.4f} {entry_hex(entry)}" for i, entry in enumerate(entries))
        + "); border: 1px solid #333;"
    )


def group_title(entries: list[ColorEntry]) -> str:
    base = next((entry for entry in entries if entry.role == "base"), None)
    lead = base or entries[0]
    return f"{lead.emitter_name}  |  {lead.section_name}"


class PropertyRow(QFrame):
    def __init__(self, entry: PropertyEntry, on_changed, compact: bool = False):
        super().__init__()
        self.entry = entry
        self.on_changed = on_changed
        self.setObjectName("PropertyChip")
        self.setFrameShape(QFrame.StyledPanel)

        layout = QGridLayout(self)
        layout.setColumnStretch(3, 1)

        title_text = entry.label if compact else f"{entry.label}  |  {entry.category}  |  line {entry.line_number}"
        title = QLabel(title_text)
        title.setStyleSheet("font-weight: 600;")
        layout.addWidget(title, 0, 0, 1, 3)

        if not compact:
            context = QLabel(f"{entry.emitter_name}  |  {entry.section_name}  |  {entry.source}")
            context.setStyleSheet("color: #aaa;")
            layout.addWidget(context, 1, 0, 1, 4)

        layout.addWidget(QLabel("Value" if compact else entry.kind), 2, 0)
        if entry.kind == "bool":
            self.editor = QComboBox()
            self.editor.addItems(["true", "false"])
            self.editor.setCurrentText(entry.current_value.lower())
            self.editor.currentTextChanged.connect(self.update_from_editor)
        else:
            self.editor = QLineEdit(entry.current_value)
            self.editor.setFixedWidth(130)
            self.editor.editingFinished.connect(self.update_from_editor)
        layout.addWidget(self.editor, 2, 1)

        original = QLabel(f"orig {entry.original_value}" if compact else f"original {entry.original_value}")
        original.setStyleSheet("color: #888;")
        layout.addWidget(original, 2, 2)

    def update_from_editor(self):
        if isinstance(self.editor, QComboBox):
            value = self.editor.currentText()
        else:
            value = self.editor.text().strip()
            if self.entry.kind == "number":
                try:
                    float(value)
                except ValueError:
                    self.editor.setText(self.entry.current_value)
                    return
        self.entry.current_value = value
        self.on_changed()


class ColorRow(QFrame):
    def __init__(self, entry: ColorEntry, on_changed, compact: bool = False):
        super().__init__()
        self.entry = entry
        self.on_changed = on_changed
        self.setObjectName("ColorRowCard")
        self.setFrameShape(QFrame.StyledPanel)

        layout = QGridLayout(self)
        layout.setColumnStretch(4, 1)

        row = 0
        if not compact:
            title = QLabel(entry.emitter_name)
            title.setStyleSheet("font-weight: 700; font-size: 13px;")
            layout.addWidget(title, row, 0, 1, 2)

            context = QLabel(f"{entry.section_name}  |  line {entry.line_number}")
            context.setStyleSheet("color: #aaa;")
            layout.addWidget(context, row, 2, 1, 2)
            row += 1

        type_label = QLabel(f"{entry.label}  |  {entry.type_text}  |  line {entry.line_number}")
        type_label.setStyleSheet("font-weight: 700; color: #F4F7FB;")
        layout.addWidget(type_label, row, 0, 1, 2)

        state = "editable RGB int"
        state_label = QLabel(state)
        state_label.setStyleSheet("color: #70D58C; font-weight: 600;")
        layout.addWidget(state_label, row + 1, 2, 1, 3)

        self.preview = QLabel()
        self.preview.setFixedSize(48, 28)
        layout.addWidget(self.preview, row, 3)

        self.hex_label = QLabel()
        self.hex_label.setStyleSheet("color: #aaa;")
        layout.addWidget(self.hex_label, row, 4)

        self.int_edit = QLineEdit("" if entry.original_value is None else str(entry.original_value))
        self.int_edit.setEnabled(entry.is_editable)
        self.int_edit.setFixedWidth(120)
        self.int_edit.editingFinished.connect(self.update_from_int)
        layout.addWidget(QLabel("RGB Int"), row + 2, 0)
        layout.addWidget(self.int_edit, row + 2, 1)

        self.pick_button = QPushButton("Pick Color")
        self.pick_button.setObjectName("PrimaryButton")
        self.pick_button.setEnabled(entry.is_editable)
        self.pick_button.clicked.connect(self.open_color_picker)
        layout.addWidget(self.pick_button, row + 2, 2)

        self.update_preview()

    def open_color_picker(self):
        if not self.entry.is_editable:
            return
        r, g, b = int_to_rgb(self.entry.current_value or 0)
        color = QColorDialog.getColor(QColor(r, g, b), self, "Pick Particle Color")
        if not color.isValid():
            return
        value = rgb_to_int(color.red(), color.green(), color.blue())
        self.entry.current_value = value
        self.int_edit.setText(str(value))
        self.update_preview()
        self.on_changed()

    def update_from_int(self):
        if not self.entry.is_editable:
            return
        try:
            value = int(self.int_edit.text().strip())
        except ValueError:
            self.int_edit.setText(str(self.entry.current_value))
            return

        self.entry.current_value = value
        self.update_preview()
        self.on_changed()

    def update_preview(self):
        color = entry_hex(self.entry)
        self.preview.setStyleSheet(f"background: {color}; border: 1px solid #55606f; border-radius: 5px;")
        self.hex_label.setText(color)


class ColorGroup(QFrame):
    def __init__(self, entries: list[ColorEntry], property_entries: list[PropertyEntry], on_changed):
        super().__init__()
        self.entries = entries
        self.property_entries = property_entries
        self.on_changed = on_changed
        self.setObjectName("ColorGroupCard")
        self.setFrameShape(QFrame.StyledPanel)

        self.base_entry = next((entry for entry in entries if entry.role == "base"), None)
        self.vertex_entries = [entry for entry in entries if entry.role == "vertex"]
        self.progression_entries = [entry for entry in entries if entry.role == "progression"]
        self.palette_entries = [entry for entry in entries if entry.role == "palette"]
        self.detail_entries = [entry for entry in entries if entry is not self.base_entry]
        self.quick_properties = self.find_quick_properties()
        self.overview_swatches: list[tuple[QLabel, ColorEntry]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        header = QHBoxLayout()
        self.toggle = QToolButton()
        self.toggle.setText(">")
        self.toggle.setCheckable(True)
        self.toggle.toggled.connect(self.set_expanded)
        header.addWidget(self.toggle)

        title = QLabel(group_title(entries))
        title.setStyleSheet("font-weight: 800; font-size: 13px; color: #F4F7FB;")
        header.addWidget(title, 1)

        count_label = QLabel(self.summary_text())
        count_label.setObjectName("ChipLabel")
        header.addWidget(count_label)
        layout.addLayout(header)

        visual = QHBoxLayout()
        if self.base_entry:
            visual.addWidget(QLabel("Base"))
            visual.addWidget(self.make_swatch(self.base_entry, 54, 28, tracked=True))
        if self.vertex_entries:
            visual.addWidget(QLabel("Vertices"))
            vertex_grid = QGridLayout()
            for index, entry in enumerate(self.vertex_entries[:4]):
                vertex_grid.addWidget(self.make_swatch(entry, 26, 26, tracked=True), index // 2, index % 2)
            visual.addLayout(vertex_grid)
        if self.progression_entries:
            visual.addWidget(QLabel("Progression"))
            self.gradient = QLabel()
            self.gradient.setFixedHeight(28)
            self.gradient.setMinimumWidth(220)
            self.gradient.setStyleSheet(gradient_stylesheet(self.progression_entries))
            visual.addWidget(self.gradient, 1)
        visual.addStretch(1)
        layout.addLayout(visual)

        if self.quick_properties:
            quick = QHBoxLayout()
            quick_label = QLabel("Quick Controls")
            quick_label.setStyleSheet("font-weight: 700; color: #9FB4D9;")
            quick.addWidget(quick_label)
            for prop in self.quick_properties:
                quick.addWidget(PropertyRow(prop, self.changed, compact=True))
            quick.addStretch(1)
            layout.addLayout(quick)

        if self.base_entry:
            layout.addWidget(ColorRow(self.base_entry, self.changed, compact=True))

        self.details_built = False
        self.details = QWidget()
        self.details_layout = QVBoxLayout(self.details)
        self.details_layout.setContentsMargins(22, 4, 0, 0)
        layout.addWidget(self.details)
        self.set_expanded(False)

    def make_swatch(self, entry: ColorEntry, width: int, height: int, tracked: bool = False) -> QLabel:
        swatch = QLabel()
        swatch.setFixedSize(width, height)
        self.update_swatch(swatch, entry)
        if tracked:
            self.overview_swatches.append((swatch, entry))
        return swatch

    def update_swatch(self, swatch: QLabel, entry: ColorEntry):
        swatch.setStyleSheet(f"background: {entry_hex(entry)}; border: 1px solid #55606f; border-radius: 5px;")

    def update_overview(self):
        for swatch, entry in self.overview_swatches:
            self.update_swatch(swatch, entry)
        if hasattr(self, "gradient"):
            self.gradient.setStyleSheet(gradient_stylesheet(self.progression_entries))

    def find_quick_properties(self) -> list[PropertyEntry]:
        lead = self.base_entry or self.entries[0]
        result: list[PropertyEntry] = []
        seen: set[tuple[str, int, int]] = set()
        for prop in self.property_entries:
            is_emitter_active = prop.tag_name == "Active" and prop.emitter_name == lead.emitter_name
            is_color_modifier = prop.color_group_id == lead.group_id and prop.tag_name in COLOR_PROPERTY_TAGS
            if not (is_emitter_active or is_color_modifier):
                continue
            key = (prop.tag_name, prop.value_start, prop.value_end)
            if key in seen:
                continue
            seen.add(key)
            result.append(prop)
        return result

    def section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("font-weight: 800; color: #D8DEE9; padding-top: 8px;")
        return label

    def summary_text(self) -> str:
        parts = []
        if self.vertex_entries:
            parts.append(f"{len(self.vertex_entries)} vertex")
        if self.progression_entries:
            parts.append(f"{len(self.progression_entries)} progression")
        if self.palette_entries:
            parts.append(f"{len(self.palette_entries)} palette")
        if not parts:
            parts.append("base only")
        return ", ".join(parts)

    def set_expanded(self, expanded: bool):
        if expanded and not self.details_built:
            self.build_details()
        self.details.setVisible(expanded)
        self.toggle.setText("v" if expanded else ">")

    def build_details(self):
        if self.vertex_entries:
            self.details_layout.addWidget(self.section_label("Vertex colors"))
            for entry in self.vertex_entries:
                self.details_layout.addWidget(ColorRow(entry, self.changed, compact=True))
        if self.progression_entries:
            self.details_layout.addWidget(self.section_label("Progression points"))
            for entry in self.progression_entries:
                self.details_layout.addWidget(ColorRow(entry, self.changed, compact=True))
        if self.palette_entries:
            self.details_layout.addWidget(self.section_label("Palette colors"))
            for entry in self.palette_entries:
                self.details_layout.addWidget(ColorRow(entry, self.changed, compact=True))
        self.details_built = True

    def changed(self):
        self.update_overview()
        self.on_changed()


class ParticleEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Halo Wars 2 Particle Editor")
        self.resize(1050, 720)
        self.setStyleSheet(APP_STYLESHEET)

        self.file_path: str | None = None
        self.encoding = "utf-8"
        self.original_text = ""
        self.color_entries: list[ColorEntry] = []
        self.property_entries: list[PropertyEntry] = []
        self.has_color_edits = False
        self.has_property_edits = False
        self.color_filter_timer = QTimer(self)
        self.color_filter_timer.setSingleShot(True)
        self.color_filter_timer.setInterval(150)
        self.color_filter_timer.timeout.connect(self.populate_colors)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.color_tab = QWidget()
        self.scale_tab = QWidget()
        self.tabs.addTab(self.color_tab, "Colors")
        self.tabs.addTab(self.scale_tab, "Scale")

        self._build_color_tab()
        self._build_scale_tab()

    def make_chip(self, text: str) -> QLabel:
        chip = QLabel(text)
        chip.setObjectName("ChipLabel")
        return chip

    def show_in_front(self):
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.show()
        self.raise_()
        self.activateWindow()
        QTimer.singleShot(900, self.release_front_hint)

    def release_front_hint(self):
        self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        self.show()

    def _build_color_tab(self):
        layout = QVBoxLayout(self.color_tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        toolbar = QFrame()
        toolbar.setObjectName("ToolbarPanel")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(12, 10, 12, 10)
        title_stack = QVBoxLayout()
        title = QLabel("Particle Color Studio")
        title.setObjectName("TitleLabel")
        subtitle = QLabel("Tune color blocks, gradients, emitter active states, and intensity values.")
        subtitle.setObjectName("SubtleLabel")
        title_stack.addWidget(title)
        title_stack.addWidget(subtitle)
        toolbar_layout.addLayout(title_stack, 1)
        buttons = QHBoxLayout()
        open_btn = QPushButton("Open PFX")
        open_btn.setObjectName("PrimaryButton")
        open_btn.clicked.connect(self.open_file)
        save_btn = QPushButton("Save Particle Edits As")
        save_btn.clicked.connect(self.save_color_edits)
        buttons.addWidget(open_btn)
        buttons.addWidget(save_btn)
        toolbar_layout.addLayout(buttons)
        layout.addWidget(toolbar)

        self.file_label = QLabel("No file selected")
        self.file_label.setObjectName("SubtleLabel")

        info_panel = QFrame()
        info_panel.setObjectName("InfoPanel")
        info_layout = QHBoxLayout(info_panel)
        info_layout.setContentsMargins(12, 8, 12, 8)
        info_layout.addWidget(self.file_label, 1)
        self.group_chip = self.make_chip("0 groups")
        self.color_chip = self.make_chip("0 colors")
        self.quick_chip = self.make_chip("0 quick controls")
        info_layout.addWidget(self.group_chip)
        info_layout.addWidget(self.color_chip)
        info_layout.addWidget(self.quick_chip)
        layout.addWidget(info_panel)

        filters = QHBoxLayout()
        self.color_search = QLineEdit()
        self.color_search.setPlaceholderText("Filter by emitter, section, type, color, or line...")
        self.color_search.textChanged.connect(self.schedule_populate_colors)
        self.editable_only = QCheckBox("Editable only")
        self.editable_only.setChecked(True)
        self.editable_only.stateChanged.connect(self.schedule_populate_colors)
        filters.addWidget(self.color_search, 1)
        filters.addWidget(self.editable_only)
        layout.addLayout(filters)

        self.color_scroll = QScrollArea()
        self.color_scroll.setWidgetResizable(True)
        self.color_container = QWidget()
        self.color_layout = QVBoxLayout(self.color_container)
        self.color_layout.addStretch(1)
        self.color_scroll.setWidget(self.color_container)
        layout.addWidget(self.color_scroll, 1)

    def _build_scale_tab(self):
        layout = QVBoxLayout(self.scale_tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        toolbar = QFrame()
        toolbar.setObjectName("ToolbarPanel")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(12, 10, 12, 10)
        title_stack = QVBoxLayout()
        title = QLabel("Scale Utility")
        title.setObjectName("TitleLabel")
        subtitle = QLabel("Scale particle UniformValue entries inside ScaleData blocks only.")
        subtitle.setObjectName("SubtleLabel")
        title_stack.addWidget(title)
        title_stack.addWidget(subtitle)
        toolbar_layout.addLayout(title_stack, 1)
        buttons = QHBoxLayout()
        open_btn = QPushButton("Open PFX")
        open_btn.setObjectName("PrimaryButton")
        open_btn.clicked.connect(self.open_file)
        save_btn = QPushButton("Apply Scale and Save As")
        save_btn.clicked.connect(self.save_scaled_file)
        buttons.addWidget(open_btn)
        buttons.addWidget(save_btn)
        toolbar_layout.addLayout(buttons)
        layout.addWidget(toolbar)

        form = QHBoxLayout()
        form.addWidget(QLabel("Scale multiplier"))
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setDecimals(4)
        self.scale_spin.setRange(-1000000.0, 1000000.0)
        self.scale_spin.setSingleStep(0.1)
        self.scale_spin.setValue(1.0)
        form.addWidget(self.scale_spin)
        form.addStretch(1)
        layout.addLayout(form)

        self.scale_status = QLabel(
            "The scale tool only changes <UniformValue> values while inside <ScaleData> blocks."
        )
        self.scale_status.setWordWrap(True)
        layout.addWidget(self.scale_status)
        layout.addStretch(1)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Halo Wars 2 Particle File",
            "",
            "Particle XML files (*.pfx *.xml);;All files (*.*)",
        )
        if not path:
            return
        self.load_file(path)

    def load_file(self, path: str):
        try:
            text, encoding = read_text_file(path)
        except Exception as exc:
            QMessageBox.critical(self, "Open failed", f"Failed to read file:\n{exc}")
            return

        self.file_path = path
        self.encoding = encoding
        self.original_text = text
        self.color_entries = find_color_entries(text)
        self.property_entries = find_quick_property_entries(text)
        self.has_color_edits = False
        self.has_property_edits = False
        self.file_label.setText(os.path.basename(path))
        self.scale_status.setText(
            "Ready. Scaling will only change <UniformValue> values while inside <ScaleData> blocks."
        )
        self.populate_colors()

    def schedule_populate_colors(self):
        self.color_filter_timer.start()

    def populate_colors(self):
        self.color_container.setUpdatesEnabled(False)
        while self.color_layout.count() > 0:
            item = self.color_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        editable_count = 0
        shown_count = 0
        shown_values = 0
        filter_text = self.color_search.text().strip().lower() if hasattr(self, "color_search") else ""
        editable_only = self.editable_only.isChecked() if hasattr(self, "editable_only") else False
        last_emitter = None

        groups: list[list[ColorEntry]] = []
        group_by_id: dict[int, list[ColorEntry]] = {}
        for entry in self.color_entries:
            group_by_id.setdefault(entry.group_id, []).append(entry)
            editable_count += int(entry.is_editable)
        groups = list(group_by_id.values())

        for group in groups:
            visible_group = [entry for entry in group if not editable_only or entry.is_editable]
            if not visible_group:
                continue

            haystack = " ".join(
                " ".join(
                    [
                        entry.emitter_name,
                        entry.section_name,
                        entry.label,
                        entry.type_text,
                        entry.metadata,
                        str(entry.current_value),
                        str(entry.line_number),
                    ]
                )
                for entry in visible_group
            ).lower()
            if filter_text and filter_text not in haystack:
                continue

            lead = visible_group[0]
            if lead.emitter_name != last_emitter:
                header = QLabel(lead.emitter_name)
                header.setObjectName("EmitterHeader")
                self.color_layout.addWidget(header)
                last_emitter = lead.emitter_name
            self.color_layout.addWidget(ColorGroup(visible_group, self.property_entries, self.mark_particle_edited))
            shown_count += 1
            shown_values += len(visible_group)

        if not self.color_entries:
            self.color_layout.addWidget(QLabel("No editable ColorData or ColourData RGB-int values found."))
        elif shown_count == 0:
            self.color_layout.addWidget(QLabel("No colors match the current filter."))
        else:
            effect = self.color_entries[0].effect_name
            prefix = f"{effect} | " if effect else ""
            summary = QLabel(
                f"{prefix}showing {shown_count}/{len(groups)} color groups and {shown_values}/{len(self.color_entries)} color values; {editable_count} RGB-int values are editable."
            )
            summary.setObjectName("SubtleLabel")
            self.color_layout.insertWidget(0, summary)

        self.color_layout.addStretch(1)
        self.color_container.setUpdatesEnabled(True)
        if hasattr(self, "group_chip"):
            self.group_chip.setText(f"{shown_count}/{len(groups)} groups")
            self.color_chip.setText(f"{shown_values}/{len(self.color_entries)} colors")
            self.quick_chip.setText(f"{len(self.property_entries)} quick controls")

    def mark_color_edited(self):
        self.has_color_edits = True

    def mark_particle_edited(self):
        self.has_color_edits = True
        self.has_property_edits = True

    def save_color_edits(self):
        if not self.original_text:
            QMessageBox.warning(self, "No file", "Open a .pfx file first.")
            return

        modified_text, color_changed, property_changed = apply_particle_edits(
            self.original_text,
            self.color_entries,
            self.property_entries,
        )
        initial = self._default_save_name("_edited")
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Edited Particle File",
            initial,
            "Particle XML files (*.pfx *.xml);;All files (*.*)",
        )
        if not path:
            return

        try:
            write_text_file(path, modified_text, self.encoding)
        except Exception as exc:
            QMessageBox.critical(self, "Save failed", f"Failed to save file:\n{exc}")
            return

        QMessageBox.information(
            self,
            "Saved",
            f"Saved {color_changed} color change(s) and {property_changed} property change(s).\nNo other XML text was rewritten.",
        )

    def save_scaled_file(self):
        if not self.original_text:
            QMessageBox.warning(self, "No file", "Open a .pfx file first.")
            return

        multiplier = float(self.scale_spin.value())
        modified_text, changed = scale_uniform_values_in_text(self.original_text, multiplier)
        initial = self._default_save_name("_scaled")
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Scaled Particle File",
            initial,
            "Particle XML files (*.pfx *.xml);;All files (*.*)",
        )
        if not path:
            return

        try:
            write_text_file(path, modified_text, self.encoding)
        except Exception as exc:
            QMessageBox.critical(self, "Save failed", f"Failed to save file:\n{exc}")
            return

        self.scale_status.setText(
            f"Saved {changed} scaled UniformValue change(s). Only values inside ScaleData blocks were touched."
        )
        QMessageBox.information(
            self,
            "Saved",
            f"Saved {changed} scaled UniformValue change(s).\nOnly <UniformValue> inside <ScaleData> blocks was changed.",
        )

    def _default_save_name(self, suffix: str) -> str:
        if not self.file_path:
            return ""
        folder = os.path.dirname(self.file_path)
        base, ext = os.path.splitext(os.path.basename(self.file_path))
        return os.path.join(folder, f"{base}{suffix}{ext or '.pfx'}")


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    window = ParticleEditor()
    window.show_in_front()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
