"""
core/validator.py
-----------------
Validates an AITable for structural and logical issues based on real HW2 AI behaviour.
Returns a list of ValidationIssue objects (severity: ERROR | WARNING | INFO).

All checks are derived from direct analysis of original and modded .ai files
and known HW2 AI system behaviour.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Set

from .models import (
    AITable, BuildingDirective, TechDirective, MissionDirective, LeaderPower
)
from .knowledge import (
    TURTLE_EXCLUSIVE_MECHANICS, RUSH_EXCLUSIVE_FLAGS,
    MIN_DEPOTS_BEFORE_TECH, MAX_HEAL_THRESHOLD, MAX_POP_THRESHOLD,
)


@dataclass
class ValidationIssue:
    severity: str   # "ERROR" | "WARNING" | "INFO"
    code: str
    message: str


def validate(table: AITable) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []

    def err(code: str, msg: str):
        issues.append(ValidationIssue("ERROR", code, msg))

    def warn(code: str, msg: str):
        issues.append(ValidationIssue("WARNING", code, msg))

    def info(code: str, msg: str):
        issues.append(ValidationIssue("INFO", code, msg))

    strategy = table.settings.strategy_type
    buildings = [d for d in table.directives if isinstance(d, BuildingDirective)]
    techs = [d for d in table.directives if isinstance(d, TechDirective)]
    missions = [d for d in table.directives if isinstance(d, MissionDirective)]

    # ----------------------------------------------------------------
    # SETTINGS
    # ----------------------------------------------------------------
    if not table.settings.faction:
        err("NO_FACTION",
            "Settings: Faction is empty. The game will not load this AI.")

    if not table.settings.commander:
        warn("NO_COMMANDER",
             "Settings: Commander is empty. This AI may not match any leader.")

    if not table.settings.strategy_type:
        err("NO_STRATEGY", "Settings: StrategyType is empty.")

    if table.settings.rally_point_movement_population_threshold < 5:
        warn("RALLY_THRESH_LOW",
             f"RallyPointMovementPopulationThreshold="
             f"{table.settings.rally_point_movement_population_threshold} is very low. "
             f"Units may march out before the economy is established.")

    if table.settings.auto_ai:
        info("AUTO_AI",
             "AutoAI=true — the game will override this file with auto-generated behaviour.")

    # ----------------------------------------------------------------
    # LEADER POWERS
    # ----------------------------------------------------------------
    lp_types: List[str] = [lp.power_type for lp in table.leader_powers]
    attack_mission_ids: Set[int] = {
        m.mission_id for m in missions
        if m.mission_id is not None and m.mission_type in ("Attack", "Defend")
    }

    for lp in table.leader_powers:
        if not lp.power_type:
            err("LP_NO_TYPE", "A LeaderPower entry has no LeaderPowerType.")
            continue

        if lp.number_of_times_to_be_used == 0:
            warn("LP_ZERO_USES",
                 f"LeaderPower '{lp.power_type}' has NumberOfTimesToBeUsed=0 — it will never fire.")

        if lp.minimum_heal_points_to_heal is not None:
            if lp.minimum_heal_points_to_heal > MAX_HEAL_THRESHOLD:
                warn("LP_HEAL_HIGH",
                     f"LeaderPower '{lp.power_type}' MinimumHealPointsToHeal="
                     f"{lp.minimum_heal_points_to_heal} is very high — power may rarely trigger.")
            # DeathEcho/DyingBreath should never have a heal threshold
            if any(k in lp.power_type for k in ("DeathEcho", "DyingBreath", "Echo")):
                warn("LP_DEATH_ECHO_HEAL",
                     f"LeaderPower '{lp.power_type}' has MinimumHealPointsToHeal set. "
                     f"DyingBreath/DeathEcho powers fire on unit death, not on HP deficit. "
                     f"This threshold will prevent the power from working as intended.")

        if lp.minimum_target_pop_to_cast is not None and lp.minimum_target_pop_to_cast > MAX_POP_THRESHOLD:
            warn("LP_POP_HIGH",
                 f"LeaderPower '{lp.power_type}' MinimumTargetPopToCast="
                 f"{lp.minimum_target_pop_to_cast} is very high — power may rarely trigger.")

        for mid in lp.assigned_mission_ids:
            if mid not in attack_mission_ids:
                info("LP_MISSION_MISSING",
                     f"LeaderPower '{lp.power_type}' is assigned to MissionID={mid} "
                     f"but no Attack/Defend mission with that ID exists. Power may never fire.")

    # ----------------------------------------------------------------
    # BUILDINGS
    # ----------------------------------------------------------------
    building_types = [b.building_type for b in buildings]

    for b in buildings:
        if not b.building_type:
            err("BLDG_NO_TYPE", "A Building directive has no BuildingType.")
            continue

        if b.number_of_building_type_needed < 1:
            warn("BLDG_ZERO_COUNT",
                 f"Building '{b.building_type}' NumberOfBuildingTypeNeeded < 1 — directive is ignored.")

        if b.prerequisite_obtained_object_count is not None and not b.prerequisite_obtained_object_type:
            err("PREREQ_COUNT_NO_TYPE",
                f"Building '{b.building_type}' has PrerequisiteObtainedObjectCount "
                f"but no PrerequisiteObtainedObjectType.")

        if b.prerequisite_sighting_object_count is not None and not b.prerequisite_sighting_object_type:
            err("SIGHT_COUNT_NO_TYPE",
                f"Building '{b.building_type}' has PrerequisiteSightingObjectCount "
                f"but no PrerequisiteSightingObjectType.")

        if b.recycle_building:
            info("RECYCLE_BUILDING",
                 f"Building '{b.building_type}' has RecycleBuilding=true. "
                 f"This is intentional in FastTech (recycles a reactor after factories are built).")

    # Eco check
    supply_buildings = [b for b in buildings if "supply" in b.building_type.lower()]
    if not supply_buildings:
        warn("NO_SUPPLY",
             "No supply depot buildings found. This AI will have no resource income.")

    # Factory check
    factories = [b for b in buildings if
                 "factory" in b.building_type.lower() or "barracks" in b.building_type.lower()]
    if not factories and strategy not in ("Turtle",):
        warn("NO_FACTORY",
             f"Strategy '{strategy}': no barracks/factory found. "
             f"AI cannot produce combat units.")

    # Rush-specific: barracks must be first building
    if strategy == "Rush" and buildings:
        first = buildings[0]
        if "barracks" not in first.building_type.lower():
            warn("RUSH_NO_BARRACKS_FIRST",
                 f"Rush strategy: first building is '{first.building_type}'. "
                 f"Rush REQUIRES a barracks as the very first directive to avoid delaying unit production.")

    # FastTech-specific: reactor must be first building
    if strategy == "FastTech" and buildings:
        first = buildings[0]
        if "reactor" not in first.building_type.lower():
            warn("FASTTECH_NO_REACTOR_FIRST",
                 f"FastTech strategy: first building is '{first.building_type}'. "
                 f"FastTech REQUIRES a reactor as the first directive — economy buildings come after.")

    # FastTech: check for RecycleBuilding
    if strategy == "FastTech":
        recycles = [b for b in buildings if b.recycle_building]
        if not recycles:
            info("FASTTECH_NO_RECYCLE",
                 "FastTech strategy: no RecycleBuilding=true found. "
                 "FastTech should recycle a reactor after 2 light factories are built to free a slot.")

    # Turtle: supply depot recycle check
    if strategy == "Turtle":
        depot_recycles = [b for b in buildings
                          if b.recycle_building and "supply" in b.building_type.lower()]
        if not depot_recycles:
            info("TURTLE_NO_DEPOT_RECYCLE",
                 "Turtle strategy: no supply depot RecycleBuilding found. "
                 "Turtle should recycle a supply depot once 3 turrets are built to free a slot.")

    # Boom: check 7 depots before reactor
    if strategy == "Boom":
        first_reactor_idx = next(
            (i for i, b in enumerate(buildings) if "reactor" in b.building_type.lower()), None
        )
        depot_count_before_reactor = 0
        if first_reactor_idx is not None:
            for b in buildings[:first_reactor_idx]:
                if "supply" in b.building_type.lower():
                    depot_count_before_reactor = max(
                        depot_count_before_reactor,
                        b.number_of_building_type_needed
                    )
            if depot_count_before_reactor < MIN_DEPOTS_BEFORE_TECH:
                warn("BOOM_REACTOR_TOO_EARLY",
                     f"Boom strategy: reactor appears before {MIN_DEPOTS_BEFORE_TECH}+ supply depots "
                     f"(found {depot_count_before_reactor}). "
                     f"Boom should delay tech until economy is secure.")

    # ----------------------------------------------------------------
    # TECH
    # ----------------------------------------------------------------
    for t in techs:
        if not t.tech_to_research:
            err("TECH_NO_NAME", "A Tech directive has no TechToResearch.")
            continue

        # Turtle structure techs used in non-Turtle strategy
        for struct_tech in ("global_structure_01", "global_structure_02", "global_structure_03"):
            if struct_tech in t.tech_to_research and strategy != "Turtle":
                warn("STRUCT_TECH_NON_TURTLE",
                     f"Tech '{t.tech_to_research}' is a structure-buff tech unique to Turtle strategy. "
                     f"Using it in '{strategy}' is unusual.")

    # ----------------------------------------------------------------
    # MISSIONS
    # ----------------------------------------------------------------
    forage_missions = [m for m in missions if m.mission_type == "Forage"]
    attack_missions = [m for m in missions if m.mission_type == "Attack"]
    reserve_missions = [m for m in missions if m.mission_type == "Reserves"]

    if not forage_missions and attack_missions:
        info("NO_FORAGE",
             "No Forage missions found. Early crate collection will be skipped — economy may suffer.")

    # Check for excessive mission count
    numbered_missions = [m for m in missions if m.mission_id is not None]
    mission_ids = [m.mission_id for m in numbered_missions]
    if len(mission_ids) > 5:
        info("MANY_MISSIONS",
             f"Found {len(mission_ids)} numbered missions. "
             f"Standard strategies use 3–5. Ensure they are intentional.")

    for m in missions:
        # Mission type check
        if m.mission_type not in ("Forage", "Scout", "BaseScout", "Attack", "Defend", "Reserves"):
            err("MISSION_BAD_TYPE",
                f"Mission has unknown MissionType='{m.mission_type}'.")

        # Attack/Defend missions need squads
        if m.mission_type in ("Attack", "Defend") and not m.squads:
            warn("MISSION_NO_SQUADS",
                 f"Mission (type={m.mission_type}, id={m.mission_id}) has no squads defined. "
                 f"The AI will stall waiting for units that never arrive.")

        # Squad min/max sanity
        for sq in m.squads:
            if sq.number_of_squads == 0:
                warn("SQUAD_ZERO_COUNT",
                     f"Squad '{sq.squad_type}' in {m.mission_type}[{m.mission_id}] "
                     f"requests 0 squads — no units will be assigned.")
            if (sq.minimum_number_of_squads is not None
                    and sq.minimum_number_of_squads > sq.number_of_squads):
                err("SQUAD_MIN_EXCEEDS_MAX",
                    f"Squad '{sq.squad_type}' in {m.mission_type}[{m.mission_id}]: "
                    f"MinimumNumberOfSquadsToSend ({sq.minimum_number_of_squads}) "
                    f"> NumberOfSquadsToSend ({sq.number_of_squads}). Mission will NEVER launch.")

        # FocusFireOnTarget outside Rush
        if m.focus_fire_on_target and strategy != "Rush":
            warn("FOCUS_FIRE_NON_RUSH",
                 f"FocusFireOnTarget=true on {m.mission_type}[{m.mission_id}]. "
                 f"This flag is Rush-exclusive in vanilla. "
                 f"On other strategies it slows map clearing by over-focusing on single targets.")

        # FocusFireOnTarget on non-Attack mission
        if m.focus_fire_on_target and m.mission_type != "Attack":
            warn("FOCUS_FIRE_NON_ATTACK",
                 f"FocusFireOnTarget=true on a {m.mission_type} mission has no effect.")

        # StreamReplaceSquads with no replace budget
        if m.stream_replace_squads and m.number_of_times_to_replace_squads == 0:
            info("STREAM_NO_REPLACE",
                 f"Mission {m.mission_type}[{m.mission_id}]: StreamReplaceSquads=true "
                 f"but NumberOfTimesToReplaceSquads=0. No restocking will occur.")

        # AssignReservesToMission=false outside Turtle
        if m.assign_reserves_to_mission is False and strategy != "Turtle":
            info("ASSIGN_RESERVES_FALSE",
                 f"Mission {m.mission_type}[{m.mission_id}]: AssignReservesToMission=false "
                 f"is a Turtle-exclusive pattern. Intentional for this strategy?")

        # InitializeAfterPreviousMissionsComplete outside Turtle
        if m.initialize_after_previous_missions_complete and strategy != "Turtle":
            warn("INIT_AFTER_PREV_NON_TURTLE",
                 f"Mission {m.mission_type}[{m.mission_id}]: InitializeAfterPreviousMissionsComplete "
                 f"is a Turtle-exclusive mechanic. Using it in '{strategy}' is unusual.")

        # Reserves with no sighting/obtained trigger
        if m.mission_type == "Reserves":
            has_prereq = any([
                m.prerequisite_sighting_object_type,
                m.prerequisite_obtained_object_type,
                m.prerequisite_tech,
                m.prerequisite_leader_power,
            ])
            if not has_prereq:
                warn("RESERVES_NO_TRIGGER",
                     f"Reserves mission[{m.mission_id}] has no prerequisite. "
                     f"It will activate immediately as unconditional standby forces.")

        # DeathEcho/DyingBreath: warn if heal threshold is set
        # (this check is in LP section above, but mission-side double check)

        # MapControl: warn if Scout mission has no TimeUntilSquadsAreReplaced
        if (strategy == "MapControl" and m.mission_type == "Scout"
                and m.time_until_squads_are_replaced is None):
            info("MAPCONTROL_SCOUT_NO_REPLACE_TIME",
                 "MapControl Scout mission has no TimeUntilSquadsAreReplaced. "
                 "The canonical MapControl Scout replaces squads every 30s to maintain map coverage.")

        # Rush: check that Jumppack Forage missions have DontTakeSquadsFromThisMission
        if strategy == "Rush" and m.mission_type == "Forage":
            has_jumppack = any("jumppack" in sq.squad_type.lower() for sq in m.squads)
            if has_jumppack and not m.dont_take_squads_from_this_mission:
                warn("RUSH_JUMPPACK_UNPROTECTED",
                     "Rush Jumppack Forage mission is missing DontTakeSquadsFromThisMission=true. "
                     "Attack missions will poach these Jumppacks, leaving no units for Forage.")

        # Missing TargetClosestObjectsToRandomEnemyFirst on Attack missions targeting bases
        if (m.mission_type == "Attack"
                and "_Base" in m.target_types
                and not m.target_closest_objects_to_random_enemy_first):
            info("ATTACK_NO_CLOSEST_RANDOM",
                 f"Attack mission[{m.mission_id}] targets bases but lacks "
                 f"TargetClosestObjectsToRandomEnemyFirst=true. "
                 f"Without this, the AI always targets in fixed list order.")

    # ----------------------------------------------------------------
    # CROSS-CUTTING CHECKS
    # ----------------------------------------------------------------

    # AA unit keywords — covers Gorgon (Covenant AA walker), Wolverine (UNSC AA tank),
    # and any modded unit with "aa" or "antiair" in its internal name.
    AA_KEYWORDS = ("gorgon", "wolverine", "antiair", "_aa_", "flak", "missile")

    def _is_aa_unit(squad_type: str) -> bool:
        low = squad_type.lower()
        return any(kw in low for kw in AA_KEYWORDS)

    has_aa_reserve = any(
        _is_aa_unit(sq.squad_type)
        for m in reserve_missions
        for sq in m.squads
        if m.prerequisite_sighting_object_type in ("_Air", "unsc_air_destroyer_01")
    )
    if not has_aa_reserve and attack_missions:
        info("NO_AA_RESERVE",
             "No AA unit (Gorgon, Wolverine, etc.) reserve triggered by air sighting. "
             "Add anti-air reserves vs _Air or unsc_air_destroyer_01 sighting.")

    # Hunter reserves vs vehicles
    has_vehicle_counter_reserve = any(
        m.prerequisite_sighting_object_type in ("_Vehicle",)
        and any("hunter" in sq.squad_type.lower() or "cyclops" in sq.squad_type.lower()
                for sq in m.squads)
        for m in reserve_missions
    )
    if not has_vehicle_counter_reserve and attack_missions:
        info("NO_VEHICLE_COUNTER",
             "No Hunter/anti-vehicle reserve triggered by vehicle sighting. "
             "Consider adding vehicle counter reserves for late-game defence.")

    # Scarab endgame without followers_2 gate
    has_scarab_mission = any(
        any("scarab" in sq.squad_type.lower() for sq in m.squads)
        for m in attack_missions
    )
    if has_scarab_mission:
        scarab_gated = any(
            any("scarab" in sq.squad_type.lower() for sq in m.squads)
            and m.prerequisite_tech and "followers_2" in m.prerequisite_tech
            for m in attack_missions
        )
        if not scarab_gated:
            info("SCARAB_NO_FOLLOWERS_GATE",
                 "Scarab attack mission found but it is not gated on cov_tech_followers_2 "
                 "(or equivalent population tech). The Scarab wave should only fire once the "
                 "AI can sustain the population cost.")

    # Alternate squad for Scarab missions
    for m in attack_missions:
        for sq in m.squads:
            if "scarab" in sq.squad_type.lower() and not sq.alternate_squad_types:
                info("SCARAB_NO_ALTERNATE",
                     f"Scarab squad in mission[{m.mission_id}] has no AlternateSquadTypeToSend. "
                     f"If no Scarab is available, the mission waits indefinitely. "
                     f"Add Wraith + Blisterback as alternates.")

    # Turtle specific checks
    if strategy == "Turtle":
        has_init_after = any(
            m.initialize_after_previous_missions_complete for m in missions
        )
        if not has_init_after:
            warn("TURTLE_NO_INIT_AFTER",
                 "Turtle strategy: no InitializeAfterPreviousMissionsComplete found. "
                 "Turtle's energy-point Defend should wait for Forage missions to complete first.")

        has_assign_false = any(
            m.assign_reserves_to_mission is False for m in missions
        )
        if not has_assign_false:
            info("TURTLE_NO_ASSIGN_RESERVES_FALSE",
                 "Turtle strategy: no AssignReservesToMission=false found. "
                 "Turtle uses this on harassment missions to keep the reserves pool full.")

        structure_techs = [t for t in techs if "global_structure" in t.tech_to_research]
        if not structure_techs:
            info("TURTLE_NO_STRUCT_TECH",
                 "Turtle strategy: no cov_tech_global_structure_01 found. "
                 "Turtle uses structure-buff techs to strengthen its fortifications.")

    return issues