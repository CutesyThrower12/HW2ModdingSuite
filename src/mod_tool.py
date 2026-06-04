import os, sys
import flet
from flet import (
    Page, Row, Column, Text, Button, Container,
    alignment, Image, Stack, Animation, ScrollMode, TextField, Checkbox, Divider, SnackBar
)
from flet import ProgressBar
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SRC_DIR)
BASE_DIR = getattr(sys, "_MEIPASS", PROJECT_ROOT)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
os.chdir(BASE_DIR)

def runtime_path(*parts: str) -> str:
    return os.path.join(BASE_DIR, *parts)

def asset_path(name: str) -> str:
    return runtime_path("assets", name)

if "--particle-editor" in sys.argv:
    from pfx_editor_pyside import main as _particle_editor_main
    raise SystemExit(_particle_editor_main())
if not hasattr(flet, "icons"):
    class _Icons:
        def __getattr__(self, name: str) -> str:
            # Flet accepts icon names as strings
            return name.lower()
    flet.icons = _Icons()
import asyncio
import inspect
import subprocess
from concurrent.futures import ThreadPoolExecutor
import re
import time
from Modules.shared_styles_fix import (
    TEAL, PANEL_BG, CARD_BG, SIDEBAR_BG, INPUT_BG, OUTPUT_BG,
    CARD_PADDING, RADIUS, PANEL_WIDTH, HERO_WIDTH, TEXT_MUTED, SMALL_WIDTH,
)

def main(page: Page):
    page.title = "Halo Wars 2 Modding Suite"
    page.theme_mode = "dark"
    page.bgcolor = "#121212"
    page.window.icon = asset_path("icon.ico")
    # Defer centering until after the UI is constructed (done in load_main_ui())
    page.window.width = 1200
    page.window.height = 800

    # Early aggressive attempt to set window position immediately to avoid visible jump
    try:
        try:
            w_early = int(page.window.width)
        except Exception:
            w_early = getattr(page.window, 'width', None) or 1200
        try:
            h_early = int(page.window.height)
        except Exception:
            h_early = getattr(page.window, 'height', None) or 800
        if os.name == 'nt':
            try:
                import ctypes
                from ctypes import wintypes

                SPI_GETWORKAREA = 0x0030

                class RECT(ctypes.Structure):
                    _fields_ = [('left', wintypes.LONG), ('top', wintypes.LONG), ('right', wintypes.LONG), ('bottom', wintypes.LONG)]

                rect = RECT()
                ok = ctypes.windll.user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0)
                if ok:
                    screen_w = rect.right - rect.left
                    screen_h = rect.bottom - rect.top
                    left_early = rect.left + max(0, (screen_w - w_early) // 2)
                    top_early = rect.top + max(0, (screen_h - h_early) // 2)
                    try:
                        page.window.left = int(left_early)
                        page.window.top = int(top_early)
                        try:
                            page.update()
                        except Exception:
                            pass
                    except Exception:
                        pass
            except Exception:
                pass
        else:
            try:
                import tkinter as _tk
                root = _tk.Tk()
                root.withdraw()
                screen_w = root.winfo_screenwidth()
                screen_h = root.winfo_screenheight()
                root.destroy()
                left_early = max(0, (screen_w - w_early) // 2)
                top_early = max(0, (screen_h - h_early) // 2)
                try:
                    page.window.left = int(left_early)
                    page.window.top = int(top_early)
                    try:
                        page.update()
                    except Exception:
                        pass
                except Exception:
                    pass
            except Exception:
                pass
    except Exception:
        pass

    INTRO_DURATION = 8.0  # seconds

    INTRO_PATH = asset_path("intro.mp4")
    PLAY_INTRO = (os.getenv("SKIP_INTRO", "0") != "1") and os.path.exists(INTRO_PATH)
    intro_finalized = False

    # Only create and add the intro video/overlay if the intro file exists and intro is enabled
    if PLAY_INTRO:
        fade_layer = Container(
            bgcolor="black",
            opacity=1.0,
            expand=True,
            animate_opacity=Animation(1000, "easeOut"),
        )
        intro_video = None
        try:
            from flet_video import Video, VideoMedia
            intro_video = Video(
                expand=True,
                autoplay=True,
                playlist=[VideoMedia(INTRO_PATH)],
                fit="contain",
                muted=False,
            )

            def skip_intro(e=None):
                nonlocal fade_layer, intro_video, intro_finalized
                try:
                    if intro_video is not None and hasattr(intro_video, "stop"):
                        try:
                            res = intro_video.stop()
                            # if stop returned a coroutine, schedule it on the running loop
                            if inspect.isawaitable(res):
                                    try:
                                        loop = asyncio.get_running_loop()
                                    except RuntimeError:
                                        loop = None
                                    if loop and loop.is_running():
                                        async def _safe_stop(coro):
                                            try:
                                                await coro
                                            except Exception:
                                                pass
                                        loop.create_task(_safe_stop(res))
                        except Exception:
                            pass
                except Exception:
                    pass
                # mark that we've already finalized intro and load UI now
                intro_finalized = True
                fade_layer = None
                try:
                    load_main_ui()
                except Exception:
                    pass

            # Attempt to center the window immediately so the intro appears centered
            try:
                try:
                    w = int(page.window.width)
                except Exception:
                    w = getattr(page.window, 'width', None) or 1200
                try:
                    h = int(page.window.height)
                except Exception:
                    h = getattr(page.window, 'height', None) or 800
                left = None
                top = None
                if os.name == 'nt':
                    try:
                        import ctypes
                        from ctypes import wintypes

                        SPI_GETWORKAREA = 0x0030

                        class RECT(ctypes.Structure):
                            _fields_ = [('left', wintypes.LONG), ('top', wintypes.LONG), ('right', wintypes.LONG), ('bottom', wintypes.LONG)]

                        rect = RECT()
                        ok = ctypes.windll.user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0)
                        if ok:
                            screen_w = rect.right - rect.left
                            screen_h = rect.bottom - rect.top
                            left = rect.left + max(0, (screen_w - w) // 2)
                            top = rect.top + max(0, (screen_h - h) // 2)
                    except Exception:
                        left = None
                        top = None
                else:
                    try:
                        import tkinter as _tk
                        root = _tk.Tk()
                        root.withdraw()
                        screen_w = root.winfo_screenwidth()
                        screen_h = root.winfo_screenheight()
                        root.destroy()
                        left = max(0, (screen_w - w) // 2)
                        top = max(0, (screen_h - h) // 2)
                    except Exception:
                        left = None
                        top = None

                if left is not None and top is not None:
                    try:
                        page.window.left = int(left)
                        page.window.top = int(top)
                        try:
                            page.update()
                        except Exception:
                            pass
                    except Exception:
                        pass
            except Exception:
                pass

            # add intro video and dark fade overlay
            page.add(Stack([intro_video, fade_layer], expand=True))

            # register a keyboard handler to skip intro on Spacebar
            def _on_key(e):
                try:
                    k = None
                    if hasattr(e, "key"):
                        k = e.key
                    elif hasattr(e, "code"):
                        k = e.code
                    elif hasattr(e, "data"):
                        k = e.data
                    elif hasattr(e, "key_code"):
                        k = e.key_code
                    # accept numeric 32 or string matches
                    if k in (" ", "Space", "Spacebar", 32) or str(k).lower() == "space":
                        try:
                            skip_intro()
                        except Exception:
                            pass
                        try:
                            page.on_keyboard_event = None
                        except Exception:
                            pass
                except Exception:
                    pass

            try:
                page.on_keyboard_event = _on_key
            except Exception:
                pass
        except Exception:
            # if video support isn't available, skip intro gracefully
            fade_layer = None
    else:
        # no intro; continue directly to UI (load_main_ui will be called below)
        fade_layer = None

    async def play_intro_then_load_ui():
        # fade out overlay so intro is visible, wait then load main UI
        nonlocal intro_finalized
        if intro_finalized:
            return
        if fade_layer is not None:
            try:
                fade_layer.opacity = 0
                page.update()
            except Exception:
                pass
        await asyncio.sleep(0.5)
        await asyncio.sleep(INTRO_DURATION)
        if intro_finalized:
            return
        if fade_layer is not None:
            try:
                fade_layer.animate_opacity = Animation(1000, "easeOut")
                fade_layer.opacity = 0
                page.update()
            except Exception:
                pass
        await asyncio.sleep(0.25)
        if not intro_finalized:
            intro_finalized = True
            load_main_ui()

    def _center_window_exact():
        try:
            # prefer work area (excludes taskbar) on Windows
            try:
                w = int(page.window.width)
            except Exception:
                w = getattr(page.window, 'width', None) or 1200
            try:
                h = int(page.window.height)
            except Exception:
                h = getattr(page.window, 'height', None) or 800
            left = None
            top = None
            if os.name == 'nt':
                try:
                    import ctypes
                    from ctypes import wintypes

                    SPI_GETWORKAREA = 0x0030

                    class RECT(ctypes.Structure):
                        _fields_ = [('left', wintypes.LONG), ('top', wintypes.LONG), ('right', wintypes.LONG), ('bottom', wintypes.LONG)]

                    rect = RECT()
                    ok = ctypes.windll.user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0)
                    if ok:
                        screen_w = rect.right - rect.left
                        screen_h = rect.bottom - rect.top
                        left = rect.left + max(0, (screen_w - w) // 2)
                        top = rect.top + max(0, (screen_h - h) // 2)
                    else:
                        screen_w = ctypes.windll.user32.GetSystemMetrics(0)
                        screen_h = ctypes.windll.user32.GetSystemMetrics(1)
                        left = max(0, (screen_w - w) // 2)
                        top = max(0, (screen_h - h) // 2)
                except Exception:
                    left = None
                    top = None
            else:
                try:
                    import tkinter as _tk
                    root = _tk.Tk()
                    root.withdraw()
                    screen_w = root.winfo_screenwidth()
                    screen_h = root.winfo_screenheight()
                    root.destroy()
                    left = max(0, (screen_w - w) // 2)
                    top = max(0, (screen_h - h) // 2)
                except Exception:
                    left = None
                    top = None

            if left is not None and top is not None:
                try:
                    page.window.left = int(left)
                    page.window.top = int(top)
                    try:
                        page.update()
                    except Exception:
                        pass
                except Exception:
                    pass
        except Exception:
            pass

    def _ensure_window_position_immediate(attempts: int = 30, delay: float = 0.02):
        try:
            import time as _time
            # compute desired left/top once
            try:
                w = int(page.window.width)
            except Exception:
                w = getattr(page.window, 'width', None) or 1200
            try:
                h = int(page.window.height)
            except Exception:
                h = getattr(page.window, 'height', None) or 800

            desired_left = None
            desired_top = None
            if os.name == 'nt':
                try:
                    import ctypes
                    from ctypes import wintypes
                    SPI_GETWORKAREA = 0x0030

                    class RECT(ctypes.Structure):
                        _fields_ = [('left', wintypes.LONG), ('top', wintypes.LONG), ('right', wintypes.LONG), ('bottom', wintypes.LONG)]

                    rect = RECT()
                    ok = ctypes.windll.user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0)
                    if ok:
                        screen_w = rect.right - rect.left
                        screen_h = rect.bottom - rect.top
                        desired_left = rect.left + max(0, (screen_w - w) // 2)
                        desired_top = rect.top + max(0, (screen_h - h) // 2)
                except Exception:
                    desired_left = None
                    desired_top = None
            else:
                try:
                    import tkinter as _tk
                    root = _tk.Tk()
                    root.withdraw()
                    screen_w = root.winfo_screenwidth()
                    screen_h = root.winfo_screenheight()
                    root.destroy()
                    desired_left = max(0, (screen_w - w) // 2)
                    desired_top = max(0, (screen_h - h) // 2)
                except Exception:
                    desired_left = None
                    desired_top = None

            if desired_left is None or desired_top is None:
                return

            for _ in range(max(1, attempts)):
                try:
                    page.window.left = int(desired_left)
                    page.window.top = int(desired_top)
                    try:
                        page.update()
                    except Exception:
                        pass
                    # quick check: if applied, break
                    try:
                        cur_l = int(getattr(page.window, 'left', -9999))
                        cur_t = int(getattr(page.window, 'top', -9999))
                        if cur_l == int(desired_left) and cur_t == int(desired_top):
                            break
                    except Exception:
                        pass
                except Exception:
                    pass
                try:
                    _time.sleep(max(0.001, float(delay)))
                except Exception:
                    pass
        except Exception:
            pass

    def load_main_ui():
            page.clean()

            # Top-level content area that will host Home / Workflows / Tools
            from Modules.shared_styles_fix import (
                TEAL, PANEL_BG, CARD_BG, SIDEBAR_BG, INPUT_BG, OUTPUT_BG,
                CARD_PADDING, RADIUS, PANEL_WIDTH, HERO_WIDTH, TEXT_MUTED,
            )
            top_content = Column(expand=True)
            card_style = dict(padding=CARD_PADDING, border_radius=RADIUS, bgcolor=CARD_BG)

            # Home content — hero banner + feature cards (visual only)

            hero = Container(
                Column([
                    Text("Halo Wars 2 Modding Suite", size=36, weight="bold"),
                    Text("Builders · Converters · Packaging", size=14, color="white70"),
                ], alignment="center", horizontal_alignment="center"),
                padding=24,
                width=HERO_WIDTH,
                bgcolor=PANEL_BG,
                border_radius=RADIUS,
            )

            card_style = dict(padding=CARD_PADDING, border_radius=RADIUS, bgcolor=CARD_BG)

            features = Row([
                Container(Column([Text("Workflows", size=16, weight="bold"), Text("Step-by-step builders for Units, Squads, UIENT, Entity and more.", color="white70", size=12), Button("Open", on_click=lambda e: set_top_content(workflows_list))], spacing=8), **card_style, expand=True),
                Container(Column([Text("Tools", size=16, weight="bold"), Text("Quick format conversions: DDS/DDX, Ancilla, Phoenix.", color="white70", size=12), Button("Open", on_click=lambda e: set_top_content(tools_list))], spacing=8), **card_style, expand=True),
            ], spacing=16, expand=True)

            home_content = Column([
                hero,
                Divider(),
                features,
                Divider(),
                Column([Text("Created by", size=18, weight="bold"), Text("CutesyThrower12", size=14, color="white70")], spacing=6, alignment="center", horizontal_alignment="center"),
            ], alignment="center", horizontal_alignment="center", expand=True, spacing=16)

            # Lazy-create builder tabs to speed up startup; create on first use
            unit_tab_content = None
            squad_tab_content = None
            uient_tab_content = None
            entity_tab_content = None
            minimap_tab_content = None
            tech_tab_content = None
            leader_tab_content = None
            packager_tab_content = None
            player_colors_tab_content = None

            def get_unit_tab():
                nonlocal unit_tab_content
                if unit_tab_content is None:
                    from ui_main import unit_builder_tab
                    unit_tab_content = unit_builder_tab(page)
                return unit_tab_content

            def get_squad_tab():
                nonlocal squad_tab_content
                if squad_tab_content is None:
                    from Modules.SquadBuilder.squad_builder import squad_builder_tab
                    squad_tab_content = squad_builder_tab(page)
                return squad_tab_content

            def get_uient_tab():
                nonlocal uient_tab_content
                if uient_tab_content is None:
                    from Modules.UIENT.uient_builder import uient_builder_tab
                    uient_tab_content = uient_builder_tab(page)
                return uient_tab_content

            def get_entity_tab():
                nonlocal entity_tab_content
                if entity_tab_content is None:
                    from Modules.Entity.entity_builder import entity_builder_tab
                    entity_tab_content = entity_builder_tab(page)
                return entity_tab_content

            def get_minimap_tab():
                nonlocal minimap_tab_content
                if minimap_tab_content is None:
                    from Modules.Minimap.minimap_and_decals_tab import minimap_and_decals_tab
                    minimap_tab_content = minimap_and_decals_tab(page)
                return minimap_tab_content

            def get_tech_tab():
                nonlocal tech_tab_content
                if tech_tab_content is None:
                    from Modules.Techs.techs_logic_tab import techs_logic_tab
                    tech_tab_content = techs_logic_tab(page)
                return tech_tab_content

            def get_leader_tab():
                nonlocal leader_tab_content
                if leader_tab_content is None:
                    from Modules.UIENT.leader_power_tab import leader_power_tab
                    leader_tab_content = leader_power_tab(page)
                return leader_tab_content

            def get_player_colors_tab():
                nonlocal player_colors_tab_content
                if player_colors_tab_content is None:
                    from Modules.PlayerColors.player_colors_tab import player_colors_tab
                    player_colors_tab_content = player_colors_tab(page)
                return player_colors_tab_content

            def get_packager_tab():
                nonlocal packager_tab_content
                if packager_tab_content is None:
                    from Modules.Packager.packager_tab import packager_tab
                    # ensure dependent tabs are created (packager reads their outputs)
                    packager_tab_content = packager_tab(page, get_unit_tab(), get_squad_tab(), get_uient_tab(), get_entity_tab(), get_minimap_tab(), get_tech_tab())
                return packager_tab_content

            # Helper to replace top_content contents
            def set_top_content(content):
                top_content.controls.clear()
                top_content.controls.append(content)
                page.update()

            # ------------------
            # Workflows UI
            # ------------------
            # When a workflow is selected we will show its sidebar and workflow area
            workflow_area = Column(expand=True)

            def open_custom_unit_workflow(e=None):
                # Build workflow sidebar (these buttons exclusively belong to this workflow)
                def switch_workflow_tab(tab_content):
                    workflow_main.controls.clear()
                    workflow_main.controls.append(tab_content)
                    page.update()

                workflow_main = Column(expand=True, scroll=ScrollMode.AUTO)

                # overview content for this workflow (styled hero + cards)
                wf_hero = Container(
                    Column([
                        Text("Custom Unit Workflow", size=24, weight="bold"),
                        Text("Guides you through preparing a custom unit for Halo Wars 2.", size=14, color="white70"),
                    ], alignment="start", horizontal_alignment="start"),
                    padding=16,
                    bgcolor=PANEL_BG,
                    border_radius=RADIUS,
                    width=PANEL_WIDTH,
                )

                # Build a stylized overview using cards for consistency
                steps = [
                    ("🖼️", "Prepare assets", "Create visuals (.vis) and textures; use the Tools tab (DDS/DDX) as needed."),
                    ("⚙️", "Create unit data", "Open the Unit Builder to define code names, stats, hitpoints and damage types."),
                    ("⚔️", "Assemble squads", "Use the Squad Builder to define squad composition, counters and behaviors."),
                    ("📝", "Edit UI strings", "Use the UIENT builder to generate string entries for the UI."),
                    ("🧬", "Create entities", "Author Object definitions and link visuals in the Entity builder."),
                    ("🗺️", "Minimap & Decals", "Configure minimap icons and decals in the Minimap tab."),
                    ("🔧", "Techs & Validate", "Validate tech logic and ensure compatibility in the Techs builder."),
                    ("📦", "Package", "Gather outputs and build your package with the Packager."),
                    ("📥", "Import/Apply", "Paste packaged outputs into the correct XML paths for the game."),
                ]

                # Preset examples for unit previews
                PRESET_NAMES = [
                    "Marine", "Warthog", "Scorpion", "Nightingale", "Hornet",
                    "Grunt", "Ghost", "Wraith", "Engineer", "Banshee",
                    "Honor Guard", "Spartan", "Condor", "Scarab",
                ]

                PRESETS = {
                    "Marine": {"code": "unsc_inf_marine_01", "display": "Marine", "role": "Infantry", "hp": "1050", "armor": "Light", "los": "65", "accel": "12", "vel": "12", "dmg_cover": "LightInCover", "desc": "Basic human infantry.", "bounty": "1.25", "veterancy": [{"Level":"1","XP":"1.25","Damage":"1.14999998","Velocity":"1","Accuracy":"1.60000002","WorkRate":"1","WeaponRange":"1","DamageTaken":"0.870000005"},{"Level":"2","XP":"3.75","Damage":"1.25","Velocity":"1","Accuracy":"1.70000005","WorkRate":"1","WeaponRange":"1","DamageTaken":"0.800000012"},{"Level":"3","XP":"7.5","Damage":"1.35000002","Velocity":"1","Accuracy":"1.79999995","WorkRate":"1","WeaponRange":"1","DamageTaken":"0.74000001"}]},
                    "Warthog": {"code": "unsc_veh_warthog_01", "display": "Warthog", "role": "Vehicle", "hp": "6562", "armor": "Medium", "los": "65", "accel": "20", "vel": "21", "desc": "Fast scout vehicle with turret.", "bounty": "15", "veterancy": [{"Level":"1","XP":"22","Damage":"1.14999998","Velocity":"1","Accuracy":"1.60000002","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.870000005"},{"Level":"2","XP":"55","Damage":"1.25","Velocity":"1","Accuracy":"1.70000005","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.800000012"},{"Level":"3","XP":"99","Damage":"1.35000002","Velocity":"1","Accuracy":"1.79999995","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.74000001"}]},
                    "Scorpion": {"code": "unsc_veh_scorpion_01", "display": "Scorpion", "role": "Vehicle", "hp": "12750", "armor": "Heavy", "los": "65", "accel": "12", "vel": "9", "desc": "Heavy assault tank.", "bounty": "25", "veterancy": [{"Level":"1","XP":"40","Damage":"1.14999998","Velocity":"1","Accuracy":"1.60000002","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.870000005"},{"Level":"2","XP":"100","Damage":"1.25","Velocity":"1","Accuracy":"1.70000005","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.800000012"},{"Level":"3","XP":"180","Damage":"1.35000002","Velocity":"1","Accuracy":"1.79999995","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.74000001"}]},
                    "Nightingale": {"code": "unsc_air_nightingale_01", "display": "Nightingale", "role": "Air", "hp": "6300", "armor": "MediumAir", "los": "65", "accel": "16", "vel": "16", "desc": "Support aircraft.", "bounty": "10", "veterancy": [{"Level":"1","XP":"0","Damage":"1.14999998","Velocity":"1","Accuracy":"1.60000002","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.870000005"},{"Level":"2","XP":"0","Damage":"1.25","Velocity":"1.04999995","Accuracy":"1.70000005","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.800000012"},{"Level":"3","XP":"0","Damage":"1.35000002","Velocity":"1.10000002","Accuracy":"1.79999995","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.74000001"}]},
                    "Hornet": {"code": "unsc_air_hornet_01", "display": "Hornet", "role": "Air", "hp": "6650", "armor": "MediumAir", "los": "65", "accel": "18", "vel": "19", "desc": "Fast attack craft.", "bounty": "10", "veterancy": [{"Level":"1","XP":"20","Damage":"1.14999998","Velocity":"1","Accuracy":"1.60000002","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.870000005"},{"Level":"2","XP":"50","Damage":"1.25","Velocity":"1","Accuracy":"1.70000005","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.800000012"},{"Level":"3","XP":"90","Damage":"1.35000002","Velocity":"1","Accuracy":"1.79999995","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.74000001"}]},
                    "Grunt": {"code": "cov_inf_grunt_01", "display": "Grunt", "role": "Infantry", "hp": "646", "armor": "Light", "los": "65", "accel": "13", "vel": "13", "dmg_cover": "LightInCover", "desc": "Small disposable infantry.", "bounty": "1", "veterancy": [{"Level":"1","XP":"0.839999974","Damage":"1.14999998","Velocity":"1","Accuracy":"1.60000002","WorkRate":"1","WeaponRange":"1","DamageTaken":"0.870000005"},{"Level":"2","XP":"2.5","Damage":"1.25","Velocity":"1","Accuracy":"1.70000005","WorkRate":"1","WeaponRange":"1","DamageTaken":"0.800000012"},{"Level":"3","XP":"5","Damage":"1.35000002","Velocity":"1","Accuracy":"1.79999995","WorkRate":"1","WeaponRange":"1","DamageTaken":"0.74000001"}]},
                    "Ghost": {"code": "cov_veh_ghost_01", "display": "Ghost", "role": "Vehicle", "hp": "3300", "armor": "MediumScout", "los": "80", "accel": "20", "vel": "26.5", "desc": "Light skimmer.", "bounty": "6", "shieldpoints": "17500", "veterancy": [{"Level":"1","XP":"8","Damage":"1.14999998","Velocity":"1","Accuracy":"1.60000002","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.870000005"},{"Level":"2","XP":"20","Damage":"1.25","Velocity":"1","Accuracy":"1.70000005","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.800000012"},{"Level":"3","XP":"36","Damage":"1.35000002","Velocity":"1","Accuracy":"1.79999995","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.74000001"}]},
                    "Wraith": {"code": "cov_veh_wraith_01", "display": "Wraith", "role": "Vehicle", "hp": "6825", "armor": "Heavy", "los": "70", "accel": "15", "vel": "15", "desc": "Siege vehicle with mortar.", "bounty": "22", "shieldpoints": "17500", "veterancy": [{"Level":"1","XP":"28","Damage":"1.14999998","Velocity":"1","Accuracy":"1.60000002","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.870000005"},{"Level":"2","XP":"70","Damage":"1.25","Velocity":"1","Accuracy":"1.70000005","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.800000012"},{"Level":"3","XP":"126","Damage":"1.35000002","Velocity":"1","Accuracy":"1.79999995","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.74000001"}]},
                    "Engineer": {"code": "cov_inf_engineer_01", "display": "Engineer", "role": "AircraftTech", "hp": "4125", "armor": "Light", "los": "65", "accel": "15", "vel": "15", "desc": "Repair and support unit.", "bounty": "6.25", "veterancy": [{"Level":"1","XP":"0","Damage":"1.14999998","Velocity":"1","Accuracy":"1.60000002","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.870000005"},{"Level":"2","XP":"0","Damage":"1.25","Velocity":"1","Accuracy":"1.70000005","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.800000012"},{"Level":"3","XP":"0","Damage":"1.35000002","Velocity":"1","Accuracy":"1.79999995","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.74000001"}]},
                    "Banshee": {"code": "cov_air_banshee_01", "display": "Banshee", "role": "Air", "hp": "5150", "armor": "MediumAir", "los": "65", "accel": "20.5", "vel": "20.5", "desc": "Maneuverable attack aircraft.", "bounty": "9", "veterancy": [{"Level":"1","XP":"16","Damage":"1.14999998","Velocity":"1","Accuracy":"1.60000002","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.870000005"},{"Level":"2","XP":"40","Damage":"1.25","Velocity":"1","Accuracy":"1.70000005","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.800000012"},{"Level":"3","XP":"72","Damage":"1.35000002","Velocity":"1","Accuracy":"1.79999995","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.74000001"}]},
                    "Honor Guard": {"code": "cov_inf_eliteCommando_01", "display": "Honor Guard", "role": "Infantry", "hp": "5000", "armor": "CovenantLeader", "los": "65", "accel": "17", "vel": "15", "desc": "Elite ceremonial infantry.", "bounty": "19", "dmg_cover": "HeavyInCover", "shieldpoints": "8500", "veterancy": [{"Level":"1","XP":"68","Damage":"1.14999998","Velocity":"1","Accuracy":"1.60000002","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.949999988"},{"Level":"2","XP":"162","Damage":"1.20000005","Velocity":"1","Accuracy":"1.70000005","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.899999976"},{"Level":"3","XP":"243","Damage":"1.25","Velocity":"1","Accuracy":"1.79999995","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.850000024"}]},
                    "Spartan": {"code": "unsc_inf_spartan_01", "display": "Spartan", "role": "Infantry", "hp": "12000", "armor": "CovenantLeader", "los": "65", "accel": "15", "vel": "15", "desc": "Powered super-soldier.", "bounty": "19", "dmg_cover": "HeavyInCover", "shieldpoints": "7000", "veterancy": [{"Level":"1","XP":"24","Damage":"1.14999998","Velocity":"1","Accuracy":"1.60000002","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.870000005"},{"Level":"2","XP":"60","Damage":"1.25","Velocity":"1","Accuracy":"1.70000005","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.800000012"},{"Level":"3","XP":"108","Damage":"1.35000002","Velocity":"1","Accuracy":"1.79999995","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.74000001"}]},
                    "Condor": {"code": "unsc_air_destroyer_01", "display": "Condor", "role": "Air", "hp": "68250", "armor": "HeavyAir", "los": "100", "accel": "13", "vel": "6", "desc": "Heavy transport aircraft.", "bounty": "100", "veterancy": [{"Level":"1","XP":"120","Damage":"1.14999998","Velocity":"1","Accuracy":"1.60000002","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.870000005"},{"Level":"2","XP":"360","Damage":"1.25","Velocity":"1","Accuracy":"1.70000005","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.800000012"},{"Level":"3","XP":"720","Damage":"1.35000002","Velocity":"1","Accuracy":"1.79999995","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.74000001"}]},
                    "Scarab": {"code": "cov_veh_scarab_01", "display": "Scarab", "role": "Vehicle", "hp": "89000", "armor": "Heavy", "los": "100", "accel": "8", "vel": "11", "desc": "Ancient massive walker.", "bounty": "100", "veterancy": [{"Level":"1","XP":"120","Damage":"1.14999998","Velocity":"1","Accuracy":"1.60000002","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.870000005"},{"Level":"2","XP":"360","Damage":"1.25","Velocity":"1","Accuracy":"1.70000005","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.800000012"},{"Level":"3","XP":"720","Damage":"1.35000002","Velocity":"1","Accuracy":"1.79999995","WorkRate":"1.20000005","WeaponRange":"1","DamageTaken":"0.74000001"}]},
                }

                # preview controls (Text) that will be updated when presets are selected
                preset_title = Text("Select a unit preset to see an example", size=16, weight="bold")
                preset_code = Text("")
                preset_display = Text("")
                preset_role = Text("")
                preset_hp = Text("")
                preset_armor = Text("")
                preset_los = Text("")
                preset_accel = Text("")
                preset_vel = Text("")
                preset_desc = Text("")
                preset_bounty = Text("")
                preset_shield = Text("")
                preset_veterancy = Text("")

                current_preset_name = PRESET_NAMES[0]

                def select_preset(name):
                    nonlocal current_preset_name
                    try:
                        data = PRESETS.get(name, {})
                        preset_title.value = f"Example — {data.get('display', name)}"
                        preset_code.value = f"Code: {data.get('code','')}"
                        preset_display.value = f"Name: {data.get('display','')}"
                        preset_role.value = f"Role: {data.get('role','')}"
                        preset_hp.value = f"HP: {data.get('hp','')}"
                        preset_armor.value = f"Armor: {data.get('armor','')}"
                        preset_los.value = f"LOS: {data.get('los','')}"
                        preset_accel.value = f"Acceleration: {data.get('accel','')}"
                        preset_vel.value = f"Velocity: {data.get('vel','')}"
                        preset_desc.value = f"{data.get('desc','')}"
                        # show bounty if present
                        try:
                            b = data.get('bounty')
                            if b is not None:
                                preset_bounty.value = f"Bounty: {b}"
                            else:
                                preset_bounty.value = ""
                        except Exception:
                            preset_bounty.value = ""
                        # show shield info if present
                        try:
                            sp = data.get('shieldpoints')
                            if sp is not None:
                                preset_shield.value = f"Shieldpoints: {sp}"
                            else:
                                preset_shield.value = ""
                        except Exception:
                            preset_shield.value = ""
                        # show veterancy summary if present
                        try:
                            vets = data.get('veterancy')
                            if isinstance(vets, list) and vets:
                                lines = []
                                for v in vets:
                                    lvl = v.get('Level')
                                    xp = v.get('XP')
                                    lines.append(f"L{lvl} XP:{xp}")
                                preset_veterancy.value = " | ".join(lines)
                            else:
                                preset_veterancy.value = ""
                        except Exception:
                            preset_veterancy.value = ""
                        try:
                            page.update()
                        except Exception:
                            pass
                        try:
                            # remember current selection for Apply button
                            current_preset_name = name
                        except Exception:
                            pass
                    except Exception:
                        pass

                # Layout preset buttons into multiple rows to avoid cutoff
                preset_buttons = [Button(n, on_click=lambda e, nm=n: select_preset(nm)) for n in PRESET_NAMES]
                def _chunk(lst, size):
                    for i in range(0, len(lst), size):
                        yield lst[i:i+size]

                presets_rows = [Row(list(chunk), spacing=8) for chunk in _chunk(preset_buttons, 5)]
                presets_container = Column(presets_rows, spacing=6)

                def apply_preset_to_unit(name):
                    try:
                        unit_tab = get_unit_tab()
                        # if unit_tab exposes apply_preset, call it
                        if hasattr(unit_tab, 'apply_preset'):
                            try:
                                unit_tab.apply_preset(PRESETS.get(name, {}))
                            except Exception:
                                pass
                        # navigate user to Unit Builder
                        try:
                            switch_workflow_tab(get_unit_tab())
                        except Exception:
                            pass
                        try:
                            page.update()
                        except Exception:
                            pass
                    except Exception:
                        pass

                apply_btn = Button("Apply to Unit Builder", on_click=lambda e: apply_preset_to_unit(current_preset_name))

                # Keep preview sized for the right column to avoid horizontal overflow
                preset_preview = Container(Column([preset_title, preset_code, preset_display, preset_role, preset_hp, preset_armor, preset_los, preset_accel, preset_vel, Divider(), preset_desc, preset_bounty, preset_shield, preset_veterancy, Row([apply_btn], alignment="center")], spacing=6), padding=CARD_PADDING, bgcolor=CARD_BG, border_radius=RADIUS, width=360)

                card_items = []
                for icon, title, desc in steps:
                    item = Container(
                        Column([
                            Text(f"{icon}  {title}", size=16, weight="bold"),
                            Text(desc, color="white70", size=12),
                        ], spacing=8),
                        **card_style,
                        expand=True,
                    )
                    card_items.append(item)

                # Layout: hero full-width, then two-column content (left: steps, right: presets + preview)
                left_column = Column([
                    Column([Text("Workflow Overview", size=18, weight="bold"), Text("Follow these steps to create, package, and publish a custom unit for Halo Wars 2.", color="white70")], spacing=6),
                    Divider(),
                    Column(card_items, spacing=12, expand=True)
                ], expand=True, spacing=12)

                right_column = Column([
                    Container(Text("Preset Examples", size=16, weight="bold"), padding=(0,0,0,6)),
                    presets_container,
                    preset_preview,
                ], width=380, spacing=8)

                overview_content = Column([
                    wf_hero,
                    Divider(),
                    Column([
                        Column([Text("Workflow Overview", size=18, weight="bold"), Text("Follow these steps to create, package, and publish a custom unit for Halo Wars 2.", color="white70")], spacing=12),
                        Divider(),
                        Column(card_items, spacing=12, expand=True),
                    ], expand=True, spacing=12),
                    Divider(),
                    Container(
                        Column([
                            Text("Preset Examples", size=16, weight="bold"),
                            presets_container,
                            preset_preview,
                        ], spacing=8),
                        padding=CARD_PADDING, bgcolor=CARD_BG, border_radius=RADIUS, width=PANEL_WIDTH
                    ),
                ], alignment="start", spacing=12, expand=True)

                workflow_sidebar = Column(
                    [
                        Text("Custom Unit Workflow", size=18, weight="bold"),
                        Button("🏠  Overview", on_click=lambda ev: switch_workflow_tab(overview_content)),
                        Button("⚙️  Unit Builder", on_click=lambda ev: switch_workflow_tab(get_unit_tab())),
                        Button("⚔️  Squad Builder", on_click=lambda ev: switch_workflow_tab(get_squad_tab())),
                        Button("📝  UIENT Builder", on_click=lambda ev: switch_workflow_tab(get_uient_tab())),
                        Button("🧬  Entity Builder", on_click=lambda ev: switch_workflow_tab(get_entity_tab())),
                        Button("🗺️  Minimap & Decals", on_click=lambda ev: switch_workflow_tab(get_minimap_tab())),
                        # Player Colors removed from Custom Unit Workflow sidebar
                        Button("🔧  Techs Logic Builder", on_click=lambda ev: switch_workflow_tab(get_tech_tab())),
                        Button("📦  Packager", on_click=lambda ev: switch_workflow_tab(get_packager_tab())),
                    ],
                    width=220,
                    spacing=8,
                    scroll=ScrollMode.AUTO,
                    expand=True,
                )

                workflow_layout = Row([
                    Container(workflow_sidebar, bgcolor=SIDEBAR_BG, padding=CARD_PADDING),
                    Container(workflow_main, expand=True, padding=16),
                ], expand=True)

                # default view for workflow — styled overview
                workflow_main.controls.clear()
                workflow_main.controls.append(overview_content)

                set_top_content(workflow_layout)

            def open_leader_power_workflow(e=None):
                # Sidebar for leader power workflow
                def switch_workflow_tab(tab_content):
                    leader_main.controls.clear()
                    leader_main.controls.append(tab_content)
                    page.update()

                leader_main = Column(expand=True, scroll=ScrollMode.AUTO)

                overview = Column([
                    Container(Column([Text("Leader Power Workflow", size=22, weight="bold"), Text("Create and manage Leader Power UIENT entries (multi-tier, active/passive).", color=TEXT_MUTED)], alignment="start", spacing=6), padding=CARD_PADDING, bgcolor=PANEL_BG, border_radius=RADIUS, width=SMALL_WIDTH),
                    Divider(),
                    Container(Column([Text("Use the builder to generate per-tier UIENT strings and copy them into your uient.xml.", color="white70")], spacing=6), **card_style)
                ], alignment="start", spacing=8, expand=True)

                sidebar = Column([
                    Text("Leader Power Workflow", size=18, weight="bold"),
                    Button("🏠 Overview", on_click=lambda ev: switch_workflow_tab(overview)),
                    Button("📝 Leader Power Builder", on_click=lambda ev: switch_workflow_tab(get_leader_tab())),
                ], width=220, spacing=8, scroll=ScrollMode.AUTO, expand=True)

                layout = Row([
                    Container(sidebar, bgcolor=SIDEBAR_BG, padding=CARD_PADDING),
                    Container(leader_main, expand=True, padding=16),
                ], expand=True)

                leader_main.controls.clear()
                leader_main.controls.append(overview)
                set_top_content(layout)

            def open_player_colors_workflow(e=None):
                def switch_workflow_tab(tab_content):
                    pc_main.controls.clear()
                    pc_main.controls.append(tab_content)
                    page.update()

                pc_main = Column(expand=True, scroll=ScrollMode.AUTO)

                overview = Column([
                    Container(Column([Text("Player Colors Workflow", size=22, weight="bold"), Text("Create and manage skirmish player color definitions.", color=TEXT_MUTED)], alignment="start", spacing=6), padding=CARD_PADDING, bgcolor=PANEL_BG, border_radius=RADIUS, width=SMALL_WIDTH),
                    Divider(),
                    Container(
                        Column([
                            Text("Use the builder to edit color palettes, assign player slots and export playercolors.xml.", color="white70"),
                            Divider(),
                            Row([
                                Container(Column([Text("Refresh", weight="bold"), Text("Press the Refresh button to update pages so edited color names appear across the app.", color="white70")], spacing=4), padding=CARD_PADDING, bgcolor=CARD_BG, border_radius=RADIUS, expand=True),
                                Container(Column([Text("Import", weight="bold"), Text("Import a playercolors.xml to use someone else's player color definitions.", color="white70")], spacing=4), padding=CARD_PADDING, bgcolor=CARD_BG, border_radius=RADIUS, expand=True),
                                Container(Column([Text("Edit Order", weight="bold"), Text("Use the Edit Order tab to change where colors are used and reorder which player has each color.", color="white70")], spacing=4), padding=CARD_PADDING, bgcolor=CARD_BG, border_radius=RADIUS, expand=True),
                            ], spacing=8),
                            Divider(),
                            Text("Export: Use 'Export playercolors.xml' to save the current player colors to an XML file for sharing or packaging.", color="white70"),
                        ], spacing=6),
                        **card_style
                    )
                ], alignment="start", spacing=8, expand=True)

                sidebar = Column([
                    Text("Player Colors Workflow", size=18, weight="bold"),
                    Button("🏠 Overview", on_click=lambda ev: switch_workflow_tab(overview)),
                    Button("🎨 Player Colors Builder", on_click=lambda ev: switch_workflow_tab(get_player_colors_tab())),
                ], width=220, spacing=8, scroll=ScrollMode.AUTO, expand=True)

                layout = Row([
                    Container(sidebar, bgcolor=SIDEBAR_BG, padding=CARD_PADDING),
                    Container(pc_main, expand=True, padding=16),
                ], expand=True)

                pc_main.controls.clear()
                pc_main.controls.append(overview)
                set_top_content(layout)

            def open_compile_mod_workflow(e=None):
                # Sidebar for Compile Mod workflow
                def switch_workflow_tab(tab_content):
                    compile_main.controls.clear()
                    compile_main.controls.append(tab_content)
                    page.update()

                compile_main = Column(expand=True, scroll=ScrollMode.AUTO)

                overview = Column([
                    Container(Column([Text("Compile Mod Workflow", size=22, weight="bold"), Text("Select a mod folder and press Compile Mod — the tool will package, checksum, generate the manifest, and export to GTS.", color=TEXT_MUTED)], alignment="start", spacing=6), padding=CARD_PADDING, bgcolor=PANEL_BG, border_radius=RADIUS, width=SMALL_WIDTH),
                    Divider(),
                    Container(Column([Text("Flow: 1) Select a mod directory. 2) Press Compile Mod to package and export.", color="white70")], spacing=6), **card_style)
                ], alignment="start", spacing=8, expand=True)

                sidebar = Column([
                    Text("Compile Mod Workflow", size=18, weight="bold"),
                    Button("🏠 Overview", on_click=lambda ev: switch_workflow_tab(overview)),
                    Button("📦 Compile Mod Builder", on_click=lambda ev: switch_workflow_tab(build_tab)),
                ], width=220, spacing=8, scroll=ScrollMode.AUTO, expand=True)

                # Build tab content
                from Modules.shared_utils_fast import crc32_bytes, crc32_file_fast, safe_set_clipboard

                pkg_file_field = TextField(label="Mod Directory", width=700, bgcolor=INPUT_BG)
                pkg_browse_btn = Button("Browse...", on_click=lambda ev: browse_pkg_file())
                pkg_crc_field = TextField(label="CRC (decimal)", width=300, bgcolor=OUTPUT_BG)
                pkg_hex_field = TextField(label="CRC (hex)", width=300, bgcolor=OUTPUT_BG)
                pkg_size_field = TextField(label="Size (bytes)", width=300, bgcolor=OUTPUT_BG)
                pkg_time_field = TextField(label="File mtime (int)", width=300, bgcolor=OUTPUT_BG)
                published_utc_field = TextField(label="published_utc", width=300, bgcolor=OUTPUT_BG)
                published_utc_str_field = TextField(label="published_utc_str", width=600, bgcolor=OUTPUT_BG)
                manifest_output = TextField(label="Manifest XML", multiline=True, min_lines=6, max_lines=20, width=900, bgcolor=OUTPUT_BG)

                def browse_pkg_file():
                    try:
                        root = _tk.Tk()
                        try:
                            root.withdraw()
                            root.attributes('-topmost', True)
                            root.update()
                        except Exception:
                            pass
                        path = _filedialog.askdirectory()
                        try:
                            root.attributes('-topmost', False)
                        except Exception:
                            pass
                        root.destroy()
                    except Exception:
                        path = ""
                    if path:
                        pkg_file_field.value = path
                        # clear PKG-specific fields until compilation runs
                        pkg_size_field.value = ""
                        pkg_time_field.value = ""
                        pkg_crc_field.value = ""
                        pkg_hex_field.value = ""
                        manifest_output.value = ""
                        page.update()

                def compute_pkg_crc(e=None):
                    path = pkg_file_field.value.strip()
                    if not path or not os.path.exists(path):
                        page.snack_bar = SnackBar(Text("Please choose a valid .pkg file first."), open=True)
                        page.update()
                        return

                    async def _compute_pkg():
                        try:
                                loop = asyncio.get_running_loop()
                                crc_val = await loop.run_in_executor(None, crc32_file_fast, path)
                        except Exception:
                            # fallback to crcmod or table-based
                            try:
                                import importlib
                                crcmod = importlib.import_module('crcmod')
                                with open(path, 'rb') as fh:
                                    data = fh.read()
                                crc32_func = crcmod.mkCrcFun(poly=0x104C11DB7, initCrc=0xFFFFFFFF, rev=True, xorOut=0xFFFFFFFF)
                                crc_val = crc32_func(data)
                            except Exception:
                                with open(path, 'rb') as fh:
                                    data = fh.read()
                                crc_val = crc32_bytes(data)

                        # ensure crc_val is an integer (handle unexpected None)
                        try:
                            if crc_val is None:
                                raise ValueError("crc_val is None")
                            crc_int = int(crc_val)
                        except Exception:
                            try:
                                with open(path, 'rb') as fh:
                                    data = fh.read()
                                crc_int = crc32_bytes(data)
                            except Exception:
                                crc_int = 0
                        pkg_crc_field.value = str(crc_int)
                        pkg_hex_field.value = f"{crc_int:08X}"
                        # update size/time
                        try:
                            pkg_size_field.value = str(os.path.getsize(path))
                        except Exception:
                            pass
                        try:
                            pkg_time_field.value = str(int(os.path.getmtime(path)))
                        except Exception:
                            pass
                        # set published time to now
                        ts = int(time.time())
                        published_utc_field.value = str(ts)
                        try:
                            published_utc_str_field.value = time.strftime("%a %b %d %H:%M:%S UTC %Y", time.gmtime(ts))
                        except Exception:
                            published_utc_str_field.value = ""
                        page.snack_bar = SnackBar(Text("CRC computed."), open=True)
                        page.update()

                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        loop = None
                    if loop and loop.is_running():
                        loop.create_task(_compute_pkg())
                    else:
                        asyncio.run(_compute_pkg())

                def generate_manifest(e=None):
                    path = pkg_file_field.value.strip()
                    if not path:
                        page.snack_bar = SnackBar(Text("Select the .pkg first."), open=True)
                        page.update()
                        return
                    pkgname = os.path.basename(path)
                    try:
                        crc_val = int(pkg_crc_field.value)
                    except Exception:
                        page.snack_bar = SnackBar(Text("Compute CRC first."), open=True)
                        page.update()
                        return
                    try:
                        published = int(published_utc_field.value) if published_utc_field.value else int(time.time())
                    except Exception:
                        published = int(time.time())
                    try:
                        published_str = published_utc_str_field.value or time.strftime("%a %b %d %H:%M:%S UTC %Y", time.gmtime(published))
                    except Exception:
                        published_str = ""
                    try:
                        size = int(pkg_size_field.value) if pkg_size_field.value else 0
                    except Exception:
                        size = 0
                    try:
                        file_time = int(pkg_time_field.value) if pkg_time_field.value else 0
                    except Exception:
                        file_time = 0
                    manifest_name = "1_11_2931_2_file_manifest.xml"
                    xml = []
                    xml.append(f'<manifest published_utc="{published}" published_utc_str="{published_str}">')
                    xml.append(f'\t<file action="replace" crc32="{crc_val}" new="{pkgname}" old="{pkgname}" size="{size}" time="{file_time}" version="1" />')
                    xml.append('</manifest>')
                    manifest_output.value = "\n".join(xml)
                    page.snack_bar = SnackBar(Text(f"Manifest generated: {manifest_name}"), open=True)
                    page.update()

                # ---------------------------
                # Export manifest and PKG to GTS folder
                # ---------------------------
                GTS_PATH_TEMPLATE = r"%localappdata%\Packages\Microsoft.HoganThreshold_8wekyb3d8bbwe\LocalState\GTS\1_11_2931_2_active"

                def export_to_gts(e=None):
                    content = manifest_output.value
                    if not content or not content.strip():
                        page.snack_bar = SnackBar(Text("Generate the manifest first."), open=True)
                        page.update()
                        return
                    try:
                        path = os.path.expandvars(GTS_PATH_TEMPLATE)
                        os.makedirs(path, exist_ok=True)
                    except Exception:
                        page.snack_bar = SnackBar(Text("Failed to resolve/create GTS folder."), open=True)
                        page.update()
                        return
                    # write manifest
                    try:
                        manifest_name = "1_11_2931_2_file_manifest.xml"
                        dest = os.path.join(path, manifest_name)
                        with open(dest, 'w', encoding='utf-8') as fh:
                            fh.write(content)
                    except Exception as ex:
                        page.snack_bar = SnackBar(Text(f"Failed to write manifest: {ex}"), open=True)
                        page.update()
                        return
                    # copy pkg if provided
                    try:
                        pkg_path = pkg_file_field.value.strip()
                    except Exception:
                        pkg_path = ""
                    if pkg_path:
                        try:
                            import shutil
                            if os.path.exists(pkg_path):
                                dest_pkg = os.path.join(path, os.path.basename(pkg_path))
                                try:
                                    shutil.copy2(pkg_path, dest_pkg)
                                except Exception:
                                    # fallback to a more explicit copy
                                    shutil.copy(pkg_path, dest_pkg)
                                page.snack_bar = SnackBar(Text(f"PKG copied: {os.path.basename(dest_pkg)}"), open=True)
                                page.update()
                            else:
                                page.snack_bar = SnackBar(Text("PKG file not found; manifest exported without PKG."), open=True)
                                page.update()
                                try:
                                    if os.name == 'nt':
                                        os.startfile(path)
                                except Exception:
                                    pass
                                return
                        except Exception as ex:
                            page.snack_bar = SnackBar(Text(f"Failed to copy PKG: {ex}"), open=True)
                            page.update()
                            try:
                                if os.name == 'nt':
                                    os.startfile(path)
                            except Exception:
                                pass
                            return
                    # success
                    page.snack_bar = SnackBar(Text("Exported manifest and PKG to GTS."), open=True)
                    page.update()
                    try:
                        if os.name == 'nt':
                            os.startfile(path)
                        else:
                            subprocess.run(["xdg-open", path], check=False)
                    except Exception:
                        pass

                def launch_hw2(e=None):
                    # Try multiple strategies to launch Halo Wars 2
                    tried = []
                    # helper: try to bring a window to foreground by pid or title keywords
                    def bring_to_front(pid=None, keywords=("halo wars", "halo wars 2", "hogan")):
                        try:
                            import ctypes
                            from ctypes import wintypes
                            user32 = ctypes.windll.user32
                            SW_RESTORE = 9

                            # find a matching window handle
                            hwnd_found = None

                            @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
                            def _enum(hwnd, lParam):
                                nonlocal hwnd_found
                                try:
                                    if not user32.IsWindowVisible(hwnd):
                                        return True
                                    length = user32.GetWindowTextLengthW(hwnd)
                                    if length == 0:
                                        return True
                                    buff = ctypes.create_unicode_buffer(length + 1)
                                    user32.GetWindowTextW(hwnd, buff, length + 1)
                                    title = buff.value
                                    pid_val = wintypes.DWORD()
                                    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid_val))
                                    wpid = pid_val.value
                                    if pid is not None:
                                        if wpid == int(pid):
                                            hwnd_found = hwnd
                                            return False
                                    else:
                                        t = title.lower()
                                        for kw in keywords:
                                            if kw in t:
                                                hwnd_found = hwnd
                                                return False
                                except Exception:
                                    pass
                                return True

                            user32.EnumWindows(_enum, 0)
                            if not hwnd_found:
                                return False

                            # Try simple SetForegroundWindow first
                            try:
                                user32.ShowWindow(hwnd_found, SW_RESTORE)
                                if user32.SetForegroundWindow(hwnd_found):
                                    try:
                                        HWND_TOPMOST = -1
                                        HWND_NOTOPMOST = -2
                                        SWP_NOSIZE = 0x0001
                                        SWP_NOMOVE = 0x0002
                                        # briefly make the game topmost, then remove topmost to force z-order
                                        user32.SetWindowPos(hwnd_found, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
                                        user32.SetWindowPos(hwnd_found, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
                                    except Exception:
                                        pass
                                    return True
                            except Exception:
                                pass

                            # Otherwise use AttachThreadInput trick
                            try:
                                fg_hwnd = user32.GetForegroundWindow()
                                tid1 = user32.GetWindowThreadProcessId(fg_hwnd, None)
                                tid2 = user32.GetWindowThreadProcessId(hwnd_found, None)
                                # Attach input threads
                                if user32.AttachThreadInput(tid1, tid2, True):
                                    brought = False
                                    try:
                                        user32.ShowWindow(hwnd_found, SW_RESTORE)
                                        user32.SetForegroundWindow(hwnd_found)
                                        brought = True
                                    finally:
                                        try:
                                            user32.AttachThreadInput(tid1, tid2, False)
                                        except Exception:
                                            pass
                                    if brought:
                                        return True
                            except Exception:
                                pass
                        except Exception:
                            pass
                        return False

                    # helper: send this modding suite window to the bottom of the z-order
                    def send_suite_to_back():
                        try:
                            import ctypes
                            user32 = ctypes.windll.user32
                            # attempt to find the window by the page title
                            title = getattr(page, 'title', 'Halo Wars 2 Modding Suite')
                            hwnd = user32.FindWindowW(None, title)
                            if hwnd:
                                HWND_BOTTOM = 1
                                SWP_NOSIZE = 0x0001
                                SWP_NOMOVE = 0x0002
                                user32.SetWindowPos(hwnd, HWND_BOTTOM, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
                                return True
                        except Exception:
                            pass
                        return False
                    # 1) Attempt to launch UWP package via shell:AppsFolder AUMID
                    pkg_family = "Microsoft.HoganThreshold_8wekyb3d8bbwe"
                    aumid_candidates = [
                        f"{pkg_family}!App",
                        f"{pkg_family}!Microsoft.HoganThreshold",
                        f"{pkg_family}!HaloWars2",
                        f"{pkg_family}!HoganThreshold",
                    ]
                    for a in aumid_candidates:
                        try:
                            tried.append(f"AppsFolder:{a}")
                            os.startfile(f"shell:AppsFolder\\{a}")
                            time.sleep(1)
                            if bring_to_front(None):
                                page.snack_bar = SnackBar(Text("Launched Halo Wars 2 (UWP) and brought to front."), open=True)
                                send_suite_to_back()
                            else:
                                page.snack_bar = SnackBar(Text("Attempted to launch Halo Wars 2 via UWP package."), open=True)
                                send_suite_to_back()
                            page.update()
                            return
                        except Exception:
                            pass

                    # 1.5) Try querying Start menu AppIDs via PowerShell (Get-StartApps)
                    try:
                        try:
                            cmd = [
                                "powershell",
                                "-NoProfile",
                                "-Command",
                                "Get-StartApps | Where-Object { $_.AppID -like '*HoganThreshold*' } | Select-Object -First 1 -ExpandProperty AppID"
                            ]
                            out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True)
                            appid = out.strip()
                        except Exception:
                            appid = ""
                        if appid:
                            tried.append(f"StartApps:{appid}")
                            try:
                                os.startfile(f"shell:AppsFolder\\{appid}")
                                time.sleep(1)
                                if bring_to_front(None):
                                    page.snack_bar = SnackBar(Text("Launched Halo Wars 2 (UWP) and brought to front."), open=True)
                                    send_suite_to_back()
                                else:
                                    page.snack_bar = SnackBar(Text("Attempted to launch Halo Wars 2 via Start menu AppID."), open=True)
                                    send_suite_to_back()
                                page.update()
                                return
                            except Exception:
                                pass
                    except Exception:
                        pass

                    # 2) Try Steam common folder heuristics
                    try:
                        steam_base = os.path.join(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'), 'Steam', 'steamapps', 'common')
                        if os.path.isdir(steam_base):
                            for child in os.listdir(steam_base):
                                if 'halo' in child.lower():
                                    candidate_dir = os.path.join(steam_base, child)
                                    for root, dirs, files in os.walk(candidate_dir):
                                        for fn in files:
                                            if fn.lower().endswith('.exe') and 'halo' in fn.lower():
                                                exe_path = os.path.join(root, fn)
                                                try:
                                                    tried.append(exe_path)
                                                    proc = subprocess.Popen([exe_path])
                                                    time.sleep(1)
                                                    if bring_to_front(proc.pid):
                                                        page.snack_bar = SnackBar(Text(f"Launched Halo Wars 2: {fn} (brought to front)"), open=True)
                                                        send_suite_to_back()
                                                    else:
                                                        page.snack_bar = SnackBar(Text(f"Launched Halo Wars 2: {fn}"), open=True)
                                                        send_suite_to_back()
                                                    page.update()
                                                    return
                                                except Exception:
                                                    pass
                    except Exception:
                        pass

                    # 3) Try Program Files search for halo executables (lightweight search)
                    try:
                        for base in (os.environ.get('PROGRAMFILES', 'C:\\Program Files'), os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')):
                            if os.path.isdir(base):
                                for name in os.listdir(base):
                                    if 'halo' in name.lower():
                                        candidate = os.path.join(base, name)
                                        for root, dirs, files in os.walk(candidate):
                                            for fn in files:
                                                if fn.lower().endswith('.exe') and 'halo' in fn.lower():
                                                    exe_path = os.path.join(root, fn)
                                                    try:
                                                        tried.append(exe_path)
                                                        proc = subprocess.Popen([exe_path])
                                                        time.sleep(1)
                                                        if bring_to_front(proc.pid):
                                                            page.snack_bar = SnackBar(Text(f"Launched Halo Wars 2: {fn} (brought to front)"), open=True)
                                                            send_suite_to_back()
                                                        else:
                                                            page.snack_bar = SnackBar(Text(f"Launched Halo Wars 2: {fn}"), open=True)
                                                            send_suite_to_back()
                                                        page.update()
                                                        return
                                                    except Exception:
                                                        pass
                    except Exception:
                        pass

                    # If we reach here, nothing launched
                    msg = "Unable to auto-launch Halo Wars 2. Tried: " + ", ".join(tried[:5])
                    page.snack_bar = SnackBar(Text(msg), open=True)
                    page.update()

                # Unified Compile Mod pipeline UI
                compile_progress_bar = ProgressBar(value=0, width=900)
                compile_progress_label = Text("Idle", size=12)
                launch_after_checkbox = Checkbox(label="Launch Halo Wars 2 after compile", value=False)
                ancilla_output = TextField(label="Ancilla Output", multiline=True, min_lines=8, max_lines=20, width=900, bgcolor=OUTPUT_BG)

                def package_directory_to_pkg(src_dir, dest_pkg, progress_callback=None):
                    try:
                        from Modules.pkg_builder import build_pkg_from_directory
                        return build_pkg_from_directory(src_dir, dest_pkg, progress_callback)
                    except Exception as ex:
                        print(f"Error in package_directory_to_pkg: {ex}")
                        return False

                async def run_ancilla_on_directory(path):
                    ancilla_output.value = ""
                    page.update()

                    ancilla_exec = local_ancilla
                    if not os.path.exists(ancilla_exec):
                        ancilla_output.value = "Ancilla executable not found. Place ancilla.exe into tools/ConvertAscended/.\n"
                        page.update()
                        return False

                    xml_files = []
                    temp_xml_map = {}
                    scanning_errors = []
                    for root_dir, dirs, files in os.walk(path):
                        for fname in files:
                            lower = fname.lower()
                            full = os.path.join(root_dir, fname)
                            if lower.endswith('.xml'):
                                xml_files.append(full)
                            elif lower.endswith('.pfx'):
                                xml_equiv = full + '.xml'
                                if os.path.exists(xml_equiv):
                                    xml_files.append(xml_equiv)
                                else:
                                    try:
                                        shutil.copy2(full, xml_equiv)
                                        xml_files.append(xml_equiv)
                                        temp_xml_map[xml_equiv] = full
                                    except Exception as ex:
                                        scanning_errors.append(f"Could not copy {full} to {xml_equiv}: {ex}")

                    if not xml_files:
                        ancilla_output.value = "Ancilla: no XML/PFX files found; skipping conversion."
                        page.update()
                        return True

                    def convert_file(infile):
                        # Determine output filename
                        if infile.lower().endswith('.tactics.xml'):
                            outfile = infile[:-4] + '.xmb'  # Remove .xml, add .xmb -> .tactics.xmb
                        else:
                            outfile = infile + '.xmb'
                        try:
                            creationflags = 0
                            startupinfo = None
                            if os.name == 'nt':
                                try:
                                    creationflags = subprocess.CREATE_NO_WINDOW
                                except Exception:
                                    creationflags = 0
                                try:
                                    si = subprocess.STARTUPINFO()
                                    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                                    si.wShowWindow = subprocess.SW_HIDE
                                    startupinfo = si
                                except Exception:
                                    startupinfo = None
                            res = subprocess.run([ancilla_exec, 'convert', infile, '-o', outfile], capture_output=True, text=True, creationflags=creationflags, startupinfo=startupinfo)
                            return infile, outfile, res.returncode, res.stdout, res.stderr
                        except Exception as ex:
                            return infile, outfile, 1, '', str(ex)

                    converted = []
                    errors = []

                    total = len(xml_files)
                    compile_progress_bar.value = 0
                    compile_progress_label.value = f"Ancilla: converting 0/{total} files"
                    page.update()

                    loop = asyncio.get_running_loop()
                    workers = max(1, min(4, (os.cpu_count() or 1)))
                    with ThreadPoolExecutor(max_workers=workers) as executor:
                        futures = [loop.run_in_executor(executor, convert_file, infile) for infile in xml_files]
                        completed = 0
                        for fut in asyncio.as_completed(futures):
                            infile, outpath, code, out, err = await fut
                            completed += 1
                            compile_progress_bar.value = completed / total
                            compile_progress_label.value = f"Ancilla: converting {completed}/{total} files"
                            page.update()

                            if code == 0:
                                converted.append((infile, outpath))
                            else:
                                error_msg = f"{infile} -> {outpath}: {err or out or 'Unknown error'}"
                                errors.append(error_msg)

                            page.update()

                    # Post-process: rename .pfx.xml.xmb files to .pfx.xmb
                    for infile, orig_pfx in temp_xml_map.items():
                        # infile is temp .xml created from a .pfx
                        # Find corresponding output file and rename it
                        xmb_output = infile + ".xmb"  # This is what was created (e.g., plasmaSmall.pfx.xml.xmb)
                        desired_output = orig_pfx + ".xmb"  # What we want (e.g., plasmaSmall.pfx.xmb)
                        try:
                            if os.path.exists(xmb_output):
                                if os.path.exists(desired_output):
                                    os.remove(desired_output)
                                os.rename(xmb_output, desired_output)
                        except Exception:
                            pass
                        # Clean up temp .xml
                        try:
                            if os.path.exists(infile):
                                os.remove(infile)
                        except Exception:
                            pass

                    if errors or scanning_errors:
                        all_errors = scanning_errors + errors
                        ancilla_output.value = f"Ancilla encountered errors during conversion. See details below:\n" + "\n".join(all_errors)
                        page.update()
                        return False
                    else:
                        ancilla_output.value = f"Ancilla completed successfully — {len(converted)} files converted!"
                        page.update()
                        return True

                async def compile_mod(e=None):
                    # Gather directory
                    dir_path = pkg_file_field.value.strip()
                    if not dir_path:
                        page.snack_bar = SnackBar(Text("Select a mod directory first."), open=True)
                        page.update()
                        return
                    if not os.path.isdir(dir_path):
                        page.snack_bar = SnackBar(Text("Selected path is not a directory."), open=True)
                        page.update()
                        return

                    # 0) Run Ancilla conversion on source directory
                    compile_progress_label.value = "Running Ancilla conversion..."
                    compile_progress_bar.value = 0
                    ancilla_output.value = ""
                    page.update()

                    try:
                        ok_ancilla = await run_ancilla_on_directory(dir_path)
                    except Exception as ex:
                        ok_ancilla = False
                        ancilla_output.value += f"Ancilla run failed: {ex}\n"
                        page.update()

                    if not ok_ancilla:
                        page.snack_bar = SnackBar(Text("Ancilla conversion failed. Check Ancilla Output log."), open=True)
                        compile_progress_label.value = "Ancilla conversion failed"
                        compile_progress_bar.value = 0
                        page.update()
                        return

                    # Destination .pkg next to directory
                    base_name = os.path.basename(os.path.normpath(dir_path))
                    dest_pkg = os.path.join(os.path.dirname(dir_path), f"{base_name}.pkg")

                    def _progress_tick(completed, total):
                        try:
                            compile_progress_bar.value = completed / total if total > 0 else 0
                            compile_progress_label.value = f"Packaging: {completed}/{total} files"
                            page.update()
                        except Exception:
                            pass

                    # 1) Package directory into .pkg (zip)
                    compile_progress_label.value = "Packaging..."
                    compile_progress_bar.value = 0
                    page.update()

                    try:
                        loop = asyncio.get_running_loop()
                        ok = await loop.run_in_executor(None, package_directory_to_pkg, dir_path, dest_pkg, _progress_tick)
                    except Exception:
                        ok = package_directory_to_pkg(dir_path, dest_pkg, _progress_tick)

                    if not ok or not os.path.exists(dest_pkg):
                        page.snack_bar = SnackBar(Text("Packaging failed."), open=True)
                        compile_progress_label.value = "Packaging failed"
                        page.update()
                        return

                    try:
                        pkg_size_field.value = str(os.path.getsize(dest_pkg))
                        pkg_time_field.value = str(int(os.path.getmtime(dest_pkg)))
                    except Exception:
                        pass

                    # 2) Compute CRC32
                    compile_progress_label.value = "Computing CRC32..."
                    compile_progress_bar.value = 0
                    page.update()
                    try:
                        loop = asyncio.get_running_loop()
                        try:
                            crc_val = await loop.run_in_executor(None, crc32_file_fast, dest_pkg)
                        except Exception:
                            with open(dest_pkg, 'rb') as fh:
                                data = fh.read()
                            crc_val = crc32_bytes(data)
                    except Exception:
                        try:
                            with open(dest_pkg, 'rb') as fh:
                                data = fh.read()
                            crc_val = crc32_bytes(data)
                        except Exception:
                            crc_val = 0
                    try:
                        crc_int = int(crc_val)
                    except Exception:
                        crc_int = 0
                    pkg_crc_field.value = str(crc_int)
                    pkg_hex_field.value = f"{crc_int:08X}"

                    # 3) Generate manifest
                    compile_progress_label.value = "Generating manifest..."
                    page.update()
                    try:
                        published = int(time.time())
                    except Exception:
                        published = 0
                    try:
                        published_str = time.strftime("%a %b %d %H:%M:%S UTC %Y", time.gmtime(published))
                    except Exception:
                        published_str = ""
                    manifest_name = "1_11_2931_2_file_manifest.xml"
                    xml = []
                    xml.append(f'<manifest published_utc="{published}" published_utc_str="{published_str}">')
                    xml.append(f'\t<file action="replace" crc32="{crc_int}" new="{os.path.basename(dest_pkg)}" old="{os.path.basename(dest_pkg)}" size="{pkg_size_field.value}" time="{pkg_time_field.value}" version="1" />')
                    xml.append('</manifest>')
                    manifest_output.value = "\n".join(xml)

                    # 4) Export to GTS
                    compile_progress_label.value = "Exporting to GTS..."
                    compile_progress_bar.value = 0
                    page.update()
                    try:
                        path = os.path.expandvars(GTS_PATH_TEMPLATE)
                        os.makedirs(path, exist_ok=True)
                        # write manifest
                        dest_manifest = os.path.join(path, manifest_name)
                        with open(dest_manifest, 'w', encoding='utf-8') as fh:
                            fh.write(manifest_output.value)
                        # copy pkg
                        dest_pkg_path = os.path.join(path, os.path.basename(dest_pkg))
                        try:
                            shutil.copy2(dest_pkg, dest_pkg_path)
                        except Exception:
                            shutil.copy(dest_pkg, dest_pkg_path)
                        page.snack_bar = SnackBar(Text(f"Exported: {os.path.basename(dest_pkg)} and manifest."), open=True)
                        page.update()
                    except Exception as ex:
                        page.snack_bar = SnackBar(Text(f"Export failed: {ex}"), open=True)
                        page.update()

                    compile_progress_label.value = "Completed"
                    compile_progress_bar.value = 1
                    page.update()

                    # 5) Optionally launch Halo Wars 2
                    try:
                        if launch_after_checkbox.value:
                            launch_hw2()
                    except Exception:
                        pass

                def compile_btn_clicked(e=None):
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        loop = None
                    if loop and loop.is_running():
                        loop.create_task(compile_mod(e))
                    else:
                        asyncio.run(compile_mod(e))

                compile_btn = Button("Compile Mod", on_click=compile_btn_clicked)

                build_tab = Column([
                    Text("Compile Mod Builder", size=20, weight="bold"),
                    Row([pkg_file_field, pkg_browse_btn], alignment="center"),
                    Row([compile_btn, launch_after_checkbox], spacing=12),
                    Divider(),
                    compile_progress_label,
                    compile_progress_bar,
                    Divider(),
                    ancilla_output,
                ], alignment="start", horizontal_alignment="start", spacing=8)

                layout = Row([
                    Container(sidebar, bgcolor=SIDEBAR_BG, padding=CARD_PADDING),
                    Container(compile_main, expand=True, padding=16),
                ], expand=True)

                compile_main.controls.clear()
                compile_main.controls.append(overview)
                set_top_content(layout)

            # Build workflows list (top-level Workflows tab) — styled like Home
            # TEAL provided by shared styles
            card_style = dict(padding=CARD_PADDING, border_radius=RADIUS, bgcolor=CARD_BG)

            wf_hero = Container(
                Column([
                    Text("Workflows", size=28, weight="bold"),
                    Text("Step-through builders to create and validate game data.", size=14, color="white70"),
                ], alignment="center", horizontal_alignment="center"),
                padding=18,
                width=PANEL_WIDTH,
                bgcolor=PANEL_BG,
                border_radius=RADIUS,
            )

            wf_features = Row([
                Container(Column([Text("Custom Unit", size=16, weight="bold"), Text("Unit, Squad, Entity, Minimap and Techs builders.", color="white70", size=12), Button("Open", on_click=open_custom_unit_workflow)], alignment="start", horizontal_alignment="start", spacing=8), **card_style, expand=True),
                Container(Column([Text("Leader Power", size=16, weight="bold"), Text("Dedicated leader power builder (multi-tier).", color="white70", size=12), Button("Open", on_click=open_leader_power_workflow)], alignment="start", horizontal_alignment="start", spacing=8), **card_style, expand=True),
                Container(Column([Text("Compile Mod", size=16, weight="bold"), Text("Build .pkg, compute CRC, and export file manifest.", color="white70", size=12), Button("Open", on_click=open_compile_mod_workflow)], alignment="start", horizontal_alignment="start", spacing=8), **card_style, expand=True),
                Container(Column([Text("Player Colors", size=16, weight="bold"), Text("Customize skirmish and campaign player colors.", color="white70", size=12), Button("Open", on_click=lambda e: open_player_colors_workflow())], alignment="start", horizontal_alignment="start", spacing=8), **card_style, expand=True),
                # (Particle Editor is kept in Tools)
            ], spacing=16, expand=True)

            workflows_list = Column([
                wf_hero,
                Divider(),
                wf_features,
            ], alignment="center", horizontal_alignment="center", expand=True, spacing=12)

            # Tools tab content: Conversion utilities
            from flet import TextField, Checkbox, SnackBar
            import shutil
            import tkinter as _tk
            from tkinter import filedialog as _filedialog

            # Minimal DDS/DDX renamer tools
            tools_path_field = TextField(label="Target Directory", width=600, bgcolor=INPUT_BG)
            tools_output = TextField(label="Results", multiline=True, min_lines=6, max_lines=20, bgcolor=OUTPUT_BG, width=900)

            # Local ConvertAscended install location inside this project
            local_tools_dir = runtime_path("tools", "ConvertAscended")
            local_ancilla = os.path.join(local_tools_dir, "ancilla.exe")

            # progress UI for ConvertAscended
            progress_bar = ProgressBar(value=0, width=900)
            progress_label = Text("Idle", size=12)

            # Phoenix progress UI (separate from Ancilla)
            phx_progress_bar = ProgressBar(value=0, width=900)
            phx_progress_label = Text("Idle", size=12)

            def browse_folder(e=None):
                try:
                    root = _tk.Tk()
                    # keep the dialog on top of the Flet window
                    try:
                        root.withdraw()
                        root.attributes('-topmost', True)
                        root.update()
                    except Exception:
                        pass
                    path = _filedialog.askdirectory()
                    try:
                        root.attributes('-topmost', False)
                    except Exception:
                        pass
                    root.destroy()
                except Exception:
                    path = ""
                if path:
                    tools_path_field.value = path
                    page.update()

            # (executable browse removed — tool uses local tools/ConvertAscended/ancilla.exe)

            # (installation / auto-detect helpers removed — tool uses local tools/ConvertAscended/ancilla.exe)

            def rename_exts(dirpath: str, from_ext: str, to_ext: str):
                renamed = []
                if not dirpath:
                    return renamed
                try:
                    for f in os.listdir(dirpath):
                        if f.lower().endswith(from_ext):
                            src = os.path.join(dirpath, f)
                            dst = os.path.join(dirpath, f[:-len(from_ext)] + to_ext)
                            try:
                                os.rename(src, dst)
                                renamed.append(dst)
                            except Exception:
                                pass
                except Exception:
                    pass
                return renamed

            def do_rename_dds_to_ddx(e=None):
                path = tools_path_field.value.strip()
                if not path:
                    page.snack_bar = SnackBar(Text("Please choose a directory first."), open=True)
                    page.update()
                    return
                renamed = rename_exts(path, ".dds", ".ddx")
                tools_output.value = f"Renamed {len(renamed)} file(s) to .ddx:\n" + "\n".join(renamed)
                page.snack_bar = SnackBar(Text(f"Renamed {len(renamed)} files to .ddx"), open=True)
                page.update()

            def do_rename_ddx_to_dds(e=None):
                path = tools_path_field.value.strip()
                if not path:
                    page.snack_bar = SnackBar(Text("Please choose a directory first."), open=True)
                    page.update()
                    return
                renamed = rename_exts(path, ".ddx", ".dds")
                tools_output.value = f"Renamed {len(renamed)} file(s) to .dds:\n" + "\n".join(renamed)
                page.snack_bar = SnackBar(Text(f"Renamed {len(renamed)} files to .dds"), open=True)
                page.update()

            # ConvertAscended conversion
            def do_convert_evolved_local(e=None):
                path = tools_path_field.value.strip()
                if not path:
                    page.snack_bar = SnackBar(Text("Please choose a directory first."), open=True)
                    page.update()
                    return
                # require local installed ancilla at tools/ConvertAscended/ancilla.exe
                ancilla = local_ancilla
                if not os.path.exists(ancilla):
                    tools_output.value = "Ancilla executable not found. Place ancilla.exe into tools/ConvertAscended/."
                    page.snack_bar = SnackBar(Text("Ancilla executable not found."), open=True)
                    page.update()
                    return
                # collect xml files first (only .xml) — also support .pfx files by
                # creating temporary .xml copies when needed so Ancilla can convert them.
                xml_files = []
                # map temporary xml -> original pfx (so we can cleanup / rename outputs)
                temp_xml_map = {}
                for root_dir, dirs, files in os.walk(path):
                    for fname in files:
                        lower = fname.lower()
                        full = os.path.join(root_dir, fname)
                        if lower.endswith('.xml'):
                            xml_files.append(full)
                        elif lower.endswith('.pfx'):
                            # if a corresponding .pfx.xml already exists, use it
                            xml_equiv = full + '.xml'
                            if os.path.exists(xml_equiv):
                                xml_files.append(xml_equiv)
                            else:
                                # create a temporary xml copy (do not rename original)
                                try:
                                    shutil.copy2(full, xml_equiv)
                                    xml_files.append(xml_equiv)
                                    temp_xml_map[xml_equiv] = full
                                except Exception:
                                    # ignore copy failures; skip this file
                                    pass

                total = len(xml_files)
                # converted: list of tuples (infile, outpath)
                converted = []
                errors = []

                # helper to run conversion synchronously in executor
                def convert_file(exe, infile, outfile):
                    try:
                        # hide console windows on Windows builds
                        creationflags = 0
                        startupinfo = None
                        if os.name == 'nt':
                            try:
                                creationflags = subprocess.CREATE_NO_WINDOW
                            except Exception:
                                creationflags = 0
                            try:
                                si = subprocess.STARTUPINFO()
                                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                                si.wShowWindow = subprocess.SW_HIDE
                                startupinfo = si
                            except Exception:
                                startupinfo = None
                        res = subprocess.run([exe, "convert", infile, "-o", outfile], capture_output=True, text=True, creationflags=creationflags, startupinfo=startupinfo)
                        return infile, outfile, res.returncode, res.stdout, res.stderr
                    except Exception as ex:
                        return infile, outfile, 1, "", str(ex)

                async def run_conversion():
                    loop = asyncio.get_running_loop()
                    total = len(xml_files)
                    workers = max(1, min(4, (os.cpu_count() or 1)))
                    with ThreadPoolExecutor(max_workers=workers) as executor:
                        futures = [loop.run_in_executor(executor, convert_file, ancilla, infile, infile + ".xmb") for infile in xml_files]
                        completed = 0
                        for fut in asyncio.as_completed(futures):
                            infile, outpath, code, out, err = await fut
                            completed += 1
                            # update progress UI (show completed count)
                            try:
                                progress_label.value = f"Converted {completed}/{total}: {os.path.basename(infile)}"
                                progress_bar.value = completed / total if total > 0 else 0
                                page.update()
                            except Exception:
                                pass
                            if code == 0:
                                converted.append((infile, outpath))
                            else:
                                errors.append((infile, err or out))
                    # finalize
                    progress_bar.value = 1
                    progress_label.value = f"Done — converted {len(converted)} files."
                    # post-process converted files: handle .pfx temporary xmls
                    final_paths = []
                    for infile, outpath in converted:
                        if infile in temp_xml_map:
                            # infile is a temp xml created from a .pfx
                            try:
                                base = os.path.splitext(infile)[0]  # removes the .xml
                                desired_out = base + ".xmb"  # e.g. ...desperateResolveCast3.pfx.xmb
                                # move/replace the generated xmb to the desired name
                                try:
                                    os.replace(outpath, desired_out)
                                except Exception:
                                    try:
                                        os.remove(desired_out)
                                        os.replace(outpath, desired_out)
                                    except Exception:
                                        pass
                                final_paths.append(desired_out)
                            except Exception:
                                final_paths.append(outpath)
                        else:
                            final_paths.append(outpath)
                    # cleanup temporary xml files
                    for temp_xml, orig_pfx in list(temp_xml_map.items()):
                        try:
                            if os.path.exists(temp_xml):
                                os.remove(temp_xml)
                        except Exception:
                            pass

                    report_lines = [f"Converted {len(final_paths)} files:"] + final_paths
                    if errors:
                        report_lines += ["", "Errors:"]
                        for p, msg in errors:
                            report_lines.append(f"{p}: {msg}")
                    tools_output.value = "\n".join(report_lines)
                    page.snack_bar = SnackBar(Text(f"Ancilla: converted {len(converted)} files."), open=True)
                    page.update()

                # schedule background conversion
                try:
                    asyncio.get_running_loop().create_task(run_conversion())
                except Exception:
                    # fallback synchronous
                    for infile in xml_files:
                        outpath = infile + ".xmb"
                        _, _, code, out, err = convert_file(ancilla, infile, outpath)
                        if code == 0:
                            converted.append((infile, outpath))
                        else:
                            errors.append((infile, err or out))

                    # post-process converted files for .pfx temp xmls (synchronous path)
                    final_paths = []
                    for infile, outpath in converted:
                        if infile in temp_xml_map:
                            try:
                                base = os.path.splitext(infile)[0]
                                desired_out = base + ".xmb"
                                try:
                                    os.replace(outpath, desired_out)
                                except Exception:
                                    try:
                                        os.remove(desired_out)
                                        os.replace(outpath, desired_out)
                                    except Exception:
                                        pass
                                final_paths.append(desired_out)
                            except Exception:
                                final_paths.append(outpath)
                        else:
                            final_paths.append(outpath)

                    # cleanup temporary xml files
                    for temp_xml, orig_pfx in list(temp_xml_map.items()):
                        try:
                            if os.path.exists(temp_xml):
                                os.remove(temp_xml)
                        except Exception:
                            pass

                    report_lines = [f"Converted {len(final_paths)} files:"] + final_paths
                    if errors:
                        report_lines += ["", "Errors:"]
                        for p, msg in errors:
                            report_lines.append(f"{p}: {msg}")
                    tools_output.value = "\n".join(report_lines)
                    page.snack_bar = SnackBar(Text(f"Ancilla: converted {len(final_paths)} files."), open=True)
                    page.update()

            browse_button = Button("Browse...", on_click=browse_folder)
            btn_dds_to_ddx = Button("Rename .dds → .ddx", on_click=do_rename_dds_to_ddx)
            btn_ddx_to_dds = Button("Rename .ddx → .dds", on_click=do_rename_ddx_to_dds)
            btn_convert_evolved = Button("Convert XML → XMB", on_click=do_convert_evolved_local)

            # DDS/DDX tools content (kept simple) — wrapped in styled container
            tools_content = Container(
                Column([
                    Text("DDS/DDX Converter" , size=20, weight="bold"),
                    Row([tools_path_field, browse_button], alignment="center"),
                    Row([btn_dds_to_ddx, btn_ddx_to_dds], spacing=12, alignment="center"),
                    Divider(),
                    tools_output
                ], alignment="start", horizontal_alignment="start", spacing=8),
                padding=CARD_PADDING,
                bgcolor=PANEL_BG,
                border_radius=RADIUS,
                width=PANEL_WIDTH,
            )

            # ConvertAscended tool content (separate) — styled container
            convert_evolved_content = Container(
                Column([
                    Text("Ancilla", size=20, weight="bold"),
                    Text("Converts editable .XML files back into .XMB format readable by Halo Wars 2.", color="white70"),
                    Row([tools_path_field, browse_button], alignment="center"),
                    Divider(),
                    Row([btn_convert_evolved], alignment="center"),
                    Divider(),
                    progress_label,
                    progress_bar,
                    Divider(),
                    tools_output
                ], alignment="start", horizontal_alignment="start", spacing=8),
                padding=CARD_PADDING,
                bgcolor=PANEL_BG,
                border_radius=RADIUS,
                width=PANEL_WIDTH,
            )

            # Phoenix Tools (launcher only) — simplified to a single button that opens PhxGui/PhxTool
            def launch_phoenix_gui(e=None):
                exe = find_phx_exe()
                if not exe:
                    page.snack_bar = SnackBar(Text("Phoenix executable not found in tools/PhxTools."), open=True)
                    page.update()
                    return
                exe_dir = os.path.dirname(exe) or os.getcwd()
                try:
                    # Launch the GUI (or tool) without blocking the UI and hide any transient console on Windows
                    ok, err = _start_process(exe, cwd=exe_dir)
                    if ok:
                        page.snack_bar = SnackBar(Text(f"Launched: {os.path.basename(exe)}"), open=True)
                    else:
                        page.snack_bar = SnackBar(Text(f"Failed to launch Phoenix: {err}"), open=True)
                except Exception as ex:
                    page.snack_bar = SnackBar(Text(f"Failed to launch Phoenix: {ex}"), open=True)
                page.update()

            def launch_pfx_editor(e=None):
                """Launch the PySide particle editor as a separate process."""
                try:
                    editor_path = (
                        runtime_path("pfx_editor_pyside.py")
                        if getattr(sys, "frozen", False)
                        else os.path.join(SRC_DIR, "pfx_editor_pyside.py")
                    )
                    if not os.path.exists(editor_path):
                        page.snack_bar = SnackBar(Text("Particle Editor script not found."), open=True)
                        page.update()
                        return

                    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
                    if getattr(sys, "frozen", False):
                        subprocess.Popen(
                            [sys.executable, "--particle-editor"],
                            cwd=BASE_DIR,
                            creationflags=creationflags,
                        )
                    else:
                        subprocess.Popen(
                            [sys.executable or "python", editor_path],
                            cwd=BASE_DIR,
                            creationflags=creationflags,
                        )
                    page.snack_bar = SnackBar(Text("Launched Particle Editor."), open=True)
                except Exception as ex:
                    try:
                        page.snack_bar = SnackBar(Text(f"Failed to launch Particle Editor: {ex}"), open=True)
                    except Exception:
                        pass
                page.update()

            phx_content = Container(
                Column([
                    Text("Phoenix Tools", size=20, weight="bold"),
                    Text("This is the Phoenix tool — allows converting .XMB to .XML via drag-and-drop using the Phoenix GUI.", color="white70"),
                    Divider(),
                    Button("Launch Phoenix GUI", on_click=launch_phoenix_gui),
                    Divider(),
                ], alignment="start", horizontal_alignment="start", spacing=8),
                padding=CARD_PADDING,
                bgcolor=PANEL_BG,
                border_radius=RADIUS,
                width=SMALL_WIDTH,
            )

            # locate candidate Phoenix executable (BUNDLED ONLY) - use PhxGui explicitly
            candidate_phx = [
                runtime_path("tools", "PhxTools", "PhxGui.exe"),
            ]

            def _start_process(exe_path, cwd=None):
                # Try a sequence of approaches to start the executable reliably while hiding transient consoles.
                if os.name == 'nt':
                    # 1) Prefer os.startfile which opens the file with associated application without a console.
                    try:
                        os.startfile(exe_path)
                        return True, None
                    except Exception:
                        pass
                    # 2) Use CREATE_NO_WINDOW with STARTUPINFO to hide console windows for console apps.
                    try:
                        creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
                        si = subprocess.STARTUPINFO()
                        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        si.wShowWindow = subprocess.SW_HIDE
                        # Use string path (not list) for Windows Popen to avoid issues.
                        proc = subprocess.Popen(exe_path, cwd=cwd or None, creationflags=creationflags, startupinfo=si)
                        # monitor briefly: try to bring window to front and detect early exit
                        def _monitor_and_bring(p):
                            try:
                                import time as _time
                                _time.sleep(0.2)
                                # Attempt to bring the launched process window to foreground (Windows)
                                try:
                                    if os.name == 'nt' and getattr(p, 'pid', None):
                                        import ctypes
                                        from ctypes import wintypes
                                        user32 = ctypes.windll.user32
                                        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

                                        def _enum_proc(hwnd, lParam):
                                            pid = wintypes.DWORD()
                                            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                                            if pid.value == p.pid:
                                                try:
                                                    SW_RESTORE = 9
                                                    user32.ShowWindow(hwnd, SW_RESTORE)
                                                    user32.SetForegroundWindow(hwnd)
                                                    user32.BringWindowToTop(hwnd)
                                                except Exception:
                                                    pass
                                                return False
                                            return True

                                        try:
                                            user32.EnumWindows(WNDENUMPROC(_enum_proc), 0)
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                                _time.sleep(0.3)
                                rc = p.poll()
                                if rc is not None and rc != 0:
                                    try:
                                        import tempfile
                                        log_path = os.path.join(tempfile.gettempdir(), f"customunittool_tool_log_{int(time.time())}.txt")
                                        try:
                                            with open(log_path, 'w', encoding='utf-8') as lf:
                                                lf.write(f"Process {exe_path} exited with code {rc}\n")
                                        except Exception:
                                            pass
                                        page.snack_bar = SnackBar(Text(f"Tool exited quickly (code {rc}). See {log_path}"), open=True)
                                        page.update()
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                        try:
                            from threading import Thread
                            Thread(target=_monitor_and_bring, args=(proc,), daemon=True).start()
                        except Exception:
                            pass
                        return True, None
                    except Exception:
                        pass
                    # 3) Last resort: use cmd start (may briefly show a console on some systems) but wrap in shell
                    try:
                        cmd = f'start "" "{exe_path}"'
                        proc = subprocess.Popen(cmd, cwd=cwd or None, shell=True)
                        def _monitor2_and_bring(p):
                            try:
                                import time as _time
                                _time.sleep(0.2)
                                try:
                                    if os.name == 'nt' and getattr(p, 'pid', None):
                                        import ctypes
                                        from ctypes import wintypes
                                        user32 = ctypes.windll.user32
                                        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

                                        def _enum_proc2(hwnd, lParam):
                                            pid = wintypes.DWORD()
                                            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                                            if pid.value == p.pid:
                                                try:
                                                    SW_RESTORE = 9
                                                    user32.ShowWindow(hwnd, SW_RESTORE)
                                                    user32.SetForegroundWindow(hwnd)
                                                    user32.BringWindowToTop(hwnd)
                                                except Exception:
                                                    pass
                                                return False
                                            return True

                                        try:
                                            user32.EnumWindows(WNDENUMPROC(_enum_proc2), 0)
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                                _time.sleep(0.3)
                                rc = p.poll()
                                if rc is not None and rc != 0:
                                    try:
                                        import tempfile
                                        log_path = os.path.join(tempfile.gettempdir(), f"customunittool_tool_log_{int(time.time())}.txt")
                                        try:
                                            with open(log_path, 'w', encoding='utf-8') as lf:
                                                lf.write(f"Process cmd start {exe_path} exited with code {rc}\n")
                                        except Exception:
                                            pass
                                        page.snack_bar = SnackBar(Text(f"Tool exited quickly (code {rc}). See {log_path}"), open=True)
                                        page.update()
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                        try:
                            from threading import Thread
                            Thread(target=_monitor2_and_bring, args=(proc,), daemon=True).start()
                        except Exception:
                            pass
                        return True, None
                    except Exception as ex3:
                        return False, ex3
                else:
                    # Unix-like: plain Popen should suffice
                    try:
                        subprocess.Popen([exe_path], cwd=cwd or None)
                        return True, None
                    except Exception as ex:
                        return False, ex

            def find_phx_exe():
                for p in candidate_phx:
                    if os.path.exists(p):
                        return p
                return None

            def open_pkg_builder_tool(e=None):
                """Open the Compile Mod Builder from Tools menu."""
                try:
                    open_compile_mod_workflow()
                except Exception as ex:
                    page.snack_bar = SnackBar(Text(f"Failed to open PKG Builder: {ex}"), open=True)
                    page.update()

            # Phoenix automated conversion removed: launcher-only UI is used instead.
            # Tools list — styled like Home
            tools_hero = Container(
                Column([
                    Text("Tools", size=28, weight="bold"),
                    Text("Quick converters and utilities for asset preparation.", size=14, color="white70"),
                ], alignment="center", horizontal_alignment="center"),
                padding=18,
                width=920,
                bgcolor=PANEL_BG,
                border_radius=RADIUS,
            )

            tools_features = Row([
                Container(Column([Text("DDS/DDX", size=16, weight="bold"), Text("Rename or batch-edit texture extensions.", color="white70", size=12), Button("Open", on_click=lambda ev: set_top_content(tools_content))], spacing=8), **card_style, expand=True),
                Container(Column([Text("Ancilla", size=16, weight="bold"), Text("Convert editable XML to XMB.", color="white70", size=12), Button("Open", on_click=lambda ev: set_top_content(convert_evolved_content))], spacing=8), **card_style, expand=True),
                Container(Column([Text("Phoenix", size=16, weight="bold"), Text("XMB to XML conversion via Phoenix GUI.", color="white70", size=12), Button("Launch", on_click=launch_phoenix_gui)], spacing=8), **card_style, expand=True),
                Container(Column([Text("PKG Builder", size=16, weight="bold"), Text("Compile folders into .pkg files.", color="white70", size=12), Button("Open", on_click=open_pkg_builder_tool)], spacing=8), **card_style, expand=True),
                Container(Column([Text("Particle Editor", size=16, weight="bold"), Text("Edit PFX colors and scale data in a PySide window.", color="white70", size=12), Button("Launch", on_click=launch_pfx_editor)], spacing=8), **card_style, expand=True),
            ], spacing=16, expand=True)

            # CRC32 Calculator — placed in a secondary row under the main tools
            from Modules.shared_utils_fast import crc32_bytes, crc32_file_fast, safe_set_clipboard

            crc_file_field = TextField(label="File", width=700, bgcolor=INPUT_BG)
            crc_hex_field = TextField(label="CRC (hex)", width=300, bgcolor=OUTPUT_BG)
            crc_dec_field = TextField(label="CRC (decimal)", width=300, bgcolor=OUTPUT_BG)

            def browse_crc_file(e=None):
                try:
                    root = _tk.Tk()
                    try:
                        root.withdraw()
                        root.attributes('-topmost', True)
                        root.update()
                    except Exception:
                        pass
                    path = _filedialog.askopenfilename()
                    try:
                        root.attributes('-topmost', False)
                    except Exception:
                        pass
                    root.destroy()
                except Exception:
                    path = ""
                if path:
                    crc_file_field.value = path
                    page.update()

            def compute_crc_for_file(e=None):
                path = crc_file_field.value.strip()
                if not path or not os.path.exists(path):
                    page.snack_bar = SnackBar(Text("Please choose a valid file first."), open=True)
                    page.update()
                    return

                async def _compute():
                    try:
                        loop = asyncio.get_running_loop()
                        crc_val = await loop.run_in_executor(None, crc32_file_fast, path)
                    except Exception:
                        # fallback to crcmod or table-based method
                        try:
                            import importlib
                            crcmod = importlib.import_module('crcmod')
                            with open(path, 'rb') as fh:
                                data = fh.read()
                            crc32_func = crcmod.mkCrcFun(poly=0x104C11DB7, initCrc=0xFFFFFFFF, rev=True, xorOut=0xFFFFFFFF)
                            crc_val = crc32_func(data)
                        except Exception:
                            try:
                                with open(path, 'rb') as fh:
                                    data = fh.read()
                                crc_val = crc32_bytes(data)
                            except Exception as ex:
                                page.snack_bar = SnackBar(Text(f"CRC failed: {ex}"), open=True)
                                page.update()
                                return
                    try:
                        # ensure crc_val is an integer
                        if crc_val is None:
                            raise ValueError("crc_val is None")
                        crc_int = int(crc_val)
                    except Exception:
                        try:
                            with open(path, 'rb') as fh:
                                data = fh.read()
                            crc_int = crc32_bytes(data)
                        except Exception:
                            page.snack_bar = SnackBar(Text("CRC computation failed."), open=True)
                            page.update()
                            return
                    try:
                        crc_hex_field.value = f"{crc_int:08X}"
                        crc_dec_field.value = str(crc_int)
                        pass
                        page.snack_bar = SnackBar(Text("CRC computed."), open=True)
                    except Exception as ex:
                        crc_hex_field.value = ""
                        crc_dec_field.value = ""
                        page.snack_bar = SnackBar(Text(f"CRC failed: {ex}"), open=True)
                    page.update()

                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                if loop and loop.is_running():
                    loop.create_task(_compute())
                else:
                    asyncio.run(_compute())

            def copy_hex(e=None):
                if crc_hex_field.value:
                    safe_set_clipboard(page, crc_hex_field.value)
                    page.snack_bar = SnackBar(Text("Hex copied to clipboard."), open=True)
                    page.update()

            def copy_dec(e=None):
                if crc_dec_field.value:
                    safe_set_clipboard(page, crc_dec_field.value)
                    page.snack_bar = SnackBar(Text("Decimal copied to clipboard."), open=True)
                    page.update()

            crc_browse_btn = Button("Browse...", on_click=browse_crc_file)
            crc_compute_btn = Button("Compute CRC", on_click=compute_crc_for_file)
            crc_copy_hex_btn = Button("Copy Hex", on_click=copy_hex)
            crc_copy_dec_btn = Button("Copy Dec", on_click=copy_dec)

            crc_content = Container(
                Column([
                    Text("CRC32 Calculator", size=20, weight="bold"),
                    Row([crc_file_field, crc_browse_btn], alignment="center"),
                    Row([crc_compute_btn, crc_copy_hex_btn, crc_copy_dec_btn], spacing=12),
                    Divider(),
                    Row([crc_hex_field, crc_dec_field], spacing=12),
                ], alignment="start", horizontal_alignment="start", spacing=8),
                padding=CARD_PADDING,
                bgcolor=PANEL_BG,
                border_radius=RADIUS,
                width=PANEL_WIDTH,
            )

            tools_secondary = Row([
                Container(Column([Text("CRC32 Calculator", size=16, weight="bold"), Text("Compute CRC-32 for files (hex + decimal).", color="white70", size=12), Button("Open", on_click=lambda ev: set_top_content(crc_content))], spacing=8), **card_style, expand=True),
            ], spacing=16, expand=True)

            tools_list = Column([
                tools_hero,
                Divider(),
                tools_features,
                Divider(),
                tools_secondary,
            ], alignment="center", horizontal_alignment="center", expand=True, spacing=12)

            # Top tab buttons
            tabs_row = Row([
                Button("Home", on_click=lambda e: set_top_content(home_content)),
                Button("Workflows", on_click=lambda e: set_top_content(workflows_list)),
                Button("Tools", on_click=lambda e: set_top_content(tools_list)),
            ], spacing=12)

            page.add(
                Stack([
                    Image(src=asset_path("background.png"), expand=True),
                    Column([
                        Container(tabs_row, padding=CARD_PADDING),
                        Container(top_content, expand=True, padding=20),
                    ], expand=True),
                ], expand=True)
            )

            # Start on Home
            set_top_content(home_content)

            # Center the window after the UI has been constructed so sizing/layout are final
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            async def _delayed_center():
                try:
                    await asyncio.sleep(0.03)
                except Exception:
                    pass
                try:
                    _center_window_exact()
                except Exception:
                    try:
                        # fallback to flet's center coroutine
                        await page.window.center()
                    except Exception:
                        pass

            if loop and loop.is_running():
                try:
                    loop.create_task(_delayed_center())
                except Exception:
                    try:
                        _center_window_exact()
                    except Exception:
                        pass
            else:
                try:
                    _center_window_exact()
                except Exception:
                    pass

    # Schedule the intro coroutine on the existing event loop instead of calling asyncio.run()
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if PLAY_INTRO:
        if loop and loop.is_running():
            loop.create_task(play_intro_then_load_ui())
        else:
            asyncio.run(play_intro_then_load_ui())
    else:
        # skip intro and load UI immediately
        load_main_ui()


if __name__ == "__main__":
    flet.run(main)
