"""
core/exporter.py
----------------
Serialises an AITable back to a game-ready HW2 AI XML string.

Rules followed strictly:
  - Tags are emitted in the same relative order the game expects
  - Boolean flags (false) are OMITTED rather than written as false=false
    (the game treats absence as false; writing false everywhere bloats files)
  - RecycleBuilding comes BEFORE Prerequisites (matches original files)
  - AlternateSquadTypeToSend is one element per alternate (not a CSV list)
  - MinimumNumberOfSquadsToSend uses the correct HW2 tag name
  - assign_reserves_to_mission is only written when explicitly set (not None)
"""
from __future__ import annotations

from xml.sax.saxutils import escape
from .models import (
    AITable, BuildingDirective, TechDirective, MissionDirective,
    LeaderPower, SquadEntry,
)


def _b(value: bool) -> str:
    return "true" if value else "false"


def _prereqs(d, out: list[str]) -> None:
    """Emit prerequisite tags that are present."""
    if getattr(d, "prerequisite_obtained_object_type", None):
        out.append(f"      <PrerequisiteObtainedObjectType>{escape(d.prerequisite_obtained_object_type)}</PrerequisiteObtainedObjectType>")
    if getattr(d, "prerequisite_obtained_object_count", None) is not None:
        out.append(f"      <PrerequisiteObtainedObjectCount>{d.prerequisite_obtained_object_count}</PrerequisiteObtainedObjectCount>")
    if getattr(d, "prerequisite_sighting_object_type", None):
        out.append(f"      <PrerequisiteSightingObjectType>{escape(d.prerequisite_sighting_object_type)}</PrerequisiteSightingObjectType>")
    if getattr(d, "prerequisite_sighting_object_count", None) is not None:
        out.append(f"      <PrerequisiteSightingObjectCount>{d.prerequisite_sighting_object_count}</PrerequisiteSightingObjectCount>")
    if getattr(d, "prerequisite_tech", None):
        out.append(f"      <PrerequisiteTech>{escape(d.prerequisite_tech)}</PrerequisiteTech>")
    if getattr(d, "prerequisite_leader_power", None):
        out.append(f"      <PrerequisiteLeaderPower>{escape(d.prerequisite_leader_power)}</PrerequisiteLeaderPower>")


def _building(d: BuildingDirective, out: list[str]) -> None:
    out.append("    <Building>")
    out.append(f"      <BuildingType>{escape(d.building_type)}</BuildingType>")
    out.append(f"      <NumberOfBuildingTypeNeeded>{d.number_of_building_type_needed}</NumberOfBuildingTypeNeeded>")
    if d.production_location_type:
        out.append(f"      <ProductionLocationType>{escape(d.production_location_type)}</ProductionLocationType>")
    # RecycleBuilding comes before prerequisites — matches original file ordering
    if d.recycle_building:
        out.append("      <RecycleBuilding>true</RecycleBuilding>")
    _prereqs(d, out)
    out.append("    </Building>")


def _tech(d: TechDirective, out: list[str]) -> None:
    out.append("    <Tech>")
    out.append(f"      <TechToResearch>{escape(d.tech_to_research)}</TechToResearch>")
    _prereqs(d, out)
    out.append("    </Tech>")


def _mission(d: MissionDirective, out: list[str]) -> None:
    out.append("    <Mission>")

    # MissionID before MissionType matches original files where ID appears first
    if d.mission_id is not None:
        out.append(f"      <MissionID>{d.mission_id}</MissionID>")
    out.append(f"      <MissionType>{escape(d.mission_type)}</MissionType>")

    # Turtle-exclusive flag goes right after MissionType
    if d.initialize_after_previous_missions_complete:
        out.append("      <InitializeAfterPreviousMissionsComplete>true</InitializeAfterPreviousMissionsComplete>")

    # Targets — emitted in pairs as the game reads them sequentially
    tbt_iter = iter(d.target_base_types)
    for i, tt in enumerate(d.target_types):
        out.append(f"      <TargetType>{escape(tt)}</TargetType>")
        tbt = next(tbt_iter, None)
        if tbt:
            out.append(f"      <TargetBaseType>{escape(tbt)}</TargetBaseType>")
        # SkipTargetIfPreviousTargetExists is placed after the FIRST target pair
        # when multiple targets are defined (this is how original files do it)
        if d.skip_target_if_previous_target_exists and i == 0 and len(d.target_types) > 1:
            out.append("      <SkipTargetIfPreviousTargetExists>true</SkipTargetIfPreviousTargetExists>")

    # Squads — one SquadTypeToSend block at a time
    for sq in d.squads:
        out.append(f"      <SquadTypeToSend>{escape(sq.squad_type)}</SquadTypeToSend>")
        # AlternateSquadTypeToSend: one element per alternate (NOT a CSV list)
        for alt in sq.alternate_squad_types:
            out.append(f"      <AlternateSquadTypeToSend>{escape(alt)}</AlternateSquadTypeToSend>")
        if sq.minimum_number_of_squads is not None:
            out.append(f"      <MinimumNumberOfSquadsToSend>{sq.minimum_number_of_squads}</MinimumNumberOfSquadsToSend>")
        out.append(f"      <NumberOfSquadsToSend>{sq.number_of_squads}</NumberOfSquadsToSend>")

    # Repeat / replace
    out.append(f"      <NumberOfTimesToRepeatMission>{d.number_of_times_to_repeat_mission}</NumberOfTimesToRepeatMission>")
    out.append(f"      <NumberOfTimesToReplaceSquads>{d.number_of_times_to_replace_squads}</NumberOfTimesToReplaceSquads>")

    # Optional timing
    if d.time_to_wait_at_target is not None:
        out.append(f"      <TimeToWaitAtTarget>{d.time_to_wait_at_target}</TimeToWaitAtTarget>")
    if d.time_until_squads_are_replaced is not None:
        out.append(f"      <TimeUntilSquadsAreReplaced>{d.time_until_squads_are_replaced}</TimeUntilSquadsAreReplaced>")

    # Boolean flags — only emit when TRUE (absence == false in HW2)
    if d.focus_fire_on_target:
        out.append("      <FocusFireOnTarget>true</FocusFireOnTarget>")
    if d.stream_replace_squads:
        out.append("      <StreamReplaceSquads>true</StreamReplaceSquads>")
    if d.take_squads_from_other_missions:
        out.append("      <TakeSquadsFromOtherMissions>true</TakeSquadsFromOtherMissions>")
    if d.dont_take_squads_from_this_mission:
        out.append("      <DontTakeSquadsFromThisMission>true</DontTakeSquadsFromThisMission>")
    if d.return_to_rally_point:
        out.append("      <ReturnToRallyPoint>true</ReturnToRallyPoint>")
    if d.target_closest_objects_to_random_enemy_first:
        out.append("      <TargetClosestObjectsToRandomEnemyFirst>true</TargetClosestObjectsToRandomEnemyFirst>")
    # assign_reserves_to_mission: only write when explicitly set to False
    # (Turtle-exclusive pattern — absence means True / default behaviour)
    if d.assign_reserves_to_mission is not None:
        out.append(f"      <AssignReservesToMission>{_b(d.assign_reserves_to_mission)}</AssignReservesToMission>")

    # Prerequisites
    _prereqs(d, out)

    out.append("    </Mission>")


def export_xml(table: AITable) -> str:
    """Return a complete, game-ready HW2 AI XML string."""
    out: list[str] = []
    out.append('<?xml version="1.0" encoding="us-ascii"?>')
    out.append("<Tables>")
    out.append("  <Table>")

    # Settings
    s = table.settings
    out.append("    <Settings>")
    out.append(f"      <Faction>{escape(s.faction)}</Faction>")
    out.append(f"      <GameMode>{escape(s.game_mode)}</GameMode>")
    out.append(f"      <StrategyType>{escape(s.strategy_type)}</StrategyType>")
    # MapName: self-closing when empty matches original files
    if s.map_name:
        out.append(f"      <MapName>{escape(s.map_name)}</MapName>")
    else:
        out.append("      <MapName />")
    out.append(f"      <Commander>{escape(s.commander)}</Commander>")
    out.append(f"      <Reserved>{_b(s.reserved)}</Reserved>")
    out.append(f"      <AutoAI>{_b(s.auto_ai)}</AutoAI>")
    out.append(f"      <RallyPointMovementPopulationThreshold>{s.rally_point_movement_population_threshold}</RallyPointMovementPopulationThreshold>")
    out.append("    </Settings>")

    # Leader Powers
    for lp in table.leader_powers:
        out.append("    <LeaderPower>")
        out.append(f"      <LeaderPowerType>{escape(lp.power_type)}</LeaderPowerType>")
        if lp.target_type:
            out.append(f"      <TargetType>{escape(lp.target_type)}</TargetType>")
        for mid in lp.assigned_mission_ids:
            out.append(f"      <AssignedMissionID>{mid}</AssignedMissionID>")
        if lp.number_of_times_to_be_used is not None:
            out.append(f"      <NumberOfTimesToBeUsed>{lp.number_of_times_to_be_used}</NumberOfTimesToBeUsed>")
        if lp.minimum_heal_points_to_heal is not None:
            out.append(f"      <MinimumHealPointsToHeal>{lp.minimum_heal_points_to_heal}</MinimumHealPointsToHeal>")
        if lp.minimum_target_pop_to_cast is not None:
            out.append(f"      <MinimumTargetPopToCast>{lp.minimum_target_pop_to_cast}</MinimumTargetPopToCast>")
        out.append("    </LeaderPower>")

    # Directives — in document order
    for d in table.directives:
        if isinstance(d, BuildingDirective):
            _building(d, out)
        elif isinstance(d, TechDirective):
            _tech(d, out)
        elif isinstance(d, MissionDirective):
            _mission(d, out)

    out.append("  </Table>")
    out.append("</Tables>")
    return "\n".join(out) + "\n"