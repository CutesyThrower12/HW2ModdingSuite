from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable
from xml.etree import ElementTree as ET

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
)
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QInputDialog,
    QMenu,
)

from triggerscript_help import explain_element, simplified_trigger_name, trigger_purpose
from triggerscript_parser import TriggerBlock, TriggerCommand, TriggerScriptDocument, child_elements, element_label, element_text


PinShapeFactory = Callable[[QRectF], QPolygonF | None]
ValidationRule = Callable[[ET.Element, TriggerScriptDocument], list[str]]
TooltipRule = Callable[[ET.Element], str | None]


@dataclass(frozen=True)
class NodeTheme:
    name: str
    header: str
    body: str
    border: str
    accent: str
    warning: str = "#FFB547"
    danger: str = "#FF6680"


@dataclass(frozen=True)
class NodeTypeDefinition:
    key: str
    label: str
    category: str
    theme: str
    editable_fields: tuple[str, ...] = ("Name", "Active", "CommentOut", "EvaluateFrequency", "Type")
    advanced_fields: tuple[str, ...] = ("ID", "DBID", "SigID", "Version", "TemplateID")


@dataclass
class GraphCustomizationRegistry:
    themes: dict[str, NodeTheme] = field(default_factory=dict)
    node_types: dict[str, NodeTypeDefinition] = field(default_factory=dict)
    categories: dict[str, str] = field(default_factory=dict)
    validation_rules: list[ValidationRule] = field(default_factory=list)
    tooltip_rules: list[TooltipRule] = field(default_factory=list)

    def add_theme(self, theme: NodeTheme) -> None:
        self.themes[theme.name] = theme

    def add_node_type(self, definition: NodeTypeDefinition) -> None:
        self.node_types[definition.key] = definition

    def add_category(self, key: str, label: str) -> None:
        self.categories[key] = label

    def add_validation_rule(self, rule: ValidationRule) -> None:
        self.validation_rules.append(rule)

    def add_tooltip_rule(self, rule: TooltipRule) -> None:
        self.tooltip_rules.append(rule)

    def node_type_for(self, element: ET.Element) -> NodeTypeDefinition:
        tag = _local_name(element.tag)
        if tag in self.node_types:
            return self.node_types[tag]
        return self.node_types["Generic"]

    def theme_for(self, element: ET.Element) -> NodeTheme:
        definition = self.node_type_for(element)
        return self.themes.get(definition.theme, self.themes["Generic"])

    def tooltip_for(self, element: ET.Element) -> str:
        for rule in self.tooltip_rules:
            text = rule(element)
            if text:
                return text
        return explain_element(element).summary

    def validate(self, element: ET.Element, doc: TriggerScriptDocument) -> list[str]:
        warnings: list[str] = []
        for rule in self.validation_rules:
            warnings.extend(rule(element, doc))
        return warnings


def default_graph_registry() -> GraphCustomizationRegistry:
    registry = GraphCustomizationRegistry()
    registry.add_theme(NodeTheme("Trigger", "#183055", "#0F1824", "#3C6EA8", "#75D8FF"))
    registry.add_theme(NodeTheme("Condition", "#1D3145", "#0F1824", "#478BBF", "#75D8FF"))
    registry.add_theme(NodeTheme("Effect", "#26314C", "#101925", "#6C7DD8", "#B2BDFF"))
    registry.add_theme(NodeTheme("Variable", "#173A35", "#0D171B", "#33A78C", "#58F2B0"))
    registry.add_theme(NodeTheme("Custom", "#3A2D18", "#14110C", "#D5A03C", "#FFD166"))
    registry.add_theme(NodeTheme("Generic", "#1A2638", "#0F1824", "#43536C", "#AAB8CA"))
    registry.add_node_type(NodeTypeDefinition("Trigger", "Trigger", "Logic", "Trigger"))
    registry.add_node_type(NodeTypeDefinition("Condition", "Condition", "Checks", "Condition"))
    registry.add_node_type(NodeTypeDefinition("Effect", "Effect", "Actions", "Effect"))
    registry.add_node_type(NodeTypeDefinition("TriggerVar", "Variable", "References", "Variable"))
    registry.add_node_type(NodeTypeDefinition("CustomNote", "Custom Note", "Notes", "Custom", ("Name", "Text"), ()))
    registry.add_node_type(NodeTypeDefinition("Generic", "Node", "Misc", "Generic"))
    registry.add_category("Objectives", "Objective and win/loss logic")
    registry.add_category("Waves", "Spawning, squad, and attack wave logic")
    registry.add_category("AI / Player Logic", "AI, player, resource, and base rules")
    registry.add_category("Cinematics", "Camera, subtitle, dialog, and movie logic")
    registry.add_category("Misc", "Everything else")
    registry.add_validation_rule(_default_validation_rule)
    return registry


class BlueprintWireItem(QGraphicsPathItem):
    def __init__(self, source: "BlueprintPinItem", target: "BlueprintPinItem | None" = None):
        super().__init__()
        self.source = source
        self.target = target
        self.temp_end = source.scenePos()
        self.setZValue(-2)
        self.setPen(QPen(QColor("#75D8FF"), 2.0))
        self.update_path()

    def set_target(self, target: "BlueprintPinItem | None") -> None:
        self.target = target
        self.update_path()

    def set_temp_end(self, point: QPointF) -> None:
        self.temp_end = point
        self.update_path()

    def update_path(self) -> None:
        start = self.source.scene_anchor()
        end = self.target.scene_anchor() if self.target else self.temp_end
        dx = max(80.0, abs(end.x() - start.x()) * 0.5)
        path = QPainterPath(start)
        path.cubicTo(QPointF(start.x() + dx, start.y()), QPointF(end.x() - dx, end.y()), end)
        self.setPath(path)


class BlueprintPinItem(QGraphicsEllipseItem):
    def __init__(
        self,
        node: "BlueprintNodeItem",
        label: str,
        direction: str,
        kind: str,
        value: str = "",
        advanced: bool = False,
    ):
        super().__init__(-6, -6, 12, 12, node)
        self.node = node
        self.label = label
        self.direction = direction
        self.kind = kind
        self.value = value
        self.advanced = advanced
        self.wires: list[BlueprintWireItem] = []
        self.setBrush(QBrush(QColor("#58F2B0" if direction == "out" else "#75D8FF")))
        self.setPen(QPen(QColor("#0B1018"), 1.2))
        self.setAcceptHoverEvents(True)
        self.setToolTip(f"{direction.title()} pin: {label}\n{value or kind}")

    def scene_anchor(self) -> QPointF:
        return self.mapToScene(QPointF(0, 0))

    def add_wire(self, wire: BlueprintWireItem) -> None:
        if wire not in self.wires:
            self.wires.append(wire)

    def remove_wire(self, wire: BlueprintWireItem) -> None:
        if wire in self.wires:
            self.wires.remove(wire)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        if self.kind == "exec":
            painter.setBrush(self.brush())
            painter.setPen(self.pen())
            polygon = QPolygonF([
                QPointF(-7, -7),
                QPointF(4, -7),
                QPointF(8, 0),
                QPointF(4, 7),
                QPointF(-7, 7),
            ])
            painter.drawPolygon(polygon)
            return
        super().paint(painter, option, widget)


class BlueprintNodeItem(QGraphicsItem):
    def __init__(
        self,
        element: ET.Element,
        title: str,
        node_type: str,
        theme: NodeTheme,
        warnings: list[str],
        doc: TriggerScriptDocument | None,
        beginner_mode: bool = False,
        is_runtime: bool = False,
        custom: bool = False,
    ):
        super().__init__()
        self.element = element
        self.title = title
        self.node_type = node_type
        self.theme = theme
        self.warnings = warnings
        self.doc = doc
        self.beginner_mode = beginner_mode
        self.is_runtime = is_runtime
        self.custom = custom
        self.collapsed = False
        self.resizing = False
        self.width = 310.0
        self.height = 230.0
        self.input_pins: list[BlueprintPinItem] = []
        self.output_pins: list[BlueprintPinItem] = []
        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self._build_pins()
        self._layout_pins()
        self.setToolTip(explain_element(element, is_runtime).as_plain_text())

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self.width, self.height if not self.collapsed else 82)

    def resize_rect(self) -> QRectF:
        rect = self.boundingRect()
        return QRectF(rect.right() - 18, rect.bottom() - 18, 18, 18)

    def _build_pins(self) -> None:
        tag = _local_name(self.element.tag)
        self.input_pins.clear()
        self.output_pins.clear()
        if tag == "Trigger":
            self.input_pins.append(BlueprintPinItem(self, "Enable", "in", "exec"))
            self.output_pins.append(BlueprintPinItem(self, "True", "out", "exec"))
            self.output_pins.append(BlueprintPinItem(self, "False", "out", "exec"))
        elif tag in {"Condition", "Effect"}:
            self.input_pins.append(BlueprintPinItem(self, "Exec", "in", "exec"))
            for port in child_elements(self.element):
                port_tag = _local_name(port.tag)
                if port_tag == "Input":
                    self.input_pins.append(BlueprintPinItem(self, port.get("Name", "Input"), "in", "value", element_text(port), _is_advanced_port(port)))
                elif port_tag == "Output":
                    self.output_pins.append(BlueprintPinItem(self, port.get("Name", "Output"), "out", "value", element_text(port), _is_advanced_port(port)))
            self.output_pins.append(BlueprintPinItem(self, "Done", "out", "exec"))
        elif tag == "TriggerVar":
            self.input_pins.append(BlueprintPinItem(self, "Set", "in", "value", self.element.get("Type", "")))
            self.output_pins.append(BlueprintPinItem(self, "Value", "out", "value", element_text(self.element)))
        else:
            self.input_pins.append(BlueprintPinItem(self, "In", "in", "value"))
            self.output_pins.append(BlueprintPinItem(self, "Out", "out", "value"))

    def _layout_pins(self) -> None:
        visible_inputs = [pin for pin in self.input_pins if not (self.beginner_mode and pin.advanced)]
        visible_outputs = [pin for pin in self.output_pins if not (self.beginner_mode and pin.advanced)]
        start_y = 76
        gap = 24
        for index, pin in enumerate(self.input_pins):
            pin.setVisible(pin in visible_inputs)
            pin.setPos(0, start_y + visible_inputs.index(pin) * gap if pin in visible_inputs else start_y)
        for index, pin in enumerate(self.output_pins):
            pin.setVisible(pin in visible_outputs)
            pin.setPos(self.width, start_y + visible_outputs.index(pin) * gap if pin in visible_outputs else start_y)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        rect = self.boundingRect()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(self.theme.border if not self.isSelected() else "#FFFFFF"), 2))
        painter.setBrush(QBrush(QColor(self.theme.body)))
        painter.drawRoundedRect(rect, 9, 9)
        header = QRectF(0, 0, rect.width(), 46)
        painter.setBrush(QBrush(QColor(self.theme.header)))
        painter.drawRoundedRect(header, 9, 9)
        painter.fillRect(QRectF(0, 33, rect.width(), 13), QColor(self.theme.header))
        painter.setPen(QColor("#EEF4FF"))
        title_font = QFont("Segoe UI", 10, QFont.Bold)
        painter.setFont(title_font)
        painter.drawText(QRectF(14, 7, rect.width() - 28, 20), Qt.AlignLeft | Qt.AlignVCenter, self.title[:48])
        painter.setPen(QColor(self.theme.accent))
        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
        painter.drawText(QRectF(14, 26, rect.width() - 28, 16), Qt.AlignLeft | Qt.AlignVCenter, self.node_type.upper())

        if self.collapsed:
            painter.setPen(QColor("#AAB8CA"))
            painter.drawText(QRectF(14, 54, rect.width() - 28, 18), Qt.AlignLeft, "Collapsed details")
            return

        painter.setPen(QColor("#D7E6FA"))
        painter.setFont(QFont("Segoe UI", 8))
        help_text = explain_element(self.element, self.is_runtime)
        body_lines = _node_body_lines(self.element, self.beginner_mode)
        body_lines.insert(0, help_text.summary)
        y = 58
        for line in body_lines[:6]:
            painter.drawText(QRectF(16, y, rect.width() - 32, 18), Qt.AlignLeft | Qt.AlignVCenter, _clip(line, 54))
            y += 19

        for pin in self.input_pins:
            if pin.isVisible():
                painter.setPen(QColor("#AAB8CA"))
                painter.drawText(QRectF(14, pin.pos().y() - 9, 125, 18), Qt.AlignLeft | Qt.AlignVCenter, _clip(pin.label, 18))
        for pin in self.output_pins:
            if pin.isVisible():
                painter.setPen(QColor("#AAB8CA"))
                painter.drawText(QRectF(rect.width() - 139, pin.pos().y() - 9, 125, 18), Qt.AlignRight | Qt.AlignVCenter, _clip(pin.label, 18))

        footer = QRectF(0, rect.height() - 46, rect.width(), 46)
        painter.setBrush(QBrush(QColor("#091019")))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(footer, 0, 0)
        painter.setPen(QColor(self.theme.warning if self.warnings else "#58F29A"))
        safe_label = "Runtime read-only" if self.is_runtime else "Editable source"
        warning_label = f"{len(self.warnings)} warning(s)" if self.warnings else "No graph warnings"
        painter.drawText(QRectF(14, rect.height() - 39, rect.width() - 28, 16), Qt.AlignLeft, safe_label)
        painter.drawText(QRectF(14, rect.height() - 21, rect.width() - 28, 16), Qt.AlignLeft, warning_label)
        if self.warnings:
            painter.setBrush(QBrush(QColor(self.theme.warning)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QRectF(rect.width() - 28, rect.height() - 31, 14, 14))
        painter.setBrush(QBrush(QColor("#43536C")))
        painter.drawRect(self.resize_rect())

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton and self.resize_rect().contains(event.pos()):
            self.resizing = True
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self.resizing:
            self.prepareGeometryChange()
            self.width = max(240.0, event.pos().x())
            self.height = max(150.0, event.pos().y())
            self._layout_pins()
            self.update_wires()
            self.update()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self.resizing = False
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        self.collapsed = not self.collapsed
        self.prepareGeometryChange()
        self.update()
        self.update_wires()
        event.accept()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            scene = self.scene()
            if isinstance(scene, BlueprintGraphScene) and scene.snap_to_grid:
                grid = scene.grid_size
                return QPointF(round(value.x() / grid) * grid, round(value.y() / grid) * grid)
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.update_wires()
        return super().itemChange(change, value)

    def update_wires(self) -> None:
        for pin in self.input_pins + self.output_pins:
            for wire in pin.wires:
                wire.update_path()


class BlueprintGraphScene(QGraphicsScene):
    def __init__(self, registry: GraphCustomizationRegistry | None = None, on_select: Callable[[ET.Element | None], None] | None = None):
        super().__init__()
        self.registry = registry or default_graph_registry()
        self.on_select = on_select
        self.snap_to_grid = True
        self.grid_size = 24
        self.node_items: list[BlueprintNodeItem] = []
        self.wire_items: list[BlueprintWireItem] = []
        self.drag_wire: BlueprintWireItem | None = None
        self.drag_pin: BlueprintPinItem | None = None
        self.current_doc: TriggerScriptDocument | None = None
        self.beginner_mode = False
        self.setSceneRect(-4000, -4000, 8000, 8000)
        self.selectionChanged.connect(self._selection_changed)

    def build_from_document(self, doc: TriggerScriptDocument | None, beginner_mode: bool = False) -> str:
        self.clear()
        self.node_items.clear()
        self.wire_items.clear()
        self.current_doc = doc
        self.beginner_mode = beginner_mode
        if doc is None:
            return "No graph loaded."
        if beginner_mode and doc.is_runtime:
            return "Beginner Mode hides runtime graphs. Load the editable .triggerscript source."

        variable_lookup = {variable.id: variable for variable in doc.variables if variable.id}
        max_triggers = 16 if beginner_mode else 28
        x_by_group = {
            "Objectives": 0,
            "Waves": 420,
            "AI / Player Logic": 840,
            "Cinematics": 1260,
            "Misc": 1680,
        }
        group_y: dict[str, float] = {key: 0.0 for key in x_by_group}
        created_by_element: dict[int, BlueprintNodeItem] = {}

        for trigger in doc.triggers[:max_triggers]:
            group = trigger_purpose(trigger.element)
            node = self._add_trigger_node(trigger, x_by_group.get(group, 1680), group_y.get(group, 0.0), doc)
            created_by_element[id(trigger.element)] = node
            group_y[group] = group_y.get(group, 0.0) + node.height + 110

            command_limit = 4 if beginner_mode else 8
            for index, command in enumerate(trigger.commands[:command_limit]):
                cx = node.pos().x() + 380 + (index % 2) * 360
                cy = node.pos().y() + (index // 2) * 260
                command_node = self._add_command_node(command, cx, cy, doc)
                created_by_element[id(command.element)] = command_node
                self._connect_nearest(node, command_node, "True" if command.branch != "TriggerEffectsOnFalse" else "False")
                if not beginner_mode:
                    for port in child_elements(command.element):
                        value = element_text(port)
                        ref = value[1:] if value.startswith("#") else value
                        variable = variable_lookup.get(ref)
                        if variable:
                            vx = command_node.pos().x() - 350
                            vy = command_node.pos().y() + 120
                            var_node = created_by_element.get(id(variable.element))
                            if var_node is None:
                                var_node = self._add_variable_node(variable.element, vx, vy, doc)
                                created_by_element[id(variable.element)] = var_node
                            self._connect_nearest(var_node, command_node, variable.name or variable.id)
                            break

        self.auto_align()
        warning_count = sum(len(node.warnings) for node in self.node_items)
        shown = min(len(doc.triggers), max_triggers)
        return f"Blueprint graph: {shown}/{len(doc.triggers)} triggers shown, {len(self.node_items)} nodes, {len(self.wire_items)} wires, {warning_count} warning(s)."

    def _add_trigger_node(self, trigger: TriggerBlock, x: float, y: float, doc: TriggerScriptDocument) -> BlueprintNodeItem:
        title = simplified_trigger_name(trigger.element) if self.beginner_mode else (trigger.name or trigger.id or "Trigger")
        return self.add_blueprint_node(trigger.element, title, "Trigger", QPointF(x, y), doc)

    def _add_command_node(self, command: TriggerCommand, x: float, y: float, doc: TriggerScriptDocument) -> BlueprintNodeItem:
        title = _friendly_command_title(command.element, self.beginner_mode)
        return self.add_blueprint_node(command.element, title, command.kind, QPointF(x, y), doc)

    def _add_variable_node(self, element: ET.Element, x: float, y: float, doc: TriggerScriptDocument) -> BlueprintNodeItem:
        return self.add_blueprint_node(element, element.get("Name") or element.get("ID") or "Variable", "Variable", QPointF(x, y), doc)

    def add_blueprint_node(
        self,
        element: ET.Element,
        title: str,
        node_type: str,
        pos: QPointF,
        doc: TriggerScriptDocument | None = None,
        custom: bool = False,
    ) -> BlueprintNodeItem:
        current_doc = doc or self.current_doc
        theme = self.registry.theme_for(element)
        warnings = self.registry.validate(element, current_doc) if current_doc else []
        node = BlueprintNodeItem(
            element,
            title,
            node_type,
            theme,
            warnings,
            current_doc,
            self.beginner_mode,
            bool(current_doc and current_doc.is_runtime),
            custom,
        )
        node.setPos(pos)
        self.addItem(node)
        self.node_items.append(node)
        return node

    def _connect_nearest(self, source: BlueprintNodeItem, target: BlueprintNodeItem, label: str = "") -> None:
        source_pin = next((pin for pin in source.output_pins if pin.isVisible()), source.output_pins[0] if source.output_pins else None)
        target_pin = next((pin for pin in target.input_pins if pin.isVisible()), target.input_pins[0] if target.input_pins else None)
        if source_pin is None or target_pin is None:
            return
        wire = BlueprintWireItem(source_pin, target_pin)
        source_pin.add_wire(wire)
        target_pin.add_wire(wire)
        wire.setToolTip(label or f"{source.title} -> {target.title}")
        self.addItem(wire)
        self.wire_items.append(wire)

    def mousePressEvent(self, event) -> None:
        item = self.itemAt(event.scenePos(), self.views()[0].transform() if self.views() else None)
        if event.button() == Qt.LeftButton and isinstance(item, BlueprintPinItem) and item.direction == "out":
            self.drag_pin = item
            self.drag_wire = BlueprintWireItem(item)
            item.add_wire(self.drag_wire)
            self.addItem(self.drag_wire)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self.drag_wire:
            self.drag_wire.set_temp_end(event.scenePos())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self.drag_wire and self.drag_pin:
            item = self.itemAt(event.scenePos(), self.views()[0].transform() if self.views() else None)
            if isinstance(item, BlueprintPinItem) and item.direction == "in" and item.node is not self.drag_pin.node:
                self.drag_wire.set_target(item)
                item.add_wire(self.drag_wire)
                self.wire_items.append(self.drag_wire)
            else:
                self.removeItem(self.drag_wire)
                self.drag_pin.remove_wire(self.drag_wire)
            self.drag_wire = None
            self.drag_pin = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event) -> None:
        menu = QMenu()
        add_note = QAction("Add Node / Comment", menu)
        align = QAction("Auto-align Nodes", menu)
        menu.addAction(add_note)
        menu.addAction(align)
        action = menu.exec(event.screenPos())
        if action == add_note:
            name, ok = QInputDialog.getText(None, "Add Blueprint Node", "Node name:")
            if ok and name.strip():
                element = ET.Element("CustomNote", {"Name": name.strip()})
                element.text = "Editor-only note. Not saved to the triggerscript yet."
                self.add_blueprint_node(element, name.strip(), "Custom Note", event.scenePos(), self.current_doc, custom=True)
        elif action == align:
            self.auto_align()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Delete:
            for item in list(self.selectedItems()):
                if isinstance(item, BlueprintNodeItem):
                    self.delete_node(item)
            event.accept()
            return
        if event.key() == Qt.Key_D and event.modifiers() & Qt.ControlModifier:
            for item in list(self.selectedItems()):
                if isinstance(item, BlueprintNodeItem):
                    self.duplicate_node(item)
            event.accept()
            return
        super().keyPressEvent(event)

    def delete_node(self, node: BlueprintNodeItem) -> None:
        for pin in node.input_pins + node.output_pins:
            for wire in list(pin.wires):
                if wire.source:
                    wire.source.remove_wire(wire)
                if wire.target:
                    wire.target.remove_wire(wire)
                if wire in self.wire_items:
                    self.wire_items.remove(wire)
                self.removeItem(wire)
        if node in self.node_items:
            self.node_items.remove(node)
        self.removeItem(node)

    def duplicate_node(self, node: BlueprintNodeItem) -> BlueprintNodeItem:
        clone_element = ET.Element(_local_name(node.element.tag), dict(node.element.attrib))
        clone_element.text = element_text(node.element)
        clone = self.add_blueprint_node(clone_element, f"{node.title} Copy", node.node_type, node.pos() + QPointF(36, 36), self.current_doc, True)
        return clone

    def auto_align(self) -> None:
        columns: dict[int, list[BlueprintNodeItem]] = {}
        for node in self.node_items:
            column = round(node.pos().x() / 380)
            columns.setdefault(column, []).append(node)
        for column, nodes in columns.items():
            for row, node in enumerate(sorted(nodes, key=lambda item: item.pos().y())):
                node.setPos(column * 380, row * 260)
                node.update_wires()

    def _selection_changed(self) -> None:
        if not self.on_select:
            return
        selected = self.selectedItems()
        for item in selected:
            if isinstance(item, BlueprintNodeItem):
                self.on_select(item.element)
                return
        self.on_select(None)


class BlueprintGraphView(QGraphicsView):
    def __init__(self, scene: BlueprintGraphScene):
        super().__init__(scene)
        self.grid_color = QColor("#172234")
        self.grid_major_color = QColor("#273449")
        self._right_panning = False
        self._last_pan_pos = None
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        painter.fillRect(rect, QColor("#080D14"))
        scene = self.scene()
        grid_size = scene.grid_size if isinstance(scene, BlueprintGraphScene) else 24
        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top = int(rect.top()) - (int(rect.top()) % grid_size)
        minor_pen = QPen(self.grid_color, 1)
        major_pen = QPen(self.grid_major_color, 1.4)
        x = left
        while x < rect.right():
            painter.setPen(major_pen if x % (grid_size * 5) == 0 else minor_pen)
            painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
            x += grid_size
        y = top
        while y < rect.bottom():
            painter.setPen(major_pen if y % (grid_size * 5) == 0 else minor_pen)
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
            y += grid_size

    def wheelEvent(self, event) -> None:
        delta = event.angleDelta().y() or event.pixelDelta().y()
        if not delta:
            event.ignore()
            return
        factor = 1.15 ** (delta / 120.0)
        current = self.transform().m11()
        target = max(0.18, min(3.0, current * factor))
        self.scale(target / current, target / current)
        event.accept()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.RightButton:
            self._right_panning = True
            self._last_pan_pos = event.position().toPoint()
            self.setDragMode(QGraphicsView.NoDrag)
            self.viewport().setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._right_panning and self._last_pan_pos is not None:
            pos = event.position().toPoint()
            delta = pos - self._last_pan_pos
            self._last_pan_pos = pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.RightButton and self._right_panning:
            self._right_panning = False
            self._last_pan_pos = None
            self.setDragMode(QGraphicsView.RubberBandDrag)
            self.viewport().unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def frame_all(self) -> None:
        items = self.scene().items()
        if not items:
            return
        rect = self.scene().itemsBoundingRect().adjusted(-80, -80, 80, 80)
        self.fitInView(rect, Qt.KeepAspectRatio)


def _default_validation_rule(element: ET.Element, doc: TriggerScriptDocument) -> list[str]:
    warnings: list[str] = []
    tag = _local_name(element.tag)
    variable_ids = {variable.id for variable in doc.variables if variable.id}
    if tag in {"Condition", "Effect"}:
        inputs = [port for port in child_elements(element) if _local_name(port.tag) == "Input"]
        if not inputs:
            warnings.append("This command has no visible inputs.")
        for port in inputs:
            value = element_text(port)
            if value.startswith("#") and value[1:] not in variable_ids:
                warnings.append(f"Broken variable reference: {value}")
        if element.get("CommentOut") == "true":
            warnings.append("This command is commented out.")
    if tag == "Trigger":
        if element.find("TriggerEffectsOnTrue") is None:
            warnings.append("Missing true branch.")
        if element.get("Active") == "false":
            warnings.append("Trigger is disabled.")
        for effect in element.findall(".//Effect"):
            effect_type = (effect.get("Type") or "").lower()
            if any(word in effect_type for word in ("activate", "launchscript")):
                for port in child_elements(effect):
                    value = element_text(port)
                    if value.startswith("#") and value[1:] == element.get("ID", ""):
                        warnings.append("Possible self-loop / infinite trigger activation.")
    if tag == "TriggerVar" and not element.get("ID"):
        warnings.append("Variable is missing an ID.")
    if doc.is_runtime:
        warnings.append("Runtime node is read-only and may differ from source.")
    return warnings[:5]


def _friendly_command_title(element: ET.Element, beginner_mode: bool) -> str:
    tag = _local_name(element.tag)
    command_type = element.get("Type") or tag
    if beginner_mode and tag == "Condition":
        return f"Check: {command_type}"
    if beginner_mode and tag == "Effect":
        return f"Do: {command_type}"
    return command_type


def _node_body_lines(element: ET.Element, beginner_mode: bool) -> list[str]:
    tag = _local_name(element.tag)
    if tag == "Trigger":
        fields = ("Active", "ConditionalTrigger", "EvaluateFrequency", "CommentOut")
    elif tag in {"Condition", "Effect"}:
        fields = ("Type", "Invert", "CommentOut") if beginner_mode else ("Type", "DBID", "Version", "Invert", "CommentOut")
    elif tag == "TriggerVar":
        fields = ("Type", "IsNull")
    else:
        fields = ("Name", "Type", "ID")
    lines = [f"{field}: {element.get(field)}" for field in fields if element.get(field) is not None]
    text = element_text(element)
    if text:
        lines.append(f"Value: {text}")
    return lines


def _is_advanced_port(element: ET.Element) -> bool:
    name = (element.get("Name") or "").lower()
    return any(part in name for part in ("dbid", "sigid", "template", "version"))


def _clip(text: str, length: int) -> str:
    return text if len(text) <= length else text[: max(0, length - 1)] + "..."


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag
