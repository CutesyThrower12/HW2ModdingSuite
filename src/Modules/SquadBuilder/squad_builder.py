import os
import json
import sys
from flet import (
    Column,
    Row,
    Text,
    TextField,
    Button,
    Dropdown,
    dropdown,
    Checkbox,
    Divider,
    ListView,
    Tabs,
    Tab,
    Slider,
    Container,
    IconButton,
    icons,
    SnackBar,
)

# -------------------------------------------------------
# LOAD LIBRARIES
# -------------------------------------------------------
def load_library(filename):
    if hasattr(sys, "_MEIPASS"):
        path = os.path.join(sys._MEIPASS, "Modules", "Library", filename)
    else:
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Library", filename)
    with open(path, "r") as f:
        return json.load(f)

parents_library = load_library("parents.json")
counters_library = load_library("counters.json")
try:
    abilities_library = load_library("abilities.json")
except Exception:
    abilities_library = []

# -------------------------------------------------------
# Helper: build XML
# -------------------------------------------------------
def build_squad_xml(
    squad_name,
    is_infantry,
    formation,
    use_parent,
    parent_element,
    build_points,
    costs,
    pop_type,
    pop_value,
    units,
    flags,
    counters,
    adv,
    include_legacy_fields=False,
    leader_dies_last=False
):
    formation_attr = f' formationType="{formation}"' if is_infantry else ""
    combat_rank = adv.get("CombatRank", "10")
    subselect = adv.get("SubSelectSort", "70")
    ai_attack_rank = adv.get("AIAttackRank", "1.5")

    portrait = adv.get("PortraitIcon", "")
    minimap_scale = adv.get("MinimapScale", "")
    display_id = adv.get("DisplayNameID", "")
    rollover_id = adv.get("RolloverTextID", "")
    stats_id = adv.get("StatsNameID", "")
    role_id = adv.get("RoleTextID", "")
    minimap_icon = adv.get("MinimapIcon", "")
    minimap_icon_size = adv.get("MinimapIconSize", "")

    heal_value = adv.get("HealValue", "")

    if not use_parent:
        cost_xml = "".join(f'\t<Cost ResourceType="{c["type"]}">{c["value"]}</Cost>\n' for c in costs)
        unit_xml = "<Units>\n" + "".join(f'\t\t<Unit count="{u["count"]}" role="{u["role"]}">{u["name"]}</Unit>\n' for u in units) + "\t</Units>\n"
        flag_xml = "".join(f"\t<Flag>{f}</Flag>\n" for f in flags)
        pop_xml = f"\t<Pop Type=\"{pop_type}\">{pop_value}</Pop>\n" if pop_type else ""
        counters_xml = "".join(f"\t<Counters>{c}</Counters>\n" for c in counters)

        xml_parts = [
            f'<Squad name="{squad_name}" dbid="00000000000000000000"{formation_attr}>',
            f'\t<CombatRank>{combat_rank}</CombatRank>',
            f'\t<SubSelectSort>{subselect}</SubSelectSort>',
            f'\t<AIAttackRank>{ai_attack_rank}</AIAttackRank>',
        ]
        # include HealValue only when provided (non-empty)
        try:
            if str(heal_value).strip() != "":
                xml_parts.append(f'\t<HealValue>{heal_value}</HealValue>')
        except Exception:
            pass

        if include_legacy_fields:
            xml_parts.extend([
                f'\t<PortraitIcon>{portrait}</PortraitIcon>',
                f'\t<MinimapScale>{minimap_scale}</MinimapScale>',
                f'\t<DisplayNameID>{display_id}</DisplayNameID>',
                f'\t<RolloverTextID>{rollover_id}</RolloverTextID>',
                f'\t<StatsNameID>{stats_id}</StatsNameID>',
                f'\t<RoleTextID>{role_id}</RoleTextID>',
                f'\t<MinimapIcon size="{minimap_icon_size}">{minimap_icon}</MinimapIcon>',
            ])

        xml_parts.append(f'\t<BuildPoints>{build_points}</BuildPoints>')
        # include global LeaderDiesLast between Units and Flags when requested
        leader_xml = "\t<LeaderDiesLast />\n" if leader_dies_last else ""
        return "\n".join(xml_parts) + "\n" + cost_xml + pop_xml + unit_xml + leader_xml + flag_xml + counters_xml + "</Squad>"

    else:
        cost_xml = "".join(f'\t<Cost ResourceType="{c["type"]}">{c["value"]}</Cost>\n' for c in costs)
        unit_xml = '<Units override_type="absolute">\n' + "".join(f'\t\t<Unit count="{u["count"]}" role="{u["role"]}">{u["name"]}</Unit>\n' for u in units) + "\t</Units>\n"
        flag_xml = "".join(f"\t<Flag>{f}</Flag>\n" for f in flags)
        pop_xml = f"\t<Pop Type=\"{pop_type}\">{pop_value}</Pop>\n" if pop_type else ""
        counters_xml = "".join(f"\t<Counters>{c}</Counters>\n" for c in counters)

        xml_parts = [
            f'<Squad name="{squad_name}" dbid="00000000000000000000"{formation_attr} parent_element="{parent_element}">',
            f'\t<CombatRank>{combat_rank}</CombatRank>',
            f'\t<SubSelectSort>{subselect}</SubSelectSort>',
            f'\t<AIAttackRank>{ai_attack_rank}</AIAttackRank>',
        ]
        try:
            if str(heal_value).strip() != "":
                xml_parts.append(f'\t<HealValue>{heal_value}</HealValue>')
        except Exception:
            pass
        xml_parts.append(f'\t<BuildPoints>{build_points}</BuildPoints>')
        leader_xml = "\t<LeaderDiesLast />\n" if leader_dies_last else ""

        return "\n".join(xml_parts) + "\n" + cost_xml + pop_xml + unit_xml + leader_xml + flag_xml + counters_xml + "</Squad>"

# -------------------------------------------------------
# Squad Builder Tab
# -------------------------------------------------------
def squad_builder_tab(page):
    TEAL = "#a0cafd"
    GRAY = "#2b2b2b"

    # ----------------------- General -----------------------
    squad_name = TextField(label="Squad Name", hint_text="unsc_inf_marine_01", bgcolor=GRAY, width=400)
    is_infantry = Checkbox(label="Is Infantry", value=True)
    formation_dropdown = Dropdown(label="Formation Type", options=[dropdown.DropdownOption("Flock"), dropdown.DropdownOption("Line")], value="Flock", width=200)

    def toggle_formation(e):
        formation_dropdown.visible = is_infantry.value
        page.update()
    is_infantry.on_change = toggle_formation
    toggle_formation(None)

    use_parent = Checkbox(label="Use Parent Element")
    parent_element = TextField(label="Parent Element", bgcolor=GRAY, width=400)
    build_points = TextField(label="Build Points (seconds)", bgcolor=GRAY, width=200, value="17")

    # ----------------------- Units -----------------------
    unit_rows = []
    units_container = Column()
    def add_unit_row(e=None):
        name_field = TextField(label="Unit Name", bgcolor=GRAY, width=350)
        count_field = TextField(label="Count", value="1", width=80, bgcolor=GRAY)
        role_field = Dropdown(label="Role", width=120, options=[dropdown.DropdownOption("normal"), dropdown.DropdownOption("leader")], value="normal")
        units_container.controls.append(Row([name_field, count_field, role_field]))
        unit_rows.append({"name": name_field, "count": count_field, "role": role_field})
        page.update()
    add_unit_row()

    # ----------------------- Costs -----------------------
    cost_rows = []
    costs_container = Column()
    def add_cost_row(e=None):
        cost_type = Dropdown(width=160, options=[dropdown.DropdownOption("Supplies"), dropdown.DropdownOption("Power"), dropdown.DropdownOption("HQLevel")], value="Supplies")
        cost_value = TextField(width=100, bgcolor=GRAY, value="0")
        entry = {"type": cost_type, "value": cost_value}
        # create row, then add a remove button that knows this row/entry
        row = Row([cost_type, cost_value])
        # store UI row in entry so other code can remove/update it
        entry["row"] = row
        def remove_cost(e, row=row, entry=entry):
            try:
                cost_rows.remove(entry)
            except ValueError:
                pass
            try:
                costs_container.controls.remove(row)
            except ValueError:
                pass
            page.update()
        remove_btn = Button("Remove", on_click=remove_cost)
        row.controls.append(remove_btn)
        cost_rows.append(entry)
        costs_container.controls.append(row)
        page.update()
    add_cost_row()

    pop_type_dropdown = Dropdown(label="Pop Type", width=160, options=[dropdown.DropdownOption("Unit"), dropdown.DropdownOption("Spartan"), dropdown.DropdownOption("HonorGuard"), dropdown.DropdownOption("Custom")], value="Unit")
    pop_custom_type = TextField(label="Custom Pop Type", bgcolor=GRAY, width=160, visible=False)
    pop_value_field = TextField(label="Pop Count", value="1", width=80, bgcolor=GRAY)
    def pop_type_changed(e):
        pop_custom_type.visible = (pop_type_dropdown.value == "Custom")
        page.update()
    pop_type_dropdown.on_change = pop_type_changed
    pop_type_changed(None)

    # ----------------------- Flags -----------------------
    FLAG_LIST = ["Repairable", "Chatter", "KBAware", "AlwaysRenderSelectionDecal"]
    flag_checkboxes = [Checkbox(label=f) for f in FLAG_LIST]
    xyz_flags = Checkbox(label="Enable XYZ Modded Flags")

    # ----------------------- Advanced -----------------------
    adv_fields = {
        "CombatRank": TextField(label="CombatRank", value="10", bgcolor=GRAY),
        "SubSelectSort": TextField(label="SubSelectSort", value="70", bgcolor=GRAY),
        "AIAttackRank": TextField(label="AIAttackRank", value="1.5", bgcolor=GRAY),
        "HealValue": TextField(label="HealValue", value="", bgcolor=GRAY),
        "PortraitIcon": TextField(label="PortraitIcon", value="ui\\flash\\HUD\\hud_menu\\hud_menu_icons\\final_unsc\\inf_marine", bgcolor=GRAY),
        "MinimapScale": TextField(label="MinimapScale", value="1", bgcolor=GRAY),
        "DisplayNameID": TextField(label="DisplayNameID", value="3000", bgcolor=GRAY),
        "RolloverTextID": TextField(label="RolloverTextID", value="3001", bgcolor=GRAY),
        "StatsNameID": TextField("StatsNameID", value="25679", bgcolor=GRAY) if False else TextField(label="StatsNameID", value="25679", bgcolor=GRAY),
        "RoleTextID": TextField(label="RoleTextID", value="500", bgcolor=GRAY),
        "MinimapIcon": TextField(label="MinimapIcon", value="Circle", bgcolor=GRAY),
        "MinimapIconSize": TextField(label="MinimapIcon Size", value="8", bgcolor=GRAY),
    }
    legacy_controls = [adv_fields["PortraitIcon"], adv_fields["MinimapScale"], adv_fields["DisplayNameID"], adv_fields["RolloverTextID"], adv_fields["StatsNameID"], adv_fields["RoleTextID"], adv_fields["MinimapIcon"], adv_fields["MinimapIconSize"]]
    show_legacy_checkbox = Checkbox(label="Show legacy HW1 fields (PortraitIcon, Minimap, IDs...)", value=True)
    def show_legacy_changed(e):
        legacy_visible = (not use_parent.value) and show_legacy_checkbox.value
        for ctl in legacy_controls:
            ctl.visible = legacy_visible
        page.update()
    show_legacy_checkbox.on_change = show_legacy_changed
    show_legacy_changed(None)

    # ----------------------- Advanced Presets -----------------------
    SQUAD_ADV_PRESET_NAMES = [
        "Marine","Warthog","Scorpion","Nightingale","Hornet","Grunt",
        "Ghost","Wraith","Engineer","Banshee","Honor Guard","Spartan",
        "Condor","Scarab"
    ]

    SQUAD_ADV_PRESETS = {
        "Marine": {"CombatRank": "3", "SubSelectSort": "600", "AIAttackRank": "1.5", "BuildPoints": "18"},
        "Warthog": {"CombatRank": "6", "SubSelectSort": "699", "AIAttackRank": "3.5", "BuildPoints": "20"},
        "Scorpion": {"CombatRank": "7", "SubSelectSort": "500", "AIAttackRank": "10", "HealValue": "1.75", "BuildPoints": "38"},
        "Nightingale": {"CombatRank": "2", "SubSelectSort": "300", "AIAttackRank": "0", "HealValue": "1.70000005", "BuildPoints": "20"},
        "Hornet": {"CombatRank": "6", "SubSelectSort": "1600", "AIAttackRank": "3.5", "BuildPoints": "22"},
        "Grunt": {"CombatRank": "3", "SubSelectSort": "1005", "AIAttackRank": "1", "BuildPoints": "13"},
        "Ghost": {"CombatRank": "2", "SubSelectSort": "705", "AIAttackRank": "2.20000005", "BuildPoints": "26"},
        "Wraith": {"CombatRank": "7", "SubSelectSort": "505", "AIAttackRank": "7", "HealValue": "1.75", "BuildPoints": "31"},
        "Engineer": {"CombatRank": "0", "SubSelectSort": "305", "AIAttackRank": "0", "HealValue": "1.75", "BuildPoints": "20"},
        "Banshee": {"CombatRank": "6", "SubSelectSort": "1705", "AIAttackRank": "3.5", "BuildPoints": "18"},
        "Honor Guard": {"CombatRank": "9", "SubSelectSort": "15", "AIAttackRank": "10", "HealValue": "1.29999995", "BuildPoints": "45"},
        "Spartan": {"CombatRank": "10", "SubSelectSort": "10", "AIAttackRank": "10", "HealValue": "1.29999995", "BuildPoints": "45"},
        "Condor": {"CombatRank": "6", "SubSelectSort": "100", "AIAttackRank": "35", "HealValue": "4.5", "BuildPoints": "120"},
        "Scarab": {"CombatRank": "10", "SubSelectSort": "95", "AIAttackRank": "30", "HealValue": "4.5", "BuildPoints": "120"},
    }

    # ----------------------- Cost Presets -----------------------
    SQUAD_COST_PRESET_NAMES = [
        "Marine","Warthog","Scorpion","Nightingale","Hornet","Grunt",
        "Ghost","Wraith","Engineer","Banshee","Honor Guard","Spartan",
        "Condor","Scarab"
    ]

    SQUAD_COST_PRESETS = {
        "Marine": {"Supplies": 150, "Power": None, "HQLevel": 0},
        "Warthog": {"Supplies": 250, "Power": None, "HQLevel": 2},
        "Scorpion": {"Supplies": 550, "Power": 90, "HQLevel": 3},
        "Nightingale": {"Supplies": 350, "Power": 50, "HQLevel": 2},
        "Hornet": {"Supplies": 300, "Power": 0, "HQLevel": 2},
        "Grunt": {"Supplies": 100, "Power": None, "HQLevel": 0},
        "Ghost": {"Supplies": 230, "Power": 15, "HQLevel": 1},
        "Wraith": {"Supplies": 550, "Power": 75, "HQLevel": 3},
        "Engineer": {"Supplies": 200, "Power": 30, "HQLevel": 1},
        "Banshee": {"Supplies": 250, "Power": 0, "HQLevel": 2},
        "Honor Guard": {"Supplies": 300, "Power": 275, "HQLevel": 1},
        "Spartan": {"Supplies": 300, "Power": 275, "HQLevel": 1},
        "Condor": {"Supplies": 2000, "Power": 2000, "HQLevel": 3},
        "Scarab": {"Supplies": 2000, "Power": 2000, "HQLevel": 3},
    }

    cost_preset_dropdown = Dropdown(label="Cost Preset", options=[dropdown.DropdownOption(n) for n in SQUAD_COST_PRESET_NAMES], value=None, width=300)

    def apply_cost_preset(e=None):
        try:
            name = cost_preset_dropdown.value
            if not name:
                return
            data = SQUAD_COST_PRESETS.get(name, {})
            if not data:
                return
            # For each cost type, either set/update or remove if N/A/None
            for t in ["Supplies", "Power", "HQLevel"]:
                v = data.get(t)
                # remove existing entries of this type if preset says N/A/None
                if v is None or (isinstance(v, str) and str(v).upper() == "N/A"):
                    for entry in list(cost_rows):
                        try:
                            if entry["type"].value == t:
                                # remove UI row and entry
                                try:
                                    costs_container.controls.remove(entry.get("row"))
                                except Exception:
                                    pass
                                try:
                                    cost_rows.remove(entry)
                                except Exception:
                                    pass
                        except Exception:
                            pass
                else:
                    # set existing value if present
                    found = False
                    for entry in cost_rows:
                        try:
                            if entry["type"].value == t:
                                entry["value"].value = str(v)
                                found = True
                                break
                        except Exception:
                            pass
                    # if not found, create a new cost row and set values
                    if not found:
                        add_cost_row()
                        entry = cost_rows[-1]
                        try:
                            entry["type"].value = t
                            entry["value"].value = str(v)
                        except Exception:
                            pass
            page.update()
        except Exception:
            pass

    apply_cost_preset_btn = Button("Apply Preset", on_click=apply_cost_preset)

    adv_preset_dropdown = Dropdown(label="Advanced Preset", options=[dropdown.DropdownOption(n) for n in SQUAD_ADV_PRESET_NAMES], value=None, width=300)
    def apply_adv_preset(e=None):
        try:
            name = adv_preset_dropdown.value
            if not name:
                return
            data = SQUAD_ADV_PRESETS.get(name, {})
            if not data:
                return
            # set advanced fields
            try:
                adv_fields["CombatRank"].value = str(data.get("CombatRank", adv_fields["CombatRank"].value))
            except Exception:
                pass
            try:
                adv_fields["SubSelectSort"].value = str(data.get("SubSelectSort", adv_fields["SubSelectSort"].value))
            except Exception:
                pass
            try:
                adv_fields["AIAttackRank"].value = str(data.get("AIAttackRank", adv_fields["AIAttackRank"].value))
            except Exception:
                pass
            try:
                # optional HealValue in presets; treat "N/A" as blank.
                # If the preset does NOT include HealValue at all, clear the field to avoid leftover values.
                if "HealValue" in data:
                    hv = data.get("HealValue")
                    if hv is None or str(hv).upper() == "N/A":
                        adv_fields["HealValue"].value = ""
                    else:
                        adv_fields["HealValue"].value = str(hv)
                else:
                    # preset has no HealValue entry — clear any previous value
                    adv_fields["HealValue"].value = ""
            except Exception:
                pass
            try:
                # Apply BuildPoints from preset if present; treat "N/A" as blank
                if "BuildPoints" in data:
                    bp = data.get("BuildPoints")
                    if bp is None or str(bp).upper() == "N/A":
                        build_points.value = ""
                    else:
                        build_points.value = str(bp)
            except Exception:
                pass
            page.update()
        except Exception:
            pass

    apply_adv_preset_btn = Button("Apply Preset", on_click=apply_adv_preset)

    # ----------------------- Counters -----------------------
    # Mode selector replaced by buttons for reliable toggling
    counter_mode = "Use In-Game Counter"
    def set_counter_mode(mode):
        nonlocal counter_mode
        counter_mode = mode
        in_game_column.visible = (mode == "Use In-Game Counter")
        custom_column.visible = (mode == "Create Custom Counter")
        page.update()

    counter_mode_buttons = Row([
        Button("Use In-Game Counter", on_click=lambda e: set_counter_mode("Use In-Game Counter")),
        Button("Create Custom Counter", on_click=lambda e: set_counter_mode("Create Custom Counter")),
    ], spacing=8)
    in_game_counter_field = TextField(label="Select In-Game Counter", bgcolor=GRAY, width=400)
    in_game_suggestions = ListView(height=150, spacing=5)

    def make_counter_callback(val):
        return lambda e: (setattr(in_game_counter_field, "value", val), in_game_suggestions.controls.clear(), page.update())
    def update_counter_suggestions(text):
        in_game_suggestions.controls.clear()
        q = text.lower()
        for item in counters_library:
            if q in item.lower():
                    in_game_suggestions.controls.append(Button(item, on_click=make_counter_callback(item), bgcolor=GRAY, color=TEAL))
        page.update()
    in_game_counter_field.on_change = lambda e: update_counter_suggestions(in_game_counter_field.value)

    custom_name = TextField(label="Counter Name", bgcolor=GRAY, width=400)

    # -------------------------------------------------------------------
    # FIXED SLIDER COLOR SYSTEM (replaces your old slider+preview block)
    # -------------------------------------------------------------------

    def value_to_color(v):
        try:
            n = int(v)
        except:
            return "#555555"
        if n >= 7:
            return "#2ecc71"     # green
        if 4 <= n <= 6:
            return "#f39c12"     # yellow
        if 1 <= n <= 3:
            return "#e74c3c"     # red
        return "#777777"         # gray

    custom_infantry_slider = Slider(min=0, max=10, divisions=10, value=0, label="{value}")
    custom_vehicle_slider = Slider(min=0, max=10, divisions=10, value=0, label="{value}")
    custom_air_slider = Slider(min=0, max=10, divisions=10, value=0, label="{value}")
    custom_structure_slider = Slider(min=0, max=10, divisions=10, value=0, label="{value}")

    infantry_preview = Container(width=48, height=48, border_radius=8, padding=6)
    vehicle_preview = Container(width=48, height=48, border_radius=8, padding=6)
    air_preview = Container(width=48, height=48, border_radius=8, padding=6)
    structure_preview = Container(width=48, height=48, border_radius=8, padding=6)

    infantry_label = Text("0")
    vehicle_label = Text("0")
    air_label = Text("0")
    structure_label = Text("0")

    def update_previews():
        # NOTE: this must be called only after the returned Column is added to the page.
        # It will set preview bgcolors and call update() on the preview Controls.
        infantry_preview.bgcolor = value_to_color(custom_infantry_slider.value)
        vehicle_preview.bgcolor = value_to_color(custom_vehicle_slider.value)
        air_preview.bgcolor = value_to_color(custom_air_slider.value)
        structure_preview.bgcolor = value_to_color(custom_structure_slider.value)
        # update numeric labels
        try:
            infantry_label.value = str(int(custom_infantry_slider.value))
            vehicle_label.value = str(int(custom_vehicle_slider.value))
            air_label.value = str(int(custom_air_slider.value))
            structure_label.value = str(int(custom_structure_slider.value))
        except Exception:
            pass
        # .update() only valid once containers are added to page UI tree:
        try:
            infantry_preview.update()
            vehicle_preview.update()
            air_preview.update()
            structure_preview.update()
        except AssertionError:
            # If called too early, silently skip updates; caller should call again after page.add(...)
            pass

    custom_infantry_slider.on_change = lambda e: update_previews()
    custom_vehicle_slider.on_change = lambda e: update_previews()
    custom_air_slider.on_change = lambda e: update_previews()
    custom_structure_slider.on_change = lambda e: update_previews()

    # NOTE: removed immediate call to update_previews() to avoid calling update() before the controls are added.

    preview_row = Row([
        Column([Text("Infantry", size=12), infantry_preview, infantry_label], alignment="center"),
        Column([Text("Vehicle", size=12), vehicle_preview, vehicle_label], alignment="center"),
        Column([Text("Air", size=12), air_preview, air_label], alignment="center"),
        Column([Text("Structure", size=12), structure_preview, structure_label], alignment="center")
    ], spacing=24, alignment="spaceEvenly")

    in_game_column = Column([in_game_counter_field, in_game_suggestions])
    # Place the preview row at the top so it's immediately visible
    custom_column = Column([
        Container(Column([Text("Custom Counter Preview", weight="bold"), preview_row], alignment="center"), padding=8),
        custom_name,
        Text("Infantry"), custom_infantry_slider,
        Text("Vehicle"), custom_vehicle_slider,
        Text("Air"), custom_air_slider,
        Text("Structure"), custom_structure_slider,
    ])

    # Use explicit buttons for counter mode selection (more reliable than Dropdown across Flet versions)
    counter_mode = "Use In-Game Counter"
    def set_counter_mode(mode):
        nonlocal counter_mode
        counter_mode = mode
        in_game_column.visible = (mode == "Use In-Game Counter")
        custom_column.visible = (mode == "Create Custom Counter")
        page.update()

    counter_mode_buttons = Row([
        Button("Use In-Game Counter", on_click=lambda e: set_counter_mode("Use In-Game Counter")),
        Button("Create Custom Counter", on_click=lambda e: set_counter_mode("Create Custom Counter")),
    ], spacing=8)

    # initialize visibility
    set_counter_mode(counter_mode)

    # ----------------------- Abilities -----------------------
    has_ability = Checkbox(label="Squad Has Ability", value=False)
    ability_preset_dropdown = Dropdown(label="Ability Preset (optional)", options=[dropdown.DropdownOption(a) for a in abilities_library]+[dropdown.DropdownOption("Custom")], value=None, width=300)
    ability_mode = Dropdown(label="Ability Mode", options=[dropdown.DropdownOption("Active"), dropdown.DropdownOption("Unlockable")], value="Active", width=220, visible=False)
    ability_type = TextField(label="Ability Type (or pick preset)", bgcolor=GRAY, width=300, visible=False)
    ability_preset_dropdown.on_change = lambda e: setattr(ability_type, "value", ability_preset_dropdown.value) if ability_preset_dropdown.value and ability_preset_dropdown.value!="Custom" else None
    has_ability.on_change = lambda e: (setattr(ability_mode, "visible", has_ability.value), setattr(ability_type, "visible", has_ability.value), setattr(ability_preset_dropdown, "visible", has_ability.value), page.update())

    # ----------------------- Output -----------------------
    output_box = TextField(multiline=True,min_lines=16,max_lines=24,bgcolor="#111111",width=900)
    generate_button = Button("Generate XML")
    def copy_output(e):
        if not output_box.value.strip():
            return
        try:
            from Modules.shared_utils_fast import safe_set_clipboard
            safe_set_clipboard(page, output_box.value)
        except Exception:
            try:
                page.set_clipboard(output_box.value)
            except Exception:
                try:
                    page.clipboard = output_box.value
                except Exception:
                    pass

    copy_button = Button("Copy XML", on_click=copy_output)

    # ----------------------- Reset -----------------------
    reset_button = Button("Reset", on_click=lambda e: (
        setattr(squad_name,"value",""),
        setattr(is_infantry,"value",True),
        setattr(formation_dropdown,"value","Flock"),
        setattr(use_parent,"value",False),
        setattr(parent_element,"value",""),
        setattr(build_points,"value","17"),
        [setattr(u["name"],"value","") or setattr(u["count"],"value","1") or setattr(u["role"],"value","normal") for u in unit_rows],
        cost_rows.clear(),
        costs_container.controls.clear(),
        add_cost_row(),
        setattr(pop_type_dropdown,"value","Unit"),
        setattr(pop_custom_type,"value",""),
        setattr(pop_value_field,"value","1"),
        [setattr(cb,"value",False) for cb in flag_checkboxes],
        setattr(xyz_flags,"value",False),
        set_counter_mode("Use In-Game Counter"),
        setattr(in_game_counter_field,"value",""),
        setattr(custom_name,"value",""),
        setattr(custom_infantry_slider,"value",0),
        setattr(custom_vehicle_slider,"value",0),
        setattr(custom_air_slider,"value",0),
        setattr(custom_structure_slider,"value",0),
        setattr(has_ability,"value",False),
        setattr(ability_mode,"visible",False),
        setattr(ability_type,"visible",False),
        setattr(ability_preset_dropdown,"visible",False),
        [setattr(f,"value","") for f in adv_fields.values()],
        setattr(output_box,"value",""),
        toggle_formation(None),
        show_legacy_changed(None),
        # ensure counter UI reset
        set_counter_mode("Use In-Game Counter"),
        update_previews(),
        page.update()
    ))

    # ----------------------- Generate Logic -----------------------
    def generate_xml(e):
        final_units = [{"name": u["name"].value, "count": u["count"].value, "role": u["role"].value} for u in unit_rows]
        final_costs = [{"type": c["type"].value, "value": c["value"].value} for c in cost_rows]
        flags_list = [cb.label for cb in flag_checkboxes if cb.value]
        if xyz_flags.value:
            flags_list += ["UseNameForSelectionDecal","UseNameForSelectionIcon","UseNameForMenuIcon"]
        adv = {k:v.value for k,v in adv_fields.items()}

        counters_list = []
        append_custom_counter_def = None
        if counter_mode=="Use In-Game Counter" and in_game_counter_field.value:
            counters_list.append(in_game_counter_field.value)
        elif counter_mode=="Create Custom Counter":
            name=custom_name.value.strip()
            inf_v=int(custom_infantry_slider.value)
            veh_v=int(custom_vehicle_slider.value)
            air_v=int(custom_air_slider.value)
            str_v=int(custom_structure_slider.value)
            if name:
                counters_list.append(name)
                append_custom_counter_def=(name,inf_v,veh_v,air_v,str_v)

        pop_type_val = pop_custom_type.value.strip() if pop_type_dropdown.value=="Custom" else pop_type_dropdown.value
        pop_value_val = pop_value_field.value.strip()

        xml = build_squad_xml(
            squad_name=squad_name.value,
            is_infantry=is_infantry.value,
            formation=formation_dropdown.value if is_infantry.value else "",
            use_parent=use_parent.value,
            parent_element=parent_element.value,
            build_points=build_points.value,
            costs=final_costs,
            pop_type=pop_type_val,
            pop_value=pop_value_val,
            units=final_units,
            flags=flags_list,
            counters=counters_list,
            adv=adv,
            include_legacy_fields=(not use_parent.value) and show_legacy_checkbox.value,
            leader_dies_last=bool(leader_dies_last_chk.value)
        )

        if append_custom_counter_def:
            n,inf_v,veh_v,air_v,str_v=append_custom_counter_def
            xml = xml.rstrip()[:-8] + f'\t<Counter Name="{n}" Infantry="{inf_v}" Vehicle="{veh_v}" Air="{air_v}" Structure="{str_v}" />\n</Squad>'
        if has_ability.value:
            chosen_name = ability_type.value.strip() if ability_type.value.strip() else ability_preset_dropdown.value
            if chosen_name:
                active_xml = f'\t<ActiveAbilityType>{chosen_name}</ActiveAbilityType>\n' if ability_mode.value=="Active" else f'\t<UnlockableActiveAbilityType>{chosen_name}</UnlockableActiveAbilityType>\n'
                xml = xml.rstrip()[:-8]+active_xml+"</Squad>"
        output_box.value=xml
        page.update()
        try:
            from Modules.shared_outputs import outputs_registry
            outputs_registry["squad"] = output_box.value
        except Exception:
            pass
    generate_button.on_click=generate_xml

    # ----------------------- Tabs -----------------------
    general_tab = Column([Text("Squad Builder", size=20, weight="bold"), squad_name, is_infantry, formation_dropdown, use_parent, parent_element, Divider(), has_ability, ability_preset_dropdown, ability_mode, ability_type])
    # Global checkbox at bottom of Units section to control a single <LeaderDiesLast /> tag
    leader_dies_last_chk = Checkbox(label="Leader Dies Last (Squad)", value=False)
    units_tab = Column([Text("Squad Builder", size=20, weight="bold"), units_container, Row([Button("Add Unit", on_click=add_unit_row), leader_dies_last_chk])])
    costs_tab = Column([Text("Squad Builder", size=20, weight="bold"), Row([cost_preset_dropdown, apply_cost_preset_btn], spacing=12), costs_container, Button("Add Cost", on_click=add_cost_row), Divider(), Row([pop_type_dropdown, pop_custom_type, pop_value_field], spacing=10)])
    flags_tab = Column([Text("Squad Builder", size=20, weight="bold"), *flag_checkboxes, Divider(), xyz_flags])
    counters_tab = Column([Text("Squad Builder", size=20, weight="bold"), counter_mode_buttons, Divider(), in_game_column, custom_column])
    advanced_tab = Column([
        Text("Squad Builder", size=20, weight="bold"),
        Column([
            Row([adv_preset_dropdown, apply_adv_preset_btn], spacing=12),
            adv_fields["CombatRank"], adv_fields["SubSelectSort"], adv_fields["AIAttackRank"], adv_fields["HealValue"], build_points, Divider(), show_legacy_checkbox, *legacy_controls
        ])
    ])
    output_tab = Column([output_box, Row([generate_button, copy_button, reset_button], spacing=10)])

    # Replace Tabs with header buttons + content area for compatibility
    tab_contents = [general_tab, units_tab, costs_tab, flags_tab, counters_tab, advanced_tab, output_tab]
    content_area = Column(expand=True)

    def switch_tab(i):
        content_area.controls.clear()
        content_area.controls.append(tab_contents[i])
        page.update()
        # If user opened Counters tab, update preview boxes now that controls are attached
        try:
            if i == 4:
                try:
                    update_previews()
                except Exception:
                    pass
        except Exception:
            pass

    headers = Row([
        Button("General", on_click=lambda e: switch_tab(0)),
        Button("Units", on_click=lambda e: switch_tab(1)),
        Button("Costs", on_click=lambda e: switch_tab(2)),
        Button("Flags", on_click=lambda e: switch_tab(3)),
        Button("Counters", on_click=lambda e: switch_tab(4)),
        Button("Advanced Settings", on_click=lambda e: switch_tab(5)),
        Button("Output", on_click=lambda e: switch_tab(6)),
    ], spacing=8)

    switch_tab(0)

    content = Column([Text("Squad Builder", size=28, weight="bold"), headers, content_area], expand=True, spacing=20)

    # Attach helpers and expose output for external tools (Packager)
    setattr(content, "update_previews", update_previews)
    setattr(content, "output_box", output_box)

    return content
