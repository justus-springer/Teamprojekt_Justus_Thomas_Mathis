# Woche 2: Roboter

### [<- Zurück](/../index.md) zur Projektübersicht
---

## Roboter

Zuerst programmierten wir das Spielfeld:

```python

self.wallTexture = QPixmap('textures/wall.png')
self.grassTexture = QPixmap('textures/grass.png')
self.mudTexture = QPixmap('textures/mud.png')

...

def drawTiles(self, event, qp):

    qp.setPen(Qt.NoPen)
    for row in range(NUMBER_OF_TILES):
        for column in range(NUMBER_OF_TILES):
            if(self.levelMatrix[row][column] == LevelLoader.WALL_TILE):
                texture = self.wallTexture
            elif(self.levelMatrix[row][column] == LevelLoader.FLOOR_TILE):
                texture = self.grassTexture
            elif(self.levelMatrix[row][column] == LevelLoader.MUD_TILE):
                texture = self.mudTexture

            qp.drawPixmap(column*TILE_SIZE,
                        row*TILE_SIZE,
                        texture)

...


def loadLevel(filePath):
    result = []

    f = open(filePath, "r")
    for i in range(LevelLoader.LEVEL_SIZE):
        line = f.readline()
        row = []
        for c in line:
            if c == '0':
                row.append(LevelLoader.FLOOR_TILE)
            elif c == '1':
                row.append(LevelLoader.WALL_TILE)
            elif c == '2':
                row.append(LevelLoader.MUD_TILE)
            elif c == '\n':
                pass
            else:
                raise Exception('Unknown symbol: "' + c + '" in level "' + filePath + '"')
        result.append(row)

    return result

              
```

Dieser Code zeichnet das Spielfeld mit 100x100 Blöcken:

![](https://raw.githubusercontent.com/justus-springer/Teamprojekt_Justus_Thomas_Mathis/gh-pages/week2/Board.png)


Nach dem Spielfeld zeichneten wir den Roboter:

```python

def draw(self, qp):
    qp.setBrush(QColor(255,255,0))
    qp.setPen(QColor(0,0,0))
    qp.drawEllipse(self.x - self.r, self.y - self.r, 2 * self.r, 2 * self.r)

    # Endpunkte der Linie
    newx = self.r * math.cos(math.radians(self.alpha))
    newy = self.r * math.sin(math.radians(self.alpha))

    qp.drawLine(self.x, self.y, self.x + newx, self.y + newy)

```


![](https://raw.githubusercontent.com/justus-springer/Teamprojekt_Justus_Thomas_Mathis/gh-pages/week2/robot.png)


Zuletzt sorgten wir dafür, dass der Roboter sich über das Feld bewegt:

```python

def update(self):

    # Compute distance to target
    deltaX = self.targetX - self.x
    deltaY = self.targetY - self.y
    dist = math.sqrt(deltaX*deltaX + deltaY*deltaY)

    # Orient yourself toward the target
    self.setAlphaRadians(math.atan2(deltaY, deltaX))

    if dist > TILE_SIZE:
        # Compute normalized direction vector (normalized)
        dirX = math.cos(math.radians(self.alpha))
        dirY = math.sin(math.radians(self.alpha))

        # Move into that direction

        self.x += dirX * self.MOVEMENT_PER_TICK
        self.y += dirY * self.MOVEMENT_PER_TICK

def setAlphaDegrees(self, alpha_degrees):
    self.alpha = alpha_degrees

def setAlphaRadians(self, alpha_radians):
    self.alpha = math.degrees(alpha_radians)

def setTarget(self, targetX, targetY):
    self.targetX = targetX
    self.targetY = targetY

def mousePressEvent(self, event):
    self.myRobot.setTarget(event.x(), event.y())

```

