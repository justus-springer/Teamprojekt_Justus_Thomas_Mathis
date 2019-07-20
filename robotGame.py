import sys, math
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import random

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

    keysPressedSignal = pyqtSignal(list)

    def __init__(self):
        super().__init__()

        # Load level data from file
        self.levelMatrix, self.obstacles, metadata = LevelLoader.loadLevel('levels/menu.txt')
        self.spawnPlayer1 = QVector2D(75, 500)
        self.spawnPlayer2 = QVector2D(925, 500)

        self.initUI()
        self.initTextures()
        self.initRobots('menu', metadata)
        self.initTimer()

        self.keysPressed = []

        self.points = [0, 0]

        self.bluePlayerColor = QColor(50, 120, 220, 255)
        self.redPlayerColor = QColor(120, 30, 30, 255)
        self.backgroundColor = QColor(80, 80, 80, 160)
        self.innerBackgroundColor = QColor(20, 20, 20, 240)


    def initTextures(self):

        self.tileTextures = {tileEnum : QPixmap('textures/' + tileName + '.png') for tileName, tileEnum in Tile.__members__.items()}

    def initUI(self):

        self.setFocus()

        self.gameState = "menu"
        self.chosenGameMode = ""
        self.chosenMap = ""

        self.setGeometry(35, 35, 1200, 1000)
        self.setWindowTitle(WINDOW_TITLE)

        startButton = QPushButton("Start game", self)
        startButton.setGeometry(1025, 50, 150, 50)
        startButton.show()
        startButton.clicked.connect(self.startGame)

        chooseModeButton = QPushButton("Choose mode", self)
        chooseModeButton.setGeometry(1025, 150, 150, 50)
        chooseModeButton.show()

        chooseModeMenu = QMenu(self)
        singlePlayerAction = QAction('single player', self)
        singlePlayerAction.triggered.connect(lambda : self.setGameMode('single'))
        chooseModeMenu.addAction(singlePlayerAction)
        duelPlayerAction = QAction('duel mode', self)
        duelPlayerAction.triggered.connect(lambda : self.setGameMode('duel'))
        chooseModeMenu.addAction(duelPlayerAction)
        chooseModeButton.setMenu(chooseModeMenu)

        chooseMapButton = QPushButton("Choose map", self)
        chooseMapButton.setGeometry(1025, 200, 150, 50)
        chooseMapMenu = QMenu(self)
        for levelName in ['Squares', 'Arena', 'Arctic', 'Volcano']:
            chooseMapAction = QAction(levelName, self)
            levelPath = 'levels/' + levelName.lower() + '.txt'
            chooseMapAction.triggered.connect((lambda x : (lambda : self.setMap(x)))(levelPath))
            chooseMapMenu.addAction(chooseMapAction)

        chooseCustomMapAction = QAction('Chustom Map', self)
        chooseCustomMapAction.triggered.connect(self.chooseCustomMap)
        chooseMapMenu.addAction(chooseCustomMapAction)

        chooseMapButton.setMenu(chooseMapMenu)
        chooseMapButton.show()

        self.show()

    def setGameMode(self, mode):
        self.chosenGameMode = mode

    def setMap(self, mapFilePath):
        self.chosenMap = mapFilePath

    def chooseCustomMap(self):
        url = QFileDialog.getOpenFileUrl(self, "Load custom map", QDir.currentPath(), "TXT files (*.txt)")
        filePath = url[0].toLocalFile()
        self.setMap(filePath)

    def initTimer(self):

        self.gameTimer = QBasicTimer()
        self.gameTimer.start(TICK_INTERVALL, self)

        # For deltaTime
        self.elapsedTimer = QElapsedTimer()
        self.elapsedTimer.start()
        self.previous = 0
        self.tickCounter = 0

    def initRobots(self, mode, metadata):

        if mode == 'menu':

            spawn_x, spawn_y = metadata['single_spawn']
            player = robots.TestRobot(1, spawn_x * TILE_SIZE, spawn_y * TILE_SIZE, control.PlayerController)

            handgun = Handgun(player, 500, 0.1, 80)
            shotgun = Shotgun(player, 200, 0.1, 10, 20)
            grenade = GrenadeLauncher(player, 200, 0.1, 10, 100)
            handgun.hitSignal.connect(self.hitSignalSlot)
            shotgun.hitSignal.connect(self.hitSignalSlot)
            grenade.hitSignal.connect(self.hitSignalSlot)
            player.equipWithGuns(handgun, shotgun, grenade)

            self.keysPressedSignal.connect(player.controller.keysPressedSlot)

            self.robots = {1 : player}

        elif mode == 'single':

            spawn_x, spawn_y = metadata['single_spawn']
            player = robots.TestRobot(1, spawn_x * TILE_SIZE, spawn_y * TILE_SIZE, control.PlayerController)

            handgun = Handgun(player, 500, 1, 80)
            shotgun = Shotgun(player, 200, 2, 10, 20)
            grenade = GrenadeLauncher(player, 200, 3, 10, 100)

            handgun.hitSignal.connect(self.hitSignalSlot)
            shotgun.hitSignal.connect(self.hitSignalSlot)
            grenade.hitSignal.connect(self.hitSignalSlot)

            player.equipWithGuns(handgun, shotgun, grenade)
            self.keysPressedSignal.connect(player.controller.keysPressedSlot)

            chaser1_x, chaser1_y = metadata['chaser_spawns'][0]
            chaser2_x, chaser2_y = metadata['chaser_spawns'][1]
            chaser3_x, chaser3_y = metadata['chaser_spawns'][2]

            chaser1 = robots.ChaserRobot(3, chaser1_x * TILE_SIZE, chaser1_y * TILE_SIZE, 1, 200, control.ChaseDirectlyController)
            handgun1 = Handgun(chaser1, 500, 2, 80)
            chaser1.equipWithGuns(handgun1)
            handgun1.hitSignal.connect(self.hitSignalSlot)

            chaser2 = robots.ChaserRobot(4, chaser2_x * TILE_SIZE, chaser2_y * TILE_SIZE, 1, 200, control.ChasePredictController)
            handgun2 = Handgun(chaser2, 500, 2, 80)
            chaser2.equipWithGuns(handgun2)
            handgun2.hitSignal.connect(self.hitSignalSlot)

            chaser3 = robots.ChaserRobot(5, chaser3_x * TILE_SIZE, chaser3_y * TILE_SIZE, 1, 200, control.ChaseGuardController)
            handgun3 = Handgun(chaser3, 500, 2, 80)
            chaser3.equipWithGuns(handgun3)
            handgun3.hitSignal.connect(self.hitSignalSlot)

            self.robots = {robot.id: robot for robot in [player, chaser1, chaser2, chaser3]}

        elif mode =='duel':

            player = robots.TestRobot(1, self.spawnPlayer1.x(), self.spawnPlayer1.y(), control.PlayerController)
            player2 = robots.TestRobot(2, self.spawnPlayer2.x(), self.spawnPlayer2.y(), control.XboxController)

            handgun = Handgun(player, 500, 1, 80)
            shotgun = Shotgun(player, 200, 2, 10, 20)
            grenade = GrenadeLauncher(player, 200, 3, 10, 100)
            handgun_player_2 = Handgun(player2, 500, 1, 80)
            shotgun_player_2 = Shotgun(player2, 200, 2, 10, 20)
            grenade_player_2 = GrenadeLauncher(player2, 200, 3, 10, 100)

            handgun.hitSignal.connect(self.hitSignalSlot)
            shotgun.hitSignal.connect(self.hitSignalSlot)
            grenade.hitSignal.connect(self.hitSignalSlot)
            handgun_player_2.hitSignal.connect(self.hitSignalSlot)
            shotgun_player_2.hitSignal.connect(self.hitSignalSlot)
            grenade_player_2.hitSignal.connect(self.hitSignalSlot)

            player.equipWithGuns(handgun, shotgun, grenade)
            player2.equipWithGuns(handgun_player_2, shotgun_player_2, grenade_player_2)

            self.keysPressedSignal.connect(player.controller.keysPressedSlot)

            self.robots = {robot.id : robot for robot in [player, player2]}

        # Connect everything and start the controller threads
        for robot in self.robots.values():

            robot.connectSignals()

            # Tell the controller the specs of the robot (a_max and a_alpha_max)
            robot.robotSpecsSignal.emit(robot.a_max, robot.a_alpha_max, robot.v_max, robot.v_alpha_max)

            # Start the controller threads
            robot.controller.start()

    def startGame(self):
        self.setFocus()
        if self.chosenMap != "" and self.chosenGameMode != "":

            self.gameState = self.chosenGameMode
            self.resetEverything()
            self.levelMatrix, self.obstacles, metadata = LevelLoader.loadLevel(self.chosenMap)
            self.initRobots(self.chosenGameMode, metadata)

        else:
            print("Please choose a map and a mode first, stupid!")

    def resetEverything(self):
        for robot in self.robots.values():
            robot.terminateThread()
        self.robots = {}
        self.keysPressedSignal.disconnect()
        self.points = [0, 0]

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

        if self.gameState == 'duel':
            self.drawScore(event, qp)

        qp.end()

    def drawScore(self, event, qp):

        qp.setFont(QFont('Decorative', 40))

        qp.setPen(self.redPlayerColor)
        qp.drawText(400, 135, str((self.points[1])))

        qp.setPen(self.bluePlayerColor)
        qp.drawText(580, 135, str((self.points[0])))

        if self.points[0] >= 2 or self.points[1] >= 2:

            qp.setBrush(self.backgroundColor)
            qp.setPen(self.backgroundColor)
            qp.drawRect(0, 0, 1000, 1000)

            qp.setBrush(self.innerBackgroundColor)
            qp.setPen(Qt.black)
            qp.drawRect(0, 400, 1000, 200)

            qp.setFont(QFont('Decorative', 120))
            qp.setPen(Qt.black)

            if self.points[0] >= 2:
                qp.setPen(self.bluePlayerColor)
                qp.drawText(160, 550, "blue wins!")
            else:
                qp.setPen(self.redPlayerColor)
                qp.drawText(190, 550, "red wins!")

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

        if deltaTime < 0.5:

            # Update robots
            for robot in self.robots.values():
                robot.update(deltaTime, self.levelMatrix, self.robots)

            # send positions data every 5th tick
            if self.tickCounter % 5 == 0:
                for robot in self.robots.values():
                    self.emitRobotSensorData(robot)

            # send key information to player controller
            self.keysPressedSignal.emit(self.keysPressed)

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

    def keyPressEvent(self, event):
        self.keysPressed.append(event.key())

    def keyReleaseEvent(self, event):
        if self.keysPressed != []:
            self.keysPressed.remove(event.key())

    ### Slots

    # Will be called whenever a robot damages another robot. id is the id of the robots that has to be damaged
    def hitSignalSlot(self, id, damage):
        self.robots[id].dealDamage(damage)

        if self.robots[id].active and not self.robots[id].protected and self.robots[id].health == 0:
            self.robots[id].killRobot()
            if self.gameState == 'duel':
                self.points[id-1] = self.points[id-1] + 1


if __name__ == '__main__':

    app = QApplication(sys.argv)

    game = RobotGame()

    sys.exit(app.exec_())
