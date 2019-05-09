import sys
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QColor, QFont, QIcon
from PyQt5.QtCore import Qt

BLACK_COLOR = QColor(0, 0, 0)
WHITE_COLOR = QColor(255, 255, 255)

TILE_WIDTH = 50
TILE_HEIGHT = 50
PADDING = 50

class ChessBoard(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        self.setGeometry(300, 300, 500, 500)
        self.setWindowTitle('ChessBoard')
        self.show()

    def paintEvent(self, event):

        qp = QPainter()
        qp.begin(self)
        self.drawRectangles(event, qp)
        qp.end()

    def drawRectangles(self, event, qp):

        # this is for outlines
        qp.setPen(BLACK_COLOR)

        for y in range(8):
            for x in range(8):
                qp.setBrush(self.getColorForPosition(x, y))
                qp.drawRect(PADDING + x * TILE_WIDTH,
                            PADDING + y * TILE_HEIGHT,
                            TILE_WIDTH,
                            TILE_HEIGHT)



    def getColorForPosition(self, x, y):
        if (x+y) % 2 == 0:
            return WHITE_COLOR
        else:
            return BLACK_COLOR

if __name__ == '__main__':

    app = QApplication(sys.argv)

    chessBoard = ChessBoard()

    sys.exit(app.exec_())
