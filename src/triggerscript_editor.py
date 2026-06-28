from __future__ import annotations

import os
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QUndoCommand, QUndoStack
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
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
        self.undo_btn = QPushButton("Undo")
        self.redo_btn = QPushButton("Redo")
        for button in (self.open_btn, self.open_runtime_btn, self.save_btn, self.undo_btn, self.redo_btn):
            header_layout.addWidget(button)
        layout.addWidget(header)

        self.meta_label = QLabel("No triggerscript loaded.")
        self.meta_label.setObjectName("Muted")
        layout.addWidget(self.meta_label)

        self.tabs = QTabWidget()
        self.structure_tab = QWidget()
        self.compare_tab = QWidget()
        self.xml_tab = QWidget()
        self.tabs.addTab(self.structure_tab, "Structure")
        self.tabs.addTab(self.compare_tab, "Compare")
        self.tabs.addTab(self.xml_tab, "XML Preview")
        layout.addWidget(self.tabs, 1)

        self._build_structure_tab()
        self._build_compare_tab()
        self._build_xml_tab()
        self.setCentralWidget(root)

        self.open_btn.clicked.connect(self.open_script)
        self.open_runtime_btn.clicked.connect(self.open_runtime)
        self.save_btn.clicked.connect(self.save_as)
        self.undo_btn.clicked.connect(self.undo_stack.undo)
        self.redo_btn.clicked.connect(self.undo_stack.redo)
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
        layout.addWidget(self.search_field)
        splitter = QSplitter(Qt.Horizontal)
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
        inspector_layout.addWidget(self.inspector_title)
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
        splitter.setSizes([520, 880])
        layout.addWidget(splitter, 1)

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
        self.current_element = None
        self.meta_label.setText("   ".join(f"{key}: {value}" for key, value in doc.metadata.items() if key in {"Type", "Size", "Variables", "Triggers", "Commands", "Template Mappings", "Mode"}))
        self.populate_tree(doc)
        self.update_xml_preview()
        self.update_compare()

    def populate_tree(self, doc: TriggerScriptDocument):
        self.tree.clear()
        root_item = QTreeWidgetItem([Path(doc.path).name])
        root_item.setData(0, Qt.UserRole, doc.script_root)
        self.tree.addTopLevelItem(root_item)

        self._add_metadata_node(root_item, doc)
        vars_item = QTreeWidgetItem(["Variables"])
        root_item.addChild(vars_item)
        for var in doc.variables:
            item = QTreeWidgetItem([var.display_name])
            item.setData(0, Qt.UserRole, var.element)
            vars_item.addChild(item)

        triggers_item = QTreeWidgetItem(["Triggers"])
        root_item.addChild(triggers_item)
        for trigger in doc.triggers:
            trigger_item = QTreeWidgetItem([trigger.display_name])
            trigger_item.setData(0, Qt.UserRole, trigger.element)
            triggers_item.addChild(trigger_item)
            branches: dict[str, QTreeWidgetItem] = {}
            for command in trigger.commands:
                branch_item = branches.get(command.branch)
                if branch_item is None:
                    branch_item = QTreeWidgetItem([command.branch])
                    branches[command.branch] = branch_item
                    trigger_item.addChild(branch_item)
                command_item = QTreeWidgetItem([command.display_name])
                command_item.setData(0, Qt.UserRole, command.element)
                branch_item.addChild(command_item)
                for port in command.ports:
                    port_item = QTreeWidgetItem([element_label(port)])
                    port_item.setData(0, Qt.UserRole, port)
                    command_item.addChild(port_item)

        mappings_item = QTreeWidgetItem(["Template Mappings"])
        root_item.addChild(mappings_item)
        for mapping in doc.mappings:
            item = QTreeWidgetItem([mapping.display_name])
            item.setData(0, Qt.UserRole, mapping.element)
            mappings_item.addChild(item)
            for child in child_elements(mapping.element, MAPPING_TAGS):
                port_item = QTreeWidgetItem([element_label(child)])
                port_item.setData(0, Qt.UserRole, child)
                item.addChild(port_item)

        notes_item = QTreeWidgetItem([f"Notes ({len(doc.notes)})"])
        root_item.addChild(notes_item)
        for note in doc.notes:
            item = QTreeWidgetItem([note.findtext("Title") or element_label(note)])
            item.setData(0, Qt.UserRole, note)
            notes_item.addChild(item)

        groups_item = QTreeWidgetItem([f"UI Groups ({len(doc.groups)})"])
        root_item.addChild(groups_item)
        for group in doc.groups:
            item = QTreeWidgetItem([group.get("Name") or group.findtext("Title") or element_label(group)])
            item.setData(0, Qt.UserRole, group)
            groups_item.addChild(item)

        root_item.setExpanded(True)
        triggers_item.setExpanded(True)

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
            self._loading_inspector = False
            return
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
