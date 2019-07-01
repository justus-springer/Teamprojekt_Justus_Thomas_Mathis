from PyQt5.Qt import Qt
from PyQt5.QtGui import QVector2D

class Bar:
    def __init__(self, maxWidth, height, minValue, maxValue, color):
        self.maxWidth = maxWidth
        self.height = height
        self.minValue = minValue
        self.maxValue = maxValue
        self.color = color
        self.pos = QVector2D(0,0)

        self.currentWidth = 0
        self.currentValue = minValue

    def draw(self, qp):

        qp.setBrush(self.color)
        qp.setPen(Qt.black)
        qp.drawRect(self.pos.x() - self.maxWidth / 2, self.pos.y(), self.currentWidth, self.height)

    def update(self, new_value, new_pos):

        self.currentValue = new_value
        self.currentWidth = self.maxWidth * (self.currentValue / (self.maxValue - self.minValue))
        self.pos = new_pos

    def setColor(self, color):
        self.color = color

# Reload Display Options

RELOAD_BAR_MAX_WIDTH = 60
RELOAD_BAR_HEIGHT = 5
RELOAD_BAR_COLOR = Qt.blue
RELOAD_BAR_Y_BUFFER = 2

class ReloadBar(Bar):
    def __init__(self, timeToReload):
        super().__init__(RELOAD_BAR_MAX_WIDTH, RELOAD_BAR_HEIGHT, 0, timeToReload, RELOAD_BAR_COLOR)

    def update(self, new_value, new_pos):
        super().update(new_value, new_pos)
        self.pos = QVector2D(new_pos.x(), new_pos.y() + RELOAD_BAR_Y_BUFFER)


# Health Bar options

HEALTH_BAR_MAX_WIDTH = 60
HEALTH_BAR_MAX_HEIGHT = 5
HEALTH_BAR_COLOR = Qt.red

class HealthBar(Bar):
    def __init__(self, maxHealth):
        super().__init__(HEALTH_BAR_MAX_WIDTH, HEALTH_BAR_MAX_HEIGHT, 0, maxHealth, HEALTH_BAR_COLOR)
