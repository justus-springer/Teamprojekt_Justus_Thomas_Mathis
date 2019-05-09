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

        col = QColor(0, 0, 0)
        col.setNamedColor('#d4d4d4')
        qp.setPen(col)

        qp.setBrush(QColor(200, 0, 0))

        for y in range(8):
            for x in range(8):
                qp.drawRect(PADDING + x * TILE_WIDTH, PADDING + y * TILE_HEIGHT, TILE_WIDTH, TILE_HEIGHT)


if __name__ == '__main__':

    app = QApplication(sys.argv)

    chessBoard = ChessBoard()

    sys.exit(app.exec_())
