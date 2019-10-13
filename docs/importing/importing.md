# Importing models into Blender

NMSDK is capable of importing NMS *SCENE* files and loading the models.

At the moment the functionality is still in beta and has many issues, primarily due to the custom shader setup used by NMS.

Importing scenes from the game is simple. An option can be found in the `Import` drop-down menu found by selecting `File` > `Import`

![importing](../../images/import.png)

This will open up a file selection dialog which lets you select the scene you wish to import.
Keep in mind that at the moment NMSDK will import **all** of the components of a scene including ones that are referenced by the scene. So for a large scene such as the freighter scene it may actually take a minute or two to load all the data.

## Import settings

When importing scenes into blender, there are a number of options that can be changed to allow for flexibility when importing. These are as follows:

#### Draw bounded hulls

This setting is essentially for debugging purposes. There is never going to be a time in standard use that you will want to enable this.

#### Clear scene

This will remove any existing objects in the scene (except camera and light) then import the scene into the empty blender scene. If you are wanting to import multiple scenes into the one blender scene then you can disable this option.

#### Import collisions

If you are simply wanting to see what the model looks like, you can safely disable this option. This may be used for debugging existing models.
This is enabled by default, however these collisions are not drawn (see next option...)

#### Draw collisions

If collisions are imported, specify whether they should be drawn intially. This is disabled by default and will probably be removed as an option soon as it has been superseded by the ability to toggle the collision visibility via the [NMSDK properties panel](../settings.md#scene_tools).

#### Import bones

Whether or not to import the bones for models that have them. This is useful if you are importing models to animate yourself as they are already rigged.
This functionality is still reasonably broken so do not expect good results if this is enabled.

#### Max loaded animations

Specify the maximum number of animations to be imported.  
The default is set to 10 as you generally don't want to be importing many more than this as it can take a while.  
To disable importing any animations set this value to `0`.  
To force all animations to load (generally **not** recommended), set the value to `-1`.  
Otherwise, set the value to a positive integer.

Keep in mind that for the player model there are over 300 animations to load so it takes an extremely long time to load all of them.
For more on loading animations after the scene has been loaded, see [here](../settings.md#animation_controls).