import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from levelLoader import Tile, LevelLoader
from toolbox import minmax


WINDOW_SIZE_X = 1200
WINDOW_SIZE_Y = 1000
NUMBER_OF_TILES = 100
TILE_SIZE = 10

class LevelEditor(QWidget):

    def __init__(self):
        super().__init__()

        self.mouse_x = 0
        self.mouse_y = 0
        self.brushShape = "rect"
        self.brushSize = 3
        self.selected_tile = Tile.grass

        self.levelMatrix = []
        for y in range(NUMBER_OF_TILES):
            self.levelMatrix.append([])
            for x in range(NUMBER_OF_TILES):
                self.levelMatrix[y].append(Tile.grass)

        self.tileTextures = {tileEnum : QPixmap('textures/' + tileName + '.png') for tileName, tileEnum in Tile.__members__.items()}

        self.setTileFunctions = {
            tileName : (lambda x : (lambda : self.setTile(x)))(tileEnum) for tileName, tileEnum in Tile.__members__.items()
        }

        self.initUI()
        self.setMouseTracking(True)


    def initUI(self):
        self.setGeometry(100, 100, WINDOW_SIZE_X, WINDOW_SIZE_Y)
        self.setWindowTitle("Level Editor")
        self.show()

        loadButton = QPushButton("Load", self)
        loadButton.setGeometry(1000, 50, 100, 40)
        loadButton.show()
        loadButton.clicked.connect(self.loadFile)

        saveButton = QPushButton("Save", self)
        saveButton.setGeometry(1100, 50, 100, 40)
        saveButton.show()
        saveButton.clicked.connect(self.saveFile)

        chooseTileButton = QPushButton("Choose Tile", self)
        chooseTileButton.setGeometry(1030, 150, 140, 40)
        chooseTileButton.show()

        tileMenu = QMenu(self)
        for tileName, tileEnum in Tile.__members__.items():
            action = QAction(tileName, self)
            action.setIcon(QIcon("textures/" + tileName + ".png"))
            action.triggered.connect(self.setTileFunctions[tileName])
            tileMenu.addAction(action)

        chooseTileButton.setMenu(tileMenu)

        chooseShapeButton = QPushButton("Choose shape", self)
        chooseShapeButton.setGeometry(1030, 200, 140, 40)
        chooseShapeButton.show()

        shapeMenu = QMenu(self)
        rectAction = QAction('rectangle', self)
        rectAction.triggered.connect(lambda : self.setShape('rect'))
        shapeMenu.addAction(rectAction)
        circleAction = QAction('circle', self)
        circleAction.triggered.connect(lambda : self.setShape('circle'))
        shapeMenu.addAction(circleAction)
        chooseShapeButton.setMenu(shapeMenu)


    def setTile(self, tile):
        self.selected_tile = tile

    def setShape(self, shape):
        self.brushShape = shape

    def loadFile(self):
        url = QFileDialog.getOpenFileUrl(self, "Save File", QDir.currentPath(), "TXT files (*.txt)")
        filePath = url[0].toLocalFile()
        self.levelMatrix, _ = LevelLoader.loadLevel(filePath)

    def saveFile(self):
        url = QFileDialog.getSaveFileUrl(self, "Save File", QDir.currentPath(), "TXT files (*.txt)")
        filePath = url[0].toLocalFile()
        file = open(filePath, "w+")
        for row in self.levelMatrix:
            for tile in row:
                file.write(str(tile.value))
            file.write('\n')
        file.close()

    def fillBrush(self):
        rect = self.mouseRect()
        worldRect = QRectF(rect.x() * TILE_SIZE, rect.y() * TILE_SIZE, rect.width() * TILE_SIZE, rect.height() * TILE_SIZE)

        if self.brushShape == 'rect':
            for x in range(rect.x(), rect.x() + self.brushSize):
                for y in range(rect.y(), rect.y() + self.brushSize):
                    self.levelMatrix[y][x] = self.selected_tile
        elif self.brushShape == 'circle':
            shape = QPainterPath()
            shape.addEllipse(worldRect)
            for x in range(rect.x(), rect.x() + self.brushSize):
                for y in range(rect.y(), rect.y() + self.brushSize):
                    center = QPointF(x * TILE_SIZE + TILE_SIZE / 2, y * TILE_SIZE + TILE_SIZE / 2)
                    if shape.contains(center):
                        self.levelMatrix[y][x] = self.selected_tile

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        self.drawTiles(qp)

        qp.setPen(Qt.blue)

        rect = self.mouseRect()
        worldRect = QRectF(rect.x() * TILE_SIZE, rect.y() * TILE_SIZE, rect.width() * TILE_SIZE, rect.height() * TILE_SIZE)
        if self.brushShape == 'rect':
            qp.drawRect(worldRect)
        elif self.brushShape == 'circle':
            qp.drawEllipse(worldRect)

        qp.end()

    def drawTiles(self, qp):

        qp.setPen(Qt.NoPen)
        for row in range(NUMBER_OF_TILES):
            for column in range(NUMBER_OF_TILES):
                tile = self.levelMatrix[row][column]
                texture = self.tileTextures[tile]
                qp.drawPixmap(column*TILE_SIZE, row*TILE_SIZE, texture)


    def mouseMoveEvent(self, event):
        # check bounds
        minVal = self.brushSize * TILE_SIZE / 2
        maxVal = NUMBER_OF_TILES * TILE_SIZE - minVal
        self.mouse_x = minmax(event.x(), minVal, maxVal)
        self.mouse_y = minmax(event.y(), minVal, maxVal)

        if event.buttons() == Qt.LeftButton:
            self.fillBrush()

        self.update()

    def mousePressEvent(self, event):
        self.fillBrush()
        self.update()

    def wheelEvent(self, event):
        THRESHOLD = 60
        delta_y = event.angleDelta().y() # should be 120 or -120 for a normal mouse
        if delta_y > THRESHOLD:
            self.brushSize += 1
        elif delta_y < -THRESHOLD:
            self.brushSize -= 1
            if self.brushSize < 0:
                self.brushSize = 0

        self.update()

    def mouseRect(self):
        # This is ugly and i dont understand it
        self.x = self.mouse_x + TILE_SIZE / 2
        self.y = self.mouse_y + TILE_SIZE / 2
        topLeft_x = (self.x - self.brushSize * TILE_SIZE / 2) // 10
        topLeft_y = (self.y - self.brushSize * TILE_SIZE / 2) // 10

        return QRect(topLeft_x, topLeft_y, self.brushSize, self.brushSize)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    game = LevelEditor()
    sys.exit(app.exec_())
