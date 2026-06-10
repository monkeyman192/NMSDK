import tomllib

with open("src/addon/nmsdk/blender_manifest.toml", "rb") as f:
    print(tomllib.load(f)["version"])
