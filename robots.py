import sys
from PyQt5.QtGui import QPainter, QVector2D, QColor
from PyQt5.QtCore import Qt, QThread
import math
import random

import robotGame

class BaseRobot:

    def __init__(self, x, y, r = 30, alpha = 0, color = QColor(255,255,255)):

        self.pos = QVector2D(x, y)
        self.target = QVector2D(x, y)
        self.r = r
        self.alpha = alpha # unit: degrees
        self.color = color

        self.a = 0 # unit: pixels/second^2
        self.a_max = 200 # unit: pixels/second^2
        self.v = 0 # unit: pixels/second
        self.v_max = 200

        self.a_alpha = 0 # unit: degrees/second^2
        self.a_alpha_max = 360 # unit: degrees/second^2
        self.v_alpha = 0 # unit: degrees/second
        self.v_alpha_max = 360

    def draw(self, qp):
        qp.setBrush(self.color)
        qp.setPen(QColor(0,0,0))
        qp.drawEllipse(self.x() - self.r, self.y() - self.r, 2 * self.r, 2 * self.r)

        # Endpunkte der Linie
        newx = self.r * math.cos(math.radians(self.alpha))
        newy = self.r * math.sin(math.radians(self.alpha))

        qp.drawLine(self.x(), self.y(), self.x() + newx, self.y() + newy)


    def update(self, deltaTime):

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
        #self.alpha %= 360

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
















#hey
