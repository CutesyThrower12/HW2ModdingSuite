import random
from Modules.Name.unit_name import generate_unit_name

def generate_dbid() -> int:
    """Generate a random 64-bit number"""
    return random.getrandbits(64)

class UnitObject:
    def __init__(
        self,
        faction: str,
        unit_type: str,
        nickname: str,
        index: int,
        parent: str,
        visual_path: str,
        tactics_path: str,
        velocity: int,
        acceleration: int,
        los: int,
        hitpoints: int,
        damage_normal: str,
        damage_cover: str,
        ability_command: str = "",
        object_type: str = "InfantryTech"
    ):
        self.name = generate_unit_name(faction, unit_type, nickname, index)
        self.dbid = generate_dbid()
        self.parent = parent
        self.visual = visual_path
        self.tactics = tactics_path
        self.velocity = velocity
        self.acceleration = acceleration
        self.los = los
        self.hitpoints = hitpoints
        self.ability_command = ability_command
        self.object_type = object_type
        self.damage_normal = damage_normal
        self.damage_cover = damage_cover

    def to_xml(self) -> str:
        """Return XML string of the object"""
        from xml.etree.ElementTree import Element, SubElement, tostring
        from xml.dom import minidom

        root = Element("Object", {
            "name": self.name,
            "dbid": str(self.dbid),
            "parent_element": self.parent
        })

        SubElement(root, "Visual").text = self.visual
        SubElement(root, "Tactics").text = self.tactics
        SubElement(root, "Flag").text = "HasHPBar"
        SubElement(root, "Velocity").text = str(self.velocity)
        SubElement(root, "Acceleration").text = str(self.acceleration)
        SubElement(root, "LOS").text = str(self.los)
        SubElement(root, "Hitpoints").text = str(self.hitpoints)

        if self.ability_command:
            SubElement(root, "AbilityCommand").text = self.ability_command

        SubElement(root, "ObjectType").text = self.object_type

        SubElement(root, "DamageType", direction="Full", mode="Normal").text = self.damage_normal
        SubElement(root, "DamageType", direction="Full", mode="Cover").text = self.damage_cover

        # Pretty print
        rough = tostring(root, encoding="unicode")
        return minidom.parseString(rough).toprettyxml(indent="\t")
