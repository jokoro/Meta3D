import pygame
import math
import collections
import object3d
import geometry
import algebra

SubFace = collections.namedtuple('SubFace', ['face', 'o', 'p'])
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 700

SIDE = 200
SCREEN_DIST = SIDE / math.sqrt(2) + 1
EYE_DIST = SCREEN_DIST + 2 * SIDE  # the bigger it is, the closer to no perspective, best around SCREEN_DIST + SIDE
DOT_SIZE = 5

PI = math.pi

BLACK = 0, 0, 0
WHITE = 255, 255, 255
RED = 255, 0, 0
GREEN = 0, 255, 0
BLUE = 0, 0, 255
YELLOW = 255, 255, 0
MAGENTA = 255, 0, 255
CYAN = 0, 255, 255
ORANGE = 255, 122, 0
BACKGROUND_COLOR = ORANGE

IS_ORTHOGONAL = False
MIN_DISTANCE = -50
CHANGE_DIST = 50

COLORING = True
SHADING = False

ROTATE_STEP = PI / 16
LIGHT_VECTOR = geometry.Vector(0, 0, 1)

DIVISOR = 20
BOUND = 500
RADIUS = 200
SCALE = 100
EQUATION = \
    algebra.Equation(f'x^2+z^2={SCALE}*y')

# algebra.Equation(f'x^2-y^2+z^2={SCALE}')
# [f'math.sqrt({SCALE} - x ** 2 + y ** 2)',
# f'-math.sqrt({SCALE} - x ** 2 + y ** 2)']
# SCALE > 0:                                      1 sheet hyperboloid (finger trap)
# SCALE = 0:                                      cone(s)
# SCALE < 0:                                      2 sheet hyperboloid (2 bowls)
# scale and/or divisor need to be big for this one
#
# algebra.Equation(f'x^2-y^2={SCALE}*z')
# [f'math.sqrt(x ** 2 + {SCALE}*y)',
# f'-math.sqrt(x ** 2 + {SCALE}*y)']
#                                                  hyperbolic paraboloid (saddle)
#
# this way it maps points that wouldn't
# otherwise be on graph onto the graph
# (make it bigger than bound)
#
# algebra.Equation(f'x^2+z^2={SCALE}*y')
# [f'math.sqrt({SCALE}*y - x ** 2)',
# f'-math.sqrt({SCALE}*y - x ** 2)']
#                                                   elliptic paraboloid (bowl)
#
# algebra.Equation(f'x^2+y^2+z^2={SCALE}')
# [f'math.sqrt({RADIUS} ** 2 - x ** 2 - y ** 2)',
# f'-math.sqrt({RADIUS} ** 2 - x ** 2 - y ** 2)']
#                                                   sphere/ellipsoid (potato)
BOUNDARY = object3d.Boundary([algebra.Equation(f'x={-BOUND}'), algebra.Equation(f'x={BOUND}'),
                              algebra.Equation(f'y={-BOUND}'), algebra.Equation(f'y={BOUND}'),
                              algebra.Equation(f'z={-BOUND}'), algebra.Equation(f'z={BOUND}')])
FRAME_RATE = 30


class Simulation3D:
    def __init__(self):
        self._running = True
        self._object = object3d.Object3D([object3d.Part(EQUATION, BOUNDARY)], DIVISOR)
        self._clock = pygame.time.Clock()
        self._angle = 0
        self._this_rel = (0, 0)
        self._since_last_rel = (0, 0)
        self._screen_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
        self._center = geometry.Vector(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, 0)
        self._trans_surface = None

    def run(self):
        pygame.init()

        self._this_rel = pygame.mouse.get_rel()
        self._resize_surface()
        self._running = True

        while self._running:
            self._clock.tick(FRAME_RATE)
            self._handle_events()
            self._handle_mouse_clicks()
            self._handle_keys()
            self._redraw()
        pygame.quit()

    def _resize_surface(self) -> None:
        pygame.display.set_mode(self._screen_size, pygame.RESIZABLE)
        self._center = geometry.Vector(self._screen_size[0] / 2, self._screen_size[1] / 2, 0)

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._end_simulation()

            elif event.type == pygame.VIDEORESIZE:
                self._screen_size = event.size
                self._resize_surface()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    self._object.rotate(0, 0, -PI / 2)
                elif event.key == pygame.K_d:
                    self._object.rotate(0, 0, PI / 2)
                elif event.key == pygame.K_w:
                    self._object.rotate(0, -PI / 2, 0)
                elif event.key == pygame.K_s:
                    self._object.rotate(0, PI / 2, 0)

    def _handle_keys(self):
        if pygame.key.get_pressed()[pygame.K_LEFT]:
            self._object.rotate(0, 0, ROTATE_STEP)

        if pygame.key.get_pressed()[pygame.K_RIGHT]:
            self._object.rotate(0, 0, -ROTATE_STEP)

        if pygame.key.get_pressed()[pygame.K_UP]:
            self._object.rotate(0, ROTATE_STEP, 0)

        if pygame.key.get_pressed()[pygame.K_DOWN]:
            self._object.rotate(0, -ROTATE_STEP, 0)

        if pygame.key.get_pressed()[pygame.K_l]:
            self._object.rotate(-ROTATE_STEP, 0, 0)

        if pygame.key.get_pressed()[pygame.K_j]:
            self._object.rotate(ROTATE_STEP, 0, 0)

        if pygame.key.get_pressed()[pygame.K_n]:
            pass
        if pygame.key.get_pressed()[pygame.K_m]:
            pass
        self._handle_events()

    def _handle_mouse_clicks(self):
        if pygame.mouse.get_pressed()[0]:
            mouse_pos = pygame.mouse.get_pos()
            mx, my = mouse_pos[0], mouse_pos[1]
            x, y = self._center.x, self._center.y
            max_length = BOUND

            # move from where mouse was 1/FRAME_RATE ago to where it is now
            pygame.mouse.get_rel()
            self._clock.tick(FRAME_RATE)
            self._handle_events()
            self._this_rel = pygame.mouse.get_rel()

            scale = -ROTATE_STEP / 2  # - math.sqrt(2) * PI / 2 # / BOUND / 2  # relatively arbitrary
            mouse_angle = math.atan2(my - y, mx - x)

            cos_pos = math.cos(mouse_angle)
            sin_pos = math.sin(mouse_angle)

            if x - max_length < mx < x + max_length and y - max_length < my < y + max_length:
                theta_yz = self._this_rel[1] * scale
                theta_xz = self._this_rel[0] * scale
                self._object.rotate(0, theta_yz, theta_xz)
            else:
                theta_xy = (self._this_rel[0] * sin_pos + self._this_rel[1] * cos_pos) * scale / 2
                self._object.rotate(theta_xy, 0, 0)

            self._handle_events()

    def _redraw(self):
        surface = pygame.display.get_surface()
        surface.fill(BACKGROUND_COLOR)
        self._trans_surface = pygame.Surface(self._screen_size, pygame.SRCALPHA)

        self._draw_object()

        surface.blit(self._trans_surface, (0, 0))
        pygame.display.flip()

    def get_face_points(self, face):
        corners = []
        for corner in face.corners:
            corner1 = corner.plus(self._center)
            corner2 = self._center.minus(corner)
            corners += [(corner1.x, corner2.y)]
        return corners

    def _draw_object(self):
        surface = pygame.display.get_surface()
        for face in self._object.faces:
            if COLORING:
                pygame.draw.polygon(surface, BLUE, self.get_face_points(face))
                pygame.draw.lines(surface, BLACK, True, self.get_face_points(face))
            if SHADING:
                # alpha = center_to_sub_face.angle_between_vectors(LIGHT_VECTOR) * 255 / math.pi
                pygame.draw.polygon(surface, BLUE, self.get_face_points(face))

    def _end_simulation(self):
        self._running = False


if __name__ == '__main__':
    Simulation3D().run()
