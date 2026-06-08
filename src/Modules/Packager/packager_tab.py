import flet
from flet import Column, Row, Text, TextField, Checkbox, Button, ScrollMode, SnackBar
import os
from Modules.shared_styles_fix import OUTPUT_BG

def packager_tab(page, unit_tab=None, squad_tab=None, uient_tab=None, entity_tab=None, minimap_tab=None, tech_tab=None):
    TEAL = "#75D8FF"

    # ---------------------------
    # Helper: Snackbar
    # ---------------------------
    def show_snack(msg, color="white"):
        page.snack_bar = SnackBar(Text(msg, color=color))
        page.snack_bar.open = True
        page.update()

    # ---------------------------
    # Checkboxes for optional modules
    # ---------------------------
    cb_unit = Checkbox(label="Unit Builder", value=True)
    cb_squad = Checkbox(label="Squad Builder", value=True)
    cb_uient = Checkbox(label="UIENT Builder", value=True)
    cb_entity = Checkbox(label="Entity Builder", value=True)
    cb_minimap = Checkbox(label="Minimap Output", value=True)
    cb_decals = Checkbox(label="Decals Output", value=True)
    cb_tech = Checkbox(label="Tech Logic Builder", value=True)

    # ---------------------------
    # Output fields for each module
    # ---------------------------
    unit_box = TextField(label="Unit Builder Output", multiline=True, min_lines=6, max_lines=12, width=900, bgcolor=OUTPUT_BG)
    squad_box = TextField(label="Squad Builder Output", multiline=True, min_lines=6, max_lines=12, width=900, bgcolor=OUTPUT_BG)
    uient_box = TextField(label="UIENT Builder Output", multiline=True, min_lines=6, max_lines=12, width=900, bgcolor=OUTPUT_BG)
    entity_box = TextField(label="Entity Builder Output", multiline=True, min_lines=6, max_lines=12, width=900, bgcolor=OUTPUT_BG)
    minimap_box = TextField(label="Minimap Output", multiline=True, min_lines=6, max_lines=12, width=900, bgcolor=OUTPUT_BG)
    decals_box = TextField(label="Decals Output", multiline=True, min_lines=6, max_lines=12, width=900, bgcolor=OUTPUT_BG)
    tech_box = TextField(label="Tech Logic Builder Output", multiline=True, min_lines=6, max_lines=12, width=900, bgcolor=OUTPUT_BG)

    # ---------------------------
    # Final packaged output
    # ---------------------------
    final_output = TextField(label="Packaged Output", multiline=True, min_lines=12, max_lines=20, width=900, bgcolor=OUTPUT_BG)

    # ---------------------------
    # Packaging logic
    # ---------------------------
    def package_outputs(e):
        sections = []

        if cb_unit.value and unit_box.value.strip():
            sections.append("<!-- This belongs in the all_objects.xml! -->\n" + unit_box.value.strip())

        if cb_squad.value and squad_box.value.strip():
            sections.append("<!-- This belongs in the all_squads.xml! -->\n" + squad_box.value.strip())

        if cb_uient.value and uient_box.value.strip():
            sections.append("<!-- This belongs in the uient.xml! -->\n" + uient_box.value.strip())

        if cb_entity.value and entity_box.value.strip():
            sections.append("<!-- This belongs in the entities.xml! -->\n" + entity_box.value.strip())

        if cb_minimap.value and minimap_box.value.strip():
            sections.append("<!-- This belongs in the minimap.xml! -->\n" + minimap_box.value.strip())

        if cb_decals.value and decals_box.value.strip():
            sections.append("<!-- This belongs in both unsc_decals.xml and cov_decals.xml! -->\n" + decals_box.value.strip())

        if cb_tech.value and tech_box.value.strip():
            sections.append("<!-- This belongs in the techs.xml! -->\n" + tech_box.value.strip())

        if not sections:
            show_snack("No outputs to package!", "red")
            return

        final_output.value = "\n\n".join(sections)
        page.update()
        show_snack("Outputs packaged!", TEAL)

    # ---------------------------
    # Copy packaged output
    # ---------------------------
    def copy_final(e):
        if not final_output.value.strip():
            show_snack("Nothing to copy!", "red")
            return
        try:
            from Modules.shared_utils_fast import safe_set_clipboard
            safe_set_clipboard(page, final_output.value)
        except Exception:
            try:
                page.set_clipboard(final_output.value)
            except Exception:
                try:
                    page.clipboard = final_output.value
                except Exception:
                    pass
        show_snack("Packaged output copied!", TEAL)

    copy_button = Button("Copy Packaged Output", on_click=copy_final)
    package_button = Button("Package Outputs", on_click=package_outputs)
    # (GTS open/export helpers removed — this functionality is handled in Compile Mod workflow)

    # ---------------------------
    # Auto-fill from other tabs (if tab references were provided)
    # ---------------------------
    def auto_fill(e=None):
        filled = 0
        try:
            # prefer registry values when available
            from Modules.shared_outputs import outputs_registry
        except Exception:
            outputs_registry = {}
        try:
            if outputs_registry.get("unit"):
                unit_box.value = outputs_registry.get("unit")
                filled += 1
            elif unit_tab and hasattr(unit_tab, "output_box") and unit_tab.output_box.value.strip():
                unit_box.value = unit_tab.output_box.value
                filled += 1
            if outputs_registry.get("squad"):
                squad_box.value = outputs_registry.get("squad")
                filled += 1
            elif squad_tab and hasattr(squad_tab, "output_box") and squad_tab.output_box.value.strip():
                squad_box.value = squad_tab.output_box.value
                filled += 1
            if outputs_registry.get("uient"):
                uient_box.value = outputs_registry.get("uient")
                filled += 1
            elif uient_tab and hasattr(uient_tab, "output_box") and uient_tab.output_box.value.strip():
                uient_box.value = uient_tab.output_box.value
                filled += 1
            if outputs_registry.get("entity"):
                entity_box.value = outputs_registry.get("entity")
                filled += 1
            elif entity_tab and hasattr(entity_tab, "output_box") and entity_tab.output_box.value.strip():
                entity_box.value = entity_tab.output_box.value
                filled += 1
            # minimap / decals
            if outputs_registry.get("minimap"):
                minimap_box.value = outputs_registry.get("minimap")
                filled += 1
            elif minimap_tab and hasattr(minimap_tab, "minimap_output") and minimap_tab.minimap_output.value.strip():
                minimap_box.value = minimap_tab.minimap_output.value
                filled += 1
            if outputs_registry.get("decals"):
                decals_box.value = outputs_registry.get("decals")
                filled += 1
            elif minimap_tab and hasattr(minimap_tab, "decals_output") and minimap_tab.decals_output.value.strip():
                decals_box.value = minimap_tab.decals_output.value
                filled += 1
            if outputs_registry.get("tech"):
                tech_box.value = outputs_registry.get("tech")
                filled += 1
            elif tech_tab and hasattr(tech_tab, "output_box") and tech_tab.output_box.value.strip():
                tech_box.value = tech_tab.output_box.value
                filled += 1
        except Exception:
            pass
        page.update()
        if filled:
            show_snack(f"Auto-filled {filled} outputs.", TEAL)
        else:
            show_snack("No outputs found to auto-fill.", "red")
    autofill_button = Button("Auto-fill from open builders", on_click=auto_fill)
    # ---------------------------
    # Layout
    # ---------------------------
    layout = Column(
        [
            Text("Packager Module", size=20, weight="bold"),
            Row([cb_unit, cb_squad, cb_uient, cb_entity, cb_minimap, cb_decals, cb_tech], spacing=15),
            unit_box,
            squad_box,
            uient_box,
            entity_box,
            minimap_box,
            decals_box,
            tech_box,
            Row([autofill_button, package_button, copy_button], spacing=12),
            final_output,
        ],
        scroll="always",
        expand=True,
        spacing=12
    )

    # perform an immediate auto-fill when the Packager is created/opened
    try:
        auto_fill()
    except Exception:
        pass

    return layout
