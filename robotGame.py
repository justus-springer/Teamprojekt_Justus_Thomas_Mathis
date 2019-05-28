import sys
from PyQt5.QtWidgets import QWidget, QApplication, QLabel
from PyQt5.QtGui import QPainter, QColor, QPixmap, QVector2D
from PyQt5.QtCore import Qt, QBasicTimer, QPointF, QElapsedTimer
import numpy as np
import math

from levelLoader import LevelLoader
import robots


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

        # Initialize robots
        self.robots = []
        robot1 = robots.BaseRobot(500, 500, 30, 0, Qt.GlobalColor.cyan)
        robot1.setBehaviour(robots.BackAndForthBehaviour(robot1))
        self.robots.append(robot1)

        robot2 = robots.BaseRobot(300, 300, 30, 0, Qt.GlobalColor.magenta)
        robot2.setBehaviour(robots.CircleBehaviour(robot2))
        self.robots.append(robot2)

        robot3 = robots.BaseRobot(500, 500, 30, 0, Qt.GlobalColor.yellow)
        robot3.setBehaviour(robots.RandomBehaviour(robot3, 0.3))
        self.robots.append(robot3)

        robot4 = robots.BaseRobot(500, 700, 30, 0, Qt.GlobalColor.red)
        self.targetBehaviour = robots.TargetBehaviour(robot4)
        robot4.setBehaviour(self.targetBehaviour)
        self.robots.append(robot4)

        robot5 = robots.BaseRobot(50, 700, 30, 0, Qt.GlobalColor.green)
        robot5.setBehaviour(robots.CurveBehaviour(robot5))
        self.robots.append(robot5)

        # Start their behaviour threads
        for robot in self.robots:
            robot.startBehaviour()


        self.elapsedTimer = QElapsedTimer()
        self.elapsedTimer.start()
        self.previous = 0

    def initUI(self):

        self.setGeometry(START_WINDOW_X_POS, START_WINDOW_Y_POS, START_WINDOW_WIDTH, START_WINDOW_HEIGHT)
        self.setWindowTitle(WINDOW_TITLE)
        self.show()

    def paintEvent(self, event):

        qp = QPainter()
        qp.begin(self)
        self.drawTiles(event, qp)
        for robot in self.robots:
            robot.draw(qp)
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

        elapsed = self.elapsedTimer.elapsed()
        deltaTimeMillis = elapsed - self.previous
        deltaTime = deltaTimeMillis / MILLISECONDS_PER_SECOND

        if event.timerId() == self.gameTimer.timerId():
            for robot in self.robots:
                robot.update(deltaTime, self.robots)
            self.update()

        self.previous = elapsed

    def mousePressEvent(self, event):

        self.targetBehaviour.setNewTarget(event.x(), event.y())

        if not self.targetBehaviour.isRunning():
            self.targetBehaviour.start()


if __name__ == '__main__':

    app = QApplication(sys.argv)

    game = RobotGame()

    sys.exit(app.exec_())
