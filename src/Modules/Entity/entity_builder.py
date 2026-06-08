import os
from flet import (
    Column,
    Row,
    Text,
    TextField,
    Button,
    Dropdown,
    dropdown,
    Divider,
    Tabs,
    Tab,
    SnackBar,
)

# ---------------------------
# Entity Builder Module
# ---------------------------

def entity_builder_tab(page):
    TEAL = "#75D8FF"
    GRAY = "#0B1018"

    # ---------------------------
    # Helper: Snackbar
    # ---------------------------
    def show_snack(msg, color="white"):
        page.snack_bar = SnackBar(Text(msg, color=color))
        page.snack_bar.open = True
        page.update()

    # ---------------------------
    # Fields
    # ---------------------------
    key_field = TextField(label="Entity Key", hint_text="cov_inf_bruteJumpPack_02", bgcolor=GRAY, width=500)

    icon_field = TextField(
        label="Icon Path",
        hint_text=r"..\\textures\\hud\\icons\\entityIcons\\<your_icon>",
        value=r"..\textures\hud\icons\entityIcons\placeholder_modded",
        bgcolor=GRAY,
        width=600,
    )

    ability_field = TextField(
        label="Ability Icon Path (auto-generated from key)",
        value=r"..\textures\hud\icons\entityIcons\placeholder_modded_ability_icon",
        bgcolor=GRAY,
        width=600,
    )

    locked_default = r"..\textures\hud\icons\entityIcons\cov_bruteJumpPack_upgrade1_locked_icon"
    locked_field = TextField(
        label="Locked Icon Path (defaulted to hardcoded locked icon)",
        value=locked_default,
        bgcolor=GRAY,
        width=600,
    )

    uient_name = TextField(label="UIENT - Name (auto)", value="", bgcolor=GRAY, width=600)
    uient_role = TextField(label="UIENT - Role (auto)", value="", bgcolor=GRAY, width=600)

    ENTITY_TYPES = [
        "unit", "vehicle", "air", "upgrade", "uber",
        "supply", "power", "hq", "research",
        "turret", "turretCloak", "turretShield", "turretSensor"
    ]

    type_dropdown = Dropdown(
        label="Entity Type",
        options=[dropdown.DropdownOption(t) for t in ENTITY_TYPES] + [dropdown.DropdownOption("custom...")],
        value="unit",
        width=240,
    )

    custom_type_field = TextField(label="Custom Type (when selected above)", value="", bgcolor=GRAY, width=240)

    # Output box
    output_box = TextField(multiline=True, min_lines=12, max_lines=20, bgcolor="#080D14", width=900)

    # ---------------------------
    # Auto update ability path + UIENT when key changes
    # ---------------------------
    def refresh_from_key(e=None):
        k = key_field.value.strip()
        if not k:
            ability_field.value = ""
            uient_name.value = ""
            uient_role.value = ""
        else:
            ability_field.value = rf"..\textures\hud\icons\entityIcons\{k}_ability_icon"

            etype = type_dropdown.value
            if etype == "custom...":
                etype = custom_type_field.value.strip() or "unit"

            # Special case: upgrades use RadialCenter
            if etype == "upgrade":
                uient_name.value = f"UIENT.{k}.RadialCenter.Name"
                uient_role.value = "N/A"
            else:
                uient_name.value = f"UIENT.{k}.RadialEdge.Name"
                uient_role.value = f"UIENT.{k}.RadialEdge.Role"

        page.update()

    key_field.on_change = refresh_from_key

    def on_type_change(e):
        refresh_from_key()

    type_dropdown.on_change = on_type_change
    custom_type_field.on_change = on_type_change

    # ---------------------------
    # XML generation
    # ---------------------------
    def generate_xml(e):
        k = key_field.value.strip()
        if not k:
            show_snack("Entity Key is required.")
            return

        icon_val = icon_field.value.strip() or r"..\textures\hud\icons\entityIcons\placeholder_modded"
        ability_val = ability_field.value.strip() or rf"..\textures\hud\icons\entityIcons\{k}_ability_icon"
        locked_val = locked_field.value.strip() or locked_default

        name_val = uient_name.value.strip() or f"UIENT.{k}.RadialEdge.Name"
        role_val = uient_role.value.strip() or f"UIENT.{k}.RadialEdge.Role"

        t = type_dropdown.value
        if t == "custom...":
            t = custom_type_field.value.strip() or "unit"

        xml = "\n".join([
            "<entry>",
            f"\t<key>{k}</key>",
            f"\t<value>{icon_val}</value>",
            f"\t<value>{ability_val}</value>",
            f"\t<value>{locked_val}</value>",
            f"\t<value>{name_val}</value>",
            f"\t<value>{role_val}</value>",
            f"\t<value>{t}</value>",
            "</entry>",
        ])

        output_box.value = xml
        page.update()
        show_snack("Entity entry generated.", TEAL)
        try:
            from Modules.shared_outputs import outputs_registry
            outputs_registry["entity"] = output_box.value
        except Exception:
            pass

    # ---------------------------
    # Copy
    # ---------------------------
    def copy_xml(e):
        if not output_box.value:
            show_snack("Nothing to copy — generate XML first.")
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
        show_snack("Copied to clipboard.", TEAL)

    # ---------------------------
    # Reset
    # ---------------------------
    def reset_fields(e):
        key_field.value = ""
        icon_field.value = r"..\textures\hud\icons\entityIcons\placeholder_modded"
        ability_field.value = r"..\textures\hud\icons\entityIcons\placeholder_modded_ability_icon"
        locked_field.value = locked_default
        uient_name.value = ""
        uient_role.value = ""
        type_dropdown.value = "unit"
        custom_type_field.value = ""
        output_box.value = ""
        page.update()
        show_snack("All fields reset.", TEAL)
        try:
            from Modules.shared_outputs import outputs_registry
            outputs_registry["entity"] = ""
        except Exception:
            pass

    generate_button = Button("Generate XML", on_click=generate_xml)
    copy_button = Button("Copy XML", on_click=copy_xml)
    reset_button = Button("Reset", on_click=reset_fields)

    # ---------------------------
    # INPUT TAB
    # ---------------------------
    input_tab = Column(
        [
            Text("Entity Entry Builder", size=20, weight="bold"),
            key_field,
            icon_field,
            ability_field,
            locked_field,
            Divider(),
            Text("UIENT (auto)"),
            uient_name,
            uient_role,
            Divider(),
            Text("Type"),
            Row([type_dropdown, custom_type_field], spacing=10),
        ],
        spacing=12,
    )

    # ---------------------------
    # OUTPUT TAB
    # ---------------------------
    output_tab = Column(
        [
            output_box,
            Row([generate_button, copy_button, reset_button], spacing=20),
        ],
        spacing=10,
    )

    # Replace Tabs with header buttons + content area
    tab_contents = [input_tab, output_tab]
    content_area = Column(expand=True)

    def switch_tab(i):
        content_area.controls.clear()
        content_area.controls.append(tab_contents[i])
        page.update()

    headers = Row([
        Button("Entity", on_click=lambda e: switch_tab(0)),
        Button("Output", on_click=lambda e: switch_tab(1)),
    ], spacing=8)

    switch_tab(0)
    content = Column(
        [
            Text("Entity Builder", size=28, weight="bold"),
            headers,
            content_area
        ],
        expand=True,
        spacing=20
    )

    # expose output_box for external tools (Packager) to read
    setattr(content, "output_box", output_box)
    return content
