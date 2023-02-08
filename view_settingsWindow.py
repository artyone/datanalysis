from PyQt5 import QtWidgets as qtw

class SettingsWindow(qtw.QWidget):
    def __init__(self, controller, parent=None):
        super().__init__()
        self.parent = parent
        self.controller = controller
        self.initUI()

    def initUI(self):
        self.setGeometry(0, 0, 700, 500)
        self.setWindowTitle("Settings menu")
        layout = qtw.QVBoxLayout()
        
        tabWidget = qtw.QTabWidget()
        tabWidget.addTab(self.planeTabUI(), 'Planes')
        
        
        
        saveButton = qtw.QPushButton('Save')
        layout.addWidget(tabWidget)
        layout.addWidget(saveButton)
        self.setLayout(layout)

    def planeTabUI(self):
        planesWidget = qtw.QWidget()
        layoutPlanes = qtw.QVBoxLayout()
        planesComboBox = qtw.QComboBox()
        planesComboBox.addItems(['mdm', 'm2', 'IL78m90a', 'IL76md90a', 'tu22', 'tu160'])
        layoutPlanes.addWidget(planesComboBox)
        planesWidget.setLayout(layoutPlanes)
        return planesWidget