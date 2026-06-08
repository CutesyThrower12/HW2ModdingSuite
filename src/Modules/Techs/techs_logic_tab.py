import flet
from flet import (
    Column, Row, Text, TextField, Dropdown, dropdown,
    Button, Tabs, Tab, SnackBar
)

# ------------------------------------------------------------
# Techs Logic Builder
# ------------------------------------------------------------
def techs_logic_tab(page):
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
    # Dropdown data
    # ---------------------------
    factions = ["unsc", "cov"]
    base_tech_trees = ["unsc_basic", "cov_basic"]

    leader_tech_trees = [
        "unsc_leaderCutter", "unsc_leaderKeyes", "cov_leaderBrute", "cov_leaderElite"
    ]

    unit_or_building = ["Unit", "Building"]

    # ---------------------------
    # Fields
    # ---------------------------
    faction_dropdown = Dropdown(
        label="Faction",
        options=[dropdown.Option(f) for f in factions],
        value="unsc",
        width=200
    )

    base_tree_dropdown = Dropdown(
        label="Base Tech Tree",
        options=[dropdown.Option(t) for t in base_tech_trees],
        value="unsc_basic",
        width=200
    )

    type_dropdown = Dropdown(
        label="Type",
        options=[dropdown.Option(t) for t in unit_or_building],
        value="Unit",
        width=200
    )

    key_field = TextField(
        label="Unit/Building Key",
        hint_text="ex: unsc_inf_nerfedOdst_01 or unsc_bldg_vehicledepot_01",
        bgcolor=GRAY,
        width=400
    )

    exclusive_checkbox = Dropdown(
        label="Exclusivity",
        options=[dropdown.Option("All Leaders"), dropdown.Option("Single Leader")],
        value="All Leaders",
        width=200
    )

    leader_tree_dropdown = Dropdown(
        label="Leader Tech Tree (if Single Leader)",
        options=[dropdown.Option(l) for l in leader_tech_trees],
        value="unsc_leaderCutter",
        width=200
    )

    # ---------------------------
    # Output box
    # ---------------------------
    output_box = TextField(
        multiline=True,
        min_lines=12,
        max_lines=20,
        bgcolor="#080D14",
        width=900
    )

    # ---------------------------
    # XML Generation Logic
    # ---------------------------
    def generate_xml(e):
        key = key_field.value.strip()
        if not key:
            show_snack("Unit/Building Key is required!", "red")
            return

        type_val = type_dropdown.value
        target_type = "ProtoSquad" if type_val == "Unit" else "ProtoUnit"
        entry_type_lower = type_val.lower()

        faction_val = faction_dropdown.value
        base_tree = base_tree_dropdown.value
        exclusivity = exclusive_checkbox.value
        leader_tree = leader_tree_dropdown.value

        xml_blocks = []

        if exclusivity == "All Leaders":
            amount = 1
            comment = f"<!-- This {entry_type_lower} is available to all leaders -->\n" \
                      f"<!-- This {entry_type_lower} belongs in the {base_tree} tech tree ({faction_val})! -->"
            xml_blocks.append(f"""{comment}
<Effect type="Data" amount="{amount}" subtype="Enable" relativity="Absolute">
    <Target type="{target_type}">{key}</Target>
</Effect>""")
        else:
            # Single leader exclusivity
            # Disable in base tree
            comment_disable = f"<!-- This {entry_type_lower} is marked as leader exclusive! -->\n" \
                              f"<!-- This {entry_type_lower} belongs in the {base_tree} tech tree ({faction_val})! -->"
            xml_disable = f"""{comment_disable}
<Effect type="Data" amount="0" subtype="Enable" relativity="Absolute">
    <Target type="{target_type}">{key}</Target>
</Effect>"""

            # Enable in leader tech tree
            comment_enable = f"<!-- This {entry_type_lower} is marked as leader exclusive! -->\n" \
                             f"<!-- This {entry_type_lower} belongs in the {leader_tree} tech tree ({faction_val})! -->"
            xml_enable = f"""{comment_enable}
<Effect type="Data" amount="1" subtype="Enable" relativity="Absolute">
    <Target type="{target_type}">{key}</Target>
</Effect>"""

            xml_blocks = [xml_disable, xml_enable]

        output_box.value = "\n\n".join(xml_blocks)
        page.update()
        show_snack("Tech XML generated.", TEAL)
        try:
            from Modules.shared_outputs import outputs_registry
            outputs_registry["tech"] = output_box.value
        except Exception:
            pass

    # ---------------------------
    # Copy button
    # ---------------------------
    def copy_xml(e):
        if not output_box.value.strip():
            show_snack("Nothing to copy — generate XML first!", "red")
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
    # Reset button
    # ---------------------------
    def reset_fields(e):
        faction_dropdown.value = "unsc"
        base_tree_dropdown.value = "unsc_basic"
        type_dropdown.value = "Unit"
        key_field.value = ""
        exclusive_checkbox.value = "All Leaders"
        leader_tree_dropdown.value = "unsc_leaderCutter"
        output_box.value = ""
        page.update()
        show_snack("All fields have been reset.", TEAL)

    copy_button = Button("Copy XML", on_click=copy_xml)
    generate_button = Button("Generate XML", on_click=generate_xml)
    reset_button = Button("Reset", on_click=reset_fields)

    # ---------------------------
    # Layout
    # ---------------------------
    input_tab = Column(
        [
            Text("Tech Logic Builder", size=20, weight="bold"),
            Row([faction_dropdown, base_tree_dropdown, type_dropdown], spacing=15),
            key_field,
            Row([exclusive_checkbox, leader_tree_dropdown], spacing=15),
        ],
        spacing=12
    )

    output_tab = Column(
        [
            output_box,
            Row([generate_button, copy_button, reset_button], spacing=20)
        ],
        spacing=10
    )

    # Replace Tabs with header buttons + content area for compatibility
    tab_contents = [input_tab, output_tab]
    content_area = Column(expand=True)

    def switch_tab(i):
        content_area.controls.clear()
        content_area.controls.append(tab_contents[i])
        page.update()

    headers = Row([
        Button("Input", on_click=lambda e: switch_tab(0)),
        Button("Output", on_click=lambda e: switch_tab(1)),
    ], spacing=8)

    switch_tab(0)
    content = Column(
        [
            Text("Techs Logic Builder", size=28, weight="bold"),
            headers,
            content_area
        ],
        expand=True,
        spacing=20
    )

    # expose output_box for external tools (Packager) to read
    setattr(content, "output_box", output_box)
    return content
