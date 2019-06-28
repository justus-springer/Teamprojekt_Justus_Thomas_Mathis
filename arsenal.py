from PyQt5.QtGui import QPainter, QPen, QVector2D
from PyQt5.QtCore import Qt, pyqtSignal, QObject
import math

class Handgun(QObject):

    # This will be emitted when the handgun hits another robot. It transmits the id of the robot that has been hit
    hitSignal = pyqtSignal(int)

    def __init__(self, owner, baseSpeed, timeToReload):
        super().__init__()

        self.owner = owner
        self.pos = self.owner.pos
        self.baseSpeed = 300
        self.timeToReload = 2 # seconds
        self.reloadTimer = 0
        self.radius = 5

        self.bullets = []

    def update(self, deltaTime, levelMatrix, robotsDict):
        self.pos = self.owner.pos

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

        # decrement reload timer. If it hits zero, the gun can shoot again
        if not self.readyToShoot():
            self.reloadTimer -= deltaTime

    def draw(self, qp):
        for bullet in self.bullets:
            bullet.draw(qp)

    def shoot(self, direction):
        if self.readyToShoot():
            bulletSpeed = self.baseSpeed + self.owner.v
            bullet = Bullet(self.owner, self.pos, direction, bulletSpeed)
            self.bullets.append(bullet)

            self.resetTimer()

    def readyToShoot(self):
        return self.reloadTimer <= 0

    def resetTimer(self):
        self.reloadTimer = self.timeToReload


class Shotgun(QObject):

    # This will be emitted when the shotgun hits another robot. It transmits the id of the robot that has been hit
    hitSignal = pyqtSignal(int)

    def __init__(self, owner, baseSpeed, timeToReload):
        super().__init__()

        self.owner = owner
        self.pos = self.owner.pos
        self.baseSpeed = 300
        self.timeToReload = 2 # seconds
        self.reloadTimer = 0
        self.radius = 3

        self.bullets = []

    def update(self, deltaTime, levelMatrix, robotsDict):
        self.pos = self.owner.pos

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

            if bullet.outOfRange() == True:
                self.bullets.remove(bullet)


        # decrement reload timer. If it hits zero, the gun can shoot again
        if not self.readyToShoot():
            self.reloadTimer -= deltaTime

    def draw(self, qp):
        for bullet in self.bullets:
            bullet.draw(qp)

    def shoot(self, direction):
        if self.readyToShoot():
            bulletSpeed = self.baseSpeed + self.owner.v
            bullet = Bullet(self.owner, self.pos, direction, bulletSpeed, self.radius)
            bullet2 = Bullet(self.owner, self.pos, (direction * QVector2D(0.8, 1.2)).normalized(), bulletSpeed, self.radius)
            bullet3 = Bullet(self.owner, self.pos, (direction * QVector2D(1.2, 0.8)).normalized(), bulletSpeed, self.radius)
            self.bullets.append(bullet)
            self.bullets.append(bullet2)
            self.bullets.append(bullet3)
            self.resetTimer()

    def readyToShoot(self):
        return self.reloadTimer <= 0

    def resetTimer(self):
        self.reloadTimer = self.timeToReload

class Bullet:

    def __init__(self, owner, startPos, direction, speed, radius):
        self.owner = owner
        self.pos = QVector2D(startPos.x(), startPos.y())
        self.direction = direction
        self.speed = speed
        self.radius = radius

    def update(self, deltaTime, levelMatrix, robotsDict):
        self.pos += deltaTime * self.speed * self.direction

    # Returns true if the bullet collides with the world
    def collidesWithWorld(self, levelMatrix):
        # TODO: Implement correctly

        if self.x > 1000 or self.x < 0 or self.y > 1000 or self.y < 0:
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


    def outOfRange(self):
        if (math.fabs((self.owner.pos - self.pos).length()) > 200):
            return True
        else:
            return False



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
