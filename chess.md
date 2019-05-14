# Woche 1: Schachbrett

### [<- Zurück](/index.md) zur Projektübersicht

Hier folgt der Blogeintrag.

```python
def drawChessboard(self, event, qp):

      for column in range(8):
          for row in range(8):
              qp.setBrush(self.getColorForPosition(row, column))
              qp.drawRect(row * TILE_WIDTH,
                          column * TILE_HEIGHT,
                          TILE_WIDTH,
                          TILE_HEIGHT)
```
