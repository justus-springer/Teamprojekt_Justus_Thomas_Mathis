# Woche 1: Schachbrett

### [<- Zurück](/../index.md) zur Projektübersicht
---

## Schachbrettmuster

Donnerstags haben wir uns im Poolraum getroffen um mit PyQt5 etwas rumzuspielen. Dabei ist folgender erster Versuch rausgekommen:

```python
TILE_WIDTH = 50
TILE_HEIGHT = 50
PADDING = 50

...

def paintEvent(self, event):

        qp = QPainter()
        qp.begin(self)
        self.drawRectangles(event, qp)
        qp.end()

def drawRectangles(self, event, qp):

        col = QColor(0, 0, 0)
        col.setNamedColor('#d4d4d4')
        qp.setPen(col)

        qp.setBrush(QColor(200, 0, 0))

        for y in range(8):
            for x in range(8):
                qp.drawRect(PADDING + x * TILE_WIDTH, PADDING + y * TILE_HEIGHT, TILE_WIDTH, TILE_HEIGHT)              
```

Dieser Code zeichnet schonmal ein Muster von 8x8 Rechtecken:

![](https://raw.githubusercontent.com/justus-springer/Teamprojekt_Justus_Thomas_Mathis/gh-pages/week1/Template.png)

Das Problem was wir lösen mussten: Wie macht man es, dass die Farben der Rechtecke sich abwechseln, wie bei einem Schachbrett? Erste schnelle Lösung:

```python
def drawBoard(self, qp):
       black = QColor(0, 0, 0, 255)
       white = QColor(0, 0, 0, 0)
       qp.setPen(black)


       x = 0
       y = 0
       col = white

       for i in range(1, 9):

           for j in range(1, 9):
               qp.setBrush(col)
               qp.drawRect(x, y, 125, 125)

               if (col == black):
                  col = white
               else:
                   col = black

               x = x + 125

           y = y + 125
           x = 0
           if (col == black):
               col = white
           else:
               col = black
```

Hier wird in jedem Schleifendurchgang die Farbe des Painters gewechselt. Das produziert das gewünschte Schachbrettmuster:

![](https://raw.githubusercontent.com/justus-springer/Teamprojekt_Justus_Thomas_Mathis/gh-pages/week1/Schachbrett.PNG)

Dieser Code ist noch nicht optimal lesbar und nicht effizient. Am Ende entschieden wir uns für diese lesbarere Variante:

```python
def drawChessboard(self, event, qp):

    for column in range(8):
        for row in range(8):
            qp.setBrush(self.getColorForPosition(row, column))
            qp.drawRect(row * TILE_WIDTH,
                        column * TILE_HEIGHT,
                        TILE_WIDTH,
                        TILE_HEIGHT)

def getColorForPosition(self, x, y):
    if (x + y) % 2 == 0:
        return WHITE_COLOR
    else:
        return BLACK_COLOR
```

In dieser Version gibt es eine Hilfsfunktion *getColorForPosition(x, y)*  die für zwei Koordinaten x und y entscheidet, ob das Feld schwarz oder weiß werden soll.

## Königin

Als zusätzliches Feature haben wir noch eine Königin eingebaut, die sich auf dem Schachfeld bewegen kann:

```python
class Queen(QLabel):

    def __init__(self, parent):
        super().__init__(parent)

        self.setPixmap(QPixmap('queen.png'))

    def moveCenter(self, x, y):
        newX = x - self.width() / 2
        newY = y - self.height() / 2
        self.move(newX, newY)
```

Zu Beginn wird ein Objekt dieser Klasse initialisiert. In der Hauptklasse müssen dann noch die Methoden implementiert werden, die mit Mausbewegungen und Klicks umgehen:

```python
def mouseMoveEvent(self, e):
        self.queen.moveCenter(e.x(), e.y())

def mouseReleaseEvent(self, e):
        # Move to nearest whole tile
        newX = e.x() - (e.x() % TILE_WIDTH)
        newY = e.y() - (e.y() % TILE_HEIGHT)
        self.queen.move(newX, newY)
```

*mouseMoveEvent*  wird immer dann aufgerufen, wenn die Maus sich bewegt und die Maustaste gedrückt ist. Dadurch folgt die Königin der Maus und kann sich per "Drag and Drop" bewegen.
*mouseReleaseEvent*  wird aufgerufen wenn der Mauszeiger losgelassen wird. Dann wird die Königin auf das Schachfeld gesetzt, was dem Mauszeiger am nächsten ist.
