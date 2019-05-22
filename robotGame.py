import sys
from PyQt5.QtWidgets import QWidget, QApplication, QLabel
from PyQt5.QtGui import QPainter, QColor, QPixmap, QVector2D
from PyQt5.QtCore import Qt, QBasicTimer, QPointF
import numpy as np
import math

from levelLoader import LevelLoader


#Window options

START_WINDOW_WIDTH = 1000
START_WINDOW_HEIGHT = 1000
START_WINDOW_X_POS = 100
START_WINDOW_Y_POS = 50
WINDOW_TITLE = "Cooles Spiel"

# Game constants

NUMBER_OF_TILES = 100
WALL_TILE_COLOR = QColor(0, 0, 0)
FLOOR_TILE_COLOR = QColor(255, 255, 255)
TILE_SIZE = 10

FPS = 30
MILLISECONDS_PER_SECOND = 1000
TICK_INTERVALL = int(MILLISECONDS_PER_SECOND / FPS)

class RobotGame(QWidget):

    def __init__(self):
        super().__init__()
        #initialize textures
        self.wallTexture = QPixmap('textures/wall.png')
        self.grassTexture = QPixmap('textures/grass.png')
        self.mudTexture = QPixmap('textures/mud.png')

        # Load level data from file
        self.levelMatrix = LevelLoader.loadLevel('level1.txt')
        self.initUI()

        # Initialize timer
        self.gameTimer = QBasicTimer()
        self.gameTimer.start(TICK_INTERVALL, self)

        # Initialize robot
        self.myRobot = BaseRobot(100, 100, 25, 45)


    def initUI(self):

        self.setGeometry(START_WINDOW_X_POS, START_WINDOW_Y_POS, START_WINDOW_WIDTH, START_WINDOW_HEIGHT)
        self.setWindowTitle(WINDOW_TITLE)
        self.show()

    def paintEvent(self, event):

        qp = QPainter()
        qp.begin(self)
        self.drawTiles(event, qp)
        self.myRobot.draw(qp)
        qp.end()

    def drawTiles(self, event, qp):

        qp.setPen(Qt.NoPen)
        for row in range(NUMBER_OF_TILES):
            for column in range(NUMBER_OF_TILES):
                if(self.levelMatrix[row][column] == LevelLoader.WALL_TILE):
                    texture = self.wallTexture
                elif(self.levelMatrix[row][column] == LevelLoader.FLOOR_TILE):
                    texture = self.grassTexture
                elif(self.levelMatrix[row][column] == LevelLoader.MUD_TILE):
                    texture = self.mudTexture

                qp.drawPixmap(column*TILE_SIZE,
                            row*TILE_SIZE,
                            texture)

    def timerEvent(self, event):

        if event.timerId() == self.gameTimer.timerId():
            self.myRobot.update()
            self.update()

    def mousePressEvent(self, event):
        self.myRobot.setTarget(event.x(), event.y())

class BaseRobot:

    # Speed in pixels per second
    SPEED = 200
    MOVEMENT_PER_TICK = TICK_INTERVALL * (SPEED / MILLISECONDS_PER_SECOND)

    def __init__(self, x, y, r, alpha):

        self.pos = QVector2D(x, y)
        self.target = QVector2D(x, y)
        self.r = r
        self.alpha = alpha

    def draw(self, qp):
        qp.setBrush(QColor(255,255,0))
        qp.setPen(QColor(0,0,0))
        qp.drawEllipse(self.x() - self.r, self.y() - self.r, 2 * self.r, 2 * self.r)

        # Endpunkte der Linie
        newx = self.r * math.cos(math.radians(self.alpha))
        newy = self.r * math.sin(math.radians(self.alpha))

        qp.drawLine(self.x(), self.y(), self.x() + newx, self.y() + newy)


    def update(self):

        # Compute distance to target
        delta = self.target - self.pos
        dist = delta.length()
        direction = delta.normalized()

        # Orient yourself toward the target
        self.setAlphaRadians(math.atan2(direction.y(), direction.x()))

        if dist > TILE_SIZE:
            # Move into that direction
            self.pos += self.MOVEMENT_PER_TICK * direction

    def setAlphaDegrees(self, alpha_degrees):
        self.alpha = alpha_degrees

    def setAlphaRadians(self, alpha_radians):
        self.alpha = math.degrees(alpha_radians)

    def setTarget(self, targetX, targetY):
        self.target.setX(targetX)
        self.target.setY(targetY)

    @property
    def x(self):
        return self.pos.x

    @property
    def y(self):
        return self.pos.y


if __name__ == '__main__':

    app = QApplication(sys.argv)

    game = RobotGame()

    sys.exit(app.exec_())
