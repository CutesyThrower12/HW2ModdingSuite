import sys
import os
from Modules.Object.unit_object import UnitObject
from Modules.Library.lib import load_library, suggest_items

# -------------------------
# Helper Functions
# -------------------------
def resource_path(relative_path):
    """
    Get absolute path to resource.
    Works for PyInstaller EXE or normal script.
    """
    if hasattr(sys, "_MEIPASS"):
        # Running in PyInstaller bundle
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


def get_int_input(prompt):
    """Ask user for integer input until valid."""
    while True:
        value = input(prompt)
        if value.isdigit():
            return int(value)
        else:
            print("Please enter a valid number.")


def select_from_library(library, prompt):
    """
    Suggest items from a library based on user input.
    Keeps asking until exactly one match is selected.
    """
    while True:
        query = input(prompt)
        matches = suggest_items(query, library)

        if len(matches) == 1:
            print(f"Selected: {matches[0]}")
            return matches[0]

        elif len(matches) > 1:
            print("Matches:")
            for m in matches[:10]:
                print(" -", m)
            print("(Keep typing to refine search)")

        else:
            print("No matches. Try again.")


# -------------------------
# Main Program
# -------------------------
def main():
    print("Halo Wars 2 Object Generator")
    print("-----------------------------")

    # Basic unit info
    faction = input("Faction (unsc/cov/custom): ")
    unit_type = input("Unit type (inf/veh/air): ")
    nickname = input("Nickname: ")
    index = get_int_input("Index number: ")

    # Load and select Parent Element
    parents_path = resource_path("Modules/Library/parents.json")
    parents_lib = load_library(parents_path)
    parent = select_from_library(parents_lib, "Parent element (type to search): ")

    # Load and select Tactics file
    tactics_path = resource_path("Modules/Library/tactics.json")
    tactics_lib = load_library(tactics_path)
    tactics = select_from_library(tactics_lib, "Tactics (type to search): ")

    # Load and select Damage Types
    damage_path = resource_path("Modules/Library/damage_types.json")
    damage_lib = load_library(damage_path)

    print("\nSelect Normal DamageType:")
    damage_normal = select_from_library(damage_lib, "Type to search: ")

    print("\nSelect Cover DamageType:")
    damage_cover = select_from_library(damage_lib, "Type to search: ")

    # Other inputs
    visual = input("Visual path (.vis): ")
    velocity = get_int_input("Velocity: ")
    acceleration = get_int_input("Acceleration: ")
    los = get_int_input("Line of Sight (LOS): ")
    hitpoints = get_int_input("Hitpoints: ")
    ability = input("Ability command (optional): ")

    # Create Unit Object
    obj = UnitObject(
        faction=faction,
        unit_type=unit_type,
        nickname=nickname,
        index=index,
        parent=parent,
        visual_path=visual,
        tactics_path=tactics,
        velocity=velocity,
        acceleration=acceleration,
        los=los,
        hitpoints=hitpoints,
        damage_normal=damage_normal,
        damage_cover=damage_cover,
        ability_command=ability
    )

    # Output XML
    print("\nGenerated Object XML:\n")
    print(obj.to_xml())

    input("\nPress ENTER to exit...")


if __name__ == "__main__":
    main()
