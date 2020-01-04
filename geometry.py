import math
import collections


class InvalidCalcError(Exception):
    pass


class PlanePointsError(Exception):
    pass


class ZeroVectorError(Exception):
    pass


Point2 = collections.namedtuple('Point2', ['x', 'y'])
Point3 = collections.namedtuple('Point3', ['x', 'y', 'z'])
# Vector = collections.namedtuple('Vector', ['x', 'y', 'z'])  # only in R^3


def duplicate_points(points: [Point3]) -> bool:
    if len(points) > 1:
        for point in points[1:]:
            if points[0] == point:
                return True
        else:
            return duplicate_points(points[1:])
    else:
        return False


class Vector:
    def __init__(self, x, y, z) -> None:
        self.x = x
        self.y = y
        self.z = z
        self.magnitude = self.magnitude()

    def plus(self, v: 'Vector') -> 'Vector':
        """ Adds two vectors """
        return Vector(self.x + v.x, self.y + v.y, self.z + v.z)

    def minus(self, v: 'Vector') -> 'Vector':
        """ Subtracts two vectors """
        return Vector(self.x - v.x, self.y - v.y, self.z - v.z)

    def times(self, scalar) -> 'Vector':
        """ Multiplies vector by a scalar """
        return Vector(scalar * self.x, scalar * self.y, scalar * self.z)

    def dot_product(self, v: 'Vector') -> int or float:
        """ Performs dot product on two vectors """
        return self.x * v.x + self.y * v.y + self.z * v.z

    def cross_product(self, v: 'Vector') -> 'Vector':
        """ Performs cross product on two vectors """
        return Vector(self.y * v.z - v.y * self.z,
                      v.x * self.z - self.x * v.z,
                      self.x * v.y - v.x * self.y)

    def magnitude(self) -> float:
        """ Magnitude of a vector """
        return math.sqrt(self.dot_product(self))

    def unit_vector(self) -> 'Vector':
        """ Returns vector of same direction but magnitude of 1 """
        magnitude = self.magnitude
        if magnitude == 0:
            raise ZeroVectorError()
        else:
            return Vector(self.x / magnitude, self.y / magnitude, self.z / magnitude)

    def angle_between_vectors(self, v: 'Vector') -> float:
        """ Angle between two vectors """
        return math.acos(self.dot_product(v) / self.magnitude() / v.magnitude())


class Plane:
    def __init__(self, points: [Vector]) -> None:
        if len(points) != 3 or duplicate_points(points):
            raise PlanePointsError('Need exactly three distinct points to make a plane.')
        self.normal_vector = self.new_normal_vector(points)
        # self.point = self.new_point(points[0])

    def new_normal_vector(self, points: [Point3, Point3, Point3]) -> Vector:
        """ Calculates the plane's perpendicular, or normal, vector """
        p1 = points[0]
        p2 = points[1]
        p3 = points[2]

        v1 = Vector(p1.x, p1.y, p1.z)
        v2 = Vector(p2.x, p2.y, p2.z)
        v3 = Vector(p3.x, p3.y, p3.z)

        return v1.minus(v2).cross_product(v3.minus(v2)).unit_vector()

    def new_point(self, point):
        p = Vector(point.x, point.y, point.z)
        n = self.normal_vector

        if n == Vector(0, 0, 0):
            raise ZeroVectorError()
        return n.times(p.dot_product(n) / n.dot_product(n))

    def intersect_plane(self, plane: 'Plane'):
        n1 = self.normal_vector
        n2 = plane.normal_vector
        p1 = self.point
        p2 = plane.point

        return n1.minus(n2), p1.dot_product(n1) - p2.dot_product(n2)


class Line:
    def __init__(self):
        pass


class Face:
    def __init__(self, corners: [Vector]) -> None:
        if len(corners) < 3 or duplicate_points(corners):
            raise PlanePointsError('Must have at least 3 distinct corners in a face.')
        self.corners = corners
        self.normal_vector = self.new_normal_vector()

    def new_normal_vector(self):
        p1 = self.corners[0]
        p2 = self.corners[1]
        p3 = self.corners[2]

        return Plane([p1, p2, p3]).normal_vector
