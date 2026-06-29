from __future__ import annotations

import os
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QUndoCommand, QUndoStack
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from triggerscript_graph import BlueprintGraphScene, BlueprintGraphView, default_graph_registry
from triggerscript_help import (
    explain_element,
    modding_tips,
    simplified_trigger_name,
    tooltip_for_element,
    trigger_purpose,
)
from triggerscript_parser import (
    MAPPING_TAGS,
    PORT_TAGS,
    TriggerScriptDocument,
    child_elements,
    compare_documents,
    element_label,
    element_text,
    parse_triggerscript,
)


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
QLabel { background: transparent; }
QLabel#Title { font-size: 24px; font-weight: 800; }
QLabel#Kicker { color: #75D8FF; font-weight: 800; }
QLabel#Muted { color: #AAB8CA; }
QLineEdit, QTextEdit, QTreeWidget, QTableWidget {
    background: #080D14;
    border: 1px solid #2C394C;
    border-radius: 6px;
    color: #F5F8FF;
    selection-background-color: #2F80ED;
}
QTextEdit#HelpText {
    background: transparent;
    border: none;
    color: #D7E6FA;
}
QFrame#TipPanel, QFrame#HelpPanel {
    background: #0D1420;
    border: 1px solid #273449;
    border-radius: 8px;
}
QLineEdit { padding: 7px 9px; }
QTreeWidget::item { padding: 5px; border-radius: 4px; }
QTreeWidget::item:selected { background: #1B3559; }
QHeaderView::section {
    background: #111A27;
    color: #AAB8CA;
    border: none;
    padding: 6px;
}
QPushButton {
    background: #1C2635;
    border: 1px solid #34445A;
    border-radius: 6px;
    color: #EEF4FF;
    padding: 8px 13px;
    font-weight: 700;
}
QPushButton:hover { background: #243249; border-color: #4E6480; }
QPushButton#PrimaryButton { background: #2F80ED; border-color: #5EA3FF; }
QPushButton#DangerButton { background: #49202A; border-color: #8B4050; }
QPushButton:checked { background: #245B8F; border-color: #75D8FF; }
QTabWidget::pane { border: 1px solid #273449; border-radius: 8px; top: -1px; }
QTabBar::tab {
    background: #111A27;
    border: 1px solid #273449;
    border-bottom: none;
    padding: 8px 16px;
    margin-right: 4px;
    border-top-left-radius: 7px;
    border-top-right-radius: 7px;
}
QTabBar::tab:selected { background: #1A2638; color: white; }
QSplitter::handle { background: #172234; }
"""


class ElementEditCommand(QUndoCommand):
    def __init__(self, element: ET.Element, field: str, old: str, new: str, callback):
        super().__init__(f"Edit {field}")
        self.element = element
        self.field = field
        self.old = old
        self.new = new
        self.callback = callback

    def redo(self):
        self._set(self.new)

    def undo(self):
        self._set(self.old)

    def _set(self, value: str):
        if self.field == "__text__":
            self.element.text = value
        else:
            self.element.set(self.field, value)
        self.callback()


class TriggerScriptEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Halo Wars 2 Triggerscript Editor")
        self.resize(1420, 860)
        self.setStyleSheet(APP_STYLESHEET)
        self.undo_stack = QUndoStack(self)
        self.document: TriggerScriptDocument | None = None
        self.runtime_document: TriggerScriptDocument | None = None
        self.current_element: ET.Element | None = None
        self._loading_inspector = False
        self.beginner_mode = False
        self._build_ui()

    def _build_ui(self):
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        header = QFrame()
        header.setObjectName("Header")
        header_layout = QHBoxLayout(header)
        title_col = QVBoxLayout()
        kicker = QLabel("TRIGGER WORKSTATION")
        kicker.setObjectName("Kicker")
        title = QLabel("Halo Wars 2 Triggerscript Editor")
        title.setObjectName("Title")
        subtitle = QLabel("Inspect trigger graphs, edit variables and commands, and compare runtime output safely.")
        subtitle.setObjectName("Muted")
        title_col.addWidget(kicker)
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_layout.addLayout(title_col, 1)
        self.open_btn = QPushButton("Open Script")
        self.open_runtime_btn = QPushButton("Open Runtime")
        self.save_btn = QPushButton("Save As")
        self.save_btn.setObjectName("PrimaryButton")
        self.beginner_btn = QPushButton("Beginner Mode")
        self.beginner_btn.setCheckable(True)
        self.undo_btn = QPushButton("Undo")
        self.redo_btn = QPushButton("Redo")
        self.open_btn.setToolTip("Open an editable .triggerscript source graph.")
        self.open_runtime_btn.setToolTip("Open a .triggerscript_runtime file as a read-only comparison/reference.")
        self.save_btn.setToolTip("Save the editable source script while preserving unknown XML structure.")
        self.beginner_btn.setToolTip("Simplify the tree, hide runtime/advanced views, and keep explanations open.")
        self.undo_btn.setToolTip("Undo the last in-memory inspector edit.")
        self.redo_btn.setToolTip("Redo the last undone inspector edit.")
        for button in (self.open_btn, self.open_runtime_btn, self.save_btn, self.beginner_btn, self.undo_btn, self.redo_btn):
            header_layout.addWidget(button)
        self.docs_btn = QPushButton("Hide Tips")
        self.help_btn = QPushButton("Hide Help")
        self.docs_btn.setToolTip("Show or hide the built-in triggerscript modding guide.")
        self.help_btn.setToolTip("Show or hide contextual explanations for the current selection.")
        header_layout.addWidget(self.docs_btn)
        header_layout.addWidget(self.help_btn)
        layout.addWidget(header)

        self.meta_label = QLabel("No triggerscript loaded.")
        self.meta_label.setObjectName("Muted")
        layout.addWidget(self.meta_label)

        self.tabs = QTabWidget()
        self.structure_tab = QWidget()
        self.compare_tab = QWidget()
        self.graph_tab = QWidget()
        self.xml_tab = QWidget()
        self.tabs.addTab(self.structure_tab, "Structure")
        self.tabs.addTab(self.graph_tab, "Graph")
        self.tabs.addTab(self.compare_tab, "Compare")
        self.tabs.addTab(self.xml_tab, "XML Preview")
        layout.addWidget(self.tabs, 1)

        self._build_structure_tab()
        self._build_graph_tab()
        self._build_compare_tab()
        self._build_xml_tab()
        self.setCentralWidget(root)

        self.open_btn.clicked.connect(self.open_script)
        self.open_runtime_btn.clicked.connect(self.open_runtime)
        self.save_btn.clicked.connect(self.save_as)
        self.undo_btn.clicked.connect(self.undo_stack.undo)
        self.redo_btn.clicked.connect(self.undo_stack.redo)
        self.beginner_btn.toggled.connect(self.set_beginner_mode)
        self.docs_btn.clicked.connect(self.toggle_docs_panel)
        self.help_btn.clicked.connect(self.toggle_help_panel)
        self.search_field.textChanged.connect(self.apply_filter)
        self.tree.currentItemChanged.connect(self.on_tree_selection)
        self.attr_table.itemChanged.connect(self.on_attr_item_changed)
        self.text_edit.textChanged.connect(self.on_text_changed)
        self.undo_stack.canUndoChanged.connect(self.undo_btn.setEnabled)
        self.undo_stack.canRedoChanged.connect(self.redo_btn.setEnabled)
        self.undo_btn.setEnabled(False)
        self.redo_btn.setEnabled(False)

    def _build_structure_tab(self):
        layout = QVBoxLayout(self.structure_tab)
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search trigger names, command types, variables, IDs, or parameter values...")
        self.search_field.setToolTip("Filter the tree by trigger name, command type, variable name, ID, or parameter value.")
        layout.addWidget(self.search_field)
        splitter = QSplitter(Qt.Horizontal)
        self.docs_panel = QFrame()
        self.docs_panel.setObjectName("TipPanel")
        docs_layout = QVBoxLayout(self.docs_panel)
        docs_title = QLabel("Modding Tips")
        docs_title.setObjectName("Kicker")
        docs_title.setToolTip("Built-in beginner documentation for reading and editing trigger scripts.")
        self.docs_text = QTextEdit()
        self.docs_text.setObjectName("HelpText")
        self.docs_text.setReadOnly(True)
        self.docs_text.setPlainText(modding_tips())
        docs_layout.addWidget(docs_title)
        docs_layout.addWidget(self.docs_text, 1)
        splitter.addWidget(self.docs_panel)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Script Structure"])
        self.tree.header().setStretchLastSection(True)
        splitter.addWidget(self.tree)

        inspector = QFrame()
        inspector.setObjectName("Panel")
        inspector_layout = QVBoxLayout(inspector)
        self.inspector_title = QLabel("Inspector")
        self.inspector_title.setObjectName("Title")
        self.inspector_hint = QLabel("Select a trigger, command, variable, mapping, input, or output.")
        self.inspector_hint.setObjectName("Muted")
        inspector_header = QHBoxLayout()
        inspector_header.addWidget(self.inspector_title, 1)
        self.what_btn = QPushButton("What Is This?")
        self.what_btn.setToolTip("Open a deeper explanation for the selected trigger, command, variable, or mapping.")
        inspector_header.addWidget(self.what_btn)
        inspector_layout.addLayout(inspector_header)
        inspector_layout.addWidget(self.inspector_hint)
        self.attr_table = QTableWidget(0, 2)
        self.attr_table.setHorizontalHeaderLabels(["Field", "Value"])
        self.attr_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.attr_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        inspector_layout.addWidget(self.attr_table, 1)
        form = QFormLayout()
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Element text / value")
        self.text_edit.setMaximumHeight(120)
        form.addRow("Text", self.text_edit)
        inspector_layout.addLayout(form)
        self.ports_table = QTableWidget(0, 4)
        self.ports_table.setHorizontalHeaderLabels(["Kind", "Name", "Type/SigID", "Value"])
        self.ports_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        inspector_layout.addWidget(QLabel("Inputs / Outputs / Mappings"))
        inspector_layout.addWidget(self.ports_table, 1)
        splitter.addWidget(inspector)

        self.help_panel = QFrame()
        self.help_panel.setObjectName("HelpPanel")
        help_layout = QVBoxLayout(self.help_panel)
        help_title = QLabel("Contextual Help")
        help_title.setObjectName("Kicker")
        help_title.setToolTip("Plain-English explanation for the selected item.")
        self.help_text = QTextEdit()
        self.help_text.setObjectName("HelpText")
        self.help_text.setReadOnly(True)
        self.help_text.setPlainText(explain_element(None).as_plain_text())
        help_layout.addWidget(help_title)
        help_layout.addWidget(self.help_text, 1)
        splitter.addWidget(self.help_panel)
        splitter.setSizes([280, 520, 760, 340])
        layout.addWidget(splitter, 1)
        self.what_btn.clicked.connect(self.show_what_is_this)

    def _build_graph_tab(self):
        layout = QVBoxLayout(self.graph_tab)
        toolbar = QHBoxLayout()
        hint = QLabel("Blueprint Graph: drag nodes, wire output pins to input pins, double-click nodes to collapse, DEL deletes, CTRL+D duplicates.")
        hint.setObjectName("Muted")
        toolbar.addWidget(hint, 1)
        self.graph_snap_btn = QPushButton("Snap")
        self.graph_snap_btn.setCheckable(True)
        self.graph_snap_btn.setChecked(True)
        self.graph_snap_btn.setToolTip("Snap moved and resized graph nodes to the current grid.")
        self.graph_grid_btn = QPushButton("Compact Grid")
        self.graph_grid_btn.setCheckable(True)
        self.graph_grid_btn.setToolTip("Switch between roomy and compact graph grid spacing.")
        self.graph_align_btn = QPushButton("Auto Align")
        self.graph_align_btn.setToolTip("Arrange nodes into readable columns.")
        self.graph_frame_btn = QPushButton("Frame All")
        self.graph_frame_btn.setToolTip("Zoom the graph view to show all current nodes.")
        for button in (self.graph_snap_btn, self.graph_grid_btn, self.graph_align_btn, self.graph_frame_btn):
            toolbar.addWidget(button)
        layout.addLayout(toolbar)
        self.graph_registry = default_graph_registry()
        self.graph_scene = BlueprintGraphScene(self.graph_registry, self.inspect_element)
        self.graph_view = BlueprintGraphView(self.graph_scene)
        layout.addWidget(self.graph_view, 1)
        self.graph_status = QLabel("Open a triggerscript to build the Blueprint graph.")
        self.graph_status.setObjectName("Muted")
        layout.addWidget(self.graph_status)
        self.graph_preview = QTextEdit()
        self.graph_preview.setObjectName("HelpText")
        self.graph_preview.setReadOnly(True)
        self.graph_preview.setMaximumHeight(116)
        self.graph_preview.setPlainText(
            "Live preview will summarize selected node effects, variable references, runtime expansion notes, and validation warnings."
        )
        layout.addWidget(self.graph_preview)
        self.graph_snap_btn.toggled.connect(self.set_graph_snap)
        self.graph_grid_btn.toggled.connect(self.set_graph_grid_density)
        self.graph_align_btn.clicked.connect(self.auto_align_graph)
        self.graph_frame_btn.clicked.connect(self.graph_view.frame_all)

    def _build_compare_tab(self):
        layout = QVBoxLayout(self.compare_tab)
        self.compare_hint = QLabel("Load both a .triggerscript and .triggerscript_runtime file to compare structure.")
        self.compare_hint.setObjectName("Muted")
        layout.addWidget(self.compare_hint)
        self.compare_table = QTableWidget(0, 3)
        self.compare_table.setHorizontalHeaderLabels(["Area", "Item", "Difference"])
        self.compare_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.compare_table, 1)

    def _build_xml_tab(self):
        layout = QVBoxLayout(self.xml_tab)
        self.xml_preview = QTextEdit()
        self.xml_preview.setReadOnly(True)
        self.xml_preview.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(self.xml_preview)

    def open_script(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Halo Wars 2 Trigger Script",
            "",
            "Trigger scripts (*.triggerscript *.triggerscript_runtime *.xml);;All files (*.*)",
        )
        if path:
            self.load_document(Path(path), runtime=False)

    def open_runtime(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Runtime Trigger Script",
            "",
            "Runtime trigger scripts (*.triggerscript_runtime *.triggerscript *.xml);;All files (*.*)",
        )
        if path:
            self.load_document(Path(path), runtime=True)

    def load_document(self, path: Path, runtime: bool):
        try:
            doc = parse_triggerscript(path)
        except Exception as exc:
            QMessageBox.critical(self, "Parse Failed", str(exc))
            return
        if runtime or doc.is_runtime:
            self.runtime_document = doc
        else:
            self.document = doc
            self.undo_stack.clear()
        if self.document is None and self.runtime_document is not None:
            self.document = self.runtime_document
        self.populate()

    def populate(self):
        doc = self.document
        if doc is None:
            return
        if self.beginner_mode and doc.is_runtime:
            self.meta_label.setText("Beginner Mode hides runtime files. Open the editable .triggerscript source file.")
            return
        self.current_element = None
        self.meta_label.setText("   ".join(f"{key}: {value}" for key, value in doc.metadata.items() if key in {"Type", "Size", "Variables", "Triggers", "Commands", "Template Mappings", "Mode"}))
        self.populate_tree(doc)
        self.update_xml_preview()
        self.update_compare()
        self.update_graph()
        self.update_mode_visibility()

    def populate_tree(self, doc: TriggerScriptDocument):
        self.tree.clear()
        root_item = QTreeWidgetItem([Path(doc.path).name])
        root_item.setData(0, Qt.UserRole, doc.script_root)
        self.tree.addTopLevelItem(root_item)

        if not self.beginner_mode:
            self._add_metadata_node(root_item, doc)
        vars_item = QTreeWidgetItem(["Variables"])
        root_item.addChild(vars_item)
        for var in doc.variables:
            item = QTreeWidgetItem([var.display_name])
            item.setData(0, Qt.UserRole, var.element)
            item.setToolTip(0, tooltip_for_element(var.element, doc.is_runtime))
            vars_item.addChild(item)

        trigger_parents: dict[str, QTreeWidgetItem] = {}
        triggers_item = QTreeWidgetItem(["Triggers"])
        root_item.addChild(triggers_item)
        if self.beginner_mode:
            for group_name in ("Objectives", "Waves", "AI / Player Logic", "Cinematics", "Misc"):
                group_item = QTreeWidgetItem([group_name])
                group_item.setToolTip(0, f"Beginner grouping for {group_name.lower()} related trigger logic.")
                triggers_item.addChild(group_item)
                trigger_parents[group_name] = group_item
        for trigger in doc.triggers:
            trigger_item = QTreeWidgetItem([simplified_trigger_name(trigger.element) if self.beginner_mode else trigger.display_name])
            trigger_item.setData(0, Qt.UserRole, trigger.element)
            trigger_item.setToolTip(0, tooltip_for_element(trigger.element, doc.is_runtime))
            parent = trigger_parents.get(trigger_purpose(trigger.element), triggers_item)
            parent.addChild(trigger_item)
            branches: dict[str, QTreeWidgetItem] = {}
            for command in trigger.commands:
                branch_item = branches.get(command.branch)
                if branch_item is None:
                    branch_item = QTreeWidgetItem([self._friendly_branch_name(command.branch) if self.beginner_mode else command.branch])
                    branch_item.setToolTip(0, self._branch_tooltip(command.branch))
                    branches[command.branch] = branch_item
                    trigger_item.addChild(branch_item)
                command_item = QTreeWidgetItem([self._friendly_command_name(command.element) if self.beginner_mode else command.display_name])
                command_item.setData(0, Qt.UserRole, command.element)
                command_item.setToolTip(0, tooltip_for_element(command.element, doc.is_runtime))
                branch_item.addChild(command_item)
                if not self.beginner_mode:
                    for port in command.ports:
                        port_item = QTreeWidgetItem([element_label(port)])
                        port_item.setData(0, Qt.UserRole, port)
                        port_item.setToolTip(0, tooltip_for_element(port, doc.is_runtime))
                        command_item.addChild(port_item)

        if not self.beginner_mode:
            mappings_item = QTreeWidgetItem(["Template Mappings"])
            root_item.addChild(mappings_item)
            for mapping in doc.mappings:
                item = QTreeWidgetItem([mapping.display_name])
                item.setData(0, Qt.UserRole, mapping.element)
                item.setToolTip(0, tooltip_for_element(mapping.element, doc.is_runtime))
                mappings_item.addChild(item)
                for child in child_elements(mapping.element, MAPPING_TAGS):
                    port_item = QTreeWidgetItem([element_label(child)])
                    port_item.setData(0, Qt.UserRole, child)
                    port_item.setToolTip(0, tooltip_for_element(child, doc.is_runtime))
                    item.addChild(port_item)

            notes_item = QTreeWidgetItem([f"Notes ({len(doc.notes)})"])
            root_item.addChild(notes_item)
            for note in doc.notes:
                item = QTreeWidgetItem([note.findtext("Title") or element_label(note)])
                item.setData(0, Qt.UserRole, note)
                item.setToolTip(0, tooltip_for_element(note, doc.is_runtime))
                notes_item.addChild(item)

            groups_item = QTreeWidgetItem([f"UI Groups ({len(doc.groups)})"])
            root_item.addChild(groups_item)
            for group in doc.groups:
                item = QTreeWidgetItem([group.get("Name") or group.findtext("Title") or element_label(group)])
                item.setData(0, Qt.UserRole, group)
                item.setToolTip(0, tooltip_for_element(group, doc.is_runtime))
                groups_item.addChild(item)

        root_item.setExpanded(True)
        triggers_item.setExpanded(True)
        if self.beginner_mode:
            vars_item.setHidden(True)
            for index in range(triggers_item.childCount()):
                triggers_item.child(index).setExpanded(True)

    def _add_metadata_node(self, root_item: QTreeWidgetItem, doc: TriggerScriptDocument):
        meta_item = QTreeWidgetItem(["Metadata"])
        root_item.addChild(meta_item)
        for key, value in doc.metadata.items():
            QTreeWidgetItem(meta_item, [f"{key}: {value}"])

    def on_tree_selection(self, current: QTreeWidgetItem | None, _previous: QTreeWidgetItem | None):
        if current is None:
            return
        element = current.data(0, Qt.UserRole)
        self.inspect_element(element if isinstance(element, ET.Element) else None)

    def inspect_element(self, element: ET.Element | None):
        self._loading_inspector = True
        self.current_element = element
        self.attr_table.setRowCount(0)
        self.ports_table.setRowCount(0)
        self.text_edit.clear()
        if element is None:
            self.inspector_title.setText("Inspector")
            self.inspector_hint.setText("Select a structured item.")
            self.help_text.setPlainText(explain_element(None).as_plain_text())
            self.update_graph_preview(None)
            self._loading_inspector = False
            return
        doc = self.document
        is_runtime = bool(doc and doc.is_runtime)
        self.help_text.setPlainText(explain_element(element, is_runtime).as_plain_text())
        self.update_graph_preview(element)
        self.inspector_title.setText(element_label(element))
        self.inspector_hint.setText(f"XML node: {element.tag}")
        editable = self.is_current_editable()
        self.attr_table.setEditTriggers(QTableWidget.AllEditTriggers if editable else QTableWidget.NoEditTriggers)
        self.text_edit.setReadOnly(not editable)
        for row, (key, value) in enumerate(element.attrib.items()):
            self.attr_table.insertRow(row)
            key_item = QTableWidgetItem(key)
            key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)
            value_item = QTableWidgetItem(value)
            value_item.setData(Qt.UserRole, (element, key, value))
            self.attr_table.setItem(row, 0, key_item)
            self.attr_table.setItem(row, 1, value_item)
        self.text_edit.setPlainText(element_text(element))
        ports = child_elements(element, PORT_TAGS | MAPPING_TAGS)
        self.ports_table.setRowCount(len(ports))
        for row, port in enumerate(ports):
            values = [
                port.tag,
                port.get("Name", ""),
                port.get("Type") or port.get("SigID", ""),
                element_text(port),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.ports_table.setItem(row, col, item)
        self._loading_inspector = False

    def on_attr_item_changed(self, item: QTableWidgetItem):
        if self._loading_inspector or item.column() != 1 or not self.is_current_editable():
            return
        data = item.data(Qt.UserRole)
        if not data:
            return
        element, key, old = data
        new = item.text()
        if new == old:
            return
        self.undo_stack.push(ElementEditCommand(element, key, old, new, self.after_edit))

    def on_text_changed(self):
        if self._loading_inspector or self.current_element is None or not self.is_current_editable():
            return
        old = element_text(self.current_element)
        new = self.text_edit.toPlainText()
        if old == new:
            return
        QTimer.singleShot(0, lambda: self.undo_stack.push(ElementEditCommand(self.current_element, "__text__", old, new, self.after_edit)))

    def after_edit(self):
        self.update_xml_preview()
        self.update_graph()
        current = self.tree.currentItem()
        element = self.current_element
        if current and element is not None:
            current.setText(0, element_label(element))
            self.inspect_element(element)

    def is_current_editable(self) -> bool:
        doc = self.document
        return bool(doc and doc.editable)

    def apply_filter(self, text: str):
        needle = text.strip().lower()
        for index in range(self.tree.topLevelItemCount()):
            self._filter_item(self.tree.topLevelItem(index), needle)

    def _filter_item(self, item: QTreeWidgetItem, needle: str) -> bool:
        own_match = not needle or needle in item.text(0).lower()
        child_match = False
        for index in range(item.childCount()):
            child_match = self._filter_item(item.child(index), needle) or child_match
        visible = own_match or child_match
        item.setHidden(not visible)
        if child_match and needle:
            item.setExpanded(True)
        return visible

    def set_beginner_mode(self, enabled: bool):
        self.beginner_mode = enabled
        self.beginner_btn.setText("Beginner Mode On" if enabled else "Beginner Mode")
        if enabled:
            self.help_panel.show()
            self.help_btn.setText("Hide Help")
        if self.document is not None:
            self.populate()
        self.update_mode_visibility()

    def update_mode_visibility(self):
        self.open_runtime_btn.setVisible(not self.beginner_mode)
        compare_index = self.tabs.indexOf(self.compare_tab)
        if compare_index >= 0:
            self.tabs.setTabVisible(compare_index, not self.beginner_mode)
        xml_index = self.tabs.indexOf(self.xml_tab)
        if xml_index >= 0:
            self.tabs.setTabVisible(xml_index, not self.beginner_mode)

    def toggle_docs_panel(self):
        self.docs_panel.setVisible(not self.docs_panel.isVisible())
        self.docs_btn.setText("Hide Tips" if self.docs_panel.isVisible() else "Show Tips")

    def toggle_help_panel(self):
        self.help_panel.setVisible(not self.help_panel.isVisible())
        self.help_btn.setText("Hide Help" if self.help_panel.isVisible() else "Show Help")

    def show_what_is_this(self):
        doc = self.document
        help_content = explain_element(self.current_element, bool(doc and doc.is_runtime))
        dialog = QDialog(self)
        dialog.setWindowTitle(help_content.title)
        dialog.resize(720, 620)
        layout = QVBoxLayout(dialog)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(help_content.as_plain_text())
        layout.addWidget(text, 1)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)
        dialog.exec()

    def _friendly_branch_name(self, branch: str) -> str:
        return {
            "TriggerConditions": "When this is true",
            "TriggerEffectsOnTrue": "Then do this",
            "TriggerEffectsOnFalse": "Otherwise do this",
        }.get(branch, branch)

    def _branch_tooltip(self, branch: str) -> str:
        return {
            "TriggerConditions": "Conditions are questions the trigger checks.",
            "TriggerEffectsOnTrue": "Effects here run when all required conditions pass.",
            "TriggerEffectsOnFalse": "Effects here run when conditions fail.",
        }.get(branch, "Trigger branch")

    def _friendly_command_name(self, element: ET.Element) -> str:
        tag = element.tag.rsplit("}", 1)[-1]
        command_type = element.get("Type") or tag
        if tag == "Condition":
            return f"Check: {command_type}"
        if tag == "Effect":
            return f"Do: {command_type}"
        return element_label(element)

    def update_xml_preview(self):
        doc = self.document
        if doc is None:
            self.xml_preview.clear()
            return
        try:
            self.xml_preview.setPlainText(doc.serialize().decode(doc.encoding, errors="replace"))
        except Exception as exc:
            self.xml_preview.setPlainText(f"Could not render XML preview: {exc}")

    def update_compare(self):
        self.compare_table.setRowCount(0)
        if self.document is None or self.runtime_document is None:
            self.compare_hint.setText("Load both a .triggerscript and .triggerscript_runtime file to compare structure.")
            return
        rows = compare_documents(self.document, self.runtime_document)
        self.compare_hint.setText(f"{len(rows)} structural difference(s) detected.")
        self.compare_table.setRowCount(len(rows))
        for row, values in enumerate(rows):
            for col, value in enumerate(values):
                self.compare_table.setItem(row, col, QTableWidgetItem(value))

    def update_graph(self):
        status = self.graph_scene.build_from_document(self.document, self.beginner_mode)
        self.graph_status.setText(status)
        self.graph_view.frame_all()

    def set_graph_snap(self, enabled: bool):
        self.graph_scene.snap_to_grid = enabled
        self.graph_snap_btn.setText("Snap On" if enabled else "Snap Off")

    def set_graph_grid_density(self, compact: bool):
        self.graph_scene.grid_size = 16 if compact else 24
        self.graph_grid_btn.setText("Roomy Grid" if compact else "Compact Grid")
        self.graph_view.viewport().update()

    def auto_align_graph(self):
        self.graph_scene.auto_align()
        self.graph_view.frame_all()

    def update_graph_preview(self, element: ET.Element | None):
        if not hasattr(self, "graph_preview"):
            return
        doc = self.document
        if element is None:
            self.graph_preview.setPlainText(
                "Select a Blueprint node to see variable changes, affected trigger hints, runtime expansion notes, and validation warnings."
            )
            return
        help_content = explain_element(element, bool(doc and doc.is_runtime))
        warnings = self.graph_registry.validate(element, doc) if doc is not None else []
        affected = self._affected_trigger_summary(element)
        preview = [
            help_content.summary,
            "",
            f"Variable changes: {self._variable_change_summary(element)}",
            f"Affected triggers: {affected}",
            f"Runtime expansion: {help_content.runtime_notes}",
            "Warnings:",
        ]
        preview.extend(f"- {warning}" for warning in warnings)
        if not warnings:
            preview.append("- No graph validation warnings for this node.")
        self.graph_preview.setPlainText("\n".join(preview))

    def _variable_change_summary(self, element: ET.Element) -> str:
        ports = child_elements(element, PORT_TAGS)
        refs = [element_text(port) for port in ports if element_text(port).startswith("#")]
        if refs:
            return ", ".join(refs[:6])
        if element.tag.rsplit("}", 1)[-1] == "TriggerVar":
            return f"{element.get('Name') or element.get('ID')}: {element_text(element) or '(empty)'}"
        return "No direct variable references detected."

    def _affected_trigger_summary(self, element: ET.Element) -> str:
        doc = self.document
        if doc is None:
            return "No loaded source document."
        element_id = element.get("ID")
        owners = []
        for trigger in doc.triggers:
            if trigger.element is element or any(command.element is element for command in trigger.commands):
                owners.append(trigger.name or trigger.id or "(unnamed trigger)")
            elif element_id and any(element_id in element_text(port) for command in trigger.commands for port in child_elements(command.element, PORT_TAGS)):
                owners.append(trigger.name or trigger.id or "(unnamed trigger)")
        return ", ".join(owners[:5]) if owners else "No direct trigger ownership/reference found."

    def save_as(self):
        doc = self.document
        if doc is None:
            QMessageBox.information(self, "No File", "Open a triggerscript first.")
            return
        if not doc.editable:
            QMessageBox.warning(self, "Runtime Is Read-only", ".triggerscript_runtime files are shown read-only to protect compiled/runtime data.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Trigger Script",
            str(doc.path.with_suffix(".triggerscript")),
            "Trigger scripts (*.triggerscript *.xml);;All files (*.*)",
        )
        if not path:
            return
        try:
            doc.save(Path(path))
            QMessageBox.information(self, "Saved", f"Saved trigger script:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Save Failed", str(exc))


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("Halo Wars 2 Triggerscript Editor")
    window = TriggerScriptEditor()
    if len(sys.argv) > 1:
        first = Path(sys.argv[1])
        if first.exists():
            window.load_document(first, first.suffix.lower().endswith("_runtime"))
    window.show()
    window.raise_()
    window.activateWindow()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
