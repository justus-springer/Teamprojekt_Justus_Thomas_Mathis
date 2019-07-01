import sys, math
from PyQt5.QtWidgets import QWidget, QApplication, QLabel
from PyQt5.QtGui import QPainter, QColor, QPixmap, QVector2D, QBrush, QFont
from PyQt5.QtCore import Qt, QBasicTimer, QPointF, QElapsedTimer, pyqtSignal, QRectF, QDateTime, QObject

from levelLoader import LevelLoader, Tile
import robots
import control
from arsenal import Handgun, Shotgun, GrenadeLauncher

DEBUG_LINES = False

#Window options

WINDOW_SIZE = 1000
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
    keyPressedSignal = pyqtSignal(int)

    def __init__(self):
        super().__init__()

        # Load level data from file
        self.levelMatrix, self.obstacles = LevelLoader.loadLevel('level1.txt')

        self.initUI()
        self.initTextures()
        self.initTimer()
        self.initRobots()

    def initTextures(self):

        self.tileTextures = {tileEnum : QPixmap('textures/' + tileName + '.png') for tileName, tileEnum in Tile.__members__.items()}

    def initUI(self):

        self.setGeometry(START_WINDOW_X_POS, START_WINDOW_Y_POS, WINDOW_SIZE, WINDOW_SIZE)
        self.setWindowTitle(WINDOW_TITLE)
        self.show()

    def initTimer(self):

        self.gameTimer = QBasicTimer()
        self.gameTimer.start(TICK_INTERVALL, self)

        # For deltaTime
        self.elapsedTimer = QElapsedTimer()
        self.elapsedTimer.start()
        self.previous = 0
        self.tickCounter = 0

    def initRobots(self):

        self.robots = {}
        id = 1

        testRobot = robots.TestRobot(id, 500, 500)
        self.robots[id] = testRobot
        id += 1
        handgun = Handgun(testRobot, 500, 0.5, 60)
        shotgun = Shotgun(testRobot, 200, 1, 10, 20)
        grenade = GrenadeLauncher(testRobot, 200, 2, 50, 20)
        handgun.hitSignal.connect(self.hitSignalSlot)
        shotgun.hitSignal.connect(self.hitSignalSlot)
        grenade.hitSignal.connect(self.hitSignalSlot)
        testRobot.equipWithGuns(handgun, shotgun, grenade)
        self.setTargetSignal.connect(testRobot.controller.setTargetSlot)
        self.keyPressedSignal.connect(testRobot.controller.keyPressedSlot)


        spawnPoints = [(200, 500), (500, 200), (500, 800), (800, 500)]

        for x,y in spawnPoints:
            self.robots[id] = robots.ChaserRobot(id, x, y, 1, 200, control.ChaseDirectlyController)
            id += 1

        print(len(self.robots))

        for robot in self.robots.values():

            robot.connectSignals()

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
                tile = self.levelMatrix[row][column]
                texture = self.tileTextures[tile]
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

        if not deltaTime > 0.5:

            # Update robots
            for robot in self.robots.values():
                robot.update(deltaTime, self.levelMatrix, self.robots)

            # send positions data every 5th tick
            if self.tickCounter % 5 == 0:
                for robot in self.robots.values():
                    self.emitRobotSensorData(robot)


            # Update visuals
            self.update()

        self.previous = elapsed


    def emitRobotSensorData(self, robot):

        cone = robot.view_cone()
        robotsInView = {}
        timestamp = QDateTime.currentMSecsSinceEpoch()

        # Special case for runner robot: He sees everything:
        if isinstance(robot, robots.RunnerRobot):
            ids = self.robots.keys()
            wallsInView = self.obstacles
        else:
            # Get ids of all robots that are in view, i.e. that intersect with the view cone
            ids = filter(lambda id : cone.intersects(self.robots[id].shape()), self.robots)
            wallsInView = filter(cone.intersects, self.obstacles)

        for id in ids:
            other = self.robots[id]
            dist = (robot.pos - other.pos).length()
            angle = math.degrees(math.atan2(other.y - robot.y, other.x - robot.x))
            robotsInView[id] = {'x' : other.x,
                                'y' : other.y,
                                'id': other.id,
                                'pos' : QVector2D(other.x, other.y),
                                'dist' : dist,
                                'angle' : angle,
                                'timestamp' : timestamp}

        robot.robotsInViewSignal.emit(robotsInView)
        robot.wallsInViewSignal.emit(list(wallsInView))


    def mouseMoveEvent(self, event):
        self.setTargetSignal.emit(event.x(), event.y())

    def keyPressEvent(self, event):
        self.keyPressedSignal.emit(event.key())

    ### Slots

    # Will be called whenever a robot kills another robot. id is the id of the robots that has to be killed
    def hitSignalSlot(self, id, damage):
        self.robots[id].dealDamage(damage)

if __name__ == '__main__':

    app = QApplication(sys.argv)

    game = RobotGame()

    sys.exit(app.exec_())
