"""
core/parser.py
--------------
Parses any HW2 .ai / .xml file into AITable model objects.

KEY DESIGN PRINCIPLE: HW2 AI files are ORDER-SENSITIVE. The game processes
Building, Tech, and Mission directives in document order. We must preserve
that order in a single directives list rather than collecting each type
separately (which would silently re-order them).

Bugs fixed vs. original:
  - Document order preserved via single-pass child iteration
  - SkipTargetIfPreviousTargetExists no longer stomped into target_closest field
  - MinimumNumberOfSquadsToSend correctly parsed (was 'minimumnumberofsquads')
  - AlternateSquadTypeToSend correctly handled (one element per alternate)
  - assign_reserves_to_mission parsed and stored as Optional[bool]
  - Iterable import added (was NameError)
  - assigned_mission_ids no longer strips legitimate 0 values
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Optional, Iterable

from .models import (
    AITable, AISettings, LeaderPower, BuildingDirective,
    TechDirective, MissionDirective, SquadEntry,
)


# ---------------------------------------------------------------------------
# Primitive helpers
# ---------------------------------------------------------------------------

def _int(text: Optional[str], default: Optional[int] = None) -> Optional[int]:
    if text is None:
        return default
    try:
        return int(text.strip())
    except (ValueError, AttributeError):
        return default


def _bool(text: Optional[str]) -> bool:
    return (text or "").strip().lower() in ("1", "true", "yes")


def _str(text: Optional[str]) -> str:
    return (text or "").strip()


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def _parse_settings(elem: ET.Element) -> AISettings:
    s = AISettings()
    for child in elem:
        tag = child.tag.lower()
        text = _str(child.text)
        if tag == "faction":
            s.faction = text
        elif tag == "gamemode":
            s.game_mode = text
        elif tag == "strategytype":
            s.strategy_type = text
        elif tag == "commander":
            s.commander = text
        elif tag == "mapname":
            s.map_name = text
        elif tag == "rallypointmovementpopulationthreshold":
            s.rally_point_movement_population_threshold = _int(text, 10)
        elif tag == "reserved":
            s.reserved = _bool(text)
        elif tag == "autoai":
            s.auto_ai = _bool(text)
    return s


# ---------------------------------------------------------------------------
# Leader Power
# ---------------------------------------------------------------------------

def _parse_leader_power(elem: ET.Element) -> LeaderPower:
    lp = LeaderPower()
    for child in elem:
        tag = child.tag.lower()
        text = _str(child.text)
        if tag in ("leaderpowertype", "powertype"):
            lp.power_type = text
        elif tag == "targettype":
            lp.target_type = text or None
        elif tag == "assignedmissionid":
            v = _int(text)
            if v is not None:
                lp.assigned_mission_ids.append(v)
        elif tag == "numberoftimestobeused":
            lp.number_of_times_to_be_used = _int(text)
        elif tag == "minimumhealpointstoheal":
            lp.minimum_heal_points_to_heal = _int(text)
        elif tag == "minimumtargetpoptocast":
            lp.minimum_target_pop_to_cast = _int(text)
    return lp


# ---------------------------------------------------------------------------
# Building directive
# ---------------------------------------------------------------------------

def _parse_building(elem: ET.Element) -> BuildingDirective:
    d = BuildingDirective()
    for child in elem:
        tag = child.tag.lower()
        text = _str(child.text)
        if tag == "buildingtype":
            d.building_type = text
        elif tag == "numberofbuildingtypeneeded":
            d.number_of_building_type_needed = _int(text, 1)
        elif tag == "productionlocationtype":
            d.production_location_type = text or None
        elif tag == "recyclebuilding":
            d.recycle_building = _bool(text)
        elif tag == "prerequisiteobtainedobjecttype":
            d.prerequisite_obtained_object_type = text or None
        elif tag == "prerequisiteobtainedobjectcount":
            d.prerequisite_obtained_object_count = _int(text)
        elif tag == "prerequisitesightingobjecttype":
            d.prerequisite_sighting_object_type = text or None
        elif tag == "prerequisitesightingobjectcount":
            d.prerequisite_sighting_object_count = _int(text)
        elif tag == "prerequisitetech":
            d.prerequisite_tech = text or None
        elif tag == "prerequisiteleaderpower":
            d.prerequisite_leader_power = text or None
    return d


# ---------------------------------------------------------------------------
# Tech directive
# ---------------------------------------------------------------------------

def _parse_tech(elem: ET.Element) -> TechDirective:
    d = TechDirective()
    for child in elem:
        tag = child.tag.lower()
        text = _str(child.text)
        if tag in ("techtoresearch", "tech"):
            d.tech_to_research = text
        elif tag == "prerequisiteobtainedobjecttype":
            d.prerequisite_obtained_object_type = text or None
        elif tag == "prerequisiteobtainedobjectcount":
            d.prerequisite_obtained_object_count = _int(text)
        elif tag == "prerequisitesightingobjecttype":
            d.prerequisite_sighting_object_type = text or None
        elif tag == "prerequisitesightingobjectcount":
            d.prerequisite_sighting_object_count = _int(text)
        elif tag == "prerequisitetech":
            d.prerequisite_tech = text or None
        elif tag == "prerequisiteleaderpower":
            d.prerequisite_leader_power = text or None
    return d


# ---------------------------------------------------------------------------
# Mission directive
# ---------------------------------------------------------------------------

def _parse_mission(elem: ET.Element) -> MissionDirective:
    """
    Parse a Mission element.

    Squads are built by tracking SquadTypeToSend / NumberOfSquadsToSend /
    MinimumNumberOfSquadsToSend / AlternateSquadTypeToSend in the order they
    appear, which matches the HW2 schema exactly.

    TargetType and TargetBaseType can appear multiple times in one Mission
    (defining multiple targets in order). They are collected as parallel lists.

    SkipTargetIfPreviousTargetExists is a SEPARATE flag from
    TargetClosestObjectsToRandomEnemyFirst — they control different behaviours.
    """
    d = MissionDirective()

    # Accumulator state for squad building
    current_squad: Optional[SquadEntry] = None

    for child in elem:
        tag = child.tag.lower()
        text = _str(child.text)

        # --- Core identity ---
        if tag == "missiontype":
            d.mission_type = text
        elif tag == "missionid":
            d.mission_id = _int(text)

        # --- Targets (multiple, parallel) ---
        elif tag == "targettype":
            d.target_types.append(text)
        elif tag == "targetbasetype":
            d.target_base_types.append(text)

        # --- Repeat / replace counts ---
        elif tag == "numberoftimestorepeatmission":
            d.number_of_times_to_repeat_mission = _int(text, -1)
        elif tag == "numberoftimestoreplacesquads":
            d.number_of_times_to_replace_squads = _int(text, 0)

        # --- Timing ---
        elif tag == "timetowaitattarget":
            d.time_to_wait_at_target = _int(text)
        elif tag == "timeuntilsquadsarereplaced":
            d.time_until_squads_are_replaced = _int(text)

        # --- Boolean flags (each maps to its correct field) ---
        elif tag in ("focusfireontarget", "focussfireontarget"):
            d.focus_fire_on_target = _bool(text)
        elif tag == "streamreplacesquads":
            d.stream_replace_squads = _bool(text)
        elif tag == "takesquadsfromothermissions":
            d.take_squads_from_other_missions = _bool(text)
        elif tag == "donttakesquadsfromthismission":
            d.dont_take_squads_from_this_mission = _bool(text)
        elif tag == "returntorallypoint":
            d.return_to_rally_point = _bool(text)
        elif tag == "targetclosestobjectstorandomenemyfirst":
            # This flag makes the AI target the closest objects to a RANDOM
            # enemy rather than targeting in list order. Separate from Skip.
            d.target_closest_objects_to_random_enemy_first = _bool(text)
        elif tag == "skiptargetifprevioustargetexists":
            # This flag skips to the next target if the previous still exists.
            # e.g. attack expansion first, skip to main base only if expansion
            # is already destroyed.
            d.skip_target_if_previous_target_exists = _bool(text)
        elif tag == "initializeafterpreviousmissionscomplete":
            d.initialize_after_previous_missions_complete = _bool(text)
        elif tag == "assignreserverstomission" or tag == "assignreservestomission":
            # Only written to model when explicitly present in XML.
            # None means the tag was absent (don't emit it on export).
            d.assign_reserves_to_mission = _bool(text)

        # --- Prerequisites ---
        elif tag == "prerequisiteobtainedobjecttype":
            d.prerequisite_obtained_object_type = text or None
        elif tag == "prerequisiteobtainedobjectcount":
            d.prerequisite_obtained_object_count = _int(text)
        elif tag == "prerequisitesightingobjecttype":
            d.prerequisite_sighting_object_type = text or None
        elif tag == "prerequisitesightingobjectcount":
            d.prerequisite_sighting_object_count = _int(text)
        elif tag == "prerequisitetech":
            d.prerequisite_tech = text or None
        elif tag == "prerequisiteleaderpower":
            d.prerequisite_leader_power = text or None

        # --- Squads (stateful: each SquadTypeToSend starts a new entry) ---
        elif tag == "squadtypetosend":
            # Finalise any in-progress squad before starting a new one
            if current_squad is not None:
                d.squads.append(current_squad)
            current_squad = SquadEntry(squad_type=text)

        elif tag == "numberofsquadstosend":
            if current_squad is not None:
                current_squad.number_of_squads = _int(text, 1)

        elif tag == "minimumnumberofsquadstosend":
            # Correct HW2 tag name (was wrongly parsed as 'minimumnumberofsquads')
            if current_squad is not None:
                current_squad.minimum_number_of_squads = _int(text)

        elif tag == "alternatesquadtypetosend":
            # One AlternateSquadTypeToSend element per alternate unit.
            # They belong to the CURRENT squad entry.
            if current_squad is not None:
                current_squad.alternate_squad_types.append(text)

    # Don't forget the last squad if any was in progress
    if current_squad is not None:
        d.squads.append(current_squad)

    return d


# ---------------------------------------------------------------------------
# Top-level file parser
# ---------------------------------------------------------------------------

def parse_file(path: str) -> AITable:
    """
    Parse any HW2 .ai or .xml file into an AITable.

    CRITICAL: directives (Building, Tech, Mission) are added to table.directives
    in the exact order they appear in the XML. The game processes them in order.
    We iterate the Table's direct children in a single pass rather than using
    findall() for each type separately (which would reorder them).

    Encoding note: some hand-authored files declare us-ascii in the XML header
    but contain non-ASCII characters in comments (e.g. em-dashes). We strip
    XML comments before parsing to handle this gracefully.
    """
    import re as _re
    table = AITable()
    try:
        with open(path, "rb") as _f:
            raw = _f.read()
        # Strip XML comments — they are never part of AI logic and can contain
        # non-ASCII characters that break strict parsers.
        raw = _re.sub(rb"<!--.*?-->", b"", raw, flags=_re.DOTALL)
        # Also replace the us-ascii declaration so ElementTree won't reject
        # any stray high bytes that survive comment stripping.
        raw = raw.replace(b'encoding="us-ascii"', b'encoding="utf-8"')
        raw = raw.replace(b"encoding='us-ascii'", b"encoding='utf-8'")
        root = ET.fromstring(raw)
    except Exception:
        return table

    # Find the <Table> element wherever it lives
    table_elem = root if root.tag.lower() == "table" else root.find(".//Table")
    if table_elem is None:
        table_elem = root  # fallback: treat root as the table

    for child in table_elem:
        tag = child.tag.lower()
        if tag == "settings":
            table.settings = _parse_settings(child)
        elif tag == "leaderpower":
            table.leader_powers.append(_parse_leader_power(child))
        elif tag in ("building", "buildingdirective"):
            table.directives.append(_parse_building(child))
        elif tag in ("tech", "techdirective"):
            table.directives.append(_parse_tech(child))
        elif tag in ("mission", "missiondirective"):
            table.directives.append(_parse_mission(child))
        # Unknown tags are silently skipped to allow forward compatibility

    return table