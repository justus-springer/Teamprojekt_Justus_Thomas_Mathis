import sys
from PyQt5.QtWidgets import QWidget, QApplication, QLabel
from PyQt5.QtGui import QPainter, QColor, QPixmap, QVector2D, QBrush
from PyQt5.QtCore import Qt, QBasicTimer, QPointF, QElapsedTimer, pyqtSignal, QRectF
import numpy as np
import math

from levelLoader import LevelLoader
import robots
import control

DEBUG_LINES = True

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

    def __init__(self):
        super().__init__()
        #initialize textures
        self.wallTexture = QPixmap('textures/wall.png')
        self.grassTexture = QPixmap('textures/grass.png')
        self.sandTexture = QPixmap('textures/sand.png')

        # Load level data from file
        self.levelMatrix, self.obstacles = LevelLoader.loadLevel('level1.txt')
        self.initUI()

        # Initialize timer
        self.gameTimer = QBasicTimer()
        self.gameTimer.start(TICK_INTERVALL, self)

        # Initialize robots

        robot1 = robots.BaseRobot(1, 900, 900, 30, 30, 0, Qt.GlobalColor.cyan)
        robot2 = robots.BaseRobot(2, 500, 500, 30, 30, 0, Qt.GlobalColor.red)
        robot3 = robots.BaseRobot(3, 700, 700, 30, 30, 0, Qt.GlobalColor.yellow)

        self.robots = {1 : robot1, 2 : robot2, 3 : robot3}

        # Initialize controllers
        followController = control.FollowController(1, 2)
        targetController = control.TargetController(2)
        runController = control.runController(3, 2)

        robot1.controller = followController
        robot2.controller = targetController
        robot3.controller = runController
        self.setTargetSignal.connect(targetController.setTarget)

        for robot in self.robots.values():

            # connect signals (hook up the controller to the robot)
            robot.robotSpecsSignal.connect(robot.controller.receiveRobotSpecs)
            robot.robotInfoSignal.connect(robot.controller.receiveRobotInfo)
            robot.controller.fullStopSignal.connect(robot.fullStop)
            robot.controller.fullStopRotationSignal.connect(robot.fullStopRotation)
            robot.robotsInViewSignal.connect(robot.controller.receiveRobotsInView)
            robot.wallsInViewSignal.connect(robot.controller.receiveWallsInView)

            # Tell the controller the specs of the robot (a_max and a_alpha_max)
            robot.robotSpecsSignal.emit(robot.a_max, robot.a_alpha_max)

            # Start the controller threads
            robot.controller.start()

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
        for robot in self.robots.values():
            robot.draw(qp)

        if DEBUG_LINES:
            self.drawObstaclesDebugLines(qp)
            for robot in self.robots.values():
                robot.drawDebugLines(qp)

        qp.end()

    def drawTiles(self, event, qp):

        qp.setPen(Qt.NoPen)
        for row in range(NUMBER_OF_TILES):
            for column in range(NUMBER_OF_TILES):
                if(self.levelMatrix[row][column] == LevelLoader.WALL_TILE):
                    texture = self.wallTexture
                elif(self.levelMatrix[row][column] == LevelLoader.FLOOR_TILE):
                    texture = self.grassTexture
                elif(self.levelMatrix[row][column] == LevelLoader.SAND_TILE):
                    texture = self.sandTexture

                qp.drawPixmap(column*TILE_SIZE, row*TILE_SIZE, texture)

    def drawObstaclesDebugLines(self, qp):
        qp.setPen(Qt.blue)
        qp.setBrush(QBrush(Qt.NoBrush))
        for rect in self.obstacles:
            qp.drawRect(rect)

    def timerEvent(self, event):

        self.tickCounter += 1

        elapsed = self.elapsedTimer.elapsed()
        deltaTimeMillis = elapsed - self.previous
        deltaTime = deltaTimeMillis / MILLISECONDS_PER_SECOND

        # Update robots
        for robot in self.robots.values():
            robot.update(deltaTime, robot.collisionRadar(self.levelMatrix), self.robots.values())

        # send positions data every 10th tick
        if self.tickCounter % 10 == 0:
            allRobotInfos = {}
            for other in self.robots.values():
                allRobotInfos[other.id] = {'x' : other.x, 'y' : other.y}

            for robot in self.robots.values():
                cone = robot.view_cone_path()
                robotsInView = {id : info for id,info in allRobotInfos.items()
                                          if self.robots[id].shape().intersects(cone)}

                robot.robotsInViewSignal.emit(robotsInView)


        # Update visuals
        self.update()

        self.previous = elapsed

    def mouseMoveEvent(self, event):

        self.setTargetSignal.emit(event.x(), event.y())


if __name__ == '__main__':

    app = QApplication(sys.argv)

    game = RobotGame()

    sys.exit(app.exec_())
