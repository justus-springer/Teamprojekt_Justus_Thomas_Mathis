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

        # Get myself a queen
        self.queen = QLabel(self)
        self.queen.setPixmap(QPixmap('queen.png'))
        # Remain hidden until the first mouse click
        self.queen.hide()

        self.show()

    def mousePressEvent(self, e):

        # Show youself
        self.queen.show()

        # Fetch the x and y coordinate of the mouse click
        x = e.x()
        y = e.y()

        # Compute the row and column number of the mouse click
        column = (x - (x % TILE_WIDTH)) / TILE_WIDTH
        row = (y - (y % TILE_HEIGHT)) / TILE_HEIGHT

        self.queen.move(column * TILE_WIDTH, row * TILE_HEIGHT)

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


if __name__ == '__main__':

    app = QApplication(sys.argv)

    chessBoard = ChessBoard()

    sys.exit(app.exec_())
