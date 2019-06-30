from PyQt5.QtGui import QPainter, QPen, QVector2D
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.Qt import QSoundEffect, QUrl
import math
import random

from toolbox import vectorToAngle, angleToVector, posToTileIndex, onPlayground
from levelLoader import Tile

# abstract
class Gun(QObject):

    # This will be emitted when the handgun hits another robot. It transmits the id of the robot that has been hit
    hitSignal = pyqtSignal(int)

    def __init__(self, owner, baseSpeed, timeToReload, bulletRadius):
        super().__init__()

        self.owner = owner
        self.pos = QVector2D(0,0)
        self.x = owner.x
        self.y = owner.y
        self.baseSpeed = baseSpeed
        self.timeToReload = timeToReload # seconds
        self.bulletRadius = bulletRadius
        self.reloadTimer = 0

        self.bullets = []

    def update(self, deltaTime, levelMatrix, robotsDict):
        self.pos = self.owner.pos

        # decrement reload timer. If it hits zero, the gun can shoot again
        if not self.readyToFire():
            self.reloadTimer -= deltaTime

    def draw(self, qp):
        for bullet in self.bullets:
            bullet.draw(qp)

    # abstract
    def fire(self, direction):
        raise NotImplementedError("Implement this method, stupid!")

    def readyToFire(self):
        return self.reloadTimer <= 0

    def resetTimer(self):
        self.reloadTimer = self.timeToReload

class Handgun(Gun):

    def __init__(self, owner, baseSpeed, timeToReload):
        super().__init__(owner, baseSpeed, timeToReload, bulletRadius=5)

        self.soundEffect = QSoundEffect(self)
        self.soundEffect.setSource(QUrl.fromLocalFile("sounds/shoot.wav"))
        self.soundEffect.setVolume(0.25)

    def update(self, deltaTime, levelMatrix, robotsDict):
        super().update(deltaTime, levelMatrix, robotsDict)

        for bullet in self.bullets:
            bullet.update(deltaTime, levelMatrix, robotsDict)
            if bullet.collidesWithWorld(levelMatrix):
                self.bullets.remove(bullet)
                del bullet
                continue

            robot = bullet.collidesWithRobots(robotsDict)
            if robot != None:
                self.hitSignal.emit(robot.id)
                self.bullets.remove(bullet)
                del bullet

    def fire(self, direction):
        if self.readyToFire():
            bulletSpeed = self.baseSpeed + self.owner.v
            bullet = Bullet(self.owner, self.pos, direction, bulletSpeed, self.bulletRadius, 10)
            self.bullets.append(bullet)

            self.resetTimer()
            self.soundEffect.play()


class Shotgun(Gun):

    def __init__(self, owner, baseSpeed, timeToReload, bulletsPerShot):
        super().__init__(owner, baseSpeed, timeToReload, bulletRadius=3)

        self.bulletsPerShot = bulletsPerShot

        self.soundEffect = QSoundEffect(self)
        self.soundEffect.setSource(QUrl.fromLocalFile("sounds/shotgun.wav"))
        self.soundEffect.setVolume(0.25)

    def update(self, deltaTime, levelMatrix, robotsDict):
        super().update(deltaTime, levelMatrix, robotsDict)

        for bullet in self.bullets:
            bullet.update(deltaTime, levelMatrix, robotsDict)
            if bullet.isTooOld() or bullet.collidesWithWorld(levelMatrix):
                self.bullets.remove(bullet)
                del bullet
                continue

            robot = bullet.collidesWithRobots(robotsDict)
            if robot != None:
                self.hitSignal.emit(robot.id)
                self.bullets.remove(bullet)
                del bullet

    def fire(self, direction):
        MAX_SCATTER_ANGLE = 10
        MAX_SCATTER_SPEED = 20

        if self.readyToFire():
            bulletSpeed = self.baseSpeed + self.owner.v
            baseAngle = vectorToAngle(direction)
            for i in range(self.bulletsPerShot):
                scatteredAngle = baseAngle + random.uniform(-MAX_SCATTER_ANGLE, MAX_SCATTER_ANGLE)
                scatteredDirection = angleToVector(scatteredAngle)
                scatteredSpeed = bulletSpeed + random.uniform(-MAX_SCATTER_SPEED, MAX_SCATTER_SPEED)
                self.bullets.append(Bullet(self.owner, self.pos, scatteredDirection, scatteredSpeed, self.bulletRadius, 1))

            self.resetTimer()
            self.soundEffect.play()


class Bullet:

    def __init__(self, owner, startPos, direction, speed, radius, maxAge):
        self.owner = owner
        self.pos = QVector2D(startPos.x(), startPos.y())
        self.direction = direction
        self.speed = speed
        self.radius = radius
        self.maxAge = maxAge
        self.age = 0

    def update(self, deltaTime, levelMatrix, robotsDict):
        self.pos += deltaTime * self.speed * self.direction
        self.age += deltaTime

    # Returns true if the bullet collides with the world
    def collidesWithWorld(self, levelMatrix):

        if not onPlayground(self.pos):
            return True

        if not posToTileIndex(self.pos, levelMatrix).walkable():
            return True

        return False

    # If the bullet collides with a robot, it returns that robot
    # Otherwise returns None
    def collidesWithRobots(self, robotsDict):
        for robot in robotsDict.values():
            # The owner should not be killed by its own bullet
            if robot.id == self.owner.id:
                continue

            if (self.pos - robot.pos).length() <= robot.r:
                return robot

        return None

    # Returns true if the bullet should be deleted
    def isTooOld(self):
        return self.age > self.maxAge

    def draw(self, qp):
        qp.setPen(QPen(Qt.NoPen))
        qp.setBrush(Qt.black)
        qp.drawEllipse(self.pos.toPointF(), self.radius, self.radius)

    ### properties

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
