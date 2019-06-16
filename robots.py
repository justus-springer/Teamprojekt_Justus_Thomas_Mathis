import sys
from PyQt5.QtGui import QPainter, QVector2D, QColor, QPainterPath, QPolygonF, QBrush, QPen, QFont
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QRectF, QPointF
import math
import random

import robotGame, control
from toolbox import minmax

# Epsilon values represent the smallest reasonable value greater than 0
# Any speed/distance below their epsilon value should be interpreted as practically 0
# Handle with caution
EPSILON_V = 20
EPSILON_V_ALPHA = 20
EPSILON_ALPHA = 10
EPSILON_POS = 10

# Acceleration properties
A_MAX = 100
A_ALPHA_MAX = 360

# Collision properties
COLL_BUFFER = 10

# Drawing properties
ID_FONT = QFont("Calibri", 20)

class BaseRobot(QObject):

    # This will be emittet once at the beginning of the game to tell the controller the values a_max and a_alpha_max
    robotSpecsSignal = pyqtSignal(float, float, float, float)

    # This will be emittet every tick to tell the controller current values of x, y, alpha, v, v_alpha
    robotInfoSignal = pyqtSignal(float, float, float, float, float)

    # This will be emitted every 10th tick
    robotsInViewSignal = pyqtSignal(dict)
    wallsInViewSignal = pyqtSignal(list)

    def __init__(self, id, x, y, aov, v_max, r = 30, alpha = 0, color = QColor(255,255,255)):

        super().__init__()

        self.id = id
        self.pos = QVector2D(x, y)
        self.aov = aov
        self.r = r
        self.alpha = alpha # unit: degrees
        self.color = color

        self.a = 0 # unit: pixels/second^2
        self.a_max = A_MAX # unit: pixels/second^2
        self.v = 0 # unit: pixels/second
        self.v_max = v_max # unit pixels/second

        self.a_alpha = 0 # unit: degrees/second^2
        self.a_alpha_max = A_ALPHA_MAX # unit: degrees/second^2
        self.v_alpha = 0 # unit: degrees/second
        self.v_alpha_max = 360 # unit: degrees/second

    def draw(self, qp):

        qp.setBrush(self.color)
        qp.setPen(Qt.black)
        qp.drawEllipse(self.boundingRect())

        vec = self.r * self.direction()

        qp.drawLine(self.x, self.y, self.x + vec.x(), self.y + vec.y())

        # Draw your id
        qp.setPen(QPen(Qt.black))
        qp.setFont(ID_FONT)
        qp.drawText(self.boundingRect(), Qt.AlignCenter, str(self.id))

    def drawDebugLines(self, qp):
        qp.setBrush(QBrush(Qt.NoBrush))
        qp.setPen(Qt.red)
        qp.drawPath(self.view_cone())

    def update(self, deltaTime, obstacles, robotList):

        # Fetch acceleration values from your thread
        self.a, self.a_alpha = self.controller.fetchValues()
        # But not too much
        self.a = minmax(self.a, -self.a_max, self.a_max)
        self.a_alpha = minmax(self.a_alpha, -self.a_alpha_max, self.a_alpha_max)

        # Apply acceleration
        self.v += self.a * deltaTime
        self.v_alpha += self.a_alpha * deltaTime
        # But not too much
        self.v = minmax(self.v, -self.v_max, self.v_max)
        self.v_alpha = minmax(self.v_alpha, -self.v_alpha_max, self.v_alpha_max)

        self.collideWithWalls(obstacles)

        # Apply velocity
        self.pos += self.v * deltaTime * self.direction()
        self.alpha += self.v_alpha * deltaTime
        self.alpha %= 360

        # send current information to the controller
        self.robotInfoSignal.emit(self.x, self.y, self.alpha, self.v, self.v_alpha)

        self.collideWithRobots(robotList, obstacles)

    def collideWithWalls(self, obstacles):

        for rect in obstacles:

            rect_center = QVector2D(rect.center())
            vec = self.pos - rect_center
            length = vec.length()
            # scale the vector so it has length l-r
            vec *= (length-self.r) / length
            # This is the point of the robot which is closest to the rectangle
            point = (rect_center + vec).toPointF()

            if rect.contains(point):
                if self.x >= rect_center.x() and self.y >= rect_center.y():
                    corner = rect.bottomRight()
                elif self.x >= rect_center.x() and self.y <= rect_center.y():
                    corner = rect.topRight()
                elif self.x <= rect_center.x() and self.y >= rect_center.y():
                    corner = rect.bottomLeft()
                elif self.x <= rect_center.x() and self.y <= rect_center.y():
                    corner = rect.topLeft()

                overlap = corner - point

                if abs(overlap.x()) > abs(overlap.y()):
                    self.translate(0, overlap.y())
                else:
                    self.translate(overlap.x(), 0)

                # Set speed to zero (almost)
                self.v = EPSILON_V


    def collision(self, obstacles):

        for rect in obstacles:

            rect_center = QVector2D(rect.center())
            vec = self.pos - rect_center
            length = vec.length()
            vec *= (length-self.r) / length

            point = (rect_center + vec).toPointF()

            if rect.contains(point):
                return True

        return False

    def collideWithRobots(self, robotList, obstacles):

        for robot in robotList:
            if robot != self:
                # distance to other robot
                distance = (self.pos - robot.pos).length()
                direction = (self.pos - robot.pos).normalized()

                if distance <= self.r + robot.r:
                    overlap = self.r + robot.r - distance

                    if self.collision(obstacles):
                        robot.pos = robot.pos - overlap * direction

                    else:
                        self.pos += overlap / 2 * direction
                        robot.pos = robot.pos - overlap / 2 * direction


    def collisionRadar(self,levelMatrix):
        #Calculate Limits

        x_min = minmax(int((self.x - self.r - COLL_BUFFER) // 10), 0, len(levelMatrix))
        x_max = minmax(int((self.x + self.r + COLL_BUFFER + 1) // 10), 0, len(levelMatrix))
        y_min = minmax(int((self.y - self.r - COLL_BUFFER) // 10), 0, len(levelMatrix))
        y_max = minmax(int((self.y + self.r + COLL_BUFFER + 1) // 10), 0, len(levelMatrix))

        #Fill obstacle list
        obstacles =[]
        for y in range(y_min, y_max):
            for x in range(x_min, x_max):
                if levelMatrix[y][x] == 1:
                    obstacles.append(QRectF(x*10, y*10, 10, 10))

        return obstacles


    def fullStop(self):
        """ This is a special operation to fully top the robot, i.e. set v to zero.
            It can only be called, if v is reasonably small, i.e. if |v| < EPSILON_V
            returns True if the operation was succesfull
        """

        if abs(self.v) < EPSILON_V:
            self.v = 0
            return True
        else:
            return False

    def fullStopRotation(self):
        """ see above
        """
        if abs(self.v_alpha) < EPSILON_V_ALPHA:
            self.v_alpha = 0
            return True
        else:
            return False

    def direction(self):
        return QVector2D(math.cos(self.alpha_radians), math.sin(self.alpha_radians))

    def boundingRect(self):
        return QRectF(self.x - self.r, self.y - self.r, 2*self.r, 2*self.r)

    def shape(self):
        shape = QPainterPath()
        shape.addEllipse(self.boundingRect())
        return shape

    def view_cone(self):
        path = QPainterPath()
        a = self.pos.toPointF()
        b = a + QPointF(5000 * math.cos(math.radians(self.alpha + self.aov)),
                    5000 * math.sin(math.radians(self.alpha + self.aov)))
        c = a + QPointF(5000 * math.cos(math.radians(self.alpha - self.aov)),
                    5000 * math.sin(math.radians(self.alpha - self.aov)))
        path.addPolygon(QPolygonF([a, b, c]))
        path.closeSubpath()
        return path

    def translate(self, x, y):
        self.pos += QVector2D(x, y)

    ### properties

    def get_alpha_radians(self):
        return math.radians(self.alpha)

    def set_alpha_radians(self, new_alpha):
        self.alpha = math.degrees(new_alpha)

    alpha_radians = property(get_alpha_radians, set_alpha_radians)

    def setController(self, controller):
        self._controller = controller

    def getController(self):
        return self._controller

    controller = property(getController, setController)

    def get_x(self):
        return self.pos.x()

    def set_x(self, new_x):
        self.pos.setX(new_x)

    x = property(get_x, set_x)

    def get_y(self):
        return self.pos.y()

    def set_y(self, new_y):
        self.pos.setY(new_y)

    y = property(get_y, set_y)

class ChaserRobot(BaseRobot):

    scoreSignal = pyqtSignal(int)

    def __init__(self, id, spawn_x, spawn_y, targetId, controllerClass):
        super().__init__(id, spawn_x, spawn_y, 30, 150, 30, 0, Qt.gray)
        self.spawn_x = spawn_x
        self.spawn_y = spawn_y

        self.controller = controllerClass(id, targetId)

    def collideWithRobots(self, robotList, obstacles):

        for robot in robotList:
            if robot != self:
                # distance to other robot
                distance = (self.pos - robot.pos).length()
                direction = (self.pos - robot.pos).normalized()

                if distance <= self.r + robot.r:
                    overlap = self.r + robot.r - distance

                    if self.collision(obstacles):
                        robot.pos = robot.pos - overlap * direction

                    else:
                        self.pos += overlap / 2 * direction
                        robot.pos = robot.pos - overlap / 2 * direction

                    # if the other robot was a runner, teleport to your spawn
                    if isinstance(robot, RunnerRobot):
                        self.teleportToFarthestPoint(robot.pos)
                        self.scoreSignal.emit(self.id)

    def drawDebugLines(self, qp):
        super().drawDebugLines(qp)
        qp.setBrush(QBrush(Qt.blue))
        qp.setPen(Qt.blue)
        p = self.controller.aimPos.toPointF()
        qp.drawEllipse(p, 5, 5)

    def teleportToFarthestPoint(self, robot_pos):
        middle = QVector2D(robotGame.WINDOW_SIZE / 2, robotGame.WINDOW_SIZE / 2)
        vec = middle - robot_pos
        vec *= 400 / vec.length()
        self.pos = middle + vec

class RunnerRobot(BaseRobot):

    def __init__(self, id, x, y, chaserIds):
        super().__init__(id, x, y, 50, 100, 25, 0, Qt.green)
        self.controller = control.RunController(id, chaserIds)

class TestRobot(BaseRobot):

    def __init__(self, id, x, y):
        super().__init__(id, x, y, 30, 200, 30, 0, Qt.red)
        self.controller = control.TargetController(id)
