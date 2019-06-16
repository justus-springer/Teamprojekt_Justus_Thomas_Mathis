# Woche 5: Verfolgungsjagd

### [<- Zurück](/../index.md) zur Projektübersicht
---

## Sichtkegel
Die Roboter sollen von nun an einen "Sichtkegel" besitzen, das heißt sie sehen nur noch diejenigen Roboter und Wände, die sich vor ihnen befinden. Um zu überprüfen, welche Roboter im Sichtkegel sind, benutzen wir die Klasse QPainterPath. Ein QPainterPath ist ein allgemeines geometrisches Objekt, das aus Polygonen, Linien und Kreisen besteht. Mit QPainterPath.intersects(...) kann überprüft werden, ob zwei QPainterPath's sich überschneiden.

```python

class BaseRobot(QObject):

    ...

    def shape(self):
        shape = QPainterPath()
        shape.addEllipse(self.boundingRect())
        return shape

    def view_cone(self):
        a = self.pos.toPointF()
        b = a + QPointF(5000 * math.cos(math.radians(self.alpha + self.aov)),
                    5000 * math.sin(math.radians(self.alpha + self.aov)))
        c = a + QPointF(5000 * math.cos(math.radians(self.alpha - self.aov)),
                    5000 * math.sin(math.radians(self.alpha - self.aov)))
        return QPolygonF([a, b, c])

    def view_cone_path(self):
        path = QPainterPath()
        path.addPolygon(self.view_cone())
        return path

    def drawDebugLines(self, qp):
        qp.setBrush(QBrush(Qt.NoBrush))
        qp.setPen(Qt.red)
        qp.drawConvexPolygon(self.view_cone())

```
Jeder Roboter hat ein Attribut self.aov (angle of view). Mit diesen Hilfsmethoden werden QPainterPath's für den Roboter und sein Sichtfeld generiert. Die Methode drawDebugLines zeichnet die Sichtkegel der Roboter.
