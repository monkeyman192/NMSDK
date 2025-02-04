# API guide

Due to how Blender handles adding and registering functions that can be publically used, all public API functions are located within the `bpy.ops.nmsdk` namespace.
All operators **MUST** also be called with keyword arguments (see examples)

## Exporting data from Blender

### __bpy.ops.nmsdk.export_scene(**parameters)__

Export the entire current blender file.

**Parameters**:  
*output_directory* : string  
> The full path of the directory the data is to be exported to. All subsequent folders will reside within this one.
*export_directory* : string  
> The name of the path you want the data to be relative to the `PCBANKS` folder within the games' files.  
> *Default*: `'CUSTOMMODELS'`.

*group_name* : string  
> Name of the sub-folder which the scene will be placed in. This can be used to group multiple exports all into the same folder.  
> *Default*: `scene_name`.

*scene_name* : string  
> Name of the scene being exported. Many files will use this as the main component of their filename.  
> *Default*: The name of the scene object (Ie. the object in the scene that is an empty reference node).

*AT_only* : boolean  
> Whether or not to export just the action triggers in the scene.  
> *Default*: `False`.

*no_vert_colours* : boolean  
> Whether or not the vertex colours should be exported. Generally models won't have vertex colouring unless you add it manually.  
> *Default*: `False`.

*idle_anim* : string  
> The name of the idle animation. If the scene contains no animations then this is not needed. If the scene is animated however this **MUST** be provided.  
> *Default*: `''`.  

**Notes**:  
    This calls the same function as is used when operating NMSDK visually with blender, but with a slightly different call signature to allow exactness.  
    As this call is a blender operator, the scene itself must be loaded by an instance of blender.  

**Example**:  
```python
# First, you need to have to have loaded the blender file with blender
# Let's say we have blender file with a scene node in it called 'NEWMODEL'
# In blender, you can then call the operator as follows:
bpy.ops.nmsdk.export_scene(output_directory='C:\\OUTPUT_PATH', 
                           export_directory='CUSTOMMODELS',
                           group_name='TESTMODEL')
# In this example the files will be produced in the directory
# C:\OUTPUT_PATH\CUSTOMMODELS\TESTMODEL\
# with files such as 'NEWMODEL.SCENE.MBIN', etc.

# If we want to be extra-specific, or overwrite the name in the blender file we can:
bpy.ops.nmsdk.export_scene(output_directory='C:\\OUTPUT_PATH', 
                           export_directory='CUSTOMMODELS',
                           group_name='TESTMODEL',
                           scene_name='SOMETHINGELSE')
# Where we will now get the files output in the same folder as before, but as a scene called 'SOMETHINGELSE.SCENE.MBIN', etc
```

---

## Importing data into Blender

### __bpy.ops.nmsdk.import_scene(path)__

Import a complete NMS scene into blender.

**Parameters**:  
*path* : string  
> The complete file path to a `SCENE.MBIN` or `SCENE.MXML` file to be loaded into blender.

**Notes**:  
    The entire scene will be loaded into the active scene in blender.

**Example**:
```python
bpy.ops.nmsdk.import_scene(path='C:\\NMS-1.77\\MODELS\\PLANETS\\BIOMES\\COMMON\\CRYSTALS\\LARGE\\CRYSTAL_LARGE.SCENE.MBIN')
```

### __bpy.ops.nmsdk.import_mesh(path, mesh_id)__

Import part of a scene specified by the id of a mesh node in the scene file.

**Parameters**:  
*path* : string
> The complete file path to a `SCENE.MBIN` or `SCENE.MXML` file to be loaded into blender.

*mesh_id* : string
> The `Name` of the `TkSceneNodeData` in the Scene being loaded.

**Notes**:  
    Only this object will be loaded. None of the children will be.

**Example**:
```python
bpy.ops.nmsdk.import_mesh(path='C:\\NMS-1.77\\MODELS\\PLANETS\\BIOMES\\COMMON\\CRYSTALS\\LARGE\\CRYSTAL_LARGE.SCENE.MBIN', mesh_id='_CRYSTAL_A')
```