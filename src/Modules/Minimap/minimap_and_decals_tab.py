import flet
from flet import (
    Column, Row, Text, TextField, Dropdown, dropdown,
    Button, Container, Tabs, Tab, Slider,
    SnackBar, Divider
)

# ------------------------------------------------------------
#  MINIMAP + DECALS BUILDER (Styled like Entity Builder)
# ------------------------------------------------------------

def minimap_and_decals_tab(page):
    from Modules.shared_styles_fix import TEAL, INPUT_BG, OUTPUT_BG

    # ---------------------------
    # Helper: Snackbar
    # ---------------------------
    def show_snack(msg, color="white"):
        page.snack_bar = SnackBar(Text(msg, color=color))
        page.snack_bar.open = True
        page.update()

    # ------------------------------------------------------------
    #  DROPDOWN DATA
    # ------------------------------------------------------------
    minimap_icon_types = [
        "conduits", "healing_spire", "prison", "particle_cannon", "teleporter",
        "spirit_dropship", "firefight_route", "firefight_supply_drop",
        "firefight_power_drop", "firefight_heal_drop", "firefight_veterancy_drop",
        "Firefight_Barricade", "Firefight_Nexus", "Firefight_Enemy_Spawn",
        "mini_base_slot", "Banished_mini_base", "unsc_mini_base", "unsc_unit_air",
        "rally_point", "vision_tower", "unsc_unit_infantry", "supply_crate",
        "power_crate", "capture_point_drop", "energy_core",
        "camera_other_player_directional", "banished_unit_infantry",
        "banished_unit_hero", "unsc_unit_hero", "banished_unit_air",
        "banished_unit_vehicle", "banished_unit_special", "unsc_unit_vehicle",
        "banished_base", "Stronghold_Base", "unsc_base", "capture_point_energy",
        "capture_point_supply", "capture_point_dominationA",
        "capture_point_dominationB", "capture_point_dominationC",
        "capture_point_dominationD", "capture_point_dominationE",
        "unsc_unit_special", "objective_primary", "base_slot",
        "objective_secondary", "ping_takedamage", "retriever_sentinel_leader"
    ]

    decal_names = [
        "Selection3D",
        "UNSCHero-VIP","UNSCHero-Rocket","UNSCHero-Melee","UNSCHero-Laser",
        "UNSCHero-Flame","UNSCHero-Bullets","UNSCHero-Johnson","UNSCHero-EnergySword",
        "UNSCHero-Hydra","UNSCHero-Plasma","UNSCHero-Railgun","UNSCHero-Ice",
        "BanishedHero-VIP","BanishedHero-Rocket","BanishedHero-Melee","BanishedHero-Laser",
        "BanishedHero-Flame","BanishedHero-Bullets","BanishedHero-Colony",
        "BanishedHero-EnergySword","BanishedHero-Hydra","BanishedHero-Plasma",
        "BanishedHero-Railgun","BanishedHero-Ice","BanishedHero-Needler",
        "BanishedHero-Unbreakable","BanishedHero-Corrupted",
        "Infantry","Vehicle","VehicleLarge","Air","AirLarge",
        "UNSC_BuildingPlot","UNSC_BuildingHQ","UNSC_BuildingMinibase",
        "UNSC_BuildingTurret","Banished_BuildingPlot","Banished_BuildingHQ",
        "Banished_BuildingMinibase","Banished_BuildingTurret",
        "LeaderPower_AOE_Large","LeaderPower_AOE_Medium","LeaderPower_AOE_Small",
        "LeaderPower_ArrowsDirectional","LeaderPower_Cone","LeaderPower_Drop",
        "LeaderPower_DropHQ","LeaderPower_PlanetaryCleansing","LeaderPower_Point",
        "LeaderPower_ArrowDirectional","LeaderPower_PincerBeam",
        "LeaderPower_ConduitOfRage_Large","LeaderPower_ConduitOfRage_Medium",
        "LeaderPower_ConduitOfRage_Small",
        "RosterModePlayInfantryCard","RosterModePlayVehicleCard",
        "RosterModePlayAirCard","RosterModePlayPowerCard",
    ]

    # ---------------------------
    # Output boxes (separate minimap and decals)
    # ---------------------------
    minimap_output = TextField(
        label="Minimap Generated XML",
        multiline=True,
        min_lines=6,
        max_lines=12,
        bgcolor=OUTPUT_BG,
        width=900
    )
    decals_output = TextField(
        label="Decal Generated XML",
        multiline=True,
        min_lines=6,
        max_lines=12,
        bgcolor=OUTPUT_BG,
        width=900
    )

    # ---------------------------
    # Minimap Entry UI
    # ---------------------------
    minimap_unit_key = TextField(label="Unit Key", bgcolor=INPUT_BG, width=400)
    minimap_icon_dropdown = Dropdown(
        label="Icon Type",
        options=[dropdown.Option(v) for v in minimap_icon_types],
        width=300
    )
    minimap_unknown_value = TextField(label="Unknown Value", value="1", bgcolor=INPUT_BG, width=200)

    def generate_minimap_xml(e):
        key = minimap_unit_key.value.strip()
        icon = minimap_icon_dropdown.value
        val3 = minimap_unknown_value.value.strip()

        if not key or not icon:
            show_snack("⚠️ Missing required fields!", "red")
            return

        xml = f"""<entry>
    <key>{key}</key>
    <value>{icon}</value>
    <value>{val3}</value>
</entry>"""
        minimap_output.value = xml
        page.update()
        show_snack("Minimap XML generated.", TEAL)
        try:
            from Modules.shared_outputs import outputs_registry
            outputs_registry["minimap"] = minimap_output.value
        except Exception:
            pass

    # ---------------------------
    # Decal Entry UI
    # Decal presets (name -> preset values)
    DECAL_PRESETS = {
        "Marine": {"name": "Infantry", "owner": "unsc_inf_marine_01", "SizeX": 6, "SizeZ": 6, "I1": 1, "I2": 2, "I3": 2},
        "Warthog": {"name": "Vehicle", "owner": "unsc_veh_warthog_01", "SizeX": 6, "SizeZ": 6, "I1": 1, "I2": 2, "I3": 2},
        "Scorpion": {"name": "Vehicle", "owner": "unsc_veh_scorpion_01", "SizeX": 8, "SizeZ": 8, "I1": 1, "I2": 2, "I3": 2},
        "Nightingale": {"name": "Air", "owner": "unsc_air_nightingale_01", "SizeX": 6, "SizeZ": 6, "I1": 1, "I2": 2, "I3": 2},
        "Hornet": {"name": "Air", "owner": "unsc_air_hornet_01", "SizeX": 6, "SizeZ": 6, "I1": 1, "I2": 2, "I3": 2},
        "Grunt": {"name": "Infantry", "owner": "cov_inf_grunt_01", "SizeX": 8, "SizeZ": 8, "I1": 1, "I2": 2, "I3": 2},
        "Ghost": {"name": "Vehicle", "owner": "cov_veh_ghost_01", "SizeX": 6, "SizeZ": 6, "I1": 1, "I2": 2, "I3": 2},
        "Wraith": {"name": "Vehicle", "owner": "cov_veh_wraith_01", "SizeX": 8, "SizeZ": 8, "I1": 1, "I2": 2, "I3": 2},
        "Engineer": {"name": "Infantry", "owner": "cov_inf_engineer_01", "SizeX": 6, "SizeZ": 6, "I1": 1, "I2": 2, "I3": 2},
        "Banshee": {"name": "Air", "owner": "cov_air_banshee_01", "SizeX": 6, "SizeZ": 6, "I1": 1, "I2": 2, "I3": 2},
        "Honor Guard": {"name": "BanishedHero-Melee", "owner": "cov_inf_eliteCommando_01", "SizeX": 6, "SizeZ": 6, "I1": 1, "I2": 2, "I3": 2},
        "Spartan": {"name": "UNSCHero-Bullets", "owner": "unsc_inf_spartan_01", "SizeX": 6, "SizeZ": 6, "I1": 1, "I2": 2, "I3": 2},
        "Condor": {"name": "AirLarge", "owner": "unsc_air_destroyer_01", "SizeX": 16, "SizeZ": 16, "I1": 1, "I2": 2, "I3": 2},
        "Scarab": {"name": "VehicleLarge", "owner": "cov_veh_scarab_01", "SizeX": 24, "SizeZ": 24, "I1": 1, "I2": 2, "I3": 2},
    }

    decal_preset_dropdown = Dropdown(
        label="Decal Presets",
        options=[dropdown.Option(k) for k in ("",) + tuple(DECAL_PRESETS.keys())],
        width=300
    )

    # ---------------------------
    decal_name_dropdown = Dropdown(
        label="Decal Name",
        options=[dropdown.Option(n) for n in decal_names],
        width=300
    )
    decal_size_x = Slider(label="SizeX", min=1, max=32, divisions=31, value=6)
    decal_size_z = Slider(label="SizeZ", min=1, max=32, divisions=31, value=6)
    decal_int1 = Slider(label="Intensity1", min=0, max=10, divisions=10, value=1)
    decal_int2 = Slider(label="Intensity2", min=0, max=10, divisions=10, value=2)
    decal_int3 = Slider(label="Intensity3", min=0, max=10, divisions=10, value=2)
    decal_owner = TextField(label="Owner", bgcolor=INPUT_BG, width=400)

    def generate_decal_xml(e):
        name = decal_name_dropdown.value
        owner = decal_owner.value.strip()

        if not name or not owner:
            show_snack("⚠️ Missing required fields!", "red")
            return

        xml = (
f"""<Icon type="uniticon" name="{name}" SizeX="{int(decal_size_x.value)}" """
f"""SizeZ="{int(decal_size_z.value)}" Intensity1="{int(decal_int1.value)}" """
f"""Intensity2="{int(decal_int2.value)}" Intensity3="{int(decal_int3.value)}" """
f"""owner="{owner}">-1</Icon>"""
        )
        decals_output.value = xml
        page.update()
        show_snack("Decal XML generated.", TEAL)
        try:
            from Modules.shared_outputs import outputs_registry
            outputs_registry["decals"] = decals_output.value
        except Exception:
            pass

    # ---------------------------
    # Apply preset when selected (via button)
    # ---------------------------
    def apply_decal_preset(e=None):
        try:
            sel = decal_preset_dropdown.value
            if not sel:
                return
            p = DECAL_PRESETS.get(sel)
            if not p:
                return
            decal_name_dropdown.value = p.get("name")
            decal_owner.value = p.get("owner")
            # clamp sizes to slider bounds to avoid Flet ValueError
            def _clamp_to_slider(val, slider):
                try:
                    mn = slider.min
                    mx = slider.max
                except Exception:
                    mn, mx = 1, 32
                try:
                    v = int(val)
                except Exception:
                    v = int(slider.value)
                if v < mn:
                    v = int(mn)
                if v > mx:
                    v = int(mx)
                return v

            decal_size_x.value = _clamp_to_slider(p.get("SizeX", decal_size_x.value), decal_size_x)
            decal_size_z.value = _clamp_to_slider(p.get("SizeZ", decal_size_z.value), decal_size_z)
            decal_int1.value = _clamp_to_slider(p.get("I1", decal_int1.value), decal_int1)
            decal_int2.value = _clamp_to_slider(p.get("I2", decal_int2.value), decal_int2)
            decal_int3.value = _clamp_to_slider(p.get("I3", decal_int3.value), decal_int3)
            page.update()
        except Exception:
            pass

    apply_decal_preset_btn = Button("Apply Preset", on_click=apply_decal_preset)

    # ---------------------------
    # Copy button
    # ---------------------------
    def copy_minimap(e):
        if not minimap_output.value.strip():
            show_snack("Nothing to copy — generate minimap XML first.", "red")
            return
        try:
            from Modules.shared_utils_fast import safe_set_clipboard
            safe_set_clipboard(page, minimap_output.value)
        except Exception:
            try:
                page.set_clipboard(minimap_output.value)
            except Exception:
                try:
                    page.clipboard = minimap_output.value
                except Exception:
                    pass
        show_snack("Minimap XML copied.", TEAL)

    def copy_decals(e):
        if not decals_output.value.strip():
            show_snack("Nothing to copy — generate decal XML first.", "red")
            return
        try:
            from Modules.shared_utils_fast import safe_set_clipboard
            safe_set_clipboard(page, decals_output.value)
        except Exception:
            try:
                page.set_clipboard(decals_output.value)
            except Exception:
                try:
                    page.clipboard = decals_output.value
                except Exception:
                    pass
        show_snack("Decal XML copied.", TEAL)

    copy_minimap_button = Button("Copy Minimap XML", on_click=copy_minimap)
    copy_decals_button = Button("Copy Decal XML", on_click=copy_decals)

    # ---------------------------
    # Reset button
    # ---------------------------
    def reset_fields(e):
        # Minimap
        minimap_unit_key.value = ""
        minimap_icon_dropdown.value = None
        minimap_unknown_value.value = "1"
        # Decal
        decal_name_dropdown.value = None
        decal_owner.value = ""
        decal_size_x.value = 6
        decal_size_z.value = 6
        decal_int1.value = 1
        decal_int2.value = 2
        decal_int3.value = 2
        # Output
        minimap_output.value = ""
        decals_output.value = ""
        page.update()
        show_snack("All fields reset.", TEAL)
        try:
            from Modules.shared_outputs import outputs_registry
            outputs_registry["minimap"] = ""
            outputs_registry["decals"] = ""
        except Exception:
            pass

    reset_button = Button("Reset", on_click=reset_fields)

    # ---------------------------
    # Assemble Tabs
    # ---------------------------
    minimap_tab = Column(
        [
            Text("Minimap Entry Builder", size=20, weight="bold"),
            minimap_unit_key,
            minimap_icon_dropdown,
            minimap_unknown_value,
            Button("Generate Minimap XML", on_click=generate_minimap_xml),
        ],
        spacing=12
    )

    decals_tab = Column(
        [
            Text("Decal Entry Builder", size=20, weight="bold"),
            Text("⚠️ This decal tag must go in BOTH decals_unsc.xml and decals_covenant.xml."),
            Row([decal_preset_dropdown, apply_decal_preset_btn], spacing=12),
            decal_name_dropdown,
            decal_owner,
            decal_size_x,
            decal_size_z,
            decal_int1,
            decal_int2,
            decal_int3,
            Button("Generate Decal XML", on_click=generate_decal_xml),
        ],
        spacing=12
    )

    output_tab = Column(
        [
            Text("Minimap Output", weight="bold"),
            minimap_output,
            Row([copy_minimap_button], spacing=12),
            Divider(),
            Text("Decals Output", weight="bold"),
            decals_output,
            Row([copy_decals_button, reset_button], spacing=12),
        ],
        spacing=10
    )

    # Replace Tabs with header buttons + content area
    tab_contents = [minimap_tab, decals_tab, output_tab]
    content_area = Column(expand=True)

    def switch_tab(i):
        content_area.controls.clear()
        content_area.controls.append(tab_contents[i])
        page.update()

    headers = Row([
        Button("Minimap Entry", on_click=lambda e: switch_tab(0)),
        Button("Decal Entry", on_click=lambda e: switch_tab(1)),
        Button("Output", on_click=lambda e: switch_tab(2)),
    ], spacing=8)

    switch_tab(0)

    content = Column(
        [
            Text("Minimap & Decal Builder", size=28, weight="bold"),
            headers,
            content_area
        ],
        expand=True,
        spacing=20
    )

    # expose both outputs for external tools (Packager) to read
    setattr(content, "minimap_output", minimap_output)
    setattr(content, "decals_output", decals_output)
    return content
