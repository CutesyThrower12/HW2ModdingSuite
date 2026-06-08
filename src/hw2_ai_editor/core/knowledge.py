"""
core/knowledge.py
-----------------
Full game-accurate HW2 AI strategy knowledge base.
Derived directly from analysis of original and modded .ai files.
Used by KnowledgePanel (UI), validator warnings, and wizard tooltips.
"""
from __future__ import annotations
from typing import Dict, List


# ============================================================
# STRATEGY DESCRIPTIONS, TIPS, AND MISTAKES
# ============================================================

STRATEGY_INFO: Dict[str, Dict] = {
    "Boom": {
        "tagline": "Economy-first snowball — build an overwhelming late-game force.",
        "description": (
            "Boom prioritises maximum resource infrastructure before any military production. "
            "The AI targets 7+ supply depots before placing a reactor or factory, running "
            "multiple Forage missions in parallel from turn one. Attack waves escalate through "
            "four phases: early infantry blob → mixed vehicle/infantry push → combined-arms "
            "with air support → Scarab/siege endgame. Reactive Reserves and sighting-triggered "
            "turrets guard against specific threats throughout."
        ),
        "common_mistakes": [
            "Building reactor or factory before 3+ supply depots → economy starvation before first army.",
            "RallyPointMovementPopulationThreshold too low → small squads march out prematurely.",
            "Assigning a healing/support power to no MissionIDs → it never fires in combat.",
            "Not gating Mission 4 behind cov_tech_followers_2 → Scarab wave arrives before eco supports it.",
            "FocusFireOnTarget on a Boom attack mission → slows map clearing, wastes time on turrets.",
            "Forgetting to add Gorgon reserves triggered by _Air sighting → AI has no AA response.",
            "Missing Hunter reserves vs _Vehicle sighting → late-game vehicle blobs go uncountered.",
        ],
        "tuning_tips": [
            "First Building: supplyDepot_01 × 3 (no prerequisites). Economy before everything.",
            "Forage missions: NumberOfTimesToRepeatMission=3 so they run but eventually free units.",
            "Gate the first expansion builder on PrerequisiteObtainedObjectCount of 3+ supply depots.",
            "Reactive turrets: sight×2 → 1 turret, sight×4 → 2, sight×8 → 3. Escalate per threat.",
            "FieldRecalibration/ShieldPower: MinimumHealPointsToHeal 16000 (Tier 1) → 20000 (Tier 3).",
            "DeathEcho/DyingBreath equivalent: no MinimumHealPointsToHeal — it fires on death naturally.",
            "Mission 2 minimum squads: at least 8 primary + 2 engineers to avoid premature launches.",
            "Endgame Scarab wave: AlternateSquadTypeToSend=Wraith + Blisterback as fallbacks.",
        ],
        "recommended_rally_threshold": 10,
    },

    "FastTech": {
        "tagline": "Skip economy, race to tech — strike before the enemy is ready.",
        "description": (
            "FastTech builds a reactor BEFORE supply depots, racing straight to high-tech units. "
            "The signature mechanic is RecycleBuilding=true on one reactor after 2 light factories "
            "are built, freeing a slot for economy. The primary attack is a large air force (Banshees "
            "or equivalent). Ground forces appear in later waves. Has 5 missions. "
            "The first expansion is gated on a Leader Power having been used (FieldRecalibration1 "
            "or equivalent healing power). DeathEcho/DyingBreath fires unlimited with no HP threshold."
        ),
        "common_mistakes": [
            "Forgetting RecycleBuilding=true on the reactor after factories are built → wastes a slot forever.",
            "Gating the first expansion on a power not yet unlocked → AI never expands.",
            "Mission 2 air wave MinimumNumberOfSquadsToSend below 6 → launches too early and gets crushed.",
            "Adding MinimumHealPointsToHeal to DeathEcho/DyingBreath → defeats the on-death trigger purpose.",
            "Missing Mission 1 entirely → no early Forage, no early pressure, full economy stall.",
            "Placing supplyDepots before the reactor → the entire strategy identity is lost.",
        ],
        "tuning_tips": [
            "FIRST directive: reactor_01. Then reactor_02. Supply depots come AFTER, not before.",
            "RecycleBuilding: prereq lightfactory_01 × 2. Recycles one reactor to free a slot.",
            "Mission 2 (air blob): 14 total, MinimumNumberOfSquadsToSend=6, gated on lightfactory × 1.",
            "First expansion (builder_01): use PrerequisiteLeaderPower=FieldRecalibration1 as the gate.",
            "DeathEcho/DyingBreath: NumberOfTimesToBeUsed=10000, NO MinimumHealPointsToHeal.",
            "Mission 3: mix air + ground vehicles. Mission 4: full combined-arms. Mission 5: siege endgame.",
            "DevastationSalvo/CleansingBeam tier 1: 1 use across all 5 missions (pop ≥ 20).",
        ],
        "recommended_rally_threshold": 10,
    },

    "MapControl": {
        "tagline": "Dominate the map with fast raiders before transitioning to a full army.",
        "description": (
            "MapControl uses fast raider units (Brute Choppers or equivalent) for both Forage AND "
            "combat from the very first turns, while aggressively expanding to multiple mini-bases. "
            "The central gating mechanic is a specific unit upgrade (cov_bruteChopper_upgrade4 in vanilla) "
            "that must be researched before the AI can build supplyDepot_02 or further outposts — "
            "this is the strategy's tempo lever. The persistent Scout mission (TimeUntilSquadsAreReplaced=30) "
            "is unique to MapControl. Has 5 missions."
        ),
        "common_mistakes": [
            "Forgetting PrerequisiteTech=<upgrade> on supplyDepot_02 and builder_01 → upgrade gate has no effect.",
            "Omitting TakeSquadsFromOtherMissions=true on BaseScout → scout can't pull from idle pool.",
            "Mission 2 MinimumNumberOfSquadsToSend below 7 → Chopper blob attacks too thin.",
            "Removing TimeUntilSquadsAreReplaced from the Scout mission → becomes a one-shot scout.",
            "Not protecting energy-point missions with DontTakeSquadsFromThisMission → army steals those units.",
            "Forgetting Grunt Forage missions alongside Chopper Forage → income is weak early.",
        ],
        "tuning_tips": [
            "Early Forage: mix cov_veh_brutechopper_01 (or raider) AND cov_inf_generic_grunt missions.",
            "BaseScout missions: TakeSquadsFromOtherMissions=true so they actually launch.",
            "Persistent Scout: TimeUntilSquadsAreReplaced=30, NumberOfTimesToReplaceSquads=1.",
            "Mission 2 (raider attack): 18 squads target, min 7, gated on reactor × 1.",
            "Upgrade gate (e.g. cov_bruteChopper_upgrade4): prereq ObtainedObjectCount of raider ≥ 6.",
            "Energy point defend: mix raiders + Grunts, DontTakeSquadsFromThisMission=true.",
            "Banshee reserves vs _Vehicle sighting (4–8 vehicles) complement mid-game ground forces.",
        ],
        "recommended_rally_threshold": 10,
    },

    "Rush": {
        "tagline": "Hit the enemy before they can build. Win fast or die trying.",
        "description": (
            "Rush places a barracks FIRST, then pushes assault infantry (Brute Jumppack or equivalent) "
            "with Forage missions that are protected using DontTakeSquadsFromThisMission=true. "
            "Mission 1 is the ONLY strategy that uses FocusFireOnTarget=true, concentrating fire "
            "on single targets. The first minibase is gated on a Leader Power having been used. "
            "Reactive turrets only fire against vehicles — the AI already has anti-infantry units. "
            "Vehicle-threat Grunt reserves use NumberOfTimesToReplaceSquads=1 (not -1 or 0). Has 5 missions."
        ),
        "common_mistakes": [
            "Building supply depots before the barracks → delayed first unit production, ruins Rush timing.",
            "Missing DontTakeSquadsFromThisMission=true on Jumppack Forage → units get poached for attacks.",
            "Removing FocusFireOnTarget from Mission 1 → units spread fire, take longer to destroy buildings.",
            "Mission 1 Grunt MinimumNumberOfSquadsToSend below 8 → wave launches before mass is built up.",
            "Gating _Minibase on a tech instead of a Leader Power → expansion decoupled from aggression timing.",
            "Vehicle reserves: NumberOfTimesToReplaceSquads=-1 → infinite restock drains entire army pool.",
        ],
        "tuning_tips": [
            "FIRST directive: cov_bldg_barracks_01 (or equivalent). No exceptions.",
            "Jumppack Forage: DontTakeSquadsFromThisMission=true, NumberOfTimesToRepeatMission=0 or 1.",
            "Mission 1: FocusFireOnTarget=true, Jumppack min 6, Grunt min 8, TakeSquadsFromOtherMissions=true.",
            "Vehicle-counter Grunt reserves: NumberOfTimesToReplaceSquads=1 (restocked once after loss).",
            "_Minibase: PrerequisiteLeaderPower=FieldRecalibration1 (or healing power tier 1).",
            "FieldRecalibration/ShieldPower tiers: 2 uses each on missions 1-3, HP 16000/18000/18000.",
            "DevastationSalvo/CleansingBeam: missions 1/2/3/5 only (skips mission 4) — this is intentional.",
        ],
        "recommended_rally_threshold": 10,
    },

    "Turtle": {
        "tagline": "Fortify everything. Build the ultimate siege engine. Then crush them.",
        "description": (
            "Turtle builds reactors and tech before any factory, placing turrets as soon as supply depots exist. "
            "The map Scout only unlocks after 2 turrets are built. A supply depot is RECYCLED "
            "(RecycleBuilding=true) once 3 turrets are up to free a slot. "
            "Only 3 missions: reactive Chopper intercepts vs specific sighted infantry (Mission 1), "
            "a base Defend mission (Mission 2), and the Scarab endgame push (Mission 3). "
            "UNIQUE mechanics: InitializeAfterPreviousMissionsComplete=true on the first energy-point Defend; "
            "AssignReservesToMission=false on energy harassment keeps reserves pool full; "
            "cov_tech_global_structure_01 has NO prerequisites — fires immediately. "
            "ALL late-game tech, fortifications, and expansion are gated on owning a Scarab."
        ),
        "common_mistakes": [
            "Placing factories before turrets → AI attacks prematurely without defense in place.",
            "Forgetting InitializeAfterPreviousMissionsComplete on the energy-point Defend → fires immediately.",
            "Missing AssignReservesToMission=false on harassment missions → reserves drain into them.",
            "Forgetting RecycleBuilding=true on the third supply depot → wastes a building slot.",
            "Not gating late fortifications on Scarab × 1 → AI spreads resources before the Scarab exists.",
            "Adding ShieldCrawlerDrop/SpiritGunship powers — Turtle does NOT use drop powers.",
            "Adding DeathEcho/DyingBreath — Turtle has NO equivalent of this power in vanilla.",
            "Lowering Scout prereq below turret × 2 — AI scouts before it can defend the scouted information.",
        ],
        "tuning_tips": [
            "Build order: supplyDepot × 2 → reactor_01 → reactor_02 → supplyDepot × 4 (BEFORE any factory).",
            "Turret gate: 1 turret @ depot×2, 2 turrets @ depot×3, 4 turrets @ depot×4.",
            "Scout: PrerequisiteObtainedObjectType=cov_bldg_turret_01, Count=2. Don't lower this.",
            "RecycleBuilding: supplyDepot_01, Count=3, prerequisite turret × 3.",
            "Mission 1 (Chopper intercepts): MissionID=1, target _Infantry, one entry per threat type.",
            "Mission 2 (Defend): TimeToWaitAtTarget=100, StreamReplaceSquads=true.",
            "FieldRecalibration1: 4 uses (Turtle-exclusive — more than any other strategy).",
            "DevastationSalvo1: PrerequisiteLeaderPower gate on builder_04. Gates fourth base expansion.",
            "Late Scarab gate: builder_02 × 3, turret × 7, shieldtower × 3, ALL upgrade techs.",
        ],
        "recommended_rally_threshold": 10,
    },
}


# ============================================================
# PHASE GUIDES
# ============================================================

STRATEGY_PHASE_GUIDE: Dict[str, List[Dict]] = {
    "Boom": [
        {"phase": "Phase 1 — Economy",    "description": "2× Forage → supplyDepot × 3 → 4× more Forage → supplyDepot × 7"},
        {"phase": "Phase 2 — Expansion",  "description": "BaseScout → builder_01 × 3 (prereq depot × 3) → Defend energy points"},
        {"phase": "Phase 3 — First Wave", "description": "Minibase → reactor → lightfactory → barracks → Mission 1 (Grunt blob, min 8)"},
        {"phase": "Phase 4 — Mid Game",   "description": "builder_03 → heavyfactory × 2 → Mission 2 (vehicle + infantry + air)"},
        {"phase": "Phase 5 — Endgame",    "description": "builder_02 × 3–4 → Mission 3 (Marauder+Air) → Mission 4 (Scarab, prereq followers_2)"},
    ],
    "FastTech": [
        {"phase": "Phase 1 — Reactor Rush",  "description": "reactor_01 → reactor_02 → supplyDepot × 2 → Defend energy → supplyDepot × 3"},
        {"phase": "Phase 2 — Factory",       "description": "lightfactory × 2 → RecycleBuilding reactor → supplyDepot × 4 → heavyfactory"},
        {"phase": "Phase 3 — Air Strike",    "description": "Mission 2 (14 air units, min 6) gated on lightfactory × 1"},
        {"phase": "Phase 4 — Ground",        "description": "Mission 3 (air + Marauder) → builder_01 × 2 (LP-gated) → builder_02 × 2"},
        {"phase": "Phase 5 — Endgame",       "description": "Mission 4 (full combined-arms) → Mission 5 (Scarab, prereq followers_2)"},
    ],
    "MapControl": [
        {"phase": "Phase 1 — Raiders",       "description": "Grunt+Chopper Forage × 3 → supplyDepot × 2-4 → BaseScout × 2"},
        {"phase": "Phase 2 — Chopper Wave",  "description": "Mission 2 (18 raiders, min 7) gated on reactor × 1"},
        {"phase": "Phase 3 — Upgrade Gate",  "description": "Research raider upgrade → gates supplyDepot_02 × 2 AND builder_01 × 2"},
        {"phase": "Phase 4 — Ground Force",  "description": "builder_03 → heavyfactory → Mission 3 (Marauder + Ranger)"},
        {"phase": "Phase 5 — Endgame",       "description": "Mission 4 (Wraith + Marauder + Blisterback) → Mission 5 (Scarab)"},
    ],
    "Rush": [
        {"phase": "Phase 1 — Barracks First", "description": "barracks → Jumppack Forage (DontTake=true) × 3 → supplyDepot × 2-3 → reactor"},
        {"phase": "Phase 2 — First Attack",   "description": "Mission 1 (FocusFireOnTarget, Jumppack min 6 + Grunt min 8, TakeFromOthers=true)"},
        {"phase": "Phase 3 — Follow-up",      "description": "reactor_02 → _Minibase (LP-gated) → builder_01 × 2 → lightfactory"},
        {"phase": "Phase 4 — Ground Army",    "description": "builder_03 → heavyfactory → Mission 3 (Marauder + Ranger)"},
        {"phase": "Phase 5 — Endgame",        "description": "builder_04 → Mission 4 (Wraith + Blisterback) → Mission 5 (Scarab)"},
    ],
    "Turtle": [
        {"phase": "Phase 1 — Fortify",        "description": "supplyDepot × 2 → reactor → reactor_02 → supplyDepot × 4 → Forage"},
        {"phase": "Phase 2 — Turrets",        "description": "Turret @ depot×2, ×2 @ depot×3, ×4 @ depot×4. Scout only after turret × 2."},
        {"phase": "Phase 3 — Tech",           "description": "RecycleBuilding depot, reactor × 2, builder_03, reactor_02 × 2, heavyfactory"},
        {"phase": "Phase 4 — Defense Fort",   "description": "builder_01 × 2, supplyDepot × 6, _Minibase, temple × 2, builder_02 × 2"},
        {"phase": "Phase 5 — Scarab Push",    "description": "Scarab × 1 gates ALL late tech + fortifications + Mission 3 endgame"},
    ],
}


# ============================================================
# FIELD TOOLTIPS
# ============================================================

FIELD_TOOLTIPS: Dict[str, str] = {
    # Settings
    "Faction":           "Faction string (Covenant, UNSC, Banished, custom).",
    "GameMode":          "Always 'Deathmatch' for skirmish AI files.",
    "StrategyType":      "Archetype: Boom, FastTech, MapControl, Rush, or Turtle.",
    "Commander":         "Leader internal name — must match exactly (e.g. Atriox).",
    "MapName":           "Optional map filter. Leave blank for all maps.",
    "RallyPointMovementPopulationThreshold":
                         "Pop count before units move to rally. Default 10. Lower = more aggressive.",
    "AutoAI":            "If true, game overrides this file with auto-generated behaviour.",
    "Reserved":          "Reserved slot flag. Always false for active AI files.",

    # Leader Power
    "LeaderPowerType":   "Internal power code name — must match game string exactly.",
    "TargetType":        "_Unit (friendly), _Enemy, _Base, _Settlement, etc.",
    "AssignedMissionID": "Power fires only when this mission is active with units in combat.",
    "NumberOfTimesToBeUsed":
                         "Times the AI may use this power. 10000 = unlimited.",
    "MinimumHealPointsToHeal":
                         "Healing powers: min HP deficit before firing. 16000–20000 typical.\n"
                         "DyingBreath/DeathEcho: do NOT set this — fires on death, not HP.",
    "MinimumTargetPopToCast":
                         "Offensive powers: min enemy pop in range before firing.\n"
                         "20 = moderate group, 30 = large group, 35 = very large.",

    # Building
    "BuildingType":      "Internal building code (e.g. cov_bldg_supplyDepot_01, _Minibase).",
    "NumberOfBuildingTypeNeeded":
                         "Target total count of this building. AI builds until it owns this many.",
    "ProductionLocationType":
                         "Force construction at a specific location (e.g. _Minibase). Optional.",
    "RecycleBuilding":   "Sell an existing building before placing this one.\n"
                         "FastTech: recycles a reactor after 2 light factories are built.",
    "PrerequisiteObtainedObjectType":
                         "Must OWN this many of this type before directive activates.\n"
                         "Accepts buildings, units, or wildcards (_Vehicle, _Infantry, _Air).",
    "PrerequisiteObtainedObjectCount":
                         "Count threshold for PrerequisiteObtainedObjectType.",
    "PrerequisiteSightingObjectType":
                         "Must have SIGHTED this many enemy units/buildings before activating.\n"
                         "Used for reactive turrets and reserve triggers.",
    "PrerequisiteSightingObjectCount":
                         "Count threshold for PrerequisiteSightingObjectType.",
    "PrerequisiteTech":  "Must have researched this tech before directive activates.",
    "PrerequisiteLeaderPower":
                         "Must have USED this leader power before directive activates.\n"
                         "FastTech/Rush: gates first expansion on a healing power.",

    # Tech
    "TechToResearch":    "Internal tech upgrade code (e.g. cov_grunt_upgrade1).",

    # Mission
    "MissionType":       "Forage: collect crates.  Scout: patrol locations.\n"
                         "Attack: assault.  Defend: guard.  Reserves: standby until triggered.",
    "MissionID":         "Links this mission to LeaderPower AssignedMissionID entries.",
    "TargetType":        "What to target: _Base, _Settlement, hook_bldg_EnergyCapturePoint_01,\n"
                         "_Infantry, _Vehicle, _Air, etc.",
    "TargetBaseType":    "Refines base targets: Start (main), Expansion, Mini.",
    "NumberOfTimesToRepeatMission":
                         "-1 = infinite.  0 = run once.  N = repeat N times.",
    "NumberOfTimesToReplaceSquads":
                         "-1 = unlimited restock.  0 = no restock.  1 = restock once.",
    "TimeToWaitAtTarget":
                         "Seconds units linger at target. BaseScout=8, energy points=10.",
    "TimeUntilSquadsAreReplaced":
                         "Seconds before squads are replaced mid-mission.\n"
                         "MapControl Scout: 30s keeps fresh scouts patrolling.",
    "FocusFireOnTarget": "All units focus fire on one target. RUSH MISSION 1 ONLY.",
    "SkipTargetIfPreviousTargetExists":
                         "Skip to next target if the previous one still exists.\n"
                         "Use to attack expansion first, then fall back to main base.",
    "TargetClosestObjectsToRandomEnemyFirst":
                         "Target the object closest to a random enemy base.\n"
                         "Makes attacks less predictable than fixed-list order.",
    "TakeSquadsFromOtherMissions":
                         "This mission can pull units from lower-priority missions.",
    "DontTakeSquadsFromThisMission":
                         "Protect this mission's units from being poached by others.\n"
                         "Critical for Forage runners and persistent Scout missions.",
    "ReturnToRallyPoint":
                         "Units return to rally point after mission completes.",
    "InitializeAfterPreviousMissionsComplete":
                         "Wait for ALL prior missions to finish before starting.\n"
                         "TURTLE EXCLUSIVE — used on the energy-point Defend mission.",
    "AssignReservesToMission":
                         "False: reserves are never auto-assigned here.\n"
                         "TURTLE EXCLUSIVE — keeps the defence pool full.",
    "StreamReplaceSquads":
                         "Send replacement units as produced rather than waiting for a full batch.",
}



# ============================================================
# VALIDATION KNOWLEDGE (used by validator.py for specific checks)
# ============================================================

# Flags that are Turtle-exclusive — warn if used in other strategies
TURTLE_EXCLUSIVE_MECHANICS = {
    "InitializeAfterPreviousMissionsComplete",
    "AssignReservesToMission",
    "cov_tech_global_structure_01",
    "cov_tech_global_structure_02",
    "cov_tech_global_structure_03",
}

# Flag that is Rush-exclusive — warn if used in other strategies
RUSH_EXCLUSIVE_FLAGS = {
    "FocusFireOnTarget",
}

# Recommended minimum supply depot count before first reactor (Boom/MapControl)
MIN_DEPOTS_BEFORE_TECH = 3

# Maximum reasonable heal threshold for healing powers
MAX_HEAL_THRESHOLD = 25000

# Maximum reasonable pop threshold for offensive powers
MAX_POP_THRESHOLD = 50