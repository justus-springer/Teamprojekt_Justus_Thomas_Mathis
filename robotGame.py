import sys
from PyQt5.QtWidgets import QWidget, QApplication, QLabel
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtCore import Qt, QBasicTimer
from BaseRobot import BaseRobot
import numpy as np
import math


#Window options

START_WINDOW_WIDTH = 1000
START_WINDOW_HEIGHT = 1000
START_WINDOW_X_POS = 100
START_WINDOW_Y_POS = 50
WINDOW_TITLE = "Cooles Spiel"

#Playground options

PG_SIZE = 100
WALL_TILE_COLOR = QColor(0, 0, 0)
FLOOR_TILE_COLOR = QColor(255, 255, 255)
TILE_SIZE = 10

FPS = 60
TIMER_INTERVAL = int(1000 / FPS)

class RobotGame(QWidget):

    def __init__(self):
        super().__init__()
        #Initilalizie Plaground 100x100 matrix with zeros
        self.matrix = np.zeros((PG_SIZE,PG_SIZE))
        self.initializeWalls()
        self.initUI()

        self.gameTimer = QBasicTimer()
        self.gameTimer.start(TIMER_INTERVAL, self)

        self.myRobot = BaseRobot(100, 100, 25, 0)


    def initUI(self):

        self.setGeometry(START_WINDOW_X_POS, START_WINDOW_Y_POS, START_WINDOW_WIDTH, START_WINDOW_HEIGHT)
        self.setWindowTitle(WINDOW_TITLE)
        self.show()

    def paintEvent(self, event):

        qp = QPainter()
        qp.begin(self)
        self.drawTiles(event, qp)
        self.myRobot.draw(qp)
        qp.end()

    def initializeWalls(self):

        #initialize east and west walls
        for row in range(PG_SIZE):
            self.matrix[row,0] = 1
            self.matrix[row,PG_SIZE-1] = 1
        #initialize south and north walls
        for column in range(PG_SIZE):
            self.matrix[0,column] = 1
            self.matrix[PG_SIZE-1,column] = 1

    def drawTiles(self, event, qp):

        for column in range(PG_SIZE):
            for row in range(PG_SIZE):
                if(self.matrix[column,row] == 1):
                    qp.setBrush(WALL_TILE_COLOR)
                else:
                    qp.setBrush(FLOOR_TILE_COLOR)

                qp.drawRect(column*TILE_SIZE,
                            row*TILE_SIZE,
                            TILE_SIZE,
                            TILE_SIZE)

    def timerEvent(self, event):

        if event.timerId() == self.gameTimer.timerId():
            self.myRobot.update()
            super().update()


if __name__ == '__main__':

    app = QApplication(sys.argv)

    game = RobotGame()

    sys.exit(app.exec_())
