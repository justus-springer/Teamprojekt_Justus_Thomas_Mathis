# Woche 5: Verfolgungsjagd

### [<- Zurück](/../index.md) zur Projektübersicht
---

## Sichtkegel
Die Roboter sollen von nun an einen "Sichtkegel" besitzen, das heißt sie sehen nur noch diejenigen Roboter und Wände, die sich vor ihnen befinden. Um zu überprüfen, welche Roboter im Sichtkegel sind, benutzen wir die Klasse QPainterPath. Ein QPainterPath ist ein allgemeines geometrisches Objekt, das aus Polygonen, Linien und Kreisen besteht. Mit QPainterPath.intersects(...) kann überprüft werden, ob zwei QPainterPath's sich überschneiden.

```python

class BaseRobot(QObject):

    ...
    def boundingRect(self):
        return QRectF(self.x - self.r, self.y - self.r, 2*self.r, 2*self.r)

    def shape(self):
        shape = QPainterPath()
        shape.addEllipse(self.boundingRect())
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

      def drawDebugLines(self, qp):
          qp.setBrush(QBrush(Qt.NoBrush))
          qp.setPen(Qt.red)
          qp.drawPath(self.view_cone())

```
Jeder Roboter hat ein Attribut self.aov (angle of view). Mit diesen Hilfsmethoden werden QPainterPath's für den Roboter und sein Sichtfeld generiert. Die Methode drawDebugLines zeichnet die Sichtkegel der Roboter. Mit diesen Methoden kann man nun den Robotern ihre Sensordaten übermitteln:

```python
def emitRobotSensorData(self, robot):

      cone = robot.view_cone()
      robotsInView = {}
      wallsInView = {}
      timestamp = QDateTime.currentMSecsSinceEpoch()

      # Special case for runner robot: He sees everything:
      if isinstance(robot, robots.RunnerRobot):
          ids = self.robots.keys()
      else:
          # Get ids of all robots that are in view, i.e. that intersect with the view cone
          ids = [id for id in self.robots.keys() if self.robots[id].shape().intersects(cone)]

      for id in ids:
          other = self.robots[id]
          dist = (robot.pos - other.pos).length()
          angle = math.degrees(math.atan2(other.y - robot.y, other.x - robot.x))
          robotsInView[id] = {'x' : other.x,
                              'y' : other.y,
                              'pos' : QVector2D(other.x, other.y),
                              'dist' : dist,
                              'angle' : angle,
                              'timestamp' : timestamp}

      robot.robotsInViewSignal.emit(robotsInView)

      walls = [rect for rect in self.obstacles if cone.intersects(rect)]

      robot.wallsInViewSignal.emit(walls)

```
Diese Methode wird alle 10 Ticks aufgerufen. Die Signale robotsInViewSignal und wallsInViewSignal sind mit den jeweiligen Controllern der Roboter verbunden.

## Chaser Strategien

Zunächst haben wir einen allgemeinen ChaserController:

```python
class ChaseController(Controller):

    def __init__(self, robotId, targetId):
        super().__init__(robotId)

        self.targetId = targetId
        self.lastSighting = {'x' : 500, 'y' : 500, 'pos' : QVector2D(0,0), 'dist' : 0, 'angle' : 0, 'timestamp' : 1000}
        self.previousSighting = {'x' : 501, 'y' : 501, 'pos' : QVector2D(0,0), 'dist' : 0, 'angle' : 0, 'timestamp' : 0}
        self.aimPos = QVector2D(500, 500)
        self.state = "Searching"

    # This should be implemented by any inheriting class
    # returns the position to aim at
    def computeAim(self):
        return QVector2D(500, 500) # dummy

    def updateLastSighting(self):

        # if the last sighting is older than 2 seconds, return to Searching
        current_time = QDateTime.currentMSecsSinceEpoch()
        if current_time > self.lastSighting['timestamp'] + 2000:
            self.state = "Searching"

        if self.targetId in self.robotsInView:
            self.state = "Chasing"
            newSighting = self.robotsInView[self.targetId]

            # id this sighting is newer than the old one
            if newSighting['timestamp'] > self.lastSighting['timestamp']:
                self.previousSighting = self.lastSighting
                self.lastSighting = newSighting

    def run(self):

        while True:

            self.updateLastSighting()

            self.aimPos = self.computeAim()

            if self.state == "Searching":

                self.moveAtSpeed(0)
                self.rotateAtSpeed(100)

            elif self.state == "Chasing":

                self.moveTo(self.aimPos.x(), self.aimPos.y())

            self.msleep(DAEMON_SLEEP)
```

Der Controller "merkt" sich immer nur die zwei letzten Sichtungen seines Ziels. Sobald die letzte Sichtung über 2 Sekunden her ist, beginnt er, sich auf der Stelle zu drehen und sein Ziel neu zu suchen. Von dieser Klasse erben nun die drei Controller-Klassen: ChaseDirectlyController, ChasePredictController und ChaseFollowController, die die Methode computeAim alle unterschiedlich implementieren:

```python

class ChaseDirectlyController(ChaseController):

    def computeAim(self):
        return self.lastSighting['pos']

class ChasePredictController(ChaseController):

    def computeAim(self):

        delta_vec = self.lastSighting['pos'] - self.previousSighting['pos']
        timeDifference = (self.lastSighting['timestamp'] - self.previousSighting['timestamp']) / 1000
        direction = delta_vec.normalized()
        distanceTravelled = delta_vec.length()

        if timeDifference != 0:
            speed = distanceTravelled / timeDifference
            # Compute the future position estimate in one second
            futurePosEstimate = self.lastSighting['pos'] + 1 * speed * direction

            return futurePosEstimate
        else:
            return QVector2D(500, 500)

```

ChaseDirectlyController hat als Ziel immer die aktuellste Position des Runners. ChasePredictController versucht, aus den zwei letzten Sichtungen die zukünftige Position des Runners zu extrapolieren. ChaseFollowController "extrapoliert" in die Vergangenheit.

## Runner Strategie

Der Runner verfolgt seine eigene Strategie. Er hat den Vorteil, immer alle Positionen seiner Verfolger zu kennen:

```python
class RunController(Controller):

    ...

```

## Bessere Kollision

...

## Teleportieren und Scoreboard

...
