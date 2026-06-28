from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


COMMAND_TAGS = {"Condition", "Effect"}
PORT_TAGS = {"Input", "Output"}
MAPPING_TAGS = {"InputMapping", "OutputMapping", "TriggerInput", "TriggerOutput"}


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _read_text(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "us-ascii", "utf-16"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def element_label(element: ET.Element) -> str:
    tag = _local_name(element.tag)
    name = element.get("Name") or element.get("Type") or element.get("TemplateMappingName")
    if name:
        return f"{tag}: {name}"
    ident = element.get("ID") or element.get("BindID") or element.get("GroupID")
    return f"{tag}: {ident}" if ident else tag


def element_text(element: ET.Element) -> str:
    return (element.text or "").strip()


def child_elements(element: ET.Element, names: set[str] | None = None) -> list[ET.Element]:
    children = list(element)
    if names is None:
        return children
    return [child for child in children if _local_name(child.tag) in names]


@dataclass
class TriggerVariable:
    element: ET.Element

    @property
    def id(self) -> str:
        return self.element.get("ID", "")

    @property
    def name(self) -> str:
        return self.element.get("Name", "")

    @property
    def type(self) -> str:
        return self.element.get("Type", "")

    @property
    def value(self) -> str:
        return element_text(self.element)

    @property
    def display_name(self) -> str:
        label = self.name or self.id or "(unnamed)"
        return f"{label} [{self.type or 'Unknown'}]"


@dataclass
class TriggerCommand:
    element: ET.Element
    parent_trigger_id: str = ""
    branch: str = ""

    @property
    def id(self) -> str:
        return self.element.get("ID", "")

    @property
    def kind(self) -> str:
        return _local_name(self.element.tag)

    @property
    def type(self) -> str:
        return self.element.get("Type", "")

    @property
    def display_name(self) -> str:
        command_type = self.type or self.kind
        dbid = self.element.get("DBID")
        return f"{self.kind}: {command_type}" + (f"  DBID {dbid}" if dbid else "")

    @property
    def ports(self) -> list[ET.Element]:
        return child_elements(self.element, PORT_TAGS)


@dataclass
class TriggerBlock:
    element: ET.Element
    commands: list[TriggerCommand] = field(default_factory=list)

    @property
    def id(self) -> str:
        return self.element.get("ID", "")

    @property
    def name(self) -> str:
        return self.element.get("Name", "")

    @property
    def active(self) -> str:
        return self.element.get("Active", "")

    @property
    def display_name(self) -> str:
        name = self.name or self.id or "(unnamed trigger)"
        return f"{name} ({len(self.commands)} commands)"


@dataclass
class TemplateMapping:
    element: ET.Element

    @property
    def id(self) -> str:
        return self.element.get("ID", "")

    @property
    def name(self) -> str:
        return self.element.get("TemplateMappingName") or self.element.get("Name", "")

    @property
    def display_name(self) -> str:
        return f"{self.name or '(mapping)'} ({len(child_elements(self.element, MAPPING_TAGS))} ports)"


@dataclass
class TriggerScriptDocument:
    path: Path
    text: str
    tree: ET.ElementTree
    root: ET.Element
    script_root: ET.Element
    file_type: str
    encoding: str = "utf-8"
    variables: list[TriggerVariable] = field(default_factory=list)
    triggers: list[TriggerBlock] = field(default_factory=list)
    mappings: list[TemplateMapping] = field(default_factory=list)
    notes: list[ET.Element] = field(default_factory=list)
    groups: list[ET.Element] = field(default_factory=list)

    @property
    def is_runtime(self) -> bool:
        return self.file_type.endswith("_runtime")

    @property
    def editable(self) -> bool:
        return not self.is_runtime

    @property
    def metadata(self) -> dict[str, str]:
        return {
            "File": str(self.path),
            "Type": self.file_type,
            "Size": f"{self.path.stat().st_size:,} bytes" if self.path.exists() else "unknown",
            "Root": _local_name(self.root.tag),
            "Script Name": self.script_root.get("Name", self.root.get("Name", "")),
            "Script Type": self.script_root.get("Type", self.root.get("Type", "")),
            "Variables": str(len(self.variables)),
            "Triggers": str(len(self.triggers)),
            "Commands": str(sum(len(trigger.commands) for trigger in self.triggers)),
            "Template Mappings": str(len(self.mappings)),
            "Notes": str(len(self.notes)),
            "Groups": str(len(self.groups)),
            "Mode": "Read-only runtime view" if self.is_runtime else "Editable source graph",
        }

    def serialize(self) -> bytes:
        ET.indent(self.tree, space="  ")
        xml = ET.tostring(self.root, encoding=self.encoding, xml_declaration=True)
        if self.encoding.lower() == "utf-8":
            return xml
        return xml

    def save(self, path: Path | None = None) -> None:
        output = path or self.path
        output.write_bytes(self.serialize())


def parse_triggerscript(path: str | Path) -> TriggerScriptDocument:
    source = Path(path)
    text = _read_text(source)
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise ValueError(f"Could not parse trigger script XML: {exc}") from exc

    tree = ET.ElementTree(root)
    script_root = _find_script_root(root)
    suffix = source.suffix.lower().lstrip(".")
    file_type = suffix or ("triggerscript_runtime" if root.get("Type") == "Scenario" else "triggerscript")
    doc = TriggerScriptDocument(
        path=source,
        text=text,
        tree=tree,
        root=root,
        script_root=script_root,
        file_type=file_type,
        encoding=_detect_declared_encoding(text),
    )
    doc.variables = [TriggerVariable(element) for element in script_root.findall(".//TriggerVar")]
    doc.triggers = _parse_triggers(script_root)
    doc.mappings = [TemplateMapping(element) for element in root.findall(".//TriggerTemplateMapping")]
    doc.notes = root.findall(".//NoteNodeXml")
    doc.groups = root.findall(".//GroupUI")
    return doc


def _find_script_root(root: ET.Element) -> ET.Element:
    if root.get("Type") in {"TriggerScript", "Scenario"} and root.find("TriggerVars") is not None:
        return root
    for child in root.findall(".//TriggerSystem"):
        if child.find("TriggerVars") is not None or child.find("Triggers") is not None:
            return child
    return root


def _parse_triggers(script_root: ET.Element) -> list[TriggerBlock]:
    blocks: list[TriggerBlock] = []
    triggers_parent = script_root.find("Triggers")
    trigger_elements = list(triggers_parent.findall("Trigger")) if triggers_parent is not None else script_root.findall(".//Trigger")
    for trigger_element in trigger_elements:
        block = TriggerBlock(trigger_element)
        commands: list[TriggerCommand] = []
        for branch_name in ("TriggerConditions", "TriggerEffectsOnTrue", "TriggerEffectsOnFalse"):
            branch = trigger_element.find(branch_name)
            if branch is None:
                continue
            commands.extend(_commands_in_branch(branch, trigger_element.get("ID", ""), branch_name))
        block.commands = commands
        blocks.append(block)
    return blocks


def _commands_in_branch(branch: ET.Element, trigger_id: str, branch_name: str) -> list[TriggerCommand]:
    commands: list[TriggerCommand] = []
    for element in branch.iter():
        if _local_name(element.tag) in COMMAND_TAGS:
            commands.append(TriggerCommand(element, trigger_id, branch_name))
    return commands


def _detect_declared_encoding(text: str) -> str:
    head = text[:120].lower()
    if "encoding=\"us-ascii\"" in head or "encoding='us-ascii'" in head:
        return "us-ascii"
    if "encoding=\"utf-8\"" in head or "encoding='utf-8'" in head:
        return "utf-8"
    return "utf-8"


def compare_documents(left: TriggerScriptDocument, right: TriggerScriptDocument) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    rows.extend(_compare_named_counts("Variables", _ids(left.variables), _ids(right.variables)))
    rows.extend(_compare_named_counts("Triggers", _ids(left.triggers), _ids(right.triggers)))
    left_commands = _command_signature_counts(left)
    right_commands = _command_signature_counts(right)
    all_command_keys = sorted(set(left_commands) | set(right_commands))
    for key in all_command_keys:
        left_count = left_commands.get(key, 0)
        right_count = right_commands.get(key, 0)
        if left_count != right_count:
            rows.append(("Command count", key, f"{left_count} -> {right_count}"))
    return rows


def _ids(items: Iterable[object]) -> set[str]:
    return {getattr(item, "id", "") for item in items if getattr(item, "id", "")}


def _compare_named_counts(label: str, left: set[str], right: set[str]) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for missing in sorted(left - right):
        rows.append((label, missing, "missing in runtime/right"))
    for added in sorted(right - left):
        rows.append((label, added, "only in runtime/right"))
    return rows


def _command_signature_counts(doc: TriggerScriptDocument) -> dict[str, int]:
    counts: dict[str, int] = {}
    for trigger in doc.triggers:
        for command in trigger.commands:
            key = f"{command.kind}:{command.type or '(unknown)'}"
            counts[key] = counts.get(key, 0) + 1
    return counts
