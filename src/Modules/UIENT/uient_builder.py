# save as Modules/UIENT/uient_builder.py
import os
import json
from flet import (
    Column,
    Row,
    Text,
    TextField,
    Button,
    Dropdown,
    dropdown,
    Divider,
    SnackBar,
    ScrollMode,
)

# Theme colors (match existing look)
TEAL = "#75D8FF"
GRAY = "#0B1018"

def uient_builder_tab(page):
    """
    Returns a Tabs widget for UIENT generation:
    - Tab 1: Unit/Building
    - Tab 2: Leader Power (single/multi-tier; active/passive)
    - Tab 3: Output / Copy
    """

    # ---------- Unit / Building Tab Controls ----------
    ub_base_id = TextField(label="Base Code Name (UIENT. prefix added automatically)", hint_text="cov_inf_RtavuScouts_01", bgcolor=GRAY, width=700)
    ub_center_name = TextField(label="RadialCenter Name (uppercase)", hint_text="ULTRA ELITES", bgcolor=GRAY, width=700)
    ub_edge_name = TextField(label="RadialEdge Name (uppercase)", hint_text="ULTRA ELITES", bgcolor=GRAY, width=700)
    ub_edge_role = TextField(label="RadialEdge Role (e.g. SCOUT)", hint_text="SCOUT", bgcolor=GRAY, width=400)
    ub_shortdescr = TextField(label="RadialEdge ShortDescr (multiline)", multiline=True, min_lines=3, max_lines=6, bgcolor=GRAY, width=700,
                              hint_text="Light damage\nMedium range\nFast capture rate\nShielded")

    # (Leader power has been moved to its own workflow/module: Modules/UIENT/leader_power_tab.py)

    # ---------- Output ----------
    output_box = TextField(label="Generated UIENT XML", multiline=True, min_lines=20, max_lines=40, bgcolor="#080D14", width=900)

    def xml_escape_lines(s: str):
        if s is None:
            return ""
        return s.replace("\r\n", "\n").rstrip()

    def ensure_uient_prefix(s: str):
        s = (s or "").strip()
        if not s:
            return ""
        if s.upper().startswith("UIENT."):
            return "UIENT." + s[len("UIENT."):].lstrip(".")
        return "UIENT." + s

    def generate_unit_building_xml(e=None):
        base_raw = ub_base_id.value.strip()
        if not base_raw:
            page.snack_bar = SnackBar(Text("Base code name required (UIENT. will be added automatically)."), open=True)
            page.update()
            return
        base = ensure_uient_prefix(base_raw)
        center = ub_center_name.value.strip() or ub_edge_name.value.strip() or ""
        edge_name = ub_edge_name.value.strip() or center
        role = ub_edge_role.value.strip() or ""
        short = xml_escape_lines(ub_shortdescr.value or "")
        lines = [
            f'<str id="{base}.RadialCenter.Name">{center}</str>',
            f'<str id="{base}.RadialEdge.Name">{edge_name}</str>'
        ]
        if role:
            lines.append(f'<str id="{base}.RadialEdge.Role">{role}</str>')
        if short:
            lines.append(f'<str id="{base}.RadialEdge.ShortDescr">{short}</str>')
        output_box.value = "\n".join(lines)
        page.snack_bar = SnackBar(Text("Unit/Building UIENT generated — copy from Output tab."), open=True)
        page.update()
        try:
            from Modules.shared_outputs import outputs_registry
            outputs_registry["uient"] = output_box.value
        except Exception:
            pass

    # leader-power functionality has been moved to Modules/UIENT/leader_power_tab.py

    ub_generate = Button("Generate Unit/Building UIENT", on_click=generate_unit_building_xml)

    def copy_output(e):
        if not output_box.value:
            page.snack_bar = SnackBar(Text("Nothing to copy — generate UIENT first."), open=True)
            page.update()
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
        page.snack_bar = SnackBar(Text("UIENT XML copied to clipboard."), open=True)
        page.update()

    copy_button = Button("Copy UIENT XML", on_click=copy_output)

    # Tooltip/help removed — it caused excessive vertical stretching

    # ---------- Reset Functions ----------
    def reset_unit_tab(e=None):
        for c in [ub_base_id, ub_center_name, ub_edge_name, ub_edge_role, ub_shortdescr]:
            c.value = ""
        page.update()

    reset_unit_button = Button("Reset Unit Fields", on_click=reset_unit_tab)

    # ---------- Tabs layout ----------
    unit_tab = Column([
        Text("UIENT Unit Builder", size=20, weight="bold"),
        ub_base_id,
        Row([ub_center_name], alignment="start"),
        ub_edge_name,
        ub_edge_role,
        ub_shortdescr,
        Row([ub_generate, reset_unit_button], alignment="start")
    ])

    output_tab = Column([
        output_box,
        Row([copy_button], alignment="start")
    ])

    # Use a simple header button switcher for compatibility with different Flet versions
    tab_contents = [unit_tab, output_tab]
    content_area = Column(expand=True)

    def switch_tab(i):
        content_area.controls.clear()
        content_area.controls.append(tab_contents[i])
        page.update()

    headers = Row([
        Button("Unit / Building", on_click=lambda e: switch_tab(0)),
        Button("Output", on_click=lambda e: switch_tab(1)),
    ], spacing=8)

    switch_tab(0)

    content = Column([
        Text("UIENT Builder", size=28, weight="bold"),
        headers,
        content_area
    ], expand=True, spacing=20)

    # expose output_box for external tools (Packager) to read
    setattr(content, "output_box", output_box)
    return content
