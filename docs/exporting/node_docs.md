# Node Properties

Each node type has various properties that can be set. These are documented below.

## Mesh Node

The `Mesh` node is only type of node that is used for mesh data that you want to be exported into a geometry file.

- **Requires Entity** : `bool`

Indicates whether or not the specified mesh object has an associated entity.
Selecting this will add an entity panel (see the page on [adding entities](./entities.md) for more details.)

- **Material** : `str`

The path to a material file if the mesh object does not have a custom material within blender.
If you are using vanilla materials or a material you have already created/exported, then you can speed up the export process by simply setting this value to the path of the material file.

## Locator Node

A `Locator` node is used to create something at a particular point in space. Whether it me a place to group objects, or a location at which an interaction will occur at.

- **Requires Entity** : `bool`

Indicates whether or not the specified mesh object has an associated entity.
Selecting this will add an entity panel (see the page on [adding entities](./entities.md) for more details.)

## Reference Node

A `Reference` node is used to indicate that another scene is included by reference in the parent scene. This may sometimes happen multiple times in a scene in a nested fashion.

- **Reference Path** : `str`

The path to the scene that is referenced within the parent scene at the specified location.
This value can be set to nest vanilla scenes or already exported scenes within you current scene without having to export them again.

- **Scene Name** : `str`

For a scene that is to be exported separately, but kept in the original scene as a reference, this is the base name of the scene file. So for example if you want a scene to be exported with the file name `TESTCUBE.SCENE.MBIN`, you would specify this to be `testcube`. The case of the value doesn't matter as it is always changed to uppercase in the export process.

- **Is a proc-gen scene?** : `bool`

Used to indicate whether or not the scene being exported requires a descriptor to be produced, causing it be procedurally generated.
For more info on how this works see [here](./exporting/proc_gen.md).

## Collision Node

A `Collision` node is used to specify a primitive object that will be used as a collition for the model.

- **Collision Type** : one of `Box`, `Sphere` or `Cylinder`

The type of collision primitive to use.

- **Scale Transform** : one of `Transform` or `Dimensions`

Specifies whether the final transform of the collision object uses the objects' transform (`Transform`), or the actual size (`Dimensions`). This is useful if an object has has a scale transform applied to it, you can still retreive the shape of it by using the `Dimensions` option.

## Light Node

A `Light` node is used to create a light source in the scene.

- **Intensity** : `float`

The intensity of the light.

- **FOV** : `float`

The field of view of the light source. Values can range from 0 to 360 (degrees).

## Joint Node

A `Joint` node is used for animation data. This is currently not working right now butit has no further properties that need to be set to use it.