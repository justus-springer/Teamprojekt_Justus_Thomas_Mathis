import sys, math
from PyQt5.QtWidgets import QWidget, QApplication, QLabel
from PyQt5.QtGui import QPainter, QColor, QPixmap, QVector2D, QBrush, QFont
from PyQt5.QtCore import Qt, QBasicTimer, QPointF, QElapsedTimer, pyqtSignal, QRectF, QDateTime, QObject

import arsenal

class Bar:
    def __init__(self, width, height, color, pos):
        self.width = width
        self.height = height
        self.color = color
        self.pos = pos

    def drawBar(self, qp):

        qp.setBrush(self.color)
        qp.setPen(Qt.black)
        qp.drawRect(self.pos.x(), self.pos.y(), self.width, self.height)

    def update(self, new_width, new_height, new_color, new_pos):

        self.width = new_width
        self.height = new_height
        self.color = new_color
        self.pos = new_pos

# Reload Display Options

HEIGHT = 5
COLOR = Qt.blue
Y_BUFFER = 2

class ReloadDisplay(Bar):
    def __init__(self, pos):
        self.pos = pos
        self.width = 0
        self.height = HEIGHT
        self.color = COLOR

    def update(self, new_width, new_pos):
        self.width = new_width
        self.pos = QVector2D(new_pos.x(), new_pos.y() + Y_BUFFER)










