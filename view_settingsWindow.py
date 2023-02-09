from typing import LiteralString
from PyQt5 import QtWidgets as qtw
from PyQt5.QtCore import Qt

class SettingsWindow(qtw.QWidget):
    def __init__(self, controller, parent=None):
        super().__init__()
        self.parent = parent
        self.settings = self.parent.settings
        self.listPlanes = self.settings.value('planes')
        self.listCorrections = self.settings.value('corrections')
        self.listGraphs = self.settings.value('graphs')
        self.controller = controller
        self.initUI()

    def initUI(self):
        self.setGeometry(0, 0, 700, 500)
        self.setWindowTitle("Settings menu")
        layout = qtw.QVBoxLayout()
        tabWidget = qtw.QTabWidget()
        tabWidget.addTab(self.planeTab(), 'Planes')
        tabWidget.addTab(self.correctionTab(), 'Corrections')
        tabWidget.addTab(self.graphTab(), 'Graph')
        saveButton = qtw.QPushButton('Save')
        saveButton.clicked.connect(self.saveSettings)
        layout.addWidget(tabWidget)
        layout.addWidget(saveButton)
        self.setLayout(layout)

    def planeTab(self):
        tabWidget = qtw.QWidget()
        tabLayout = qtw.QVBoxLayout()
        self.planesComboBox = qtw.QComboBox()
        self.planesComboBox.addItems(self.listPlanes)
        self.planesComboBox.activated.connect(self.switchPage)
        tabLayout.addWidget(self.planesComboBox, alignment=Qt.AlignTop)
        tabWidget.setLayout(tabLayout)
        self.stackedLayout = qtw.QStackedLayout()
        for plane in self.listPlanes:
            self.stackedLayout.addWidget(self.pagePlaneStacked(plane))

        tabLayout.addLayout(self.stackedLayout)
        return tabWidget

    def pagePlaneStacked(self, plane):
        '''
        Создает страницу настроек для вкладки самолета.
        Значения берет из настроек и записывает объект в словарь listPlanes 
        для последующего быстрого сохранения
        '''
        pageWidget = qtw.QWidget()
        pageLayout = qtw.QFormLayout()
        for param, value in self.settings.value('planes')[plane].items():
            lineEdit = qtw.QLineEdit(str(value))
            pageLayout.addRow(param, lineEdit)
            self.listPlanes[plane][param] = lineEdit
        pageWidget.setLayout(pageLayout)
        return pageWidget

    def correctionTab(self):
        tabWidget = qtw.QWidget()
        tabLayout = qtw.QFormLayout()
        for correction, value in self.listCorrections.items():
            lineEdit = qtw.QLineEdit(str(value))
            tabLayout.addRow(correction, lineEdit)
            self.listCorrections[correction] = lineEdit
        tabWidget.setLayout(tabLayout)
        return tabWidget

    def graphTab(self):
        tabWidget = qtw.QWidget()
        tabLayout = qtw.QFormLayout()
        for graph, value in self.listGraphs.items():
            if graph == 'default':
                value = ','.join(['+'.join(i) for i in value])
            lineEdit = qtw.QLineEdit(str(value))
            tabLayout.addRow(graph, lineEdit)
            self.listGraphs[graph] = lineEdit
        tabWidget.setLayout(tabLayout)
        return tabWidget

    def switchPage(self):
        self.stackedLayout.setCurrentIndex(self.planesComboBox.currentIndex())

    def saveSettings(self):
        newValuePlanes = {
            plane: {
                param: float(widget.text()) 
                for param, widget in value.items()
            }
            for plane, value in self.listPlanes.items()
        }
        self.settings.setValue('planes', newValuePlanes)
        newValueCorrections = {
            correction: float(widget.text())
            for correction, widget in self.listCorrections.items()
        }
        self.settings.setValue('corrections', newValueCorrections)
        newValueGraphs = {
            graphs: (widget.text() 
            if graphs != 'default' 
            else [i.split('+') for i in widget.text().replace(' ', '').split(',')])
            for graphs, widget in self.listGraphs.items()
        }
        self.settings.setValue('graphs', newValueGraphs)
        self.parent.setNotify('success', 'Settings saved')