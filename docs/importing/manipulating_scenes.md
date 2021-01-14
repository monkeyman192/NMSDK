# Manipulating scenes imported into Blender

(Added in version 0.9.21)

When a scene is loaded in, all the values in the scene such as info about the meshes, and everything is stored in the blender scene.
When re-exporting, there is an option which exports all the values that are not modified.

![preserve nodes](../../images/preserve_import.png)

There are some limitations and considerations to keep in mind when using this mode which are listed below:

### Limitations

 - You cannot make any modifications to any of the meshes. Any changes made will be ignored.
 - Animations cannot be modified at this time. Maybe in the future this will be possible, but not right now.
 - You cannot add new LOD levels.

### Considerations

When making changes you should take the following things into consideration:

 - When you make a change to the scale, position or rotation of an object, you should do so whilst in object mode so that the change is applied. Do not apply the change within blender.
 - To add new nodes it is recommended that you add them with the handy context menu options.

![add reference nodes](../../images/add_ref_node.png)

**Note**: There may still be some issues with this process as it is still in development. If you see something not work as you think it should, please raise an issue on github!
