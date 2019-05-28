import sys
from PyQt5.QtGui import QPainter, QVector2D, QColor
from PyQt5.QtCore import Qt, QThread
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

class BaseRobot:

    def __init__(self, x, y, r = 30, alpha = 0, color = QColor(255,255,255)):

        self.pos = QVector2D(x, y)
        self.target = QVector2D(x, y)
        self.r = r
        self.alpha = alpha # unit: degrees
        self.color = color

        self.a = 0 # unit: pixels/second^2
        self.a_max = 100 # unit: pixels/second^2
        self.v = 0 # unit: pixels/second
        self.v_max = 150 # unit pixels/second

        self.a_alpha = 0 # unit: degrees/second^2
        self.a_alpha_max = 360 # unit: degrees/second^2
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


    def update(self, deltaTime, robotList):

        # Fetch acceleration values from your thread
        self.a, self.a_alpha = self.behaviour.fetchValues()
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

        # Compute direction vector (normalized)
        direction = QVector2D(math.cos(math.radians(self.alpha)),
                              math.sin(math.radians(self.alpha)))

        # Apply velocity
        self.pos += self.v * deltaTime * direction
        self.alpha += self.v_alpha * deltaTime

        self.collideWithRobots(robotList)

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


    def setBehaviour(self, behaviour):
        self.behaviour = behaviour

    def startBehaviour(self):
        self.behaviour.start()

    @property
    def x(self):
        return self.pos.x

    @property
    def y(self):
        return self.pos.y

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



class Behaviour(QThread):

    def __init__(self, robot):
        super().__init__()
        self.robot = robot

        # These will be fetched by the main program
        self.a = 0
        self.a_alpha = 0

        self.a_max = self.robot.get_a_max()
        self.a_alpha_max = self.robot.get_a_alpha_max()

    def fetchValues(self):
        return self.a, self.a_alpha


class BackAndForthBehaviour(Behaviour):

    def run(self):

        self.a = self.a_max

        while True:
            if self.robot.x() >= 700:
                self.a = -self.a_max
            elif self.robot.x() <= 300:
                self.a = self.a_max

            self.msleep(100)


class CircleBehaviour(Behaviour):

    def run(self):

        self.a = self.a_max
        self.a_alpha = self.a_alpha_max
        self.msleep(500)
        self.a_alpha = 0


class CurveBehaviour(Behaviour):

    def run(self):

        self.a = self.a_max
        self.msleep(700)
        self.a = 0

        while True:
            if self.robot.get_alpha() >= 0:
                self.a_alpha = -self.a_alpha_max/8

            elif self.robot.get_alpha() <= -10:
                self.a_alpha = self.a_alpha_max/8


class RandomBehaviour(Behaviour):

    def __init__(self, robot, volatility):
        super().__init__(robot)
        self.volatility = volatility

    def run(self):

        while True:
            # sleep random amount of time
            self.msleep(random.randrange(500, 1000))
            # set acceleration randomly
            self.a = random.uniform(-self.volatility * self.a_max, self.volatility * self.a_max)
            self.a_alpha = random.uniform(-self.volatility * self.a_alpha_max, self.volatility * self.a_alpha_max)

class TargetBehaviour(Behaviour):

    def __init__(self, robot):
        super().__init__(robot)
        self.target_x = robot.x()
        self.target_y = robot.y()

    def setNewTarget(self, target_x, target_y):
        self.target_x = target_x
        self.target_y = target_y

    def run(self):

        while True:

            # Get current values
            crnt_x = self.robot.x()
            crnt_y = self.robot.y()
            crnt_v = self.robot.get_v()
            delta_x = self.target_x - crnt_x
            delta_y = self.target_y - crnt_y
            delta_dist = math.sqrt(delta_x*delta_x + delta_y*delta_y)
            target_alpha = math.degrees(math.atan2(delta_y, delta_x))

            crnt_v_alpha = self.robot.get_v_alpha()
            crnt_alpha = self.robot.get_alpha()
            delta_alpha = math.fabs(target_alpha - crnt_alpha)

            # Target is reached
            if (delta_alpha < EPSILON_POS and
                math.fabs(crnt_v) < EPSILON_V):

                break

            # This is the remaining distance travelled if the robot starts braking now
            # EPSILON_POS is added as a buffer so he doesn't overshoot
            threshold_dist = crnt_v*crnt_v / (2 * self.a_max) + EPSILON_POS

            if delta_dist <= threshold_dist:
                self.brake()
            else:
                self.accel()

            threshold_alpha = crnt_v_alpha*crnt_v_alpha / (2 * self.a_alpha_max)

            if delta_alpha <= threshold_alpha:
                self.brake_alpha()
            else:
                self.accel_alpha(target_alpha)

            self.msleep(50)


        self.a_alpha = 0
        self.a = 0
        self.robot.fullStopRotation()
        self.robot.fullStop()


    def brake_alpha(self):
        crnt_v_alpha = self.robot.get_v_alpha()
        if crnt_v_alpha > EPSILON_V_ALPHA:
            self.a_alpha = -self.a_alpha_max
        elif crnt_v_alpha < EPSILON_V_ALPHA:
            self.a_alpha = self.a_alpha_max
        else:
            self.a_alpha = 0

    def accel_alpha(self, target_alpha):
        if target_alpha > self.robot.get_alpha():
            self.a_alpha = self.a_alpha_max
        else:
            self.a_alpha = -self.a_alpha_max

    def brake(self):
        crnt_v = self.robot.get_v()
        if crnt_v > EPSILON_V:
            self.a = -self.a_max
        elif crnt_v < EPSILON_V:
            self.a = self.a_max
        else:
            self.a = 0

    def accel(self):
        self.a = self.a_max
