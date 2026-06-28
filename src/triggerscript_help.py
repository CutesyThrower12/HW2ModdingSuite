from __future__ import annotations

from dataclasses import dataclass
from xml.etree import ElementTree as ET


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def text_value(element: ET.Element | None) -> str:
    return (element.text or "").strip() if element is not None else ""


@dataclass(frozen=True)
class HelpContent:
    title: str
    summary: str
    what_it_does: str
    how_it_fits: str
    safe_to_edit: str
    runtime_notes: str
    examples: str
    related: str

    def as_plain_text(self) -> str:
        return (
            f"{self.title}\n\n"
            f"Summary\n{self.summary}\n\n"
            f"What it does\n{self.what_it_does}\n\n"
            f"How it fits into the trigger\n{self.how_it_fits}\n\n"
            f"Safe editing notes\n{self.safe_to_edit}\n\n"
            f"Runtime differences\n{self.runtime_notes}\n\n"
            f"Examples\n{self.examples}\n\n"
            f"Related triggers / references\n{self.related}"
        )


def explain_element(element: ET.Element | None, is_runtime: bool = False) -> HelpContent:
    if element is None:
        return HelpContent(
            "No selection",
            "Select an item in the tree to see what it means.",
            "Triggerscripts are XML graphs. Triggers contain conditions and effects. Variables hold values or references used by those commands.",
            "The left tree is organized from broad script structure down to individual command parameters.",
            "Open a .triggerscript for editing. Runtime files are intentionally read-only.",
            "Runtime files are usually expanded/generated forms used by the game, so they can contain many more generated triggers and variables.",
            "Click a Trigger, Condition, Effect, Input, Output, or TriggerVar to see targeted help.",
            "Related items appear as IDs beginning with #. Search those IDs to find the referenced variable or trigger.",
        )

    tag = local_name(element.tag)
    if tag == "TriggerVar":
        return _variable_help(element, is_runtime)
    if tag == "Trigger":
        return _trigger_help(element, is_runtime)
    if tag == "Condition":
        return _condition_help(element, is_runtime)
    if tag == "Effect":
        return _effect_help(element, is_runtime)
    if tag in {"Input", "Output"}:
        return _port_help(element, is_runtime)
    if tag in {"InputMapping", "OutputMapping", "TriggerInput", "TriggerOutput", "TriggerTemplateMapping"}:
        return _mapping_help(element, is_runtime)
    if tag == "GroupUI":
        return _group_help(element, is_runtime)
    if tag == "NoteNodeXml":
        return _note_help(element, is_runtime)
    return _generic_help(element, is_runtime)


def tooltip_for_element(element: ET.Element | None, is_runtime: bool = False) -> str:
    help_text = explain_element(element, is_runtime)
    return f"{help_text.title}\n{help_text.summary}\n\nSafe: {help_text.safe_to_edit}"


def modding_tips() -> str:
    return (
        "What triggerscripts are\n"
        "Triggerscripts are XML-based logic graphs used by Halo Wars 2 maps and modes. A Trigger checks Conditions and then runs Effects.\n\n"
        "What runtime files are\n"
        ".triggerscript_runtime files are generated/flattened runtime forms. They often contain more generated variables and triggers than the editable source graph.\n\n"
        "Safe editing guidelines\n"
        "- Prefer editing named variables, trigger Active flags, and obvious numeric/string parameter values.\n"
        "- Save to a new file until you trust the change in-game.\n"
        "- Keep IDs beginning with # intact unless you know the referenced object exists.\n"
        "- Runtime files are read-only here because they are likely compiled/generated.\n\n"
        "Common mistakes\n"
        "- Deleting a TriggerVar that an Input still references.\n"
        "- Renaming IDs instead of display names.\n"
        "- Editing DBID, SigID, or Version values without knowing the command database.\n"
        "- Assuming runtime and source files should have the same trigger count.\n\n"
        "Best practices\n"
        "- Use Search to follow #ID references.\n"
        "- Compare source vs runtime to understand generated behavior.\n"
        "- Change one gameplay value at a time and test.\n"
        "- Use notes and UI groups as clues: official maps often group logic by players, waves, objectives, cinematics, or setup.\n\n"
        "Official-map examples\n"
        "Common patterns include startup triggers that initialize mode rules, repeating timers that pulse behavior, leader checks that grant techs, and population/resource effects that shape pacing."
    )


def simplified_trigger_name(element: ET.Element) -> str:
    name = element.get("Name") or element.get("ID") or "Unnamed trigger"
    active = element.get("Active")
    prefix = "Enabled" if active == "true" else "Disabled" if active == "false" else "Trigger"
    return f"{prefix}: {name}"


def trigger_purpose(element: ET.Element) -> str:
    name = (element.get("Name") or "").lower()
    text = " ".join(child.get("Type", "") for child in element.iter()).lower()
    combined = f"{name} {text}"
    if any(word in combined for word in ("objective", "win", "lose", "victory", "defeat", "score")):
        return "Objectives"
    if any(word in combined for word in ("wave", "spawn", "squad", "army", "reinforcement", "attack")):
        return "Waves"
    if any(word in combined for word in ("ai", "skirmish", "leader", "player", "base", "pop", "resource")):
        return "AI / Player Logic"
    if any(word in combined for word in ("cinematic", "camera", "dialog", "subtitle", "movie")):
        return "Cinematics"
    return "Misc"


def _variable_help(element: ET.Element, is_runtime: bool) -> HelpContent:
    name = element.get("Name") or "(unnamed)"
    value = text_value(element) or "(empty/null)"
    var_type = element.get("Type", "Unknown")
    return HelpContent(
        f"Variable: {name}",
        f"A {var_type} value that commands can read from or write to.",
        f"This TriggerVar stores a value or reference. Current value: {value}. IsNull={element.get('IsNull', 'unknown')}.",
        "Inputs and Outputs reference variables by ID. Search this variable's ID to find commands that use it.",
        "Usually safe to edit Name and simple text values. Be careful changing Type, ID, or IsNull because commands may expect a specific value type.",
        _runtime_note(is_runtime),
        "Examples: a Player variable can point commands at a player; a Float can hold population; a TechList can hold comma-separated tech names.",
        f"ID: {element.get('ID', '(none)')}",
    )


def _trigger_help(element: ET.Element, is_runtime: bool) -> HelpContent:
    name = element.get("Name") or "(unnamed)"
    active = element.get("Active", "unknown")
    conditional = element.get("ConditionalTrigger", "unknown")
    return HelpContent(
        f"Trigger: {name}",
        "A trigger is a logic block: when active, it evaluates conditions and runs effects.",
        f"This trigger is Active={active}, ConditionalTrigger={conditional}, and EvaluateFrequency={element.get('EvaluateFrequency', '0')}.",
        "Conditions live under TriggerConditions. Effects under TriggerEffectsOnTrue run when conditions pass; TriggerEffectsOnFalse runs when they fail.",
        "Safe edits: display Name, Active true/false, CommentOut true/false, and simple frequency values. Risky edits: ID, TemplateID, structural child deletion.",
        _runtime_note(is_runtime),
        "Example: a startup trigger can launch another script and activate setup triggers. A repeating trigger can periodically check population or AI state.",
        "Related commands are shown below this trigger in the tree.",
    )


def _condition_help(element: ET.Element, is_runtime: bool) -> HelpContent:
    command_type = element.get("Type", "Condition")
    return HelpContent(
        f"Condition: {command_type}",
        "A condition asks a yes/no question before effects run.",
        f"This condition uses DBID={element.get('DBID', 'unknown')} and Version={element.get('Version', 'unknown')}. Invert={element.get('Invert', 'false')} flips the result.",
        "It belongs under TriggerConditions. Multiple conditions can be combined by And/Or nodes.",
        "Safe edits: referenced Input variable IDs and Invert when you understand the logic. Risky edits: Type, DBID, SigID, Version.",
        _runtime_note(is_runtime),
        "Examples: PlayerUsingLeader checks a selected leader; CanRetrieveExternals fetches externally supplied values.",
        "Inputs below this condition point to TriggerVar IDs.",
    )


def _effect_help(element: ET.Element, is_runtime: bool) -> HelpContent:
    command_type = element.get("Type", "Effect")
    return HelpContent(
        f"Effect: {command_type}",
        "An effect performs an action when its trigger branch runs.",
        f"This effect uses DBID={element.get('DBID', 'unknown')} and Version={element.get('Version', 'unknown')}. CommentOut={element.get('CommentOut', 'false')}.",
        "Effects under TriggerEffectsOnTrue run when conditions pass. Effects under TriggerEffectsOnFalse run when conditions fail.",
        "Safe edits: simple Input/Output referenced variables and CommentOut. Risky edits: Type, DBID, Version, command structure.",
        _runtime_note(is_runtime),
        "Examples: LaunchScript starts another trigger script; TriggerActivate enables another trigger; SetPlayerPop changes population values.",
        "Inputs and Outputs below this effect are the best place to inspect what the effect touches.",
    )


def _port_help(element: ET.Element, is_runtime: bool) -> HelpContent:
    tag = local_name(element.tag)
    value = text_value(element) or "(empty)"
    return HelpContent(
        f"{tag}: {element.get('Name', '(unnamed)')}",
        f"A command {tag.lower()} that links a command socket to a variable/reference.",
        f"Name={element.get('Name', '')}, SigID={element.get('SigID', '')}, Optional={element.get('Optional', '')}, Value={value}.",
        "Inputs feed values into commands. Outputs usually receive command results into TriggerVars.",
        "Often safe to change the referenced #ID if you intentionally redirect the command to another compatible variable. Do not change SigID casually.",
        _runtime_note(is_runtime),
        "Example: an Input named Player may reference the Player TriggerVar; an Output named Float stores a calculated value.",
        "Search the #ID value to find the referenced TriggerVar.",
    )


def _mapping_help(element: ET.Element, is_runtime: bool) -> HelpContent:
    tag = local_name(element.tag)
    return HelpContent(
        f"{tag}: {element.get('Name') or element.get('TemplateMappingName') or '(unnamed)'}",
        "A visual-editor mapping node that describes how graph boxes and pins are connected.",
        "Mappings preserve editor layout, node positions, template names, and visual input/output bindings.",
        "These are mostly editor-facing. They help explain the graph but may not directly drive runtime logic.",
        "Edit with caution. Position/minimized/name fields are safer than BindID or connection text.",
        "Runtime files usually omit these because the game does not need editor layout metadata.",
        "Example: a repeatingactivate template mapping shows Start/Stop/Activate pins for a timer-like graph node.",
        f"ID: {element.get('ID', '(none)')}",
    )


def _group_help(element: ET.Element, is_runtime: bool) -> HelpContent:
    return HelpContent(
        f"UI Group: {element.get('Name') or element.findtext('Title') or '(unnamed)'}",
        "A visual editor group used to organize related trigger graph nodes.",
        "Groups are human-facing layout/documentation metadata, not direct gameplay commands.",
        "Use group names as clues for what nearby triggers do.",
        "Usually safe to edit display names and layout fields. Runtime files normally omit groups.",
        _runtime_note(is_runtime),
        "Examples: groups named Cov Players, UNSC Players, Pop Model, Waves, or Objectives often reveal script purpose.",
        f"GroupID: {element.get('GroupID', '(none)')}",
    )


def _note_help(element: ET.Element, is_runtime: bool) -> HelpContent:
    title = element.findtext("Title") or "(note)"
    description = element.findtext("Description") or ""
    return HelpContent(
        f"Note: {title}",
        "A human-authored note from the trigger editor.",
        description[:500] or "This note has no description text.",
        "Notes are documentation and context clues for nearby trigger nodes.",
        "Safe to edit, but preserve useful context for future modders.",
        "Runtime files usually omit notes.",
        "Official scripts often use notes to explain setup, leader checks, or map-specific rule exceptions.",
        "Look at nearby UI groups and trigger names for related logic.",
    )


def _generic_help(element: ET.Element, is_runtime: bool) -> HelpContent:
    tag = local_name(element.tag)
    return HelpContent(
        tag,
        "A structural XML node in the triggerscript.",
        "This node helps organize the trigger graph or stores metadata.",
        "It may contain child commands, variables, mappings, or UI/editor data.",
        "Safe edits depend on the node. Prefer editing clear display fields and values rather than IDs or schema fields.",
        _runtime_note(is_runtime),
        "Examples: TriggerConditions groups conditions; TriggerEffectsOnTrue groups actions for a passing trigger.",
        "Inspect child nodes to understand its role.",
    )


def _runtime_note(is_runtime: bool) -> str:
    if is_runtime:
        return "You are viewing a runtime file. It is read-only because it is likely generated/flattened for the game."
    return "Source .triggerscript files keep editor metadata and are the safest place to edit. Runtime can differ because it expands or resolves source graph data."
