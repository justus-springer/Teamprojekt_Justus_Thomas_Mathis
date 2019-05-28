# Woche 2: Roboter und Threads

### [<- Zurück](/../index.md) zur Projektübersicht
---

## Roboter und Threads



Durch den neuen Timer wird in jedem Schritt die Zeit gemessen, die seit dem letzten Tick vergangen ist und an den Roboter übergeben.

```python

    def timerEvent(self, event):

        elapsed = self.elapsedTimer.elapsed()
        deltaTimeMillis = elapsed - self.previous
        deltaTime = deltaTimeMillis / MILLISECONDS_PER_SECOND

        if event.timerId() == self.gameTimer.timerId():
            for robot in self.robots:
                robot.update(deltaTime)
            self.update()

self.previous = elapsed

```
Jeder Roboter bekommt nun ein Attribut vom Typ "Behaviour". Dies ist der Thread in dem der Roboter seine Bewegungen steuert.

```python

class Behaviour(QThread):

    def __init__(self, robot):
        super().__init__()
        self.robot = robot

        # These will be fetched by the main program
        self.a = 0
        self.a_alpha = 0

        self.a_max = self.robot.get_a_max()
        self.a_alpha_max = self.robot.get_a_alpha_max()

  def fetchValues(self):
	      return self.a, self.a_alpha


def setBehaviour(self, behaviour):
        self.behaviour = behaviour

def startBehaviour(self):
	      self.behaviour.start()

```
In der update Methode des Roboters werden die Werte a und a_alpha nun vom Thread abgefragt und die neuen Geschwindigkeiten und Positionen berechnet.

```python

 def update(self, deltaTime):

        # Fetch acceleration values from your thread
        self.a, self.a_alpha = self.behaviour.fetchValues()
        # But not too much
        self.a = min(self.a, self.a_max)
        self.a = max(self.a, -self.a_max)
        self.a_alpha = min(self.a_alpha, self.a_alpha_max)
        self.a_alpha = max(self.a_alpha, -self.a_alpha_max)

        # Apply acceleration
        self.v += self.a * deltaTime
        self.v_alpha += self.a_alpha * deltaTime
        # But not too much
        self.v = min(self.v, self.v_max)
        self.v = max(self.v, -self.v_max)
        self.v_alpha = min(self.v_alpha, self.v_alpha_max)
        self.v_alpha = max(self.v_alpha, -self.v_alpha_max)

        # Compute direction vector (normalized)
        direction = QVector2D(math.cos(math.radians(self.alpha)),
                              math.sin(math.radians(self.alpha)))

        # Apply velocity
        self.pos += self.v * deltaTime * direction
        self.alpha += self.v_alpha * deltaTime

        self.collideWithRobots(robotList)

```
Hier sind drei einfache Beispiel-Behaviours:

```python

class BackAndForthBehaviour(Behaviour):

    def run(self):

        self.a = self.a_max

        while True:
            if self.robot.x() >= 700:
                self.a = -self.a_max
            elif self.robot.x() <= 300:
                self.a = self.a_max

            self.msleep(100)


class CircleBehaviour(Behaviour):

    def run(self):

        self.a = self.a_max
        self.a_alpha = self.a_alpha_max
        self.msleep(500)
        self.a_alpha = 0


class RandomBehaviour(Behaviour):

    def __init__(self, robot, volatility):
        super().__init__(robot)
        self.volatility = volatility

    def run(self):

        while True:
            # sleep random amount of time
            self.msleep(random.randrange(500, 1000))
            # set acceleration randomly
            self.a = random.uniform(-self.volatility * self.a_max, self.volatility * self.a_max)
            self.a_alpha = random.uniform(-self.volatility * self.a_alpha_max, self.volatility * self.a_alpha_max)


```
Als zusätzliches Feature haben wir Kollision zwischen Robotern eingefügt:

```python
def collideWithRobots(self, robotList):

        for robot in robotList:
            if robot != self:
                # distance to other robot
                distance = (self.pos - robot.get_pos()).length()
                direction = (self.pos - robot.get_pos()).normalized()

                if distance <= self.r + robot.get_r():
                    overlap = self.r + robot.get_r() - distance
                    self.pos += overlap / 2 * direction
                    robot.set_pos(robot.get_pos() - overlap / 2 * direction)
```

```python

class TargetBehaviour(Behaviour):

    def __init__(self, robot):
        super().__init__(robot)
        self.target_x = robot.x()
        self.target_y = robot.y()

    def setNewTarget(self, target_x, target_y):
        self.target_x = target_x
        self.target_y = target_y

    def run(self):

        while True:

            # Get current values
            crnt_x = self.robot.x()
            crnt_y = self.robot.y()
            crnt_v = self.robot.get_v()
            delta_x = self.target_x - crnt_x
            delta_y = self.target_y - crnt_y
            delta_dist = math.sqrt(delta_x*delta_x + delta_y*delta_y)
            target_alpha = math.degrees(math.atan2(delta_y, delta_x))

            crnt_v_alpha = self.robot.get_v_alpha()
            crnt_alpha = self.robot.get_alpha()
            delta_alpha = math.fabs(target_alpha - crnt_alpha)

            # Target is reached
            if (delta_alpha < EPSILON_POS and
                math.fabs(crnt_v) < EPSILON_V):

                break

            # This is the remaining distance travelled if the robot starts braking now
            # EPSILON_POS is added as a buffer so he doesn't overshoot
            threshold_dist = crnt_v*crnt_v / (2 * self.a_max) + EPSILON_POS

            if delta_dist <= threshold_dist:
                self.brake()
            else:
                self.accel()

            threshold_alpha = crnt_v_alpha*crnt_v_alpha / (2 * self.a_alpha_max)

            if delta_alpha <= threshold_alpha:
                self.brake_alpha()
            else:
                self.accel_alpha(target_alpha)

            self.msleep(50)


        self.a_alpha = 0
        self.a = 0
        self.robot.fullStopRotation()
        self.robot.fullStop()


    def brake_alpha(self):
        crnt_v_alpha = self.robot.get_v_alpha()
        if crnt_v_alpha > EPSILON_V_ALPHA:
            self.a_alpha = -self.a_alpha_max
        elif crnt_v_alpha < EPSILON_V_ALPHA:
            self.a_alpha = self.a_alpha_max
        else:
            self.a_alpha = 0

    def accel_alpha(self, target_alpha):
        if target_alpha > self.robot.get_alpha():
            self.a_alpha = self.a_alpha_max
        else:
            self.a_alpha = -self.a_alpha_max

    def brake(self):
        crnt_v = self.robot.get_v()
        if crnt_v > EPSILON_V:
            self.a = -self.a_max
        elif crnt_v < EPSILON_V:
            self.a = self.a_max
        else:
            self.a = 0

    def accel(self):
        self.a = self.a_max

```
