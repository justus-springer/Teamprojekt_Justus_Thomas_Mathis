import sys
from PyQt5.QtGui import QPainter, QVector2D, QColor
<<<<<<< HEAD
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QRectF, QPointF
=======
from PyQt5.QtCore import Qt, QObject, pyqtSignal
>>>>>>> run-away
import math
import random

import robotGame

# Epsilon values represent the smallest reasonable value greater than 0
# Any speed/distance below their epsilon value should be interpreted as practically 0
# Handle with caution
EPSILON_V = 20
EPSILON_V_ALPHA = 20
EPSILON_ALPHA = 10
EPSILON_POS = 10

A_MAX = 100
A_ALPHA_MAX = 360

class BaseRobot(QObject):

    # This will be emittet once at the beginning of the game to tell the controller the values a_max and a_alpha_max
    robotSpecsSignal = pyqtSignal(float, float)

    # This will be emittet every tick to tell the controller current values of x, y, alpha, v, v_alpha
    robotInfoSignal = pyqtSignal(float, float, float, float, float)

    def __init__(self, id, x, y, r = 30, alpha = 0, color = QColor(255,255,255)):

        super().__init__()

        self._id = id
        self.pos = QVector2D(x, y)
        self.r = r
        self.alpha = alpha # unit: degrees
        self.color = color

        self.a = 0 # unit: pixels/second^2
        self.a_max = A_MAX # unit: pixels/second^2
        self.v = 0 # unit: pixels/second
        self.v_max = 150 # unit pixels/second

        self.a_alpha = 0 # unit: degrees/second^2
        self.a_alpha_max = A_ALPHA_MAX # unit: degrees/second^2
        self.v_alpha = 0 # unit: degrees/second
        self.v_alpha_max = 360 # unit: degrees/second

    def draw(self, qp):
        qp.setBrush(self.color)
        qp.setPen(QColor(0,0,0))
        qp.drawEllipse(self.x() - self.r, self.y() - self.r, 2 * self.r, 2 * self.r)

        # End points of the line
        end_x = self.r * math.cos(math.radians(self.alpha))
        end_y = self.r * math.sin(math.radians(self.alpha))

        qp.drawLine(self.x(), self.y(), self.x() + end_x, self.y() + end_y)


    def update(self, deltaTime, obstacles, robotList):

        # Fetch acceleration values from your thread
        self.a, self.a_alpha = self.controller.fetchValues()
<<<<<<< HEAD

=======
        
>>>>>>> run-away
        # But not too much
        self.a = min(self.a, self.a_max)
        self.a = max(self.a, -self.a_max)
        self.a_alpha = min(self.a_alpha, self.a_alpha_max)
        self.a_alpha = max(self.a_alpha, -self.a_alpha_max)

        # Apply acceleration
        self.v += self.a * deltaTime
        self.v_alpha += self.a_alpha * deltaTime
        # But not too much
        self.v = min(self.v, self.v_max)
        self.v = max(self.v, -self.v_max)
        self.v_alpha = min(self.v_alpha, self.v_alpha_max)
        self.v_alpha = max(self.v_alpha, -self.v_alpha_max)

        self.collideWithWalls(obstacles)

        # Compute direction vector (normalized)
        direction = QVector2D(math.cos(math.radians(self.alpha)),
                              math.sin(math.radians(self.alpha)))

        # Apply velocity
        self.pos += self.v * deltaTime * direction
        self.alpha += self.v_alpha * deltaTime
        self.alpha %= 360

        # send current information to the controller
        self.robotInfoSignal.emit(self.x(), self.y(), self.alpha, self.v, self.v_alpha)

        self.collideWithRobots(robotList)

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
                if self.x() >= rect_center.x() and self.y() >= rect_center.y():
                    corner = rect.bottomRight()
                elif self.x() >= rect_center.x() and self.y() <= rect_center.y():
                    corner = rect.topRight()
                elif self.x() <= rect_center.x() and self.y() >= rect_center.y():
                    corner = rect.bottomLeft()
                elif self.x() <= rect_center.x() and self.y() <= rect_center.y():
                    corner = rect.topLeft()

                overlap = corner - point

                if math.fabs(overlap.x()) > math.fabs(overlap.y()):
                    self.translate(0, overlap.y())
                else:
                    self.translate(overlap.x(), 0)

                # Set speed to zero (almost)
                self.v = EPSILON_V



    def collideWithRobots(self, robotList):

        for robot in robotList:
            if robot != self:
                # distance to other robot
                distance = (self.pos - robot.get_pos()).length()
                direction = (self.pos - robot.get_pos()).normalized()

                if distance <= self.r + robot.get_r():
                    overlap = self.r + robot.get_r() - distance
                    self.pos += overlap / 2 * direction
                    robot.set_pos(robot.get_pos() - overlap / 2 * direction)


    def fullStop(self):
        """ This is a special operation to fully top the robot, i.e. set v to zero.
            It can only be called, if v is reasonably small, i.e. if |v| < EPSILON_V
            returns True if the operation was succesfull
        """

        print('full stop, robot: {0}'.format(self.id))
        if math.fabs(self.v) < EPSILON_V:
            self.v = 0
            return True
        else:
            return False

    def fullStopRotation(self):
        """ see above
        """
        if math.fabs(self.v_alpha) < EPSILON_V_ALPHA:
            self.v_alpha = 0
            return True
        else:
            return False

    def setController(self, controller):
        self._controller = controller

    def getController(self):
        return self._controller

    controller = property(getController, setController)

    def get_x(self):
        return self.pos.x

    def set_x(self, x):
        self.pos.setX(x)

    x = property(get_x, set_x)

    def get_y(self):
        return self.pos.y

<<<<<<< HEAD
    def set_y(self, y):
        self.pos.setY(y)

    y = property(get_y, set_y)

    def translate(self, x, y):
        self.pos.setX(self.pos.x() + x)
        self.pos.setY(self.pos.y() + y)

=======
>>>>>>> run-away
    @property
    def id(self):
        return self._id

    def get_r(self):
        return self.r

    def get_pos(self):
        return self.pos

    def set_pos(self, pos):
        self.pos = pos

    def get_v(self):
        return self.v

    def get_alpha(self):
        return self.alpha

    def get_v_alpha(self):
        return self.v_alpha

    def get_a_max(self):
        return self.a_max

    def get_a_alpha_max(self):
        return self.a_alpha_max
