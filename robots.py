import sys
from PyQt5.QtGui import QPainter, QVector2D, QColor
from PyQt5.QtCore import Qt
import math

import robotGame

class BaseRobot:

    def __init__(self, x, y, r, alpha):

        self.pos = QVector2D(x, y)
        self.target = QVector2D(x, y)
        self.r = r

        self.v = 100 # unit: pixels/second
        self.v_alpha = 100 # unit: degrees/second
        self.a = 50 # unit: pixels/second^2
        self.a_max = 200 # unit: pixels/second^2
        self.alpha = alpha # unit: degrees
        self.a_alpha = 0 # unit: degrees/second^2
        self.a_alpha_max = 200 # unit: degrees/second^2

    def draw(self, qp):
        qp.setBrush(QColor(255,255,0))
        qp.setPen(QColor(0,0,0))
        qp.drawEllipse(self.x() - self.r, self.y() - self.r, 2 * self.r, 2 * self.r)

        # Endpunkte der Linie
        newx = self.r * math.cos(math.radians(self.alpha))
        newy = self.r * math.sin(math.radians(self.alpha))

        qp.drawLine(self.x(), self.y(), self.x() + newx, self.y() + newy)


    def update(self, deltaTime):

        # Apply acceleration
        self.v += self.a * deltaTime
        self.alpha += self.a_alpha * deltaTime

        # Compute direction vector (normalized)
        direction = QVector2D(math.cos(math.radians(self.alpha)),
                              math.sin(math.radians(self.alpha)))

        # Apply velocity
        self.pos += self.v * deltaTime * direction
        self.alpha += self.v_alpha * deltaTime

    @property
    def x(self):
        return self.pos.x

    @property
    def y(self):
        return self.pos.y
