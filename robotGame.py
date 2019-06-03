import sys
from PyQt5.QtWidgets import QWidget, QApplication, QLabel
from PyQt5.QtGui import QPainter, QColor, QPixmap, QVector2D
from PyQt5.QtCore import Qt, QBasicTimer, QPointF, QElapsedTimer, pyqtSignal
import numpy as np
import math

from levelLoader import LevelLoader
import robots
import control


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

    setTargetSignal = pyqtSignal(float, float)

    positionsDataSignal = pyqtSignal(dict)

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
        robot1 = robots.BaseRobot(1, 100, 100, 30, 0, Qt.GlobalColor.yellow)
        robot2 = robots.BaseRobot(2, 300, 300, 30, 0, Qt.GlobalColor.cyan)
        robot3 = robots.BaseRobot(3, 200, 200, 30, 0, Qt.GlobalColor.red)
        robot4 = robots.BaseRobot(4, 600, 600, 30, 0, Qt.GlobalColor.green)


        self.robots = [robot1, robot2, robot3, robot4]

        # Initialize controllers
        randomController = control.RandomController(1, 0.5)
        followController = control.FollowController(2, 4)
        targetController = control.TargetController(3)
        runController = control.runController(4, 2)
        self.setTargetSignal.connect(targetController.setTarget)

        robot1.controller = randomController
        robot2.controller = followController
        robot3.controller = targetController
        robot4.controller = runController

        for robot in self.robots:
            # Start the controller threads
            robot.controller.start()
            
            # connect signals (hook up the controller to the robot)
            robot.robotSpecsSignal.connect(robot.controller.receiveRobotSpecs)
            robot.robotInfoSignal.connect(robot.controller.receiveRobotInfo)
            robot.controller.fullStopSignal.connect(robot.fullStop)
            robot.controller.fullStopRotationSignal.connect(robot.fullStopRotation)
            self.positionsDataSignal.connect(robot.controller.receiveRobotPositions)

            # Tell the controller the specs of the robot (a_max and a_alpha_max)
            robot.robotSpecsSignal.emit(robot.get_a_max(), robot.get_a_alpha_max())

        # For deltaTime
        self.elapsedTimer = QElapsedTimer()
        self.elapsedTimer.start()
        self.previous = 0

        self.tickCounter = 0

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

        self.tickCounter += 1

        elapsed = self.elapsedTimer.elapsed()
        deltaTimeMillis = elapsed - self.previous
        deltaTime = deltaTimeMillis / MILLISECONDS_PER_SECOND

        # Update robots
        for robot in self.robots:
            robot.update(deltaTime, self.robots)

        # send positions data every 10th tick
        if self.tickCounter % 10 == 0:
            positionsData = {}
            for robot in self.robots:
                positionsData[robot.id] = {'x' : robot.x(), 'y' : robot.y()}
            self.positionsDataSignal.emit(positionsData)

        # Update visuals
        self.update()

        self.previous = elapsed

    def mousePressEvent(self, event):

        self.setTargetSignal.emit(event.x(), event.y())


if __name__ == '__main__':

    app = QApplication(sys.argv)

    game = RobotGame()

    sys.exit(app.exec_())
