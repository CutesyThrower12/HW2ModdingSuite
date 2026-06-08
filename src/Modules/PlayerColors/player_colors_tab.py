import copy
import xml.etree.ElementTree as ET
from flet import (
    Column, Row, Text, TextField, Button, Container, Divider, Dropdown, dropdown,
    IconButton, Icon, icons, SnackBar, ScrollMode, ListView, Draggable, DragTarget
)

# Simple helper to format rgb tuple into "R G B"
def rgb_str(rgb):
    try:
        r, g, b = rgb
        return f"{int(r)} {int(g)} {int(b)}"
    except Exception:
        return "0 0 0"


def player_colors_tab(page):
    GRAY = "#0B1018"

    # data
    color_defs = []  # each: {name: str, attrs: {objects:[r,g,b], corpse:..., selection:..., minimap:..., ui:..., captureeffects:..., obscuringunit:..., effects:..., lights:...}}

    # default sample color to speed up testing
    def make_color(name, rgb=(175, 175, 175), enum_val=""):
        return {
            "name": name,
            "attrs": {k: list(rgb) for k in ["objects", "corpse", "selection", "minimap", "ui", "captureeffects", "obscuringunit", "effects", "lights"]},
            "expanded": False,
            "enum": enum_val,
        }

    # Default vanilla skirmish colors (exact RGBs)
    DEFAULT_SKIRMISH = [
        ("gaia", "175 175 175", "88 88 88", "175 175 175", "175 175 175", "175 175 175", "175 175 175", "175 175 175", "175 175 175", "175 175 175", "white"),
        ("creeps", "175 175 175", "88 88 88", "255 132 255", "255 132 255", "175 175 175", "175 175 175", "175 175 175", "175 175 175", "175 175 175", "white"),
        ("unsc_red", "160 60 60", "160 60 60", "159 29 29", "209 80 80", "48 244 230", "230 20 20", "253 96 96", "165 28 28", "165 28 28", "red"),
        ("unsc_3v3red", "170 25 25", "170 25 25", "170 25 25", "255 38 38", "48 244 230", "230 20 20", "255 38 38", "170 20 20", "170 20 20", "red"),
        ("unsc_yellow", "250 220 65", "250 220 65", "171 150 44", "255 224 66", "48 244 230", "230 20 20", "255 224 66", "100 87 18", "100 87 18", "red"),
        ("unsc_orange", "220 100 30", "220 100 30", "134 49 0", "255 116 36", "48 244 230", "230 20 20", "255 116 36", "141 61 15", "141 61 15", "red"),
        ("unsc_blue", "60 90 160", "60 90 160", "38 57 102", "94 143 255", "48 244 230", "50 170 255", "94 143 255", "16 52 136", "16 52 136", "blue"),
        ("unsc_3v3navy", "30 50 160", "30 50 160", "19 32 102", "48 79 255", "48 244 230", "50 170 255", "48 79 255", "30 50 160", "30 50 160", "blue"),
        ("unsc_cyan", "80 170 250", "80 170 250", "21 127 153", "82 174 255", "48 244 230", "50 170 255", "82 174 255", "33 98 157", "33 98 157", "blue"),
        ("unsc_green", "30 130 80", "30 130 80", "18 130 74", "59 255 157", "48 244 230", "50 170 255", "59 255 157", "30 130 80", "30 130 80", "blue"),
        ("ban_red", "160 60 60", "160 60 60", "159 29 29", "209 80 80", "48 244 230", "230 20 20", "253 96 96", "165 28 28", "165 28 28", "red"),
        ("ban_3v3red", "210 30 30", "210 30 3", "210 30 30", "255 36 36", "48 244 230", "230 20 20", "255 36 36", "170 24 24", "170 24 24", "red"),
        ("ban_yellow", "240 220 45", "166 152 31", "171 157 32", "255 234 48", "48 244 230", "230 20 20", "255 234 48", "100 87 18", "100 87 18", "red"),
        ("ban_orange", "250 145 20", "250 145 20", "134 49 0", "255 149 20", "48 244 230", "230 20 20", "255 149 20", "141 61 15", "141 61 15", "red"),
        ("ban_blue", "60 90 160", "60 90 160", "14 41 102", "94 143 255", "48 244 230", "50 170 255", "94 143 255", "16 52 136", "16 52 136", "blue"),
        ("ban_3v3navy", "30 50 160", "30 50 160", "19 32 102", "48 79 255", "48 244 230", "50 170 255", "48 79 255", "30 50 160", "30 50 160", "blue"),
        ("ban_cyan", "80 170 250", "80 170 250", "33 70 102", "82 174 255", "48 244 230", "50 170 255", "82 174 255", "33 98 157", "33 98 157", "blue"),
        ("ban_green", "30 130 80", "30 130 80", "23 102 63", "59 255 157", "48 244 230", "50 170 255", "59 255 157", "30 130 80", "30 130 80", "blue"),
        ("flood", "255 0 255", "255 0 255", "255 0 255", "255 0 255", "255 0 255", "255 0 255", "255 0 255", "255 0 255", "255 0 255", "flood"),
    ]

    for name, objects, corpse, selection, minimap, ui, captureeffects, obscuringunit, effects, lights, enum in DEFAULT_SKIRMISH:
        attrs = {
            "objects": [int(x) for x in objects.split()],
            "corpse": [int(x) for x in corpse.split()],
            "selection": [int(x) for x in selection.split()],
            "minimap": [int(x) for x in minimap.split()],
            "ui": [int(x) for x in ui.split()],
            "captureeffects": [int(x) for x in captureeffects.split()],
            "obscuringunit": [int(x) for x in obscuringunit.split()],
            "effects": [int(x) for x in effects.split()],
            "lights": [int(x) for x in lights.split()],
        }
        color_defs.append({"name": name, "attrs": attrs, "expanded": False, "enum": enum})

    # skirmish civs with player slots (map names to indices using our color_defs)
    def idx_of(name):
        for i,cd in enumerate(color_defs):
            if cd.get("name") == name:
                return i
        return 0

    skirmish_civs = {
        "UNSC": [
            idx_of("unsc_red"), idx_of("unsc_3v3red"), idx_of("unsc_yellow"), idx_of("unsc_orange"), idx_of("unsc_blue"),
            idx_of("unsc_3v3navy"), idx_of("unsc_cyan"), idx_of("unsc_green"), idx_of("gaia"), idx_of("creeps"), idx_of("flood")
        ],
        "Covenant": [
            idx_of("ban_red"), idx_of("ban_3v3red"), idx_of("ban_yellow"), idx_of("ban_orange"), idx_of("ban_blue"),
            idx_of("ban_3v3navy"), idx_of("ban_cyan"), idx_of("ban_green"), idx_of("gaia"), idx_of("creeps"), idx_of("flood")
        ],
        "Flood": [idx_of("flood")] * 11,
    }

    # SPC colors (numeric names)
    spc_colors = [make_color(str(i)) for i in range(21)]

    # UI containers
    color_list_view = ListView(expand=True, spacing=6, padding=6, height=520)
    civs_col = Column(spacing=12)
    # selected color index for detailed editor
    selected_color_idx = 0
    detail_col = Column(spacing=8)
    # reference to the color buttons list in the Edit tab (updated when tab rebuilt)
    color_buttons_view = None

    # Helpers to rebuild color dropdown options
    def color_options():
        return [dropdown.DropdownOption(c["name"]) for c in color_defs]

    # Build color row UI
    def rebuild_color_list():
        color_list_view.controls.clear()
        for idx, c in enumerate(color_defs):
            name_field = TextField(label="Name", value=c["name"], bgcolor=GRAY, width=220)

            def on_name_changed(e, ci=idx, nf=name_field):
                try:
                    new_name = nf.value.strip()
                    color_defs[ci]["name"] = new_name
                    try:
                        # if edit tab is visible and the color buttons list exists, update its label in-place
                        if current_tab == "edit" and color_buttons_view is not None and ci < len(color_buttons_view.controls):
                            try:
                                btn = color_buttons_view.controls[ci]
                                row = getattr(btn, 'content', None)
                                if row and hasattr(row, 'controls') and len(row.controls) > 1:
                                    txt = row.controls[1]
                                    try:
                                        txt.value = new_name
                                        btn.update()
                                    except Exception:
                                        pass
                            except Exception:
                                # fallback: rebuild the edit tab
                                switch_tab("edit")
                    except Exception:
                        pass
                except Exception:
                    pass

            name_field.on_change = on_name_changed

            # preview box for objects color
            preview = Container(width=48, height=32, border_radius=4)
            try:
                rgb = color_defs[idx]["attrs"]["objects"]
                preview.bgcolor = f"rgb({int(rgb[0])},{int(rgb[1])},{int(rgb[2])})"
            except Exception:
                preview.bgcolor = "#444444"

            # objects rgb fields
            r_field = TextField(value=str(c["attrs"]["objects"][0]), width=60, bgcolor=GRAY)
            g_field = TextField(value=str(c["attrs"]["objects"][1]), width=60, bgcolor=GRAY)
            b_field = TextField(value=str(c["attrs"]["objects"][2]), width=60, bgcolor=GRAY)

            def update_objects(e=None, ci=idx, rf=r_field, gf=g_field, bf=b_field, p=preview):
                try:
                    r = int(rf.value) if rf.value.strip() else 0
                    g = int(gf.value) if gf.value.strip() else 0
                    b = int(bf.value) if bf.value.strip() else 0
                    color_defs[ci]["attrs"]["objects"] = [r, g, b]
                    p.bgcolor = f"rgb({r},{g},{b})"
                    page.update()
                except Exception:
                    pass

            r_field.on_change = update_objects
            g_field.on_change = update_objects
            b_field.on_change = update_objects

            # buttons: up, down, remove
            def move_up(e, i=idx):
                if i <= 0:
                    return
                color_defs[i - 1], color_defs[i] = color_defs[i], color_defs[i - 1]
                def rebuild_color_list():
                    # Left list: compact buttons inside a scrollable ListView
                    color_list_view.controls.clear()
                    for idx, c in enumerate(color_defs):
                        preview = Container(width=36, height=22, border_radius=4)
                        try:
                            rgb = c["attrs"]["objects"]
                            preview.bgcolor = f"rgb({int(rgb[0])},{int(rgb[1])},{int(rgb[2])})"
                        except Exception:
                            preview.bgcolor = "#444444"

                        sel = (selected_color_idx == idx)
                        item = Button(content=Row([preview, Text(c["name"])], alignment="center", spacing=12), height=42, bgcolor="#1B3559" if sel else "#101824", style="outlined", on_click=lambda e, i=idx: select_color(i))
                        color_list_view.controls.append(item)
                    page.update()
                    pass
                rebuild_color_list()
                rebuild_civs_ui()
                page.update()

            def move_down(e, i=idx):
                if i >= len(color_defs) - 1:
                    return
                color_defs[i + 1], color_defs[i] = color_defs[i], color_defs[i + 1]
                def _rebuild():
                    color_list_view.controls.clear()
                    for idx, c in enumerate(color_defs):
                        preview = Container(width=36, height=22, border_radius=4)
                        try:
                            rgb = c["attrs"]["objects"]
                            preview.bgcolor = f"rgb({int(rgb[0])},{int(rgb[1])},{int(rgb[2])})"
                        except Exception:
                            preview.bgcolor = "#444444"
                        sel = (selected_color_idx == idx)
                        item = Button(content=Row([preview, Text(c["name"])], alignment="center", spacing=12), height=42, bgcolor="#1B3559" if sel else "#101824", style="outlined", on_click=lambda e, i=idx: select_color(i))
                        color_list_view.controls.append(item)
                    page.update()
                _rebuild()
                rebuild_civs_ui()
                page.update()

            def remove(e, i=idx):
                try:
                    if 0 <= i < len(color_defs):
                        color_defs.pop(i)
                except Exception:
                    pass
                # rebuild list and civ mappings
                color_list_view.controls.clear()
                for idx, c in enumerate(color_defs):
                    preview = Container(width=36, height=22, border_radius=4)
                    try:
                        rgb = c["attrs"]["objects"]
                        preview.bgcolor = f"rgb({int(rgb[0])},{int(rgb[1])},{int(rgb[2])})"
                    except Exception:
                        preview.bgcolor = "#444444"
                    sel = (selected_color_idx == idx)
                    item = Button(content=Row([preview, Text(c["name"])], alignment="center", spacing=12), height=42, bgcolor="#1B3559" if sel else "#101824", style="outlined", on_click=lambda e, i=idx: select_color(i))
                    color_list_view.controls.append(item)
                # adjust skirmish civ indices that referenced removed index
                for civ, lst in skirmish_civs.items():
                    for j in range(len(lst)):
                        if lst[j] is None:
                            lst[j] = 0
                        elif lst[j] >= len(color_defs):
                            lst[j] = max(0, len(color_defs) - 1)
                rebuild_civs_ui()
                rebuild_detail_editor()
                page.update()

            def apply_name(e=None, ci=idx, nf=name_field):
                try:
                    color_defs[ci]["name"] = nf.value.strip()
                    try:
                        if current_tab == "edit":
                            switch_tab("edit")
                    except Exception:
                        pass
                except Exception:
                    pass

            apply_btn = Button("Apply", on_click=apply_name)

            btn_row = Row([
                IconButton(icon=Icon("arrow_upward"), on_click=move_up, bgcolor="#101824"),
                IconButton(icon=Icon("arrow_downward"), on_click=move_down, bgcolor="#101824"),
                IconButton(icon=Icon("delete"), on_click=remove, bgcolor="#101824"),
                IconButton(icon=Icon("edit"), on_click=lambda e, ci=idx: select_color(ci), bgcolor="#101824"),
                IconButton(icon=Icon("expand_more" if not c.get("expanded") else "expand_less"), on_click=lambda e, ci=idx: (color_defs[ci].__setitem__("expanded", not color_defs[ci].get("expanded", False)), rebuild_color_list(), page.update()), bgcolor="#101824"),
            ], spacing=6)
            row = Row([preview, name_field, apply_btn, Text("R"), r_field, Text("G"), g_field, Text("B"), b_field, btn_row], alignment="spaceBetween")
            color_list_view.controls.append(row)

            # expanded area: editable RGB per attribute
            if c.get("expanded"):
                attrs_col = Column(spacing=6)
                for attr_name in ["objects", "corpse", "selection", "minimap", "ui", "captureeffects", "obscuringunit", "effects", "lights"]:
                    av = c["attrs"].get(attr_name, [0, 0, 0])
                    ar = TextField(value=str(av[0]), width=60, bgcolor=GRAY)
                    ag = TextField(value=str(av[1]), width=60, bgcolor=GRAY)
                    ab = TextField(value=str(av[2]), width=60, bgcolor=GRAY)

                    def make_update(ai, ci=idx, rf=ar, gf=ag, bf=ab):
                        def _u(e=None):
                            try:
                                r = int(rf.value) if rf.value.strip() else 0
                                g = int(gf.value) if gf.value.strip() else 0
                                b = int(bf.value) if bf.value.strip() else 0
                                color_defs[ci]["attrs"][ai] = [r, g, b]
                                # update preview for objects attr specially
                                if ai == "objects":
                                    try:
                                        preview.bgcolor = f"rgb({r},{g},{b})"
                                    except Exception:
                                        pass
                                page.update()
                            except Exception:
                                pass
                        return _u

                    ar.on_change = make_update(attr_name)
                    ag.on_change = make_update(attr_name)
                    ab.on_change = make_update(attr_name)

                    attrs_col.controls.append(Row([Text(attr_name, width=120), Text("R"), ar, Text("G"), ag, Text("B"), ab]))

                color_list_view.controls.append(Container(attrs_col, padding=6, bgcolor="#080D14"))
        page.update()
        page.update()

    # Civs UI: show civs and player slots with drag-and-drop reorder
    def make_player_slot(civ_name, player_idx, assigned_idx):
        # assigned_idx is index into color_defs or None
        preview = Container(width=36, height=24, border_radius=4)
        if assigned_idx is not None and 0 <= assigned_idx < len(color_defs):
            rgb = color_defs[assigned_idx]["attrs"]["objects"]
            preview.bgcolor = f"rgb({int(rgb[0])},{int(rgb[1])},{int(rgb[2])})"
            assigned_name = color_defs[assigned_idx]["name"]
        else:
            preview.bgcolor = "#0D1420"
            assigned_name = ""

        dd = Dropdown(options=color_options(), value=assigned_name, width=220)

        def on_select(e, civ=civ_name, p=player_idx, dropdown_ctl=dd):
            val = dropdown_ctl.value
            # find index
            ai = next((i for i,cd in enumerate(color_defs) if cd["name"]==val), None)
            if ai is not None:
                skirmish_civs[civ][p] = ai
                rebuild_civs_ui()
                page.update()

        dd.on_change = on_select

        # Draggable wrapper for reordering player slots (drag player index)
        def on_accept(e, dst_civ=civ_name, dst_idx=player_idx):
            try:
                data = e.data
                if not data:
                    return
                src_civ, src_idx = data
                src_list = skirmish_civs.get(src_civ, [])
                dst_list = skirmish_civs.get(dst_civ, [])
                # bounds
                if not (0 <= src_idx < len(src_list)):
                    return
                item = src_list.pop(src_idx)
                dst_list.insert(dst_idx, item)
                # trim or pad to 11
                while len(src_list) > 11:
                    src_list.pop()
                while len(dst_list) > 11:
                    dst_list.pop()
                while len(src_list) < 11:
                    src_list.append(0)
                while len(dst_list) < 11:
                    dst_list.append(0)
                rebuild_civs_ui()
                page.update()
            except Exception:
                pass

        draggable = Draggable(content=Row([preview, Text(f"P{player_idx}"), dd], spacing=12), group="players", data=(civ_name, player_idx))
        drag_target = DragTarget(on_accept=on_accept, content=draggable)
        return drag_target

    def rebuild_civs_ui():
        civs_col.controls.clear()
        for civ_name, slot_list in skirmish_civs.items():
            civ_header = Text(civ_name, weight="bold")
            slots = Column()
            for i in range(len(slot_list)):
                assigned_idx = slot_list[i]
                slot = make_player_slot(civ_name, i, assigned_idx)
                slots.controls.append(slot)
            civs_col.controls.append(Column([civ_header, slots, Divider()]))
        page.update()

    # Generate XML
    def generate_xml(e=None):
        xml = build_xml()
        try:
            from Modules.shared_outputs import outputs_registry
            outputs_registry["playercolors"] = xml
        except Exception:
            pass
        page.snack_bar = SnackBar(Text("playercolors.xml generated and saved to Outputs."), open=True)
        page.update()

    def build_xml():
        lines = ['<?xml version="1.0" encoding="us-ascii"?>', '<playerColors>']
        # skirmish colors
        lines.append('    <skirmish>')
        for c in color_defs:
            name = c.get("name", "")
            attrs = c.get("attrs", {})
            parts = []
            for k in ["objects", "corpse", "selection", "minimap", "ui", "captureeffects", "obscuringunit", "effects", "lights"]:
                parts.append(f'{k}="{rgb_str(attrs.get(k, [0,0,0]))}"')
            # export enum attribute if present on the color
            enum_val = ''
            try:
                enum_raw = c.get('enum', '')
                if enum_raw:
                    enum_val = f' enum="{enum_raw}"'
            except Exception:
                enum_val = ''
            attrs_str = ' '.join(parts)
            lines.append(f'        <color name="{name}" {attrs_str}{enum_val} />')
        # civ mapping
        for civ_name, slot_list in skirmish_civs.items():
            # Output civ block with the civ label appended to the last player line
            lines.append('        <civ>')
            for idx, assigned in enumerate(slot_list):
                cn = color_defs[assigned]["name"] if 0 <= assigned < len(color_defs) else ""
                # map index to expected player num ordering: 1..8, 0, 9, 10
                if idx < 8:
                    pnum = idx + 1
                elif idx == 8:
                    pnum = 0
                else:
                    pnum = idx
                # append civ label on the last player line, then close the civ tag on same line
                if idx == len(slot_list) - 1:
                    lines.append(f'            <player num="{pnum}" colorName="{cn}" />{civ_name}</civ>')
                else:
                    lines.append(f'            <player num="{pnum}" colorName="{cn}" />')
        lines.append('    </skirmish>')
        # spc (fixed block - exported exactly as required)
        lines.append('    <spc>')
        lines.append('        <color name="0" objects="175 175 175" corpse="88 88 88" selection="175 175 175" minimap="175 175 175" ui="48 244 230" captureeffects="175 175 175" obscuringunit="175 175 175" effects="175 175 175" lights="175 175 175" />')
        lines.append('        <color name="1" objects="43 77 60" corpse="35 55 12" selection="12 89 30" minimap="9 200 60" ui="48 244 230" captureeffects="50 170 255" obscuringunit="21 153 21" effects="50 90 50" lights="60 80 40 128" />')
        lines.append('        <color name="2" objects="180 150 40" corpse="248 227 33" selection="181 147 25" minimap="255 212 56" ui="48 244 230" captureeffects="50 170 255" obscuringunit="255 212 56" effects="180 150 40" lights="240 200 20" />')
        lines.append('        <color name="3" objects="48 121 189" corpse="48 121 189" selection="26 110 189" minimap="64 163 255" ui="48 244 230" captureeffects="50 170 255" obscuringunit="64 163 255" effects="48 121 189" lights="0 163 255" />')
        lines.append('        <color name="4" objects="225 35 35" corpse="225 35 35" selection="159 29 29" minimap="255 41 41" ui="48 244 230" captureeffects="50 170 255" obscuringunit="255 41 41" effects="225 35 35" lights="200 60 0" />')
        lines.append('        <color name="5" objects="220 220 220" corpse="25 25 15" selection="220 220 220" minimap="220 220 220" ui="48 244 230" captureeffects="50 170 255" obscuringunit="220 220 220" effects="220 220 220" lights="50 50 30" />')
        lines.append('        <color name="6" objects="185 160 125" corpse="93 50 63" selection="185 160 125" minimap="229 199 156" ui="48 244 230" captureeffects="50 170 255" obscuringunit="229 199 156" effects="185 160 125" lights="185 160 125" />')
        lines.append('        <color name="7" objects="255 0 178" corpse="83 48 172" selection="255 36 189" minimap="255 36 189" ui="48 244 230" captureeffects="230 20 20" obscuringunit="255 36 189" effects="255 0 178" lights="255 0 178" />')
        lines.append('        <color name="8" objects="35 100 225" corpse="35 100 225" selection="35 100 225" minimap="41 116 255" ui="48 244 230" captureeffects="230 20 20" obscuringunit="41 116 255" effects="35 100 225" lights="255 106 0" />')
        lines.append('        <color name="9" objects="215 50 30" corpse="105 10 0" selection="159 29 29" minimap="255 58 36" ui="48 244 230" captureeffects="230 20 20" obscuringunit="255 58 36" effects="215 50 30" lights="255 0 0" />')
        lines.append('        <color name="10" objects="40 50 20" corpse="20 25 10" selection="40 50 20" minimap="40 50 20" ui="48 244 230" captureeffects="230 20 20" obscuringunit="40 50 20" effects="40 50 20" lights="40 50 20" />')
        lines.append('        <color name="11" objects="255 215 50" corpse="128 107 25" selection="255 211 36" minimap="255 215 50" ui="48 244 230" captureeffects="230 20 20" obscuringunit="255 215 50" effects="255 215 50" lights="255 215 50" />')
        lines.append('        <color name="12" objects="215 190 175" corpse="108 95 87" selection="215 200 175" minimap="215 200 175" ui="48 244 230" captureeffects="230 20 20" obscuringunit="215 200 175" effects="215 190 175" lights="215 200 175" />')
        lines.append('        <color name="13" objects="225 35 35" corpse="225 35 35" selection="159 29 29" minimap="255 41 41" ui="48 244 230" captureeffects="50 170 255" obscuringunit="255 41 41" effects="225 35 35" lights="200 60 0" />')
        lines.append('        <color name="14" objects="175 175 175" corpse="88 88 88" selection="175 175 175" minimap="175 175 175" ui="48 244 230" captureeffects="175 175 175" obscuringunit="175 175 175" effects="175 175 175" lights="175 175 175" />')
        lines.append('        <color name="15" objects="255 0 255" corpse="255 0 255" selection="255 0 255" minimap="255 0 255" ui="255 0 255" captureeffects="255 0 255" obscuringunit="255 0 255" effects="255 0 255" lights="255 0 255" enum="flood" />')
        lines.append('        <color name="16" objects="250 145 20" corpse="250 145 20" selection="134 49 0" minimap="255 149 20" ui="48 244 230" captureeffects="230 20 20" obscuringunit="255 149 20" effects="141 61 15" lights="141 61 15" />')
        lines.append('        <color name="17" objects="175 175 175" corpse="88 88 88" selection="175 175 175" minimap="175 175 175" ui="48 244 230" captureeffects="175 175 175" obscuringunit="175 175 175" effects="175 175 175" lights="175 175 175" />')
        lines.append('        <color name="18" objects="175 175 175" corpse="88 88 88" selection="175 175 175" minimap="175 175 175" ui="48 244 230" captureeffects="175 175 175" obscuringunit="175 175 175" effects="175 175 175" lights="175 175 175" />')
        lines.append('        <color name="19" objects="175 175 175" corpse="88 88 88" selection="175 175 175" minimap="175 175 175" ui="48 244 230" captureeffects="175 175 175" obscuringunit="175 175 175" effects="175 175 175" lights="175 175 175" />')
        lines.append('        <color name="20" objects="175 175 175" corpse="88 88 88" selection="175 175 175" minimap="175 175 175" ui="48 244 230" captureeffects="175 175 175" obscuringunit="175 175 175" effects="175 175 175" lights="175 175 175" />')
        lines.append('        <civ>')
        lines.append('            <player num="0" colorName="0" />')
        lines.append('            <player num="1" colorName="1" />')
        lines.append('            <player num="2" colorName="2" />')
        lines.append('            <player num="3" colorName="3" />')
        lines.append('            <player num="4" colorName="4" />')
        lines.append('            <player num="5" colorName="5" />')
        lines.append('            <player num="6" colorName="6" />')
        lines.append('            <player num="7" colorName="13" />')
        lines.append('            <player num="8" colorName="14" />UNSC</civ>')
        lines.append('        <civ>')
        lines.append('            <player num="0" colorName="0" />')
        lines.append('            <player num="1" colorName="9" />')
        lines.append('            <player num="2" colorName="7" />')
        lines.append('            <player num="3" colorName="16" />')
        lines.append('            <player num="4" colorName="10" />')
        lines.append('            <player num="5" colorName="11" />')
        lines.append('            <player num="6" colorName="12" />')
        lines.append('            <player num="7" colorName="13" />')
        lines.append('            <player num="8" colorName="14" />Covenant</civ>')
        lines.append('        <civ>')
        lines.append('            <player num="0" colorName="15" />')
        lines.append('            <player num="1" colorName="15" />')
        lines.append('            <player num="2" colorName="15" />')
        lines.append('            <player num="3" colorName="15" />')
        lines.append('            <player num="4" colorName="15" />')
        lines.append('            <player num="5" colorName="15" />')
        lines.append('            <player num="6" colorName="15" />')
        lines.append('            <player num="7" colorName="15" />')
        lines.append('            <player num="8" colorName="15" />Flood</civ>')
        lines.append('    </spc>')
        lines.append('</playerColors>')
        return "\n".join(lines)

    def select_color(i, rebuild_list=True):
        nonlocal selected_color_idx
        try:
            selected_color_idx = int(i)
        except Exception:
            selected_color_idx = 0
        # expand only the selected color's expanded area so its attributes show in the left list
        try:
            for j in range(len(color_defs)):
                color_defs[j]["expanded"] = (j == selected_color_idx)
        except Exception:
            pass
        if rebuild_list:
            rebuild_color_list()
        rebuild_detail_editor()

    def rebuild_detail_editor():
        detail_col.controls.clear()
        try:
            c = color_defs[selected_color_idx]
        except Exception:
            page.update()
            return
        name_field = TextField(label="Name", value=c.get("name",""), bgcolor=GRAY, width=300)

        def on_name_change(e):
            c["name"] = name_field.value.strip()
            rebuild_color_list()
            page.update()

        name_field.on_change = on_name_change

        # large preview for objects color (updates live)
        big_preview = Container(width=120, height=60, border_radius=6)
        try:
            ov = c["attrs"].get("objects", [0,0,0])
            big_preview.bgcolor = f"rgb({ov[0]},{ov[1]},{ov[2]})"
        except Exception:
            big_preview.bgcolor = "#0D1420"

        previews = Row()
        attrs_controls = []
        # enum selector
        enum_dd = Dropdown(options=[dropdown.DropdownOption(o) for o in ["red","blue","white","flood"]], value=c.get("enum",""), width=220)

        def on_enum_change(e):
            try:
                c["enum"] = enum_dd.value
                rebuild_color_list()
                page.update()
            except Exception:
                pass

        enum_dd.on_change = on_enum_change
        # color-picker dialog creator
        def open_picker_for(ai, rf, pr):
            # Always use native tkinter color chooser. If unavailable, show a SnackBar and do nothing.
            try:
                import tkinter as _tk
                from tkinter import colorchooser as _cc
            except Exception:
                page.snack_bar = SnackBar(Text("Native color picker unavailable on this system."), open=True)
                page.update()
                return

            try:
                root = _tk.Tk()
                root.withdraw()
                try:
                    root.attributes('-topmost', True)
                    root.lift()
                    root.update()
                except Exception:
                    pass
                rgb_tuple, hexcol = _cc.askcolor(parent=root)
                try:
                    root.attributes('-topmost', False)
                except Exception:
                    pass
                root.destroy()
                if not rgb_tuple:
                    # user cancelled
                    return
                rv = int(rgb_tuple[0])
                gv = int(rgb_tuple[1])
                bv = int(rgb_tuple[2])
                try:
                    rf.value = f"{rv},{gv},{bv}"
                except Exception:
                    pass
                try:
                    c["attrs"][ai] = [rv, gv, bv]
                except Exception:
                    pass
                try:
                    pr.bgcolor = f"rgb({rv},{gv},{bv})"
                except Exception:
                    pass
                try:
                    if ai == "objects":
                        big_preview.bgcolor = f"rgb({rv},{gv},{bv})"
                except Exception:
                    pass
                rebuild_color_list()
                rebuild_detail_editor()
                page.update()
                return
            except Exception:
                page.snack_bar = SnackBar(Text("Native color picker failed to open."), open=True)
                page.update()
                return
        for attr in ["objects", "corpse", "selection", "minimap", "ui", "captureeffects", "obscuringunit", "effects", "lights"]:
            av = c["attrs"].get(attr, [0,0,0])
            preview = Container(width=72, height=36, border_radius=6)
            try:
                preview.bgcolor = f"rgb({av[0]},{av[1]},{av[2]})"
            except Exception:
                preview.bgcolor = "#0D1420"
            rgb_field = TextField(label=f"{attr} RGB", value=f"{av[0]},{av[1]},{av[2]}", width=260, bgcolor=GRAY)

            def make_updater(an, pr=preview, rf=rgb_field):
                def _u(e=None):
                    try:
                        s = (rf.value or "").strip()
                        s = s.replace(' ', ',')
                        parts = [p for p in s.split(',') if p != '']
                        rr = int(parts[0]) if len(parts) > 0 else 0
                        gg = int(parts[1]) if len(parts) > 1 else 0
                        bb = int(parts[2]) if len(parts) > 2 else 0
                        rr = max(0, min(255, rr))
                        gg = max(0, min(255, gg))
                        bb = max(0, min(255, bb))
                        c["attrs"][an] = [rr, gg, bb]
                        pr.bgcolor = f"rgb({rr},{gg},{bb})"
                        try:
                            if an == "objects":
                                big_preview.bgcolor = f"rgb({rr},{gg},{bb})"
                        except Exception:
                            pass
                        rebuild_color_list()
                        page.update()
                    except Exception:
                        pass
                return _u

            rgb_field.on_change = make_updater(attr)

            # add a Pick button that opens the color-picker dialog
            pick_btn = Button("Pick", on_click=lambda e, ai=attr, rf=rgb_field, pr=preview: open_picker_for(ai, rf, pr))
            # layout: a stacked block per attribute
            label = Text(attr.capitalize(), width=100)
            fields_row = Row([rgb_field], spacing=12)
            pick_row = Row([pick_btn], alignment="start")
            attrs_controls.append(Column([Row([preview, label], spacing=12), fields_row, pick_row, Divider()], spacing=6))

        detail_col.controls.append(name_field)
        detail_col.controls.append(Row([Text("Enum", width=80), enum_dd]))
        # show a larger preview and an instruction under the team color preview
        try:
            detail_col.controls.append(Column([big_preview, Text("Pick a color to edit!", color="#AAB8CA")], spacing=6))
        except Exception:
            pass
        detail_col.controls.append(Divider())
        for ac in attrs_controls:
            detail_col.controls.append(ac)
        # picker area removed; native picker is used instead
        page.update()

    def export_to_file(e=None):
        try:
            xml = build_xml()
            import tkinter as _tk
            from tkinter import filedialog as _filedialog
            root = _tk.Tk()
            try:
                root.withdraw()
                root.attributes('-topmost', True)
                root.update()
            except Exception:
                pass
            path = _filedialog.asksaveasfilename(parent=root, defaultextension='.xml', filetypes=[('XML files','*.xml'), ('All files','*.*')])
            try:
                root.attributes('-topmost', False)
            except Exception:
                pass
            root.destroy()
        except Exception:
            path = ''
        if not path:
            return
        try:
            with open(path, 'w', encoding='us-ascii') as f:
                f.write(xml)
            page.snack_bar = SnackBar(Text(f"Exported playercolors.xml to {path}"), open=True)
            page.update()
        except Exception as ex:
            page.snack_bar = SnackBar(Text(f"Export failed: {ex}"), open=True)
            page.update()

    def import_from_file(e=None):
        try:
            import tkinter as _tk
            from tkinter import filedialog as _filedialog
            root = _tk.Tk()
            try:
                root.withdraw()
                root.attributes('-topmost', True)
                root.update()
            except Exception:
                pass
            path = _filedialog.askopenfilename(parent=root, filetypes=[('XML files','*.xml'), ('All files','*.*')])
            try:
                root.attributes('-topmost', False)
            except Exception:
                pass
            root.destroy()
        except Exception:
            path = ''
        if not path:
            return
        try:
            tree = ET.parse(path)
            root = tree.getroot()
            sc = root.find('skirmish')
            if sc is not None:
                new_defs = []
                for col in sc.findall('color'):
                    name = col.get('name','')
                    attrs = {}
                    for k in ["objects","corpse","selection","minimap","ui","captureeffects","obscuringunit","effects","lights"]:
                        v = col.get(k,'0 0 0')
                        parts = [int(p) for p in v.split()[:3]] if v else [0,0,0]
                        attrs[k] = parts
                    enum_attr = col.get('enum','')
                    new_defs.append({"name":name, "attrs":attrs, "expanded":False, "enum": enum_attr})
                if new_defs:
                    color_defs.clear(); color_defs.extend(new_defs)
            # civ mapping
            if sc is not None:
                civs = sc.findall('civ')
                civ_names = list(skirmish_civs.keys())
                for i, civ_elem in enumerate(civs):
                    if i < len(civ_names):
                        cname = civ_names[i]
                        players = civ_elem.findall('player')
                        arr = []
                        for p in players:
                            cn = p.get('colorName','')
                            ai = next((idx for idx,cd in enumerate(color_defs) if cd['name']==cn), 0)
                            arr.append(ai)
                        while len(arr) < 11:
                            arr.append(0)
                        skirmish_civs[cname] = arr[:11]
            rebuild_color_list(); rebuild_civs_ui(); rebuild_detail_editor()
            page.snack_bar = SnackBar(Text(f"Imported playercolors.xml from {path}"), open=True)
            page.update()
        except Exception as ex:
            page.snack_bar = SnackBar(Text(f"Import failed: {ex}"), open=True)
            page.update()

    def export_playercolors_file(e=None):
        try:
            xml = build_xml()
            import tkinter as _tk
            from tkinter import filedialog as _filedialog
            root = _tk.Tk()
            try:
                root.withdraw()
                root.attributes('-topmost', True)
                root.update()
            except Exception:
                pass
            path = _filedialog.asksaveasfilename(parent=root, defaultextension='.xml', initialfile='playercolors.xml', filetypes=[('XML files','*.xml'), ('All files','*.*')])
            try:
                root.attributes('-topmost', False)
            except Exception:
                pass
            root.destroy()
        except Exception:
            path = ''
        if not path:
            return
        try:
            with open(path, 'w', encoding='us-ascii') as f:
                f.write(xml)
            page.snack_bar = SnackBar(Text(f"Exported playercolors.xml to {path}"), open=True)
            page.update()
        except Exception as ex:
            page.snack_bar = SnackBar(Text(f"Export failed: {ex}"), open=True)
            page.update()

    # initial build
    rebuild_color_list()
    rebuild_civs_ui()

    # Tidy layout: left = color definitions (scrollable), right = detail editor + civ mapping
    # left: fixed width list with action buttons above, right: expanding detail pane
    def reset_vanilla(e=None):
        color_defs.clear()
        for name, objects, corpse, selection, minimap, ui, captureeffects, obscuringunit, effects, lights, enum in DEFAULT_SKIRMISH:
            attrs = {
                "objects": [int(x) for x in objects.split()],
                "corpse": [int(x) for x in corpse.split()],
                "selection": [int(x) for x in selection.split()],
                "minimap": [int(x) for x in minimap.split()],
                "ui": [int(x) for x in ui.split()],
                "captureeffects": [int(x) for x in captureeffects.split()],
                "obscuringunit": [int(x) for x in obscuringunit.split()],
                "effects": [int(x) for x in effects.split()],
                "lights": [int(x) for x in lights.split()],
            }
            color_defs.append({"name": name, "attrs": attrs, "expanded": False, "enum": enum})
        rebuild_color_list()
        rebuild_civs_ui()
        page.update()

    def refresh_views(e=None):
        try:
            rebuild_color_list()
        except Exception:
            pass
        # if the Edit tab's color-buttons view exists, try to update in-place for speed
        try:
            if color_buttons_view is not None:
                try:
                    if len(color_buttons_view.controls) == len(color_defs):
                        # update existing buttons' preview and text
                        for i, cd in enumerate(color_defs):
                            try:
                                btn = color_buttons_view.controls[i]
                                row = getattr(btn, 'content', None)
                                if row and hasattr(row, 'controls') and len(row.controls) > 0:
                                    # preview at index 0
                                    prev = row.controls[0]
                                    try:
                                        rgb = cd['attrs']['objects']
                                        prev.bgcolor = f"rgb({int(rgb[0])},{int(rgb[1])},{int(rgb[2])})"
                                    except Exception:
                                        prev.bgcolor = "#444444"
                                    # text at index 1
                                    if len(row.controls) > 1:
                                        txt = row.controls[1]
                                        try:
                                            txt.value = cd.get('name','')
                                        except Exception:
                                            pass
                                try:
                                    btn.update()
                                except Exception:
                                    pass
                            except Exception:
                                pass
                    else:
                        # counts differ; rebuild controls to match current defs
                        color_buttons_view.controls.clear()
                        for i,cd in enumerate(color_defs):
                            preview = Container(width=36, height=22, border_radius=4)
                            try:
                                rgb = cd["attrs"]["objects"]
                                preview.bgcolor = f"rgb({int(rgb[0])},{int(rgb[1])},{int(rgb[2])})"
                            except Exception:
                                preview.bgcolor = "#444444"
                            sel = (selected_color_idx == i)
                            btn = Button(content=Row([preview, Text(cd.get("name",""))], alignment="center", spacing=12), height=42, bgcolor="#1B3559" if sel else "#101824", on_click=lambda e, ii=i: select_color(ii, False))
                            color_buttons_view.controls.append(btn)
                except Exception:
                    pass
        except Exception:
            pass
        try:
            rebuild_civs_ui()
        except Exception:
            pass
        try:
            rebuild_detail_editor()
        except Exception:
            pass
        page.update()

    actions_row = Row([
        Button("Import playercolors.xml", on_click=import_from_file),
        Button("Reset Vanilla", on_click=reset_vanilla),
        Button("Refresh", on_click=refresh_views),
    ], spacing=8)

    left_container = Container(Column([Text("Color Definitions", weight="bold"), actions_row, Divider(), color_list_view], spacing=8), padding=12, bgcolor="#101824", width=420, height=680)
    right_container = Container(Column([Text("Selected Color", weight="bold"), detail_col, Divider(), Text("Skirmish Civs", weight="bold"), civs_col], spacing=8), padding=12, bgcolor="#101824", expand=True)

    # Simple tab switcher (avoid Tab compatibility issues)
    # "Edit Order" tab should not have import/export controls; import/reset from Edit Colors affects it.
    workflow_actions = Row([], spacing=8)

    content_area = Column(expand=True)
    current_tab = "edit"

    def switch_tab(name):
        nonlocal current_tab, color_buttons_view
        current_tab = name
        # Edit view: actions, color selector dropdown, and detailed editor
        if name == "edit":
            # create a scrollable list of buttons for each color so clicking selects and shows details
            color_buttons = ListView(expand=False, spacing=6, padding=6, height=140)
            # expose to outer scope so other handlers can update it
            color_buttons_view = color_buttons
            for i,cd in enumerate(color_defs):
                preview = Container(width=36, height=22, border_radius=4)
                try:
                    rgb = cd["attrs"]["objects"]
                    preview.bgcolor = f"rgb({int(rgb[0])},{int(rgb[1])},{int(rgb[2])})"
                except Exception:
                    preview.bgcolor = "#444444"
                sel = (selected_color_idx == i)
                btn = Button(content=Row([preview, Text(cd.get("name",""))], alignment="center", spacing=12), height=42, bgcolor="#1B3559" if sel else "#101824", on_click=lambda e, ii=i: select_color(ii, False))
                color_buttons.controls.append(btn)

            # Instruction placed under the divider below the scrollable color buttons
            instruction = Text("Pick a team color from the list above to edit its attributes.", color="#AAB8CA")
            edit_col = Column([actions_row, color_buttons, Divider(), instruction, detail_col], spacing=12, expand=True)
            content_area.controls[:] = [edit_col]
        elif name == "workflow":
            content_area.controls[:] = [Column([workflow_actions, Divider(), civs_col], expand=True, spacing=12)]
        elif name == "export":
            export_section = Column([Text("Export Player Colors", weight="bold"), Button("Export playercolors.xml", on_click=export_playercolors_file)])
            content_area.controls[:] = [Column([export_section], expand=True, spacing=12)]
        page.update()

    # unify header button backgrounds for consistent appearance
    HEADER_BG = "#101824"
    edit_btn = Button("Edit Colors", on_click=lambda e: switch_tab("edit"), bgcolor=HEADER_BG)
    workflow_btn = Button("Edit Order", on_click=lambda e: switch_tab("workflow"), bgcolor=HEADER_BG)
    export_btn = Button("Export", on_click=lambda e: switch_tab("export"), bgcolor=HEADER_BG)

    header = Row([edit_btn, workflow_btn, export_btn], spacing=8)

    # initial content
    switch_tab("edit")

    content = Column([
        Text("Player Colors", size=24, weight="bold"),
        header,
        content_area,
    ], expand=True, spacing=12)

    setattr(content, "output_box", None)
    return content
