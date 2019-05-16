from PyQt5.QtWidgets import QWidget, QApplication, QLabel
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtCore import Qt, QBasicTimer

class BaseRobot:

    # Speed in pixels per second
    SPEED = 50

    def __init__(self, x, y, r, alpha):

        self.x = x
        self.y = y
        self.r = r
        self.alpha = alpha

    def draw(self, qp):
        qp.setBrush(QColor(50,50,50))
        qp.drawRect(self.x - self.r, self.y - self.r, 2 * self.r, 2 * self.r)

    def update(self):
        self.x += 5
