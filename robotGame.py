import sys
from PyQt5.QtWidgets import QWidget, QApplication, QLabel
from PyQt5.QtGui import QPainter, QColor, QPixmap, QVector2D, QBrush
from PyQt5.QtCore import Qt, QBasicTimer, QPointF, QElapsedTimer, pyqtSignal, QRectF, QDateTime
import numpy as np
import math

from levelLoader import LevelLoader
import robots
import control

DEBUG_LINES = False

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

        self.initRobots()

        # For deltaTime
        self.elapsedTimer = QElapsedTimer()
        self.elapsedTimer.start()
        self.previous = 0

        self.tickCounter = 0

    def initUI(self):

        self.setGeometry(START_WINDOW_X_POS, START_WINDOW_Y_POS, START_WINDOW_WIDTH, START_WINDOW_HEIGHT)
        self.setWindowTitle(WINDOW_TITLE)
        self.show()

    def initRobots(self):

        chaser1 = robots.BaseRobot(1, 200, 500, 30, 30, 0, Qt.gray)
        chaser2 = robots.BaseRobot(2, 500, 200, 30, 30, 0, Qt.gray)
        chaser3 = robots.BaseRobot(3, 800, 500, 30, 30, 0, Qt.gray)
        runningRobot = robots.BaseRobot(4, 500, 500, 30, 20, 0, Qt.green)

        testRobot = robots.BaseRobot(5, 500, 800, 80, 30, 0, Qt.red)

        self.robots = {1 : chaser1, 2 : chaser2, 3 : chaser3, 4 : runningRobot, 5 : testRobot}

        # Initialize controllers
        chaser1.controller = control.FollowController(1, 4)
        chaser2.controller = control.FollowController(2, 4)
        chaser3.controller = control.FollowController(3, 4)
        runningRobot.controller = control.RunController(4, 2)
        testRobot.controller = control.TargetController(5)

        self.setTargetSignal.connect(testRobot.controller.setTarget)

        for robot in self.robots.values():

            # connect signals (hook up the controller to the robot)
            robot.robotSpecsSignal.connect(robot.controller.receiveRobotSpecs)
            robot.robotInfoSignal.connect(robot.controller.receiveRobotInfo)
            robot.controller.fullStopSignal.connect(robot.fullStop)
            robot.controller.fullStopRotationSignal.connect(robot.fullStopRotation)
            robot.robotsInViewSignal.connect(robot.controller.receiveRobotsInView)
            robot.wallsInViewSignal.connect(robot.controller.receiveWallsInView)

            # Tell the controller the specs of the robot (a_max and a_alpha_max)
            robot.robotSpecsSignal.emit(robot.a_max, robot.a_alpha_max, robot.v_max, robot.v_alpha_max)

            # Start the controller threads
            robot.controller.start()

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
            for robot in self.robots.values():
                self.emitRobotSensorData(robot)


        # Update visuals
        self.update()

        self.previous = elapsed


    def emitRobotSensorData(self, robot):
        cone = robot.view_cone_path()
        robotsInView = {}
        wallsInView = {}
        timestamp = QDateTime.currentMSecsSinceEpoch()
        # ids of all robots that are in view
        ids = [id for id in self.robots.keys() if self.robots[id].shape().intersects(cone)]

        for id in ids:
            other = self.robots[id]
            dist = (robot.pos - other.pos).length()
            angle = math.degrees(math.atan2(other.y - robot.y, other.x - robot.x))
            robotsInView[id] = {'x' : other.x, 'y' : other.y, 'dist' : dist, 'angle' : angle, 'timestamp' : timestamp}

        robot.robotsInViewSignal.emit(robotsInView)

        walls = [rect for rect in self.obstacles if cone.intersects(rect)]

        robot.wallsInViewSignal.emit(walls)


    def mouseMoveEvent(self, event):

        self.setTargetSignal.emit(event.x(), event.y())


if __name__ == '__main__':

    app = QApplication(sys.argv)

    game = RobotGame()

    sys.exit(app.exec_())
