from os import startfile
from PyQt5 import QtWidgets as qtw


class MapWindow(qtw.QWidget):

    def __init__(self, controller, parent=None):
        super().__init__()
        self.parent = parent
        self.controller = controller
        self.settings = self.parent.settings
        self.initUI()

    def initUI(self):
        self.setGeometry(0, 0, 300, 150)
        self.setWindowTitle("Create map")
        dlgLayout = qtw.QVBoxLayout()
        formLayout = qtw.QFormLayout()
        formLayout.setVerticalSpacing(20)
        self.jvdHMinLineEdit = qtw.QLineEdit(
            self.settings.value('map')['jvdHMin'])
        self.decimationLineEdit = qtw.QLineEdit(
            self.settings.value('map')['decimation'])
        formLayout.addRow("JVD_H min:", self.jvdHMinLineEdit)
        formLayout.addRow("decimation:", self.decimationLineEdit)
        self.btnBox = qtw.QDialogButtonBox()

        self.btnBox.setStandardButtons(qtw.QDialogButtonBox.Open |
                                       qtw.QDialogButtonBox.Save |
                                       qtw.QDialogButtonBox.Cancel)
        self.btnBox.rejected.connect(self.close)

        self.openButton = self.btnBox.button(qtw.QDialogButtonBox.Open)
        self.openButton.clicked.connect(self.openFile)
        self.openButton.hide()

        saveButton = self.btnBox.button(qtw.QDialogButtonBox.Save)
        saveButton.clicked.connect(self.getMapEvent)
        dlgLayout.addLayout(formLayout)
        dlgLayout.addWidget(self.btnBox)
        self.setLayout(dlgLayout)

    def getMapEvent(self):
        options = qtw.QFileDialog.Options()
        self.filePath, _ = qtw.QFileDialog.getSaveFileName(self,
                                                           "Save File", "", "html Files (*.html);;All Files(*)", options=options)
        if self.filePath:
            try:
                self.controller.save_map(self.filePath,
                                         self.jvdHMinLineEdit.text(),
                                         self.decimationLineEdit.text())
                self.openButton.show()
                self.settings.setValue('map', {
                    'jvdHMin': self.jvdHMinLineEdit.text(),
                    'decimation': self.decimationLineEdit.text()
                })
                self.parent.setNotify(
                    'success', f'html file saved to {self.filePath}')

            except PermissionError:
                self.parent.setNotify(
                    'error', 'File opened in another program')
            except Exception as e:
                self.parent.setNotify('error', str(e))

    def openFile(self):
        startfile(self.filePath)
        self.close()
