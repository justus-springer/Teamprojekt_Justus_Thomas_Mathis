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










