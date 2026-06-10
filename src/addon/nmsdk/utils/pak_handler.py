from bpy.types import PropertyGroup


pak_data = {}


class PakInfo(PropertyGroup):
    scene_paths = []
    file_mapping: dict[str, str] = {}