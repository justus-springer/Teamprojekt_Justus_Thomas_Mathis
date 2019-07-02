# Woche 5: Verfolgungsjagd

### [<- Zurück](/../index.md) zur Projektübersicht
---

## Guns
Zunächst haben wir eine Gun Klasse geschrieben:
```python
class Gun(QObject):

    # This will be emitted when the handgun hits another robot.
    # It transmits the id of the robot being hit and the amount of damage to be dealt
    hitSignal = pyqtSignal(int, float)

    def __init__(self, owner, baseSpeed, timeToReload, damage, bulletRadius):
        super().__init__()

        self.owner = owner
        self.pos = QVector2D(0,0)
        self.x = owner.x
        self.y = owner.y
        self.baseSpeed = baseSpeed
        self.timeToReload = timeToReload # seconds
        self.damage = damage
        self.bulletRadius = bulletRadius
        self.reloadTimer = 0

        self.bullets = []
        self.reloadDisplay = ReloadBar(timeToReload, self.owner.r * 2)


    def update(self, deltaTime, levelMatrix, robotsDict):
        self.pos = self.owner.pos

        # decrement reload timer. If it hits zero, the gun can shoot again
        if not self.readyToFire():
            self.reloadTimer -= deltaTime

        reloadDisplayPosition = QVector2D(self.pos.x(), self.pos.y() + self.owner.r)
        reloadDisplayValue = self.timeToReload - self.reloadTimer
        self.reloadDisplay.update(reloadDisplayValue, reloadDisplayPosition)

    def draw(self, qp):
        for bullet in self.bullets:
            bullet.draw(qp)
        if not self.readyToFire():
            self.reloadDisplay.draw(qp)

    # abstract
    def fire(self, direction):
        raise NotImplementedError("Implement this method, stupid!")

    def readyToFire(self):
        return self.reloadTimer <= 0

    def resetTimer(self):
        self.reloadTimer = self.timeToReload

```

Von dieser Klasse erben nun die Unterklassen "Handgun", "Shotgun" und "GrenadeLauncher":

```python
class Handgun(Gun):

    def __init__(self, owner, baseSpeed, timeToReload, damage):
        super().__init__(owner, baseSpeed, timeToReload, damage, bulletRadius=5)

        self.soundEffect = QSoundEffect(self)
        self.soundEffect.setSource(QUrl.fromLocalFile("sounds/handgun.wav"))
        self.soundEffect.setVolume(0.4)

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
                self.hitSignal.emit(robot.id, self.damage)
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

      ...

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
```

```python
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

        return not onPlayground(self.pos) or not posToTileIndex(self.pos, levelMatrix).walkable()

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

```
Dazu haben wir helperfunctions in die toolbox geschrieben
```python

def posToTileIndex(pos,levelMatrix):
    return levelMatrix[int(pos.y() // 10)][int(pos.x() // 10)]

def onPlayground(pos):
    if pos.x() > 1000 or pos.x() < 0 or pos.y() > 1000 or pos.y() < 0:
        return False
    return True

```

Kollidiert eine Kugel mit einem Roboter, wird das hitSignal ausgesendet. Dies ist verbunden mit einem Slot eines Servers

```python
# Will be called whenever a robot kills another robot. id is the id of the robots that has to be killed
def hitSignalSlot(self, id, damage):
    self.robots[id].dealDamage(damage)
```
Im Roboter wird dann dealDamage aufgerufen.
```python
class BaseRobot(QObject):

  ...

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
```

## Leben und Reload timer

```python
from PyQt5.Qt import Qt
from PyQt5.QtGui import QVector2D

class Bar:
    def __init__(self, maxWidth, height, minValue, maxValue, color):
        self.maxWidth = maxWidth
        self.height = height
        self.minValue = minValue
        self.maxValue = maxValue
        self.color = color
        self.pos = QVector2D(0,0)

        self.currentWidth = 0
        self.currentValue = minValue

    def draw(self, qp):

        qp.setBrush(self.color)
        qp.setPen(Qt.black)
        qp.drawRect(self.pos.x() - self.maxWidth / 2, self.pos.y(), self.currentWidth, self.height)

    def update(self, new_value, new_pos):

        self.currentValue = new_value
        self.currentWidth = self.maxWidth * (self.currentValue / (self.maxValue - self.minValue))
        self.pos = new_pos

    def setColor(self, color):
        self.color = color

# Reload Display Options

RELOAD_BAR_HEIGHT = 5
RELOAD_BAR_COLOR = Qt.blue
RELOAD_BAR_Y_BUFFER = 2

class ReloadBar(Bar):
    def __init__(self, timeToReload, maxWidth):
        super().__init__(maxWidth, RELOAD_BAR_HEIGHT, 0, timeToReload, RELOAD_BAR_COLOR)

    def update(self, new_value, new_pos):
        super().update(new_value, new_pos)
        self.pos = QVector2D(new_pos.x(), new_pos.y() + RELOAD_BAR_Y_BUFFER)
```

Die Roboter haben zusätzlich noch einen Lebensbalken. Die update Methode vom Roboter sieht nun so aus:

```python


class BaseRobot(QObject):

  ...

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
