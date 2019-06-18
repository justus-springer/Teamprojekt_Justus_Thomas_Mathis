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
      wallsInView = []
      timestamp = QDateTime.currentMSecsSinceEpoch()

      # Special case for runner robot: He sees everything:
      if isinstance(robot, robots.RunnerRobot):
          ids = self.robots.keys()
          wallsInView = self.obstacles
      else:
          # Get ids of all robots that are in view, i.e. that intersect with the view cone
          ids = [id for id in self.robots.keys() if self.robots[id].shape().intersects(cone)]
          wallsInView = [rect for rect in self.obstacles if cone.intersects(rect)]

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
      robot.wallsInViewSignal.emit(wallsInView)

```
Diese Methode wird alle 10 Ticks aufgerufen. Die Signale robotsInViewSignal und wallsInViewSignal sind mit den jeweiligen Controllern der Roboter verbunden.

## Chaser Strategien

Zunächst haben wir einen allgemeinen ChaserController:

```python
# abstract
class ChaseController(Controller):

    def __init__(self, robotId, targetId):
        super().__init__(robotId)

        self.targetId = targetId
        self.lastSighting = {'x' : 500, 'y' : 500, 'pos' : QVector2D(0,0), 'dist' : 0, 'angle' : 0, 'timestamp' : 1000}
        self.previousSighting = {'x' : 501, 'y' : 501, 'pos' : QVector2D(0,0), 'dist' : 0, 'angle' : 0, 'timestamp' : 0}
        self.aimPos = QVector2D(500, 500)
        self.state = "Searching"

    # abstract
    def computeAim(self):
        raise NotImplementedError("Implement this method, stupid!")

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

Der Controller "merkt" sich immer nur die zwei letzten Sichtungen seines Ziels. Sobald die letzte Sichtung über 2 Sekunden her ist, beginnt er, sich auf der Stelle zu drehen und sein Ziel neu zu suchen. Von dieser Klasse erben nun die drei Controller-Klassen: ChaseDirectlyController, ChasePredictController und ChaseGuardController, die die Methode computeAim alle unterschiedlich implementieren:

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
        speed = distanceTravelled / timeDifference

        # Extrapolate the position one second into the FUTURE
        futurePosEstimate = self.lastSighting['pos'] + 1 * speed * direction
        return futurePosEstimate

class ChaseGuardController(ChaseController):

    def computeAim(self):
        middle = QVector2D(500, 500)
        delta_vec = middle - self.lastSighting['pos']
        delta_vec *= 200 / delta_vec.length()

        return self.lastSighting['pos'] + delta_vec

```

ChaseDirectlyController hat als Ziel immer die aktuellste Position des Runners. ChasePredictController versucht, aus den zwei letzten Sichtungen die zukünftige Position des Runners zu extrapolieren. ChaseGuardController versucht, dem Runner den Weg zur Mitte zu versperren.

## Runner Strategie

Der Runner verfolgt seine eigene Strategie. Er hat den Vorteil, immer alle Positionen seiner Verfolger zu kennen:

```python
class RunController(Controller):

    def __init__(self, robotId, targetIds):
        super().__init__(robotId)

        self.targetIds = targetIds

    def run(self):

        while True:

            if self.robotsInView != {}:

                vecs = []
                myPosition = QVector2D(self.x, self.y)

                for id in self.targetIds:
                    robot = self.robotsInView[id]
                    v = (myPosition - robot['pos']).normalized()
                    v *= (1 / robot['dist'])
                    vecs.append(v)

                wall_vecs = []
                distances = []
                for rect in self.wallsInView:

                    rect_center = QVector2D(rect.center().x(), rect.center().y())
                    direction = (myPosition - rect_center).normalized()
                    distance = (myPosition - rect_center).length()

                    if (myPosition - rect_center).length() < 200:
                        wall_vecs.append(direction)
                        distances.append(distance)

                if len(distances) == 0:
                    avg_distance = 1000
                else:
                    avg_distance = sum(distances) / len(distances)

                result_wall_vec = sumvectors(wall_vecs).normalized()
                result_wall_vec *= 3 * (1 / avg_distance) # wall vector counts 3 times as much as a robot
                vecs.append(result_wall_vec)

                direction = sumvectors(vecs).normalized()
                self.moveInDirection(direction)


            self.msleep(DAEMON_SLEEP)

```

## Bessere Kollision

```python
def collisionRadar(self,levelMatrix):
      #Calculate Limits

      x_min = minmax(int((self.x - self.r - COLL_BUFFER) // 10), 0, len(levelMatrix))
      x_max = minmax(int((self.x + self.r + COLL_BUFFER + 1) // 10), 0, len(levelMatrix))
      y_min = minmax(int((self.y - self.r - COLL_BUFFER) // 10), 0, len(levelMatrix))
      y_max = minmax(int((self.y + self.r + COLL_BUFFER + 1) // 10), 0, len(levelMatrix))

      #Fill obstacle list
      obstacles =[]
      for y in range(y_min, y_max):
          for x in range(x_min, x_max):
              if levelMatrix[y][x] == 1:
                  obstacles.append(QRectF(x*10, y*10, 10, 10))

      return obstacles

def collideWithRobots(self, robotList, obstacles):

      for robot in robotList:
          if robot != self:
              # distance to other robot
              distance = (self.pos - robot.pos).length()
              direction = (self.pos - robot.pos).normalized()

              if distance <= self.r + robot.r:
                  overlap = self.r + robot.r - distance

                  if self.collision(obstacles):
                      robot.pos = robot.pos - overlap * direction

                  else:
                      self.pos += overlap / 2 * direction
                      robot.pos = robot.pos - overlap / 2 * direction

```


## Teleportieren und Scoreboard

Die Klasse ChaserRobot erbt von BaseRobot und hat Chaser-spezifische Funktionalitäten: Sobald der Runner berührt wird, teleportiert er sich zu dem Punkt auf der Karte, der die weiteste Distanz zum Runner aufweist.

```python
class ChaserRobot(BaseRobot):

    scoreSignal = pyqtSignal(int)

    def __init__(self, id, spawn_x, spawn_y, targetId, controllerClass):
        super().__init__(id, spawn_x, spawn_y, 30, 150, 30, 0, Qt.gray)
        self.spawn_x = spawn_x
        self.spawn_y = spawn_y

        self.controller = controllerClass(id, targetId)

    def collideWithRobots(self, robotList, obstacles):

        for robot in robotList:
            if robot != self:
                # distance to other robot
                distance = (self.pos - robot.pos).length()
                direction = (self.pos - robot.pos).normalized()

                if distance <= self.r + robot.r:
                    overlap = self.r + robot.r - distance

                    if self.collision(obstacles):
                        robot.pos = robot.pos - overlap * direction

                    else:
                        self.pos += overlap / 2 * direction
                        robot.pos = robot.pos - overlap / 2 * direction

                    # if the other robot was a runner, teleport to your spawn
                    if isinstance(robot, RunnerRobot):
                        self.teleportToFarthestPoint(robot.pos)
                        self.scoreSignal.emit(self.id)

    def teleportToFarthestPoint(self, robot_pos):
        middle = QVector2D(robotGame.WINDOW_SIZE / 2, robotGame.WINDOW_SIZE / 2)
        vec = middle - robot_pos
        vec *= 400 / vec.length()
        self.pos = middle + vec
```

Außerdem wird ein scoreSignal emittiert. Dieses ist mit einem ScoreBoard verbunden, welche für jeden Chaser die "Kills" anzeigt:


```python
class ScoreBoard(QObject):

    def __init__(self):
        super().__init__()
        self.scores = {}

    def draw(self, qp):

        qp.setPen(Qt.black)
        qp.setFont(SCOREBOARD_FONT)
        text = "SCOREBOARD:\n"
        for id in self.scores:
            text += "Chaser {0}: {1}\n".format(id, self.scores[id])

        qp.drawText(QRectF(0, 0, WINDOW_SIZE, 200), Qt.AlignCenter, text)

    ### Slots
    def scoreSignalSlot(self, id):
        if id in self.scores:
            self.scores[id] += 1
        else:
            self.scores[id] = 1
```
