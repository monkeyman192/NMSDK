from bpy.types import PropertyGroup


class PakInfo(PropertyGroup):
    scene_paths = []
    file_mapping: dict[str, str] = {}