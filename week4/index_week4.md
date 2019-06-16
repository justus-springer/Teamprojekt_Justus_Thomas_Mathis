# Woche 4: Kollision und Verfolgen

### [<- Zurück](/../index.md) zur Projektübersicht
---

## Kollision und Verfolgen



aimAt lässt den Roboter ein bestimmtes Ziel anpeilen:

```python

def aimAt(self, target_x, target_y):

        delta_x = target_x - self.crnt_x
        delta_y = target_y - self.crnt_y
        target_alpha = math.degrees(math.atan2(delta_y, delta_x)) % 360

        delta_alpha = (target_alpha - self.crnt_alpha) % 360

        # Do we need to move clockwise or counterclockwise?
        if delta_alpha > 180:
            counterclockwise = True
            delta_alpha = 360 - delta_alpha
        else:
            counterclockwise = False

        if delta_alpha < robots.EPSILON_ALPHA and self.crnt_v_alpha < robots.EPSILON_V_ALPHA:
            # If we are at the target, don't accelerate
            self.a_alpha = 0
            self.fullStopRotationSignal.emit()
        else:
	    stopping_distance = self.crnt_v_alpha*self.crnt_v_alpha / (2 * self.a_alpha_max) + robots.EPSILON_POS

            if delta_alpha <= stopping_distance:
                # In this case, brake
                if self.crnt_v_alpha > 0:
                    self.a_alpha = -self.a_alpha_max
                else:
                    self.a_alpha = self.a_alpha_max
            else:
                # In this case, accelerate
                if counterclockwise:
                    self.a_alpha = -self.a_alpha_max
                else:
                    self.a_alpha = self.a_alpha_max

```

### Controller

Dieser Code steuert das Verhalten des Verfolger-Robot:

```python

class FollowController(Controller):

    def __init__(self, robotId, targetId):
        super().__init__(robotId)

        self.targetId = targetId
        self.target_x = 0
        self.target_y = 0

    def run(self):

        self.a = self.a_max

        while True:
            if self.targetId in self.positionsData:
                self.target_x = self.positionsData[self.targetId]['x']
                self.target_y = self.positionsData[self.targetId]['y']

            self.aimAt(self.target_x, self.target_y)

            self.msleep(100)

```

Hier wird der Roboter, der verfolgt wird und "weglaufen" soll gesteuert:

```python

class runController(Controller):

    def __init__(self, robotId, targetId):
        super().__init__(robotId)

        self.target_x = 0
        self.target_y = 0
        self.targetId = targetId

    def run(self):

        self.a = self.a_max

        while True:

            if self.crnt_x > 800 or self.crnt_x < 200 or self.crnt_y > 800 or self.crnt_y < 200:
                self.target_x = 500
                self.target_y = 500

            elif self.targetId in self.positionsData:
                self.target_x = self.crnt_x + (self.crnt_x - self.positionsData[self.targetId]['x'])
                self.target_y = self.crnt_y + (self.crnt_y - self.positionsData[self.targetId]['y'])

            self.aimAt(self.target_x, self.target_y)
            self.msleep(100)

```

### Kollision

In diesem Codeabschnitt wird die Kollision mit Wänden implementiert:

```python

def collideWithWalls(self, obstacles):

        for rect in obstacles:
            rect_center = QVector2D(rect.center())
            vec = self.pos - rect_center
            length = vec.length()
            # scale the vector so it has length l-r
            vec *= (length-self.r) / length
            # This is the point of the robot which is closest to the rectangle
            point = (rect_center + vec).toPointF()
            if rect.contains(point):
                if self.x() >= rect_center.x() and self.y() >= rect_center.y():
                    corner = rect.bottomRight()
                elif self.x() >= rect_center.x() and self.y() <= rect_center.y():
                    corner = rect.topRight()
                elif self.x() <= rect_center.x() and self.y() >= rect_center.y():
                    corner = rect.bottomLeft()
                elif self.x() <= rect_center.x() and self.y() <= rect_center.y():
                    corner = rect.topLeft()

                overlap = corner - point

                if math.fabs(overlap.x()) > math.fabs(overlap.y()):
                    self.translate(0, overlap.y())
                else:
                    self.translate(overlap.x(), 0)

                # Set speed to zero (almost)
                self.v = EPSILON_V

```
