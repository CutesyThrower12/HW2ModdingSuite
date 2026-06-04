import os
from flet import (
    Column, Row, Text, TextField, Button, Divider, SnackBar, ScrollMode
)

def leader_power_tab(page):
    TEAL = "#a0cafd"
    GRAY = "#2b2b2b"

    # Controls (kept from original UIENT leader power implementation)
    lp_kind_value = "Active"

    def set_lp_kind(kind):
        nonlocal lp_kind_value
        lp_kind_value = kind
        lp_role_label.value = "ACTIVE POWER" if kind == "Active" else "PASSIVE POWER"
        page.update()

    active_btn = Button("Active", on_click=lambda e: set_lp_kind("Active"))
    passive_btn = Button("Passive", on_click=lambda e: set_lp_kind("Passive"))

    current_tiers = 1

    def set_tiers(n):
        nonlocal current_tiers
        current_tiers = max(1, min(3, int(n)))
        update_tier_display()

    tier_buttons = Row([
        Button("1", on_click=lambda e: set_tiers(1)),
        Button("2", on_click=lambda e: set_tiers(2)),
        Button("3", on_click=lambda e: set_tiers(3)),
    ], spacing=6)

    lp_base_id = TextField(label="Base Code Name (no UIENT. prefix)", hint_text="JacobConduitofRage", bgcolor=GRAY)
    lp_title = TextField(label="Power Title (ALL CAPS)", hint_text="DESPERATE MEASURES", bgcolor=GRAY)
    lp_role_label = TextField(label="Role label (e.g. ACTIVE POWER or PASSIVE POWER)", value="ACTIVE POWER", bgcolor=GRAY)
    lp_salespitch = TextField(label="Sales Pitch - Tier 1 only (multiline)", multiline=True, min_lines=2, max_lines=4, bgcolor=GRAY,
                              hint_text="Short description/sales pitch shown in UI for Tier 1.")

    lp_tier_shortdescrs = {1: TextField(multiline=True, min_lines=1, max_lines=3, bgcolor=GRAY, hint_text="Short description for tier 1"),
                           2: TextField(multiline=True, min_lines=1, max_lines=3, bgcolor=GRAY, hint_text="Short description for tier 2"),
                           3: TextField(multiline=True, min_lines=1, max_lines=3, bgcolor=GRAY, hint_text="Short description for tier 3")}

    lp_tier_pitches = {1: TextField(multiline=True, min_lines=1, max_lines=3, bgcolor=GRAY, hint_text="Upgrade pitch for tier 1 (leave blank to omit)"),
                       2: TextField(multiline=True, min_lines=1, max_lines=3, bgcolor=GRAY, hint_text="Upgrade pitch for tier 2 (leave blank to omit)")}

    tier_input_container = Column(spacing=10)

    def update_tier_display(e=None):
        tiers = int(current_tiers)
        tier_input_container.controls.clear()
        for i in range(1, tiers + 1):
            is_last = (i == tiers)
            controls = [
                Text(f"Tier {i}", weight="bold", size=12),
                Column([Text("Short Description", size=11), lp_tier_shortdescrs[i]], spacing=3)
            ]
            if not is_last:
                controls.append(Column([Text("Upgrade Pitch", size=11), lp_tier_pitches[i]], spacing=3))
            tier_input_container.controls.append(Column(controls, spacing=5))
        page.update()

    # initialize visuals
    set_lp_kind(lp_kind_value)
    update_tier_display(None)

    # output box
    output_box = TextField(label="Generated UIENT XML", multiline=True, min_lines=10, max_lines=20, bgcolor="#111111", expand=True)

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

    def generate_leader_power_xml(e=None):
        base_raw = lp_base_id.value.strip()
        if not base_raw:
            page.snack_bar = SnackBar(Text("Base code name required (UIENT. will be added automatically)."), open=True)
            page.update()
            return
        base_with_prefix = ensure_uient_prefix(base_raw)
        title = (lp_title.value.strip() or "POWER").upper()
        kind = lp_kind_value
        tiers = int(current_tiers)
        role_label = lp_role_label.value.strip() or ("ACTIVE POWER" if kind == "Active" else "PASSIVE POWER")
        sales = xml_escape_lines(lp_salespitch.value or "")
        lines = []
        for i in range(1, tiers + 1):
            tier_suffix = str(i)
            roman = ["I", "II", "III"][i - 1]
            title_t = f"{title} {roman}"
            id_with_tier = f"{base_with_prefix}{tier_suffix}"
            is_last_tier = (i == tiers)
            lines.append(f'<str id="{id_with_tier}.RADIALCENTER.NAME">{title_t}</str>')
            lines.append(f'<str id="{id_with_tier}.RADIALEDGE.NAME">{title_t}</str>')
            lines.append(f'<str id="{id_with_tier}.RADIALEDGE.ROLE">{role_label}</str>')
            if i == 1 and sales:
                lines.append(f'<str id="{id_with_tier}.RADIALEDGE.SALESPITCH">{sales}</str>')
            short = xml_escape_lines(lp_tier_shortdescrs[i].value or "")
            if short:
                lines.append(f'<str id="{id_with_tier}.RADIALEDGE.SHORTDESCR">{short}</str>')
            if not is_last_tier:
                upitch = xml_escape_lines(lp_tier_pitches[i].value or "")
                if upitch:
                    lines.append(f'<str id="{id_with_tier}.RADIALEDGE.UPGRADEPITCH">{upitch}</str>')
        output_box.value = "\n".join(lines)
        page.snack_bar = SnackBar(Text("Leader power UIENT generated — copy from Output tab."), open=True)
        page.update()
        try:
            from Modules.shared_outputs import outputs_registry
            outputs_registry["uient"] = output_box.value
        except Exception:
            pass

    def copy_output(e):
        if not output_box.value:
            page.snack_bar = SnackBar(Text("Nothing to copy — generate UIENT first."), open=True)
            page.update()
            return
        # Use set_clipboard if available, otherwise fall back to setting page.clipboard
        try:
            if hasattr(page, "set_clipboard") and callable(page.set_clipboard):
                page.set_clipboard(output_box.value)
            else:
                page.clipboard = output_box.value
        except Exception:
            try:
                page.clipboard = output_box.value
            except Exception:
                pass
        page.snack_bar = SnackBar(Text("UIENT XML copied to clipboard."), open=True)
        page.update()

    lp_generate = Button("Generate Leader Power UIENT", on_click=generate_leader_power_xml)
    copy_button = Button("Copy UIENT XML", on_click=copy_output)

    def reset_leader_tab(e=None):
        for c in [lp_base_id, lp_title, lp_role_label, lp_salespitch, *lp_tier_shortdescrs.values(), *lp_tier_pitches.values()]:
            c.value = ""
        set_lp_kind("Active")
        try:
            from Modules.shared_outputs import outputs_registry
            outputs_registry["uient"] = ""
        except Exception:
            pass
        page.update()

    reset_leader_button = Button("Reset Leader Fields", on_click=reset_leader_tab)

    content = Column([
        Text("UIENT Leader Power Builder", size=24, weight="bold"),
        Row([Row([active_btn, passive_btn], spacing=6), Text("Tiers:"), tier_buttons]),
        lp_base_id,
        lp_title,
        lp_role_label,
        lp_salespitch,
        Divider(),
        Text("Per-Tier Configuration", weight="bold", size=12),
        tier_input_container,
        Row([lp_generate, reset_leader_button], alignment="start"),
        Divider(),
        output_box,
        Row([copy_button], alignment="start")
    ], scroll=ScrollMode.AUTO, spacing=10, expand=True)

    setattr(content, "output_box", output_box)
    return content
