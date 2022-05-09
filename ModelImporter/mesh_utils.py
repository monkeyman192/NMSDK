# A collection of functions which will handle mesh operations
from math import radians
from typing import List

from mathutils import Matrix


def polygonalise(tris: List[tuple]) -> tuple:
    """ Take an n-gon and a tri which are assumed to be coplanar and extend the
    n-gon with the extra point provided by the tri and keep index ordering. """
    # Create an initial tuple.
    poly = list(tris[0])
    todos = []

    def add_tris(tri_list):
        # Loop over every tri but the first.
        for tri in tri_list:
            # Create the set of indexes in the poly.
            X = set(poly)
            # Create the set of indexes in the current tri.
            Y = set(tri)
            # Find the points that intersect.
            # There should be 2 (a shared line).
            S = X & Y
            if len(S) != 2:
                todos.append(tri)
                continue
            # The extra point will be the difference in the set of points in
            # the tri and the shared points
            extra_pt = Y - S
            S = tuple(S)
            extra_pt = extra_pt.pop()
            # Get the indexes of the points which are in the poly.
            a_idx = poly.index(S[0])
            b_idx = poly.index(S[1])
            # If the indexes are the first and last values, then we add to the
            # end of the poly
            if set((a_idx, b_idx)) == {0, len(poly) - 1}:
                poly.append(extra_pt)
            elif abs(a_idx - b_idx) == 1:
                poly.insert(max(a_idx, b_idx), extra_pt)
            else:
                todos.append(tri)

    add_tris(tris[1:])

    if todos:
        _todos = todos[:]
        todos = []
        add_tris(_todos)
    return tuple(poly)


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
