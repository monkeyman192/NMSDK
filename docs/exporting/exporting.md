# Exporting a Blender scene into a NMS compatible format

NMSDK's primary functionality is to convert scenes created in Blender into a format that NMS can load and display in the game.
This can be anything from extra rocks or plants, to custom buildings that are scattered around on planets, new parts to be added to your base, or even new ships or freighters that can be flown or part of your fleet!

To provide this functionality a new panel has been added to the blender user interface (UI) to allow the user to enter any relevant information required to export a model to the format compatible with NMS.

## Updating from old-format scenes

Previously all objects that were to be exported had to be a child of a node called `NMS_SCENE`. This requirement has been removed in the current version of NSMDK, as well as the requirement for an object to have `NMS_` at the beginning of its name.
Old format scenes in blender can be updated to the new format by simply pressing the `Change NMS Node type` button in the NMSDK side panel:

![update nodes](/../images/update_old_scenes.png)

## Setting up

NMSDK uses a consistent node setup for both imported and exported scenes to allow the `import > modify > export` workflow to be as seamless as possible.
Because of this, the `Reference` node type is given a special place.
Putting it simply, the `Reference` node type is used to denote a scene that is to be exported.
`Reference` nodes can either be at the top level of a scene (to indicate that you have multiple scenes to be exported that are potentially unrelated to each other), or nested within a scene (to indicate that the sub-scene may be referenced by other scenes).
To allow for flexibility, `Reference` nodes can be given two important properties, `Reference path` and `Scene name`.

`Reference path` is used to specify the path to an external scene file (relative to the PCBANKS folder).

`Scene name` is used to specify the name of the exported sub-scene.
This is the name of the scene that any child objects will be exported in.


To illustrate how the parameters work consider the following two images.

![sub ref example 1](/../images/sub_ref_example1.png)
![sub ref example 2](/../images/sub_ref_example2.png)

In the first image we can see that the object is a reference to a scene that already exists in the NMS game files.
In this case the scene will simply contain a `REFERENCE` node with the `SCENEGRAPH` property being the path to the specified scene.

In the second image we can see that the object has no reference path, but instead has a `Scene name`.
When the blender scene is exported, there will be two scenes exported. The main scene (with `NMS_SCENE` being the top-most reference object), and the `ref_mount` object which will export to a scene file named `CONSTRUCTMOUNT.SCENE.MBIN`.
The main scene will contain a `REFERENCE` node with the `SCENEGRAPH` property being the file path (again, relative to the PCBANKS folder) for this scene.

Once you have set at least one primary object that is to be the `Reference` node, you can specify any subsequent objects to be a `Mesh`, `Locator`, `Reference`, `Light`, `Joint` or `Collision` node.
These each have their own various uses and if you are familiar with NMS scenes it will be easy to specify what each object in a blender scene is.