def generate_unit_name(faction: str, unit_type: str, nickname: str, index: int = 1) -> str:
    faction = faction.lower()
    unit_type = unit_type.lower()
    nickname = nickname.lower()
    return f"{faction}_{unit_type}_{nickname}_{index:02d}"
