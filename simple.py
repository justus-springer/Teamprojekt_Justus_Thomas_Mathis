#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
ZetCode PyQt5 tutorial 

In this example, we create a simple
window in PyQt5.

Author: Justus Springer
Website: zetcode.com 
Last edited: August 2017
"""

import sys
from PyQt5.QtWidgets import QApplication, QWidget

WINDOW_WIDTH = 250
WINDOW_HEIGHT = 150

if __name__ == '__main__':
    
    app = QApplication(sys.argv)

    w = QWidget()
    w.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
    w.move(300, 300)
    w.setWindowTitle('Simple')
    w.show()
    
    print('Hello world')
    
    sys.exit(app.exec_())
