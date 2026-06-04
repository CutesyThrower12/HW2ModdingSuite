import sys
import os
import json
import flet
from flet import (
    Page,
    Column,
    Row,
    Text,
    TextField,
    Button,
    ListView,
    Divider,
    Tab,
    Tabs,
    SnackBar,
    Checkbox,
    Slider,
    padding,
    dropdown,
)

if not hasattr(flet, "icons"):
    class _Icons:
        def __getattr__(self, name: str) -> str:
            return name.lower()
    flet.icons = _Icons()


try:
    from flet import icons  # works on some flet versions
except Exception:
    # fall back to any existing flet.icons without importing flet_core
    icons = getattr(flet, "icons", None)
    if icons is None:
        class _Icons:
            def __getattr__(self, name: str) -> str:
                return name.lower()
        icons = _Icons()
    flet.icons = icons

def resource_path(*parts):
    # In PyInstaller onefile/onedir, this points to the extracted bundle dir
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)

def load_library(filename):
    path = resource_path("Modules", "Library", filename)
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)
# Defer loading large JSON libraries until the Unit Builder is opened to speed startup
parents_library = None
tactics_library = None
damage_library = None

def _load_if_none(var_name: str, filename: str):
    if globals().get(var_name) is None:
        try:
            globals()[var_name] = load_library(filename)
        except Exception:
            globals()[var_name] = []
    return globals()[var_name]

# ---------------------------
# Unit Name Generator
# ---------------------------
def generate_unit_name(faction: str, unit_type: str, nickname: str, index: int = 1) -> str:
    faction = faction.lower()
    unit_type = unit_type.lower()
    nickname = nickname.lower()
    return f"{faction}_{unit_type}_{nickname}_{index:02d}"

# ---------------------------
# XML Generator
# ---------------------------
def generate_object_xml(
    name, parent, tactics, los, hp, vel, acc, dmg_normal, dmg_cover, object_type,
    bounty=0, shield_enabled=False, shieldpoints=0
):
    # Always include Normal damage. Include Cover damage only for Infantry types.
    lines = [
        f'<Object name="{name}" dbid="00000000000000000000" parent_element="{parent}">',
        f'    <Visual>modded\\{name}.vis</Visual>',
        f'    <Tactics>{tactics}</Tactics>',
        f'    <Flag>HasHPBar</Flag>',
        f'    <Velocity>{vel}</Velocity>',
        f'    <Acceleration>{acc}</Acceleration>',
        f'    <LOS>{los}</LOS>',
        f'    <Hitpoints>{hp}</Hitpoints>',
        f'    <Bounty>{bounty}</Bounty>',
        f'    <ObjectType>{object_type}</ObjectType>',
        f'    <DamageType direction="Full" mode="Normal">{dmg_normal}</DamageType>',
    ]
    try:
        ot = str(object_type).strip().lower()
    except Exception:
        ot = ""
    if ot.startswith("infantry"):
        lines.append(f'    <DamageType direction="Full" mode="Cover">{dmg_cover}</DamageType>')
    # If shields are enabled, include Shieldpoints and add a Shielded DamageType
    try:
        if shield_enabled:
            try:
                sp = int(shieldpoints)
            except Exception:
                sp = 0
            lines.append(f'    <Shieldpoints>{sp}</Shieldpoints>')
            lines.append(f'    <DamageType direction="Full">Shielded</DamageType>')
    except Exception:
        pass
    # If veterancy is provided as a list of dicts, append each level
    try:
        vets = globals().get('_veterancy_override', None)
        # prefer passed-in veterancy list if set on function globals (used below)
        if isinstance(vets, list) and vets:
            for v in vets:
                try:
                    lvl = v.get('Level', v.get('level', '1'))
                    xp = v.get('XP', v.get('xp', '0'))
                    dmg = v.get('Damage', v.get('damage', '1'))
                    velm = v.get('Velocity', v.get('velocity', '1'))
                    accm = v.get('Accuracy', v.get('accuracy', '1'))
                    wr = v.get('WorkRate', v.get('workrate', '1'))
                    wrange = v.get('WeaponRange', v.get('weaponrange', '1'))
                    dt = v.get('DamageTaken', v.get('damagetaken', '1'))
                    lines.append(f'    <Veterancy Level="{lvl}" XP="{xp}" Damage="{dmg}" Velocity="{velm}" Accuracy="{accm}" WorkRate="{wr}" WeaponRange="{wrange}" DamageTaken="{dt}" />')
                except Exception:
                    pass
    except Exception:
        pass
    lines.append('</Object>')
    return "\n".join(lines)

# =====================================================================
#   ⬇️ UNIT BUILDER TAB (callback-style for embedding) ⬇️
# =====================================================================

def unit_builder_tab(page: Page):

    # Theme (shared)
    from Modules.shared_styles_fix import TEAL, INPUT_BG, OUTPUT_BG

    # ---------------------------
    # SnackBar helper
    # ---------------------------
    def show_snack(msg, color="white"):
        page.snack_bar = SnackBar(Text(msg, color=color))
        page.snack_bar.open = True
        page.update()

    # ---------------------------
    # INPUT FIELDS
    # ---------------------------
    faction = TextField(label="Faction", hint_text="unsc / cov / ban", bgcolor=INPUT_BG)
    unit_type = TextField(label="Unit Type", hint_text="inf / veh / air", bgcolor=INPUT_BG)
    nickname = TextField(label="Nickname", hint_text="marine / grunt / hog", bgcolor=INPUT_BG)
    index = TextField(label="Index", hint_text="01", bgcolor=INPUT_BG)

    los = TextField(label="Line of Sight", value="50", bgcolor=INPUT_BG)
    hp = TextField(label="Hitpoints", value="1000", bgcolor=INPUT_BG)
    vel = TextField(label="Velocity", value="10", bgcolor=INPUT_BG)
    acc = TextField(label="Acceleration", value="8", bgcolor=INPUT_BG)
    bounty = TextField(label="Bounty", value="0", bgcolor=INPUT_BG, width=120)
    shield_checkbox = Checkbox(label="Has Shields")
    shieldpoints = TextField(label="Shieldpoints", value="0", bgcolor=INPUT_BG, width=200, visible=False)
    # Veterancy controls (dynamic levels with sliders)
    vet_checkbox = Checkbox(label="Enable Veterancy")

    # container for dynamic veterancy rows
    vet_levels = []  # list of dicts: {'xp': TextField, 'damage': Slider, ...}
    vet_levels_container = Column(visible=False)

    def _make_slider(value_str, min_v=0.0, max_v=5.0, step=0.1, width=200):
        try:
            val = float(value_str)
        except Exception:
            val = 1.0
        # clamp to range
        try:
            if val < min_v:
                val = min_v
            if val > max_v:
                val = max_v
        except Exception:
            pass
        # compute divisions safely (number of steps)
        try:
            divisions = int(round((max_v - min_v) / step)) if step > 0 else None
            if divisions is not None and divisions <= 0:
                divisions = None
        except Exception:
            divisions = None
        s = Slider(min=min_v, max=max_v, value=val, divisions=divisions, width=width)
        try:
            s.label = f"{val:.1f}"
        except Exception:
            pass
        return s

    def add_vet_level(initial=None):
        # initial: dict with keys XP, Damage, Velocity, Accuracy, WorkRate, WeaponRange, DamageTaken
        idx = len(vet_levels) + 1
        xp_val = str((initial.get('XP') if initial else None) or "0")
        damage_val = str((initial.get('Damage') if initial else None) or "1")
        vel_val = str((initial.get('Velocity') if initial else None) or "1")
        acc_val = str((initial.get('Accuracy') if initial else None) or "1")
        work_val = str((initial.get('WorkRate') if initial else None) or "1")
        wr_val = str((initial.get('WeaponRange') if initial else None) or "1")
        dt_val = str((initial.get('DamageTaken') if initial else None) or "1")

        xp_field = TextField(label=f"L{idx} XP", value=xp_val, width=120, bgcolor=INPUT_BG)
        damage_slider = _make_slider(damage_val)
        velocity_slider = _make_slider(vel_val)
        accuracy_slider = _make_slider(acc_val)
        work_slider = _make_slider(work_val)
        wr_slider = _make_slider(wr_val)
        dt_slider = _make_slider(dt_val)

        # show numeric value beside slider
        damage_label = Text(f"{damage_slider.value:.1f}")
        velocity_label = Text(f"{velocity_slider.value:.1f}")
        accuracy_label = Text(f"{accuracy_slider.value:.1f}")
        work_label = Text(f"{work_slider.value:.1f}")
        wr_label = Text(f"{wr_slider.value:.1f}")
        dt_label = Text(f"{dt_slider.value:.1f}")

        def _wire(sld, lbl):
            try:
                def _onchange(e, s=sld, l=lbl):
                    try:
                        l.value = f"{s.value:.1f}"
                        try:
                            l.update()
                        except Exception:
                            pass
                    except Exception:
                        pass
                sld.on_change = _onchange
                # Only update the slider's thumb label when the user finishes the change
                try:
                    def _onchange_end(e, s=sld):
                        try:
                            s.label = f"{s.value:.1f}"
                            try:
                                s.update()
                            except Exception:
                                pass
                        except Exception:
                            pass
                    sld.on_change_end = _onchange_end
                except Exception:
                    # older flet versions may not support on_change_end
                    pass
            except Exception:
                try:
                    sld.on_change = lambda e, s=sld, l=lbl: (setattr(l, 'value', f"{s.value:.1f}"), l.update())
                except Exception:
                    pass

        _wire(damage_slider, damage_label)
        _wire(velocity_slider, velocity_label)
        _wire(accuracy_slider, accuracy_label)
        _wire(work_slider, work_label)
        _wire(wr_slider, wr_label)
        _wire(dt_slider, dt_label)

        row_top = Row([xp_field, Column([Text("Damage"), Row([damage_slider, damage_label])]), Column([Text("Velocity"), Row([velocity_slider, velocity_label])]), Column([Text("Accuracy"), Row([accuracy_slider, accuracy_label])])], wrap=True)
        row_bot = Row([Column([Text("WorkRate"), Row([work_slider, work_label])]), Column([Text("WeaponRange"), Row([wr_slider, wr_label])]), Column([Text("DamageTaken"), Row([dt_slider, dt_label])])], wrap=True)
        container = Column([row_top, row_bot])

        vet_levels.append({
            'xp': xp_field,
            'damage': damage_slider,
            'damage_label': damage_label,
            'velocity': velocity_slider,
            'velocity_label': velocity_label,
            'accuracy': accuracy_slider,
            'accuracy_label': accuracy_label,
            'work': work_slider,
            'work_label': work_label,
            'wr': wr_slider,
            'wr_label': wr_label,
            'dt': dt_slider,
            'dt_label': dt_label,
            'container': container,
        })
        vet_levels_container.controls.append(container)
        try:
            page.update()
        except Exception:
            pass

    def remove_vet_level():
        if not vet_levels:
            return
        last = vet_levels.pop()
        try:
            vet_levels_container.controls.remove(last.get('container'))
        except Exception:
            pass
        try:
            page.update()
        except Exception:
            pass

    # initialize with three default levels (values match previous defaults)
    add_vet_level({'XP': '16', 'Damage': '1.14999998', 'Velocity': '1', 'Accuracy': '1.60000002', 'WorkRate': '1.20000005', 'WeaponRange': '1', 'DamageTaken': '0.870000005'})
    add_vet_level({'XP': '40', 'Damage': '1.25', 'Velocity': '1', 'Accuracy': '1.70000005', 'WorkRate': '1.20000005', 'WeaponRange': '1', 'DamageTaken': '0.800000012'})
    add_vet_level({'XP': '72', 'Damage': '1.35000002', 'Velocity': '1', 'Accuracy': '1.79999995', 'WorkRate': '1.20000005', 'WeaponRange': '1', 'DamageTaken': '0.74000001'})

    # wrapper controls: levels container only (no add/remove buttons)
    vet_controls = Column([vet_levels_container], visible=False)

    visual_field = TextField(
        label="Visual Path (.vis)",
        hint_text="modded\\unsc\\infantry\\oniMarine01\\oniMarine01.vis",
        bgcolor=INPUT_BG,
        width=600
    )

    # ---------------------------
    # ObjectType Dropdown
    # ---------------------------
    object_type = dropdown.Dropdown(
        label="Object Type",
        options=[
            dropdown.DropdownOption("InfantryTech"),
            dropdown.DropdownOption("VehicleTech"),
            dropdown.DropdownOption("AircraftTech"),
        ],
        value="InfantryTech",
        width=200
    )

    # ---------------------------
    # SEARCHABLE DROPDOWNS
    # ---------------------------
    parent = TextField(label="Parent Element", bgcolor=INPUT_BG)
    tactics_tf = TextField(label="Tactics File", bgcolor=INPUT_BG)
    dmg_normal = TextField(label="DamageType Normal", bgcolor=INPUT_BG)
    dmg_cover = TextField(label="DamageType Cover", bgcolor=INPUT_BG)

    parent_suggestions = ListView(height=150, spacing=5)
    tactics_suggestions = ListView(height=150, spacing=5)
    dmg_normal_suggestions = ListView(height=150, spacing=5)
    dmg_cover_suggestions = ListView(height=150, spacing=5)

    def update_suggestions(text, library, suggestion_list, target_field):
        suggestion_list.controls.clear()
        text_lower = text.lower()
        for item in library:

            if text_lower in item.lower():

                def make_callback(val):
                    return lambda e: (
                        setattr(target_field, "value", val),
                        suggestion_list.controls.clear(),
                        page.update()
                    )

                suggestion_list.controls.append(
                    Button(
                            item,
                            on_click=make_callback(item),
                            bgcolor=INPUT_BG,
                            color=TEAL
                        )
                )
        page.update()

    parent.on_change = lambda e: update_suggestions(parent.value, _load_if_none('parents_library', 'parents.json'), parent_suggestions, parent)
    tactics_tf.on_change = lambda e: update_suggestions(tactics_tf.value, _load_if_none('tactics_library', 'tactics.json'), tactics_suggestions, tactics_tf)
    dmg_normal.on_change = lambda e: update_suggestions(dmg_normal.value, _load_if_none('damage_library', 'damage_types.json'), dmg_normal_suggestions, dmg_normal)
    dmg_cover.on_change = lambda e: update_suggestions(dmg_cover.value, _load_if_none('damage_library', 'damage_types.json'), dmg_cover_suggestions, dmg_cover)

    # ---------------------------
    # XML OUTPUT + COPY + GENERATE
    # ---------------------------
    xml_output = TextField(
        label="Generated XML",
        multiline=True,
        min_lines=10,
        max_lines=20,
        bgcolor=OUTPUT_BG,
        width=900
    )

    def copy_xml(e):
        if not xml_output.value:
            show_snack("Nothing to copy — generate XML first.")
            return
        try:
            from Modules.shared_utils_fast import safe_set_clipboard
            safe_set_clipboard(page, xml_output.value)
        except Exception:
            try:
                page.set_clipboard(xml_output.value)
            except Exception:
                try:
                    page.clipboard = xml_output.value
                except Exception:
                    pass
        show_snack("XML copied!", color=TEAL)

    copy_button = Button(
        "Copy XML",
        on_click=copy_xml
    )

    def generate(e):
        try:
            idx = int(index.value)
        except:
            show_snack("Index must be a number!")
            return

        name = generate_unit_name(
            faction.value,
            unit_type.value,
            nickname.value,
            idx
        )

        # determine shield state
        try:
            shield_on = bool(getattr(shield_checkbox, 'value', False))
        except Exception:
            shield_on = False

        # prepare veterancy list if enabled
        try:
            vet_on = bool(getattr(vet_checkbox, 'value', False))
        except Exception:
            vet_on = False
        vets = []
        if vet_on:
            try:
                for idx, lvl in enumerate(vet_levels, start=1):
                    try:
                        vets.append({
                            'Level': str(idx),
                            'XP': getattr(lvl['xp'], 'value', '0'),
                            'Damage': str(getattr(lvl['damage'], 'value', 1)),
                            'Velocity': str(getattr(lvl['velocity'], 'value', 1)),
                            'Accuracy': str(getattr(lvl['accuracy'], 'value', 1)),
                            'WorkRate': str(getattr(lvl['work'], 'value', 1)),
                            'WeaponRange': str(getattr(lvl['wr'], 'value', 1)),
                            'DamageTaken': str(getattr(lvl['dt'], 'value', 1)),
                        })
                    except Exception:
                        pass
            except Exception:
                vets = []

        # pass vets via a temporary global used by generate_object_xml
        try:
            if vets:
                globals()['_veterancy_override'] = vets
            elif '_veterancy_override' in globals():
                del globals()['_veterancy_override']
        except Exception:
            pass

        xml = generate_object_xml(
            name=name,
            parent=parent.value,
            tactics=tactics_tf.value,
            los=los.value,
            hp=hp.value,
            vel=vel.value,
            acc=acc.value,
            dmg_normal=dmg_normal.value,
            dmg_cover=dmg_cover.value,
            object_type=object_type.value,
            bounty=(bounty.value or "0"),
            shield_enabled=shield_on,
            shieldpoints=(shieldpoints.value or "0"),
        )

        # clear the temporary global after generation
        try:
            if '_veterancy_override' in globals():
                del globals()['_veterancy_override']
        except Exception:
            pass

        xml_output.value = xml
        page.update()
        show_snack("XML generated!", TEAL)
        try:
            from Modules.shared_outputs import outputs_registry
            outputs_registry["unit"] = xml_output.value
        except Exception:
            pass

    generate_button = Button(
        "Generate XML",
        on_click=generate
    )

    # ---------------------------
    # RESET BUTTON
    # ---------------------------
    def reset_fields(e):
        faction.value = ""
        unit_type.value = ""
        nickname.value = ""
        index.value = ""
        los.value = "50"
        hp.value = "1000"
        vel.value = "10"
        acc.value = "8"
        visual_field.value = ""
        parent.value = ""
        tactics_tf.value = ""
        dmg_normal.value = ""
        dmg_cover.value = ""
        object_type.value = "InfantryTech"
        bounty.value = "0"
        try:
            shield_checkbox.value = False
        except Exception:
            pass
        shieldpoints.value = "0"
        try:
            vet_checkbox.value = False
        except Exception:
            pass
        # reset dynamic veterancy levels to defaults
        try:
            # remove all existing levels
            while vet_levels:
                remove_vet_level()
        except Exception:
            pass
        # add defaults back
        try:
            add_vet_level({'XP': '16', 'Damage': '1.14999998', 'Velocity': '1', 'Accuracy': '1.60000002', 'WorkRate': '1.20000005', 'WeaponRange': '1', 'DamageTaken': '0.870000005'})
            add_vet_level({'XP': '40', 'Damage': '1.25', 'Velocity': '1', 'Accuracy': '1.70000005', 'WorkRate': '1.20000005', 'WeaponRange': '1', 'DamageTaken': '0.800000012'})
            add_vet_level({'XP': '72', 'Damage': '1.35000002', 'Velocity': '1', 'Accuracy': '1.79999995', 'WorkRate': '1.20000005', 'WeaponRange': '1', 'DamageTaken': '0.74000001'})
        except Exception:
            pass
        xml_output.value = ""
        parent_suggestions.controls.clear()
        tactics_suggestions.controls.clear()
        dmg_normal_suggestions.controls.clear()
        dmg_cover_suggestions.controls.clear()
        page.update()
        show_snack("All fields reset!", TEAL)
        try:
            from Modules.shared_outputs import outputs_registry
            outputs_registry["unit"] = ""
        except Exception:
            pass

    reset_button = Button(
        "Reset",
        on_click=reset_fields
    )

    # ---------------------------
    # RETURN - simple tab headers + content (avoid incompatible Tab API)
    # ---------------------------
    # Prepare tab contents
    general_content = Column([
        Text("Unit Builder", size=20, weight="bold"),
        faction,
        unit_type,
        nickname,
        index,
    ], spacing=10)

    parents_content = Column([
        Text("Unit Builder", size=20, weight="bold"),
        Text("Parent Element Input + Suggestions", color=TEAL),
        parent,
        parent_suggestions,
        Divider(),
        Text("Tactics Input + Suggestions", color=TEAL),
        tactics_tf,
        tactics_suggestions,
    ], spacing=10)

    def _update_shield_visibility(e=None):
        try:
            shieldpoints.visible = bool(getattr(shield_checkbox, 'value', False))
        except Exception:
            shieldpoints.visible = False
        try:
            page.update()
        except Exception:
            pass

    try:
        shield_checkbox.on_change = _update_shield_visibility
    except Exception:
        try:
            shield_checkbox.on_change = lambda e: _update_shield_visibility()
        except Exception:
            pass
    def _update_vet_visibility(e=None):
        try:
            val = bool(getattr(vet_checkbox, 'value', False))
            vet_controls.visible = val
            try:
                vet_levels_container.visible = val
            except Exception:
                pass
        except Exception:
            try:
                vet_controls.visible = False
            except Exception:
                pass
            try:
                vet_levels_container.visible = False
            except Exception:
                pass
        try:
            page.update()
        except Exception:
            pass

    try:
        vet_checkbox.on_change = _update_vet_visibility
    except Exception:
        try:
            vet_checkbox.on_change = lambda e: _update_vet_visibility()
        except Exception:
            pass

    stats_content = Column([
        Text("Unit Builder", size=20, weight="bold"),
        visual_field,
        Row([vel, acc, los, hp, bounty, object_type], wrap=True),
        Row([shield_checkbox, shieldpoints, vet_checkbox], wrap=True),
        vet_controls,
    ], spacing=10)

    damage_content = Column([
        Text("Unit Builder", size=20, weight="bold"),
        Text("Normal Damage Type", color=TEAL),
        dmg_normal,
        dmg_normal_suggestions,
        Divider(),
        # Cover Damage Type is shown only for InfantryTech
    ], spacing=10)

    def update_damage_visibility(e=None):
        damage_content.controls.clear()
        damage_content.controls.append(Text("Unit Builder", size=20, weight="bold"))
        damage_content.controls.append(Text("Normal Damage Type", color=TEAL))
        damage_content.controls.append(dmg_normal)
        damage_content.controls.append(dmg_normal_suggestions)
        damage_content.controls.append(Divider())
        try:
            val = str(getattr(object_type, 'value', '') or '').strip().lower()
            if val.startswith("infantry"):
                damage_content.controls.append(Text("Cover Damage Type", color=TEAL))
                damage_content.controls.append(dmg_cover)
                damage_content.controls.append(dmg_cover_suggestions)
        except Exception:
            pass
        page.update()

    # attach change handler to object_type dropdown
    try:
        object_type.on_change = update_damage_visibility
    except Exception:
        try:
            object_type.on_change = lambda e: update_damage_visibility()
        except Exception:
            pass

    # initialize damage tab visibility
    update_damage_visibility()

    output_content = Column([
        xml_output,
        Row([generate_button, copy_button, reset_button], spacing=20)
    ], spacing=10)

    tab_contents = [general_content, parents_content, stats_content, damage_content, output_content]

    content_area = Column(expand=True)

    def switch_tab(i):
        content_area.controls.clear()
        # ensure damage tab visibility is correct when opening it
        if i == 3:
            try:
                update_damage_visibility()
            except Exception:
                pass
        content_area.controls.append(tab_contents[i])
        page.update()

    headers = Row([
        Button("General", on_click=lambda e: switch_tab(0)),
        Button("Parents/Tactics", on_click=lambda e: switch_tab(1)),
        Button("Stats", on_click=lambda e: switch_tab(2)),
        Button("Damage", on_click=lambda e: switch_tab(3)),
        Button("Output", on_click=lambda e: switch_tab(4)),
    ], spacing=8)

    # initial selection
    switch_tab(0)

    content = Column([
        Text("Unit Builder", size=28, weight="bold"),
        headers,
        content_area
    ], expand=True, spacing=20)

    # expose xml output for Packager to read
    setattr(content, "output_box", xml_output)
    # expose key input controls so other modules can programmatically set values
    setattr(content, "faction", faction)
    setattr(content, "unit_type", unit_type)
    setattr(content, "nickname", nickname)
    setattr(content, "index", index)
    setattr(content, "los", los)
    setattr(content, "hp", hp)
    setattr(content, "vel", vel)
    setattr(content, "acc", acc)
    setattr(content, "visual_field", visual_field)
    setattr(content, "parent_field", parent)
    setattr(content, "tactics", tactics_tf)
    setattr(content, "dmg_normal", dmg_normal)
    setattr(content, "dmg_cover", dmg_cover)
    setattr(content, "object_type", object_type)
    setattr(content, "bounty", bounty)
    setattr(content, "shield_checkbox", shield_checkbox)
    setattr(content, "shieldpoints", shieldpoints)
    setattr(content, "vet_checkbox", vet_checkbox)
    setattr(content, "vet_controls", vet_controls)
    setattr(content, "vet_levels", vet_levels)

    def apply_preset(data: dict):
        try:
            # map preset data into fields
            code = data.get('code', '')
            parts = code.split('_') if code else []
            try:
                if len(parts) >= 4:
                    faction.value = parts[0]
                    unit_type.value = parts[1]
                    nickname.value = parts[2]
                    index.value = parts[3]
                else:
                    nickname.value = data.get('display', '')
            except Exception:
                try:
                    nickname.value = data.get('display', '')
                except Exception:
                    pass

            los.value = str(data.get('los', los.value))
            hp.value = str(data.get('hp', hp.value))
            vel.value = str(data.get('vel', vel.value))
            acc.value = str(data.get('accel', acc.value))
            # set object type based on role heuristics
            role = str(data.get('role', '')).lower()
            if 'inf' in role:
                object_type.value = 'InfantryTech'
            elif 'air' in role:
                object_type.value = 'AircraftTech'
            else:
                object_type.value = 'VehicleTech'

            # optional fields
            visual_field.value = data.get('visual', visual_field.value) or visual_field.value
            parent.value = data.get('parent', parent.value) or parent.value
            tactics_tf.value = data.get('tactics', tactics_tf.value) or tactics_tf.value
            # If preset provides an Armor category, use it as the Normal DamageType
            if data.get('armor'):
                try:
                    dmg_normal.value = str(data.get('armor'))
                except Exception:
                    pass
            else:
                dmg_normal.value = data.get('dmg_normal', dmg_normal.value) or dmg_normal.value
            dmg_cover.value = data.get('dmg_cover', dmg_cover.value) or dmg_cover.value

            # apply bounty if present
            try:
                if data.get('bounty') is not None:
                    bounty.value = str(data.get('bounty'))
            except Exception:
                pass

            # apply shield settings if present
            try:
                if data.get('shieldpoints') is not None:
                    # enable shield checkbox and set shieldpoints
                    try:
                        shield_checkbox.value = True
                    except Exception:
                        pass
                    shieldpoints.value = str(data.get('shieldpoints', shieldpoints.value))
                    try:
                        _update_shield_visibility()
                    except Exception:
                        pass
                else:
                    try:
                        shield_checkbox.value = False
                        _update_shield_visibility()
                    except Exception:
                        pass
            except Exception:
                pass

            # apply veterancy if present (populate dynamic levels)
            try:
                vets = data.get('veterancy')
                if isinstance(vets, list) and vets:
                    try:
                        vet_checkbox.value = True
                    except Exception:
                        pass
                    # adjust number of levels to match preset
                    try:
                        desired = len(vets)
                        # add missing
                        while len(vet_levels) < desired:
                            add_vet_level()
                        # remove extra
                        while len(vet_levels) > desired:
                            remove_vet_level()
                    except Exception:
                        pass
                    # populate each level
                    try:
                        for i, v in enumerate(vets):
                            try:
                                lvl = vet_levels[i]
                                lvl['xp'].value = str(v.get('XP', getattr(lvl['xp'], 'value', '0')))
                                # sliders: set numeric values
                                try:
                                    lvl['damage'].value = float(v.get('Damage', getattr(lvl['damage'], 'value', 1)))
                                except Exception:
                                    pass
                                try:
                                    if 'damage_label' in lvl:
                                        lvl['damage_label'].value = f"{lvl['damage'].value:.1f}"
                                        try:
                                            lvl['damage_label'].update()
                                        except Exception:
                                            pass
                                        try:
                                            lvl['damage'].label = f"{lvl['damage'].value:.1f}"
                                            lvl['damage'].update()
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                                try:
                                    lvl['velocity'].value = float(v.get('Velocity', getattr(lvl['velocity'], 'value', 1)))
                                except Exception:
                                    pass
                                try:
                                    if 'velocity_label' in lvl:
                                        lvl['velocity_label'].value = f"{lvl['velocity'].value:.1f}"
                                        try:
                                            lvl['velocity_label'].update()
                                        except Exception:
                                            pass
                                        try:
                                            lvl['velocity'].label = f"{lvl['velocity'].value:.1f}"
                                            lvl['velocity'].update()
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                                try:
                                    lvl['accuracy'].value = float(v.get('Accuracy', getattr(lvl['accuracy'], 'value', 1)))
                                except Exception:
                                    pass
                                try:
                                    if 'accuracy_label' in lvl:
                                        lvl['accuracy_label'].value = f"{lvl['accuracy'].value:.1f}"
                                        try:
                                            lvl['accuracy_label'].update()
                                        except Exception:
                                            pass
                                        try:
                                            lvl['accuracy'].label = f"{lvl['accuracy'].value:.1f}"
                                            lvl['accuracy'].update()
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                                try:
                                    lvl['work'].value = float(v.get('WorkRate', getattr(lvl['work'], 'value', 1)))
                                except Exception:
                                    pass
                                try:
                                    if 'work_label' in lvl:
                                        lvl['work_label'].value = f"{lvl['work'].value:.1f}"
                                        try:
                                            lvl['work_label'].update()
                                        except Exception:
                                            pass
                                        try:
                                            lvl['work'].label = f"{lvl['work'].value:.1f}"
                                            lvl['work'].update()
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                                try:
                                    lvl['wr'].value = float(v.get('WeaponRange', getattr(lvl['wr'], 'value', 1)))
                                except Exception:
                                    pass
                                try:
                                    if 'wr_label' in lvl:
                                        lvl['wr_label'].value = f"{lvl['wr'].value:.1f}"
                                        try:
                                            lvl['wr_label'].update()
                                        except Exception:
                                            pass
                                        try:
                                            lvl['wr'].label = f"{lvl['wr'].value:.1f}"
                                            lvl['wr'].update()
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                                try:
                                    lvl['dt'].value = float(v.get('DamageTaken', getattr(lvl['dt'], 'value', 1)))
                                except Exception:
                                    pass
                                try:
                                    if 'dt_label' in lvl:
                                        lvl['dt_label'].value = f"{lvl['dt'].value:.1f}"
                                        try:
                                            lvl['dt_label'].update()
                                        except Exception:
                                            pass
                                        try:
                                            lvl['dt'].label = f"{lvl['dt'].value:.1f}"
                                            lvl['dt'].update()
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                            except Exception:
                                pass
                    except Exception:
                        pass
                    try:
                        _update_vet_visibility()
                    except Exception:
                        pass
                else:
                    try:
                        vet_checkbox.value = False
                        _update_vet_visibility()
                    except Exception:
                        pass
            except Exception:
                pass

            # show stats tab so users see LOS/HP/Vel/Acc
            try:
                switch_tab(2)
            except Exception:
                pass
            page.update()
            show_snack("Preset applied to Unit Builder", TEAL)
        except Exception:
            pass

    setattr(content, 'apply_preset', apply_preset)
    return content
