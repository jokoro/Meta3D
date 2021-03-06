import geometry
import collections
import math
import matrices
import algebra
import copy

Part = collections.namedtuple('Part', ['equ', 'bound'])
Boundary = collections.namedtuple('Boundary', ['eqns'])  # list of equations, function can't pass
SetOfPlanes = collections.namedtuple('SetOfPlanes', ['x', 'y'])
PointsOfEquation = collections.namedtuple('PointsOfEquation', ['expr', 'planes'])

MAGNITUDE_STEP = 10
REVOLUTION = 2 * math.pi
ZERO_VECTOR = geometry.Vector(0, 0, 0)


class NotAVectorError(Exception):
    pass


class IntersectionsOfPlane:
    def __init__(self, value, intersections):
        self.value = value
        self.intersections = intersections


def vector_to_matrix(vector):
    return matrices.Matrix([[vector.x], [vector.y], [vector.z]])


def matrix_to_vector(matrix: matrices.Matrix):
    if matrix.rows == 3 and matrix.cols == 1:
        return geometry.Vector(matrix.matrix[0][0], matrix.matrix[1][0], matrix.matrix[2][0])
    else:
        raise NotAVectorError()


def _matrix_times_a_vector(matrix, vector):
    return matrix_to_vector(matrix.matrix_multiplication(vector_to_matrix(vector)))


def sign(num: int or float) -> int:
    if num == 0:
        return 0
    else:
        return int(num/abs(num))


class BoundaryError(Exception):
    pass


class Object3D:
    def __init__(self, parts: [Part], divisor: int) -> None:  # only takes xyz
        self.parts = parts
        self.faces = self._new_faces(REVOLUTION / divisor)
        self._update_faces()

    def rotate(self, theta_xy, theta_yz, theta_xz):
        rotate = geometry.rotate_matrix(theta_xy, theta_yz, theta_xz)
        for i, face in enumerate(self.faces):
            corners = []
            for corner in face.corners:
                rotated_corner = _matrix_times_a_vector(rotate, corner)
                corners += [rotated_corner]
            self.faces[i] = geometry.Face(corners)
        self._update_faces()

    # def _new_planes(self, boundary, divisor) -> [str]:  # ex. 'x=1'
    #     return
    #
    # def _new_faces(self, function: [str], boundary: Boundary) -> [geometry.Face]:
    #     faces = []
    #     for function in function:
    #         for i in range(len(self.planes.y) - 1):
    #             for j in range(len(self.planes.x) - 1):
    #                 corners = []
    #                 for x_plane, y_plane in [(self.planes.x[i],     self.planes.y[j]),
    #                                          (self.planes.x[i + 1], self.planes.y[j]),
    #                                          (self.planes.x[i + 1], self.planes.y[j + 1]),
    #                                          (self.planes.x[i],     self.planes.y[j + 1])]:
    #                     try:
    #                         x, y, z = self._calc_coordinates(x_plane, y_plane, function, boundary)
    #                         corners += [geometry.Vector(x, y, z)]
    #                     except ValueError:  # point not on graph, add z = 0 plane
    #                         pass
    #                         # x, y, z = self._calc_coordinates(x_plane, z_plane, '0', boundary)
    #                         # corners += [geometry.Vector(x, y, z)]
    #                     except:  # something else wrong, likely incorrect syntax or data type in exec arg
    #                         raise algebra.EquationError()
    #                 if len(corners) >= 3:
    #                     faces += [geometry.Face(corners)]  # could add center here using equation
    #     return faces

    def _new_faces(self, angle_step) -> [geometry.Face]:
        # be warned, this algorithm will be inaccurate b/c adding to desired values
        faces = []
        point = geometry.Vector(0, 1, 0).unit_vector()  # it already is a unit vector, but in case I change it
        a = copy.deepcopy(point)

        rotate_xy = geometry.rotate_matrix(angle_step, 0, 0)
        rotate_yz = geometry.rotate_matrix(0, angle_step, 0)

        for part in self.parts:
            theta_xy = 0
            while theta_xy < REVOLUTION:
                theta_yz = 0
                while theta_yz < REVOLUTION:
                    corners = []
                    for xy_coef, yz_coef in [(0, 0), (1, 0), (1, 1), (0, 1)]:
                        corner = copy.deepcopy(point)

                        corner_rotate_xy = geometry.rotate_matrix(xy_coef * angle_step, 0, 0)
                        corner_rotate_yz = geometry.rotate_matrix(0, yz_coef * angle_step, 0)

                        corner = _matrix_times_a_vector(corner_rotate_xy, corner)
                        corner = _matrix_times_a_vector(corner_rotate_yz, corner)

                        orig_func_signs, orig_bound_signs = self.get_signs(part, corner)

                        print(corner.angle_between_vectors(a))

                        while True:
                            corner = corner.plus(corner.unit_vector().times(MAGNITUDE_STEP))
                            # assuming no folds, spirals, etc from a single function
                            try:
                                func_signs, bound_signs = self.get_signs(part, corner)
                                if bound_signs != orig_bound_signs:
                                    # won't add points at bound for given func
                                    break  # don't add points past here
                                if func_signs != orig_func_signs:
                                    corners += [corner]
                                    break  # don't add points past here
                            except ValueError:  # not on graph, but further points may be, up until boundary
                                continue

                    if len(corners) >= 3:
                        faces += [geometry.Face(corners)]

                    point = _matrix_times_a_vector(rotate_yz, point)
                    theta_yz += angle_step

                point = _matrix_times_a_vector(rotate_xy, point)
                theta_xy += angle_step

        return faces

    def get_signs(self, part: Part, corner: geometry.Vector) -> ([int], [int]):
        func_signs = []
        bound_signs = []
        x, y, z = corner.x, corner.y, corner.z

        for obj_func in part.equ.funcs:
            try:
                func_signs += [sign(eval(f'corner.{part.equ.var_out} - ({obj_func})'))]
            except ValueError:
                # None is place holder for invalid, hopefully also changes when passing (all?) surfaces
                func_signs += [None]

        for bound_equ in part.bound.eqns:
            for bound_func in bound_equ.funcs:
                try:
                    bound_signs += [sign(eval(f'corner.{bound_equ.var_out} - ({bound_func})'))]
                except ValueError:
                    bound_signs += [None]

        return func_signs, bound_signs

    def _calc_coordinates(self, x_plane, y_plane, function, boundary):
        x, y = x_plane.value, y_plane.value
        z = eval(function)

        if z <= boundary.min_z or boundary.max_z <= z:
            raise ValueError

        return x, y, z

    def _sort_faces(self, faces: [str], low: int, high: int) -> None:
        """ From https://www.geeksforgeeks.org/python-program-for-quicksort/ """
        if low < high:
            pi = self._partition(faces, low, high)

            self._sort_faces(faces, low, pi - 1)
            self._sort_faces(faces, pi + 1, high)

    def _partition(self, faces: [str], low: int, high: int) -> int:
        """ From https://www.geeksforgeeks.org/python-program-for-quicksort/ """
        i = low - 1
        pivot = self.faces[high].corners[0].z

        for j in range(low, high):
            if self.faces[j].corners[0].z <= pivot:
                i += 1
                faces[i], faces[j] = faces[j], faces[i]

        faces[i + 1], faces[high] = faces[high], faces[i + 1]
        return i + 1

    def _update_faces(self):
        self._sort_faces(self.faces, 0, len(self.faces) - 1)
