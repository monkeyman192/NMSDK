# NMSDK Changelog

## Releases:

### Current - v0.9.18

 - Added the ability to import lighting. The current brightness setting is set at 1/100 of the value in the scene. This may change if better settings/node setup is found.
 - An option has been added to specify a custom location for the PCBANKS folder in case the scene file isn't located in the same folder as the unpacked data. The scene file *should* still line in a proper relative directory structure however.
 - The setting for indicating what the maximum number of animations has been changed. Now you can specify the value as a number, with `-1` being load all, `0` load none, and any positive number being the maximum number of animations to load.
 - Fixed a few other small errors that could occur in weird cases such as for some descriptors.

**NOTE**: This is the final Blender 2.79 compatible release. All future releases will be for Blender 2.80 and above.

### Past:

### v0.9.17 (28/08/2019)

 - Fixed the issue where adding the addon from a zip file wouldn't actually add it to blender.
 - NMSDK can now also be run on blender on linux, however MBINCompiler doesn't work on this platform so it has limited uses...

### v0.9.16 (20/08/2019)

 - Quick fix to implement compatibility with new Beyond-style scenes.

### v0.9.15 (13/08/2019)

 - Mostly internal updates. Made some changes to the internal API and added a new public function for exporting models via the command line. More information can be found on the [API guide](api.md) page.

### v0.9.14 (10/08/2019)

 - The animation exporting system has received a major overhaul. It is now far mor easy for each part to have mutliple animations.
 - The Idle animation can now be set from the `Animation controls` section of the NMSDK toolbar. Any animation that isn't specified as the idle one 

#### v0.9.13 (02/08/2019)

 - Import process has been expanded to allow for animations to be imported. This includes both simple animations (one with just translation/rotation/scaling of nodes in the scene), as well as complex animations which involve skinned meshes and bones. Currently complex animations are still a bit broken, but hopefully they will be fixed in the future.
 To see more details on what options are available for imported animations, see [here](importing/importing.md#import_settings).
 - Tests have been added to NMSDK! This has no affect on the plugin itself, however if you clone the repo from github you will now notice a number of files from the game which are used to test the importing capabilities of NMSDK. This will be extended greatly in the future, but for now there is only the framework and a few simple tests.

#### v0.9.12 (03/06/2019):

- Add support for importing `Box`, `Cylinder` and `Sphere` type primitive collisions.
- On import there is an option to allow for displaying the collisions which is false by default.
- Display of collisions can be toggled by the button in the NMSDK side panel.
- When importing models, importing collisions can be turned off so that no collision meshes appear in the scene.
- Default values can be set for the `export path` and `group name` export properties in the NMSDK settings panel. These will persists across multiple sessions to make exporting multiple models in the same set easier.

#### v0.9.11 (25/05/2019):

- This version (FINALLY!) implements the exporting of mesh type collisions.

To allow this the `Mesh` type has been re-enabled in the `Collision` node panel.
Currently if you wish to export a mesh type collision, you need to apply the scale and rotation transforms to the mesh, otherwise your exported data will not have these values.

#### v0.9.10 (24/05/2019):

- This version fixes a number of issues introduced in v0.9.9 when attempting to fix imports. Exports should now be far more stable.

#### v0.9.9 (23/05/2019):

- Vertex colour is now able to be exported. To add vertex colour to a model change the mode in blender to "Vertex Paint".
- Nested referenced scenes can also be exported. This gives complete flexibility to the way a scene is to be exported.
