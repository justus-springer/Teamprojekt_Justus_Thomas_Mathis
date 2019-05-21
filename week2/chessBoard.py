import sys
from PyQt5.QtWidgets import QWidget, QApplication, QLabel
from PyQt5.QtGui import QPainter, QColor, QFont, QIcon, QPixmap
from PyQt5.QtCore import Qt
import math

#Constants:

#Window options
START_WINDOW_WIDTH = 1000
START_WINDOW_HEIGHT = 1000
START_WINDOW_X_POS = 100
START_WINDOW_Y_POS = 50

#Chessboard options
BLACK_COLOR = QColor(0, 0, 0)
WHITE_COLOR = QColor(255, 255, 255)
TILE_WIDTH = 125
TILE_HEIGHT = 125

class ChessBoard(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        self.setGeometry(START_WINDOW_X_POS, START_WINDOW_Y_POS, START_WINDOW_WIDTH, START_WINDOW_HEIGHT)
        self.setWindowTitle('ChessBoard')

        self.queen = Queen(self)

        self.show()

    def mouseMoveEvent(self, e):
        self.queen.moveCenter(e.x(), e.y())

    def mouseReleaseEvent(self, e):
        # Move to nearest whole tile
        newX = e.x() - (e.x() % TILE_WIDTH)
        newY = e.y() - (e.y() % TILE_HEIGHT)
        self.queen.move(newX, newY)

    def paintEvent(self, event):

        qp = QPainter()
        qp.begin(self)
        self.drawChessboard(event, qp)
        qp.end()

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

class Queen(QLabel):

    def __init__(self, parent):
        super().__init__(parent)

        self.setPixmap(QPixmap('queen.png'))

    def moveCenter(self, x, y):
        newX = x - self.width() / 2
        newY = y - self.height() / 2
        self.move(newX, newY)


if __name__ == '__main__':

    app = QApplication(sys.argv)

    chessBoard = ChessBoard()

    sys.exit(app.exec_())
