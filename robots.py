import sys
from PyQt5.QtGui import QPainter, QVector2D, QColor, QPainterPath, QPolygonF, QBrush, QPen, QFont, QPixmap
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QRectF, QPointF
from PyQt5.Qt import QSoundEffect, QUrl
import math
import random

import robotGame, control
from toolbox import minmax, circleCircleCollision, circleRectCollision
from levelLoader import Tile
from bar import HealthBar

# Epsilon values represent the smallest reasonable value greater than 0
# Any speed/distance below their epsilon value should be interpreted as practically 0
# Handle with caution
EPSILON_V = 20
EPSILON_V_ALPHA = 20
EPSILON_ALPHA = 10
EPSILON_POS = 10

# Acceleration properties
A_MAX = 100
A_ALPHA_MAX = 360

# Collision properties
COLL_BUFFER = 10

# Drawing properties
ID_FONT = QFont("Calibri", 20)

class BaseRobot(QObject):

    # This will be emittet once at the beginning of the game to tell the controller the values a_max and a_alpha_max
    robotSpecsSignal = pyqtSignal(float, float, float, float)

    # This will be emittet every tick to tell the controller current values of x, y, alpha, v, v_alpha, readyToShoot
    robotInfoSignal = pyqtSignal(float, float, float, float, float, bool)

    # This will be emitted every 10th tick
    robotsInViewSignal = pyqtSignal(dict)
    wallsInViewSignal = pyqtSignal(list)

    def __init__(self, id, spawn_x, spawn_y, aov, v_max, maxHealth, r = 30, alpha = 0, texturePath = "textures/robot_base.png"):

        super().__init__()

        self.id = id
        self.pos = QVector2D(spawn_x, spawn_y)
        self.spawn = QVector2D(spawn_x, spawn_y)
        self.aov = aov
        self.r = r
        self.alpha = alpha # unit: degrees
        self.texture = QPixmap(texturePath)

        self.a = 0 # unit: pixels/second^2
        self.a_max = A_MAX # unit: pixels/second^2
        self.v = 0 # unit: pixels/second
        self.v_max = v_max # unit pixels/second

        self.a_alpha = 0 # unit: degrees/second^2
        self.a_alpha_max = A_ALPHA_MAX # unit: degrees/second^2
        self.v_alpha = 0 # unit: degrees/second
        self.v_alpha_max = 360 # unit: degrees/second

        self.guns = []
        self.selected_gun = None

        self.maxHealth = maxHealth
        self.health = maxHealth
        self.healthBar = HealthBar(maxHealth)
        self.active = True
        self.timeToRespawn = 0

        self.deathSound = QSoundEffect(self)
        self.deathSound.setSource(QUrl.fromLocalFile("sounds/death.wav"))
        self.deathSound.setVolume(0.1)

        self.emptyGunSound = QSoundEffect(self)
        self.emptyGunSound.setSource(QUrl.fromLocalFile("sounds/empty_gun.wav"))
        self.emptyGunSound.setVolume(0.1)

        self.respawnSound = QSoundEffect(self)
        self.respawnSound.setSource(QUrl.fromLocalFile("sounds/respawn.wav"))
        self.respawnSound.setVolume(0.1)

    def equipWithGuns(self, *guns):
        self.guns = guns
        self.selected_gun = guns[0]

    def connectSignals(self):
        self.robotSpecsSignal.connect(self.controller.receiveRobotSpecs)
        self.robotInfoSignal.connect(self.controller.receiveRobotInfo)
        self.robotsInViewSignal.connect(self.controller.receiveRobotsInView)
        self.wallsInViewSignal.connect(self.controller.receiveWallsInView)

        self.controller.fullStopSignal.connect(self.fullStop)
        self.controller.fullStopRotationSignal.connect(self.fullStopRotation)
        self.controller.shootSignal.connect(self.shoot)
        self.controller.switchToGunSignal.connect(self.swithToGun)
        self.controller.moveUpSignal.connect(self.moveUp)
        self.controller.moveDownSignal.connect(self.moveDown)
        self.controller.moveLeftSignal.connect(self.moveLeft)
        self.controller.moveRightSignal.connect(self.moveRight)

    def draw(self, qp):

        qp.save()
        qp.translate(self.x, self.y)
        qp.rotate(self.alpha)
        source = QRectF(0, 0, 64, 64)
        target = QRectF(-self.r, -self.r, 2*self.r, 2*self.r)
        qp.drawPixmap(target, self.texture, source)
        qp.restore()

        for gun in self.guns:
            gun.draw(qp)

        qp.setPen(QPen(Qt.black))
        qp.setFont(ID_FONT)
        qp.drawText(self.boundingRect(), Qt.AlignCenter, ' ') # This shold not exist

        if self.active:
            self.healthBar.draw(qp)
        else:
            qp.drawText(self.boundingRect(), Qt.AlignCenter, str(int(self.timeToRespawn) + 1))

    def drawDebugLines(self, qp):
        qp.setBrush(QBrush(Qt.NoBrush))
        pen = QPen(Qt.red)
        pen.setWidthF(1.5)
        qp.setPen(pen)
        qp.drawPath(self.view_cone())

    def update(self, deltaTime, levelMatrix, robotsDict):

        # Fetch acceleration values from your thread
        self.a, self.a_alpha = self.controller.fetchValues()
        # But not too much
        self.a = minmax(self.a, -self.a_max, self.a_max)
        self.a_alpha = minmax(self.a_alpha, -self.a_alpha_max, self.a_alpha_max)

        # Apply acceleration
        self.v += self.a * deltaTime
        self.v_alpha += self.a_alpha * deltaTime
        # But not too much
        self.v = minmax(self.v, -self.v_max, self.v_max)
        self.v_alpha = minmax(self.v_alpha, -self.v_alpha_max, self.v_alpha_max)

        obstacles = self.collisionRadar(levelMatrix)
        self.collideWithWalls(obstacles)

        # Apply velocity
        if self.active:
            self.pos += self.v * deltaTime * self.direction()
            self.alpha += self.v_alpha * deltaTime
            self.alpha %= 360
        else:
            self.timeToRespawn -= deltaTime
            if self.timeToRespawn <= 0:
                self.respawn()

        self.collideWithRobots(robotsDict, obstacles)

        # send current information to the controller
        self.robotInfoSignal.emit(self.x, self.y, self.alpha, self.v, self.v_alpha, self.readyToFire())

        for gun in self.guns:
            gun.update(deltaTime, levelMatrix, robotsDict)

        # Health bar stuff
        healthBarPosition = self.pos - QVector2D(0, self.r + 10)
        self.healthBar.update(self.health, healthBarPosition)
        color_g = int(255 * self.health / self.maxHealth)
        color_r = 255 - color_g
        self.healthBar.setColor(QColor(color_r, color_g, 0))


    def collideWithWalls(self, obstacles):

        for rect in obstacles:

            overlap = circleRectCollision(self.pos, self.r, rect)
            if overlap:

                if abs(overlap.x()) > abs(overlap.y()):
                    self.translate(0, overlap.y())
                else:
                    self.translate(overlap.x(), 0)

                # Set speed to zero (almost)
                self.v = EPSILON_V

    def isColliding(self, obstacles):

        for rect in obstacles:
            if circleRectCollision(self.pos, self.r, rect):
                return True

        return False

    def collideWithRobots(self, robotsDict, obstacles):

        for id in robotsDict:
            if id != self.id:
                robot = robotsDict[id]
                overlap_vec = circleCircleCollision(self.pos, self.r, robot.pos, robot.r)

                if overlap_vec:
                    if self.isColliding(obstacles):
                        robot.pos -= overlap_vec

                    else:
                        self.pos += overlap_vec / 2
                        robot.pos -= overlap_vec / 2

                    self.hook_collidedWith(robot)

    def hook_collidedWith(self, robot):
        pass

    def collisionRadar(self, levelMatrix):
        #Calculate Limits

        x_min = minmax(int((self.x - self.r - COLL_BUFFER) // 10), 0, len(levelMatrix))
        x_max = minmax(int((self.x + self.r + COLL_BUFFER) // 10 + 1), 0, len(levelMatrix))
        y_min = minmax(int((self.y - self.r - COLL_BUFFER) // 10), 0, len(levelMatrix))
        y_max = minmax(int((self.y + self.r + COLL_BUFFER) // 10 + 1), 0, len(levelMatrix))

        #Fill obstacle list
        obstacles = []
        for y in range(y_min, y_max):
            for x in range(x_min, x_max):
                if not levelMatrix[y][x].walkable():
                    obstacles.append(QRectF(x * 10, y * 10, 10, 10))

        return obstacles

    ### Slots

    def fullStop(self):

        if abs(self.v) < EPSILON_V:
            self.v = 0
            return True
        else:
            return False

    def fullStopRotation(self):

        if abs(self.v_alpha) < EPSILON_V_ALPHA:
            self.v_alpha = 0
            return True
        else:
            return False

    def shoot(self):
        if self.selected_gun != None and self.active:
            if self.selected_gun.readyToFire():
                self.selected_gun.fire(self.direction())
            else:
                self.emptyGunSound.play()

    def swithToGun(self, index):
        if index < len(self.guns):
            self.selected_gun = self.guns[index]

    def dealDamage(self, damage):
        if self.active:
            self.health = max(0, self.health - damage)
            if self.health == 0:
                self.active = False
                self.timeToRespawn = 3 # 3 seconds until respawn
                self.deathSound.play()

    def respawn(self):
        self.pos.setX(self.spawn.x())
        self.pos.setY(self.spawn.y())
        self.health = self.maxHealth
        self.active = True
        self.respawnSound.play()

    def moveUp(self):

        #self.controller.a = self.a_max / 2

        self.controller.target_x = self.x
        self.controller.target_y = self.y - 100

    def moveDown(self):

        #self.controller.a = - self.a_max / 2

        self.controller.target_x = self.x
        self.controller.target_y = self.y + 100


    def moveLeft(self):

        #self.controller.a_alpha = - self.a_alpha_max / 4
        self.controller.target_x = self.x - 100
        self.controller.target_y = self.y


    def moveRight(self):

        #self.controller.a_alpha = self.a_alpha_max / 4

        self.controller.target_x = self.x + 100
        self.controller.target_y = self.y

    ### properties and helperfunction

    def direction(self):
        return QVector2D(math.cos(self.alpha_radians), math.sin(self.alpha_radians))

    def boundingRect(self):
        return QRectF(self.x - self.r, self.y - self.r, 2*self.r, 2*self.r)

    def readyToFire(self):
        if self.selected_gun == None:
            return False
        else:
            return self.selected_gun.readyToFire()

    def shape(self):
        shape = QPainterPath()
        shape.addEllipse(self.pos.toPointF(), self.r, self.r)
        return shape

    def view_cone(self):
        path = QPainterPath()
        a = self.pos.toPointF()
        b = a + QPointF(5000 * math.cos(math.radians(self.alpha + self.aov)),
                    5000 * math.sin(math.radians(self.alpha + self.aov)))
        c = a + QPointF(5000 * math.cos(math.radians(self.alpha - self.aov)),
                    5000 * math.sin(math.radians(self.alpha - self.aov)))
        path.addPolygon(QPolygonF([a, b, c]))
        path.closeSubpath()
        return path

    def translate(self, x, y):
        self.pos += QVector2D(x, y)


    ### properties

    def get_alpha_radians(self):
        return math.radians(self.alpha)

    def set_alpha_radians(self, new_alpha):
        self.alpha = math.degrees(new_alpha)

    alpha_radians = property(get_alpha_radians, set_alpha_radians)

    def setController(self, controller):
        self._controller = controller

    def getController(self):
        return self._controller

    controller = property(getController, setController)

    def get_x(self):
        return self.pos.x()

    def set_x(self, new_x):
        self.pos.setX(new_x)

    x = property(get_x, set_x)

    def get_y(self):
        return self.pos.y()

    def set_y(self, new_y):
        self.pos.setY(new_y)

    y = property(get_y, set_y)

class ChaserRobot(BaseRobot):

    scoreSignal = pyqtSignal(int)

    def __init__(self, id, spawn_x, spawn_y, targetId, maxHealth, controllerClass):
        super().__init__(id, spawn_x, spawn_y, 30, 80, maxHealth, 30, 0, "textures/robot_gray.png")

        self.controller = controllerClass(id, targetId)

    def hook_collidedWith(self, robot):
        # if the other robot was a runner, teleport to your spawn
        if isinstance(robot, RunnerRobot):
            self.teleportToFarthestPoint(robot.pos)
            self.scoreSignal.emit(self.id)

    def drawDebugLines(self, qp):
        super().drawDebugLines(qp)
        qp.setBrush(QBrush(Qt.blue))
        qp.setPen(Qt.blue)
        p = self.controller.aimPos.toPointF()
        qp.drawEllipse(p, 5, 5)


class RunnerRobot(BaseRobot):

    def __init__(self, id, x, y, chaserIds):
        super().__init__(id, x, y, 50, 130, 25, 0, "textures/robot_blue.png")
        self.controller = control.RunController(id, chaserIds)

    def drawDebugLines(self, qp):
        dir = self.controller.aim_direction.toPointF()
        p1 = self.pos.toPointF()
        p2 = p1 + 70 * dir
        pen = QPen(Qt.blue)
        pen.setWidth(3)
        qp.setPen(pen)
        qp.drawLine(p1, p2)

class TestRobot(BaseRobot):

    def __init__(self, id, x, y):
        super().__init__(id, x, y, 30, 200, 500, 30, 0, "textures/robot_red.png")
        self.controller = control.PlayerController(id)
