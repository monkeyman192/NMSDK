from mathutils import Matrix


# This matrix is the inverse of the coordinate transform matrix that we apply
# to the base node to transform the NMS coordinates to blender coordinates.
# We need this to take obj.matrix_world data and convert it into the equivalent
# world matrix in the NMS coordinate space.
# We get this by doing `UNDO_COORDINATE_TRANFORM @ obj.matrix_world`
UNDO_COORDINATE_TRANFORM = Matrix((
    (1, 0, 0, 0),
    (0, 0, 1, 0),
    (0, -1, 0, 0),
    (0, 0, 0, 1)
))