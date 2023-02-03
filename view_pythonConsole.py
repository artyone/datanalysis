import sys
import controller as ctlr
import view_graphWindow as GraphWindow
import view_mapWindow as MapWindow
import view_reportWindow as ReportWindow
import qrc_resources
import pyqtgraph as pg
from PyQt5.sip import delete
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets as qtw
from functools import partial
from notificator import notificator
from notificator.alingments import BottomRight

class ConsoleWindow(qtw.QWidget):
    
    def __init__(self, data, parent):
        super().__init__()
        self.data = data
        self.parent = parent
        self.initUI()

    def initUI(self):
        self.setGeometry(0, 0, 500, 500)
        self.setWindowTitle("Python console")
        self.setLayout(qtw.QVBoxLayout())