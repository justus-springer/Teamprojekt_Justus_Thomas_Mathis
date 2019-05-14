# Woche 1: Schachbrett

### [<- Zurück](/index.md) zur Projektübersicht
---

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
