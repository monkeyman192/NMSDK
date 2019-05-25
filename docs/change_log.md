# NMSDK Changelog

## Releases:

### Current - v0.9.11 (25/05/2019):

This version (FINALLY!) implements the exporting of mesh type collisions.

To allow this the `Mesh` type has been re-enabled in the `Collision` node panel.
Currently if you wish to export a mesh type collision, you need to apply the scale and rotation transforms to the mesh, otherwise your exported data will not have these values.

### Past:

#### v0.9.10 (24/05/2019):

- This version fixes a number of issues introduced in v0.9.9 when attempting to fix imports. Exports should now be far more stable.

#### v0.9.9 (23/05/2019):

- Vertex colour is now able to be exported. To add vertex colour to a model change the mode in blender to "Vertex Paint".
- Nested referenced scenes can also be exported. This gives complete flexibility to the way a scene is to be exported.
