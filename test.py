import sys

from PyQt5.QtWidgets import QApplication, QMessageBox, QWidget, QPushButton, QToolTip
from PyQt5.QtCore import QSize, QPoint
from PyQt5.QtGui import QIcon, QFont

class Example(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        QToolTip.setFont(QFont('SansSerif', 10))

        self.setToolTip('This is a <b>QWidget</b> widget')

        btn = QPushButton('Button', self)
        btn.setToolTip('This prints "Hello world" to the console')
        btn.clicked.connect(printHelloWorld)
        btn.resize(100, 40)
        btn.move(50, 50)

        quitButton = QPushButton('Quit', self)
        quitButton.setToolTip('This quits the application')
        quitButton.clicked.connect(QApplication.instance().quit)
        quitButton.resize(100, 40)
        quitButton.move(50, 150)

        self.setGeometry(300, 300, 300, 220)
        self.setWindowTitle('Icon')
        self.setWindowIcon(QIcon('weg.png'))

        self.show()

    def closeEvent(self, event):

        reply = QMessageBox(self, 'Message', 'Are you sure to quit?',
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

def printHelloWorld():
    print('Hello world')

def multiplyByTwo(a):
    return 2*a

if __name__ == '__main__':

    app = QApplication(sys.argv)

    print(multiplyByTwo(5))
    example = Example()

    sys.exit(app.exec_())
