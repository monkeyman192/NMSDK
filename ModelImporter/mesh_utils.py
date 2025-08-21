# A collection of functions which will handle mesh operations

from mathutils import Matrix


def BB_transform_matrix(x_bounds: tuple, y_bounds: tuple,
                        z_bounds: tuple) -> Matrix:
    """ Generate the matrix to transform a default cube so that it goes to the
    expected location for the given bounds."""
    sx = x_bounds[1] - x_bounds[0]
    sy = y_bounds[1] - y_bounds[0]
    sz = z_bounds[1] - z_bounds[0]
    tx = x_bounds[0] + 0.5 * sx
    ty = y_bounds[0] + 0.5 * sy
    tz = z_bounds[0] + 0.5 * sz
    scale_mat = Matrix(
        [
            (abs(sx), 0, 0, 0),
            (0, abs(sz), 0, 0),
            (0, 0, abs(sy), 0),
            (0, 0, 0, 1)
        ]
    )
    trans_mat = Matrix.Translation((tx, tz, ty))
    return trans_mat @ scale_mat
