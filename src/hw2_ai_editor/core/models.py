from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class AISettings:
    faction: str = ""
    game_mode: str = "Deathmatch"
    strategy_type: str = "Boom"
    commander: str = ""
    map_name: str = ""
    rally_point_movement_population_threshold: int = 10
    reserved: bool = False
    auto_ai: bool = False


@dataclass
class LeaderPower:
    power_type: str = ""
    target_type: Optional[str] = None
    assigned_mission_ids: List[int] = field(default_factory=list)
    number_of_times_to_be_used: Optional[int] = None
    minimum_heal_points_to_heal: Optional[int] = None
    minimum_target_pop_to_cast: Optional[int] = None


@dataclass
class SquadEntry:
    squad_type: str = ""
    number_of_squads: int = 1
    minimum_number_of_squads: Optional[int] = None
    alternate_squad_types: List[str] = field(default_factory=list)


@dataclass
class BuildingDirective:
    building_type: str = ""
    number_of_building_type_needed: int = 1
    production_location_type: Optional[str] = None
    recycle_building: bool = False
    prerequisite_obtained_object_type: Optional[str] = None
    prerequisite_obtained_object_count: Optional[int] = None
    prerequisite_sighting_object_type: Optional[str] = None
    prerequisite_sighting_object_count: Optional[int] = None
    prerequisite_tech: Optional[str] = None
    prerequisite_leader_power: Optional[str] = None


@dataclass
class TechDirective:
    tech_to_research: str = ""
    prerequisite_obtained_object_type: Optional[str] = None
    prerequisite_obtained_object_count: Optional[int] = None
    prerequisite_sighting_object_type: Optional[str] = None
    prerequisite_sighting_object_count: Optional[int] = None
    prerequisite_tech: Optional[str] = None
    prerequisite_leader_power: Optional[str] = None


@dataclass
class MissionDirective:
    mission_type: str = "Attack"
    mission_id: Optional[int] = None
    target_types: List[str] = field(default_factory=list)
    target_base_types: List[str] = field(default_factory=list)
    # -1 = infinite, 0 = run once, N = repeat N times
    number_of_times_to_repeat_mission: int = -1
    # -1 = unlimited restock, 0 = no restock, N = restock N times
    number_of_times_to_replace_squads: int = 0
    time_to_wait_at_target: Optional[int] = None
    time_until_squads_are_replaced: Optional[int] = None
    focus_fire_on_target: bool = False
    stream_replace_squads: bool = False
    take_squads_from_other_missions: bool = False
    dont_take_squads_from_this_mission: bool = False
    return_to_rally_point: bool = False
    target_closest_objects_to_random_enemy_first: bool = False
    skip_target_if_previous_target_exists: bool = False
    initialize_after_previous_missions_complete: bool = False
    # None = field omitted entirely (not written to XML)
    assign_reserves_to_mission: Optional[bool] = None
    prerequisite_obtained_object_type: Optional[str] = None
    prerequisite_obtained_object_count: Optional[int] = None
    prerequisite_sighting_object_type: Optional[str] = None
    prerequisite_sighting_object_count: Optional[int] = None
    prerequisite_tech: Optional[str] = None
    prerequisite_leader_power: Optional[str] = None
    squads: List[SquadEntry] = field(default_factory=list)


@dataclass
class AITable:
    settings: AISettings = field(default_factory=AISettings)
    leader_powers: List[LeaderPower] = field(default_factory=list)
    # Mixed list of BuildingDirective | TechDirective | MissionDirective
    # Preserved in document order — this is critical for HW2 AI behaviour.
    directives: List = field(default_factory=list)