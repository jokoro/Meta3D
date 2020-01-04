import geometry
import collections
import math
import matrices
import algebra

Boundary = collections.namedtuple('Boundary', ['min_x', 'max_x', 'min_y', 'max_y', 'min_z', 'max_z'])
SetOfPlanes = collections.namedtuple('SetOfPlanes', ['x', 'y'])
PointsOfEquation = collections.namedtuple('PointsOfEquation', ['expr', 'planes'])


class NotAVectorError(Exception):
    pass


class IntersectionsOfPlane:
    def __init__(self, value, intersections):
        self.value = value
        self.intersections = intersections


def _check_boundary_error(boundary: Boundary) -> None:
    try:
        if boundary.min_x > boundary.max_x or \
                boundary.min_y > boundary.max_y or \
                boundary.min_z > boundary.max_z:
            raise BoundaryError()
    except TypeError:  # boundary component(s) not int/float
        raise BoundaryError()


def vector_to_matrix(vector):
    return matrices.Matrix([[vector.x], [vector.y], [vector.z]])


def matrix_to_vector(matrix: matrices.Matrix):
    if matrix.rows == 3 and matrix.cols == 1:
        return geometry.Vector(matrix.matrix[0][0], matrix.matrix[1][0], matrix.matrix[2][0])
    else:
        raise NotAVectorError()


def _rotate_matrix(theta_xy, theta_yz, theta_xz):
    xy_rotate = matrices.Matrix([[math.cos(theta_xy), -math.sin(theta_xy), 0],
                                 [math.sin(theta_xy), math.cos(theta_xy),  0],
                                 [0,                  0,                   1]])

    yz_rotate = matrices.Matrix([[1, 0, 0],
                                 [0, math.cos(theta_yz),  math.sin(theta_yz)],
                                 [0, -math.sin(theta_yz), math.cos(theta_yz)]])

    xz_rotate = matrices.Matrix([[math.cos(theta_xz), 0, -math.sin(theta_xz)],
                                 [0,                  1, 0],
                                 [math.sin(theta_xz), 0, math.cos(theta_xz)]])

    return xy_rotate.matrix_multiplication(yz_rotate).matrix_multiplication(xz_rotate)


def _matrix_times_a_vector(matrix, vector):
    return matrix_to_vector(matrix.matrix_multiplication(vector_to_matrix(vector)))


class BoundaryError(Exception):
    pass


class EquationError(Exception):
    pass


class Object3D:
    def __init__(self, equation: algebra.Equation, boundary: Boundary, divisor: int) -> None:  # only takes xyz
        _check_boundary_error(boundary)
        self.equation = equation
        self.planes = self._new_planes(boundary, divisor)
        self.faces = self._new_faces(self._new_expressions(), boundary)
        self._update_faces()

    def rotate(self, theta_xy, theta_yz, theta_xz):
        rotate = _rotate_matrix(theta_xy, theta_yz, theta_xz)
        for i, face in enumerate(self.faces):
            corners = []
            for corner in face.corners:
                rotated_corner = _matrix_times_a_vector(rotate, corner)
                corners += [rotated_corner]
            self.faces[i] = geometry.Face(corners)
        self._update_faces()

    def _new_expressions(self):
        if self.equation.z is not None:
            expr = self.equation.z
        elif self.equation.y is not None:
            expr = self.equation.y
        elif self.equation.x is not None:
            expr = self.equation.x
        else:
            raise EquationError('need at least one variable to create object')

        expressions = [expr]
        pow_idx = expr.find('math.pow')

        if pow_idx > -1:
            pow_args = algebra.paren_args(expr, pow_idx + len('math.pow'))[0]
            pow_arg2 = pow_args[pow_args.index(',') + 1:]
            if eval(f'{pow_arg2}**-1 % 2 == 0'):
                expressions += [expr.replace('math.pow', '-math.pow')]  # assuming only 1 pow & came from solving

        return expressions

    def _new_planes(self, boundary, divisor) -> [str]:  # ex. 'x=1'
        x_length = boundary.max_x - boundary.min_x
        y_length = boundary.max_y - boundary.min_y

        x_planes = []
        y_planes = []
        for i in range(divisor + 1):
            x = boundary.min_x + i * x_length / divisor
            y = boundary.min_y + i * y_length / divisor

            x_planes += [IntersectionsOfPlane(x, [])]
            y_planes += [IntersectionsOfPlane(y, [])]

        return SetOfPlanes(x_planes, y_planes)

    def _new_faces(self, z_expressions: [str], boundary: Boundary) -> [geometry.Face]:
        faces = []
        for expression in z_expressions:
            for i in range(len(self.planes.x) - 1):
                for j in range(len(self.planes.y) - 1):
                    corners = []
                    for x_plane, y_plane in [(self.planes.x[i],     self.planes.y[j]),
                                             (self.planes.x[i + 1], self.planes.y[j]),
                                             (self.planes.x[i + 1], self.planes.y[j + 1]),
                                             (self.planes.x[i],     self.planes.y[j + 1])]:
                        try:
                            x, y, z = self._calc_coordinates(x_plane, y_plane, expression, boundary)
                            corners += [geometry.Vector(x, y, z)]
                        except ValueError:  # point not on sphere, add None as a place holder
                            x, y, z = self._calc_coordinates(x_plane, y_plane, '0', boundary)
                            corners += [geometry.Vector(x, y, z)]
                        except:  # something else wrong, likely incorrect syntax or data type in exec arg
                            raise EquationError()
                    if len(corners) >= 3:
                        faces += [geometry.Face(corners)]  # could add center here using equation
        return faces

    def _calc_coordinates(self, x_plane, y_plane, expression, boundary):
        x, y = x_plane.value, y_plane.value
        z = eval(expression)

        if z <= boundary.min_z:
            z = boundary.min_z
        elif boundary.max_z <= z:
            z = boundary.max_z

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
