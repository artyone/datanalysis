from os import startfile
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets as qtw
from qtwidgets import AnimatedToggle


class ReportWindow(qtw.QWidget):

    def __init__(self, controller, parent=None) -> None:
        super().__init__()
        self.parent = parent
        self.controller = controller
        self.intervalsTxt = None
        self.initUI()

    def initUI(self):
        self.setGeometry(0, 0, 500, 500)
        self.setWindowTitle("Create report")
        self.setLayout(qtw.QVBoxLayout())

        formLayout = qtw.QFormLayout()
        horizontalLayout = qtw.QHBoxLayout()

        self.intervalsToggle = AnimatedToggle()
        self.intervalsToggle.setChecked(True)
        self.intervalsToggle.stateChanged.connect(self.addFormTxt)
        self.intervalsTxt = qtw.QPlainTextEdit()

        self.btnBox = qtw.QDialogButtonBox()

        self.btnBox.setStandardButtons(qtw.QDialogButtonBox.Open |
                                       qtw.QDialogButtonBox.Save |
                                       qtw.QDialogButtonBox.Cancel)
        self.btnBox.rejected.connect(self.close)

        self.openButton = self.btnBox.button(qtw.QDialogButtonBox.Open)
        self.openButton.clicked.connect(self.openFile)
        self.openButton.hide()

        saveButton = self.btnBox.button(qtw.QDialogButtonBox.Save)
        saveButton.clicked.connect(self.getReportEvent)

        horizontalLayout.addWidget(qtw.QLabel('<b>Intervals:</b>'), 2)
        horizontalLayout.addWidget(qtw.QLabel('auto'), 1,
                                   alignment=Qt.AlignRight)
        horizontalLayout.addWidget(self.intervalsToggle, 1)
        horizontalLayout.addWidget(qtw.QLabel('manual'), 2)

        formLayout.addRow(horizontalLayout)
        formLayout.addRow(self.intervalsTxt)

        self.layout().addLayout(formLayout, 1)
        self.layout().addWidget(self.btnBox, 1)

    def addFormTxt(self):
        if self.intervalsToggle.isChecked():
            self.intervalsTxt.show()
        else:
            self.intervalsTxt.hide()

    def getReportEvent(self):
        text = self.intervalsTxt.toPlainText()
        if self.intervalsToggle.isChecked() and not text:
            self.parent.setNotify('warning', "Need input intervals")
            return
        if not self.intervalsToggle.isChecked():
            text = ''
        options = qtw.QFileDialog.Options()
        self.filePath, _ = qtw.QFileDialog.getSaveFileName(
            self, "Save File", "", "xlsx Files (*.xlsx);;All Files(*)", options=options)
        if self.filePath:
            try:
                coef = self.parent.settings.value('koef_for_intervals')
                self.controller.save_report(self.filePath, coef, text)
                self.openButton.show()
                self.parent.setNotify(
                    'success', f'xlsx file saved to {self.filePath}')
            except PermissionError:
                self.parent.setNotify(
                    'error', 'File opened in another program')
            except ValueError:
                self.parent.setNotify('warning', 'JVD_H not found in data')
            except Exception as e:
                self.parent.setNotify('error', str(e))

    def openFile(self):
        startfile(self.filePath)
        self.close()
