from os import startfile
from unicodedata import category
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets as qtw
from qtwidgets import AnimatedToggle


class ReportWindow(qtw.QWidget):
    '''
    Класс окна получения отчета по полету.
    parent - родительское окно.
    controller - контроллер.
    intervalsTxt - текст пользовательских интервалов.
    '''

    def __init__(self, controller, parent=None) -> None:
        super().__init__()
        self.parent = parent
        self.controller = controller
        self.intervalsTxt = None
        self.initUI()

    def initUI(self):
        '''
        Метод инциализации главных элементов окна.
        '''
        self.setGeometry(0, 0, 500, 500)
        self.setWindowTitle("Создание отчёта")
        self.setLayout(qtw.QVBoxLayout())

        formLayout = qtw.QFormLayout()

        self.initCategoryBlock()
        inputBox = self.inputBox()
        btnBox = self.buttonBox()

        formLayout.addRow(self.categoryComboBox)
        formLayout.addRow(self.adrComboBox)
        formLayout.addRow(inputBox)
        formLayout.addRow(self.intervalsTxt)

        self.layout().addLayout(formLayout, 1)
        self.layout().addWidget(btnBox, 1)

    def initCategoryBlock(self):
        self.categoryComboBox = qtw.QComboBox()
        categories = self.controller.get_data().keys()
        self.categoryComboBox.addItems(categories)
        self.categoryComboBox.activated.connect(self.updateAdrComboBox)

        self.adrComboBox = qtw.QComboBox()
        current_category = self.categoryComboBox.currentText()
        adrs = self.controller.get_data()[current_category].keys()
        self.adrComboBox.addItems(adrs)

    def inputBox(self):
        self.intervalsToggle = AnimatedToggle()
        self.intervalsToggle.setChecked(True)
        self.intervalsToggle.stateChanged.connect(self.addFormTxt)
        self.intervalsTxt = qtw.QPlainTextEdit()

        horizontalLayout = qtw.QHBoxLayout()
        horizontalLayout.addWidget(qtw.QLabel('<b>Интервалы:</b>'), 2)
        horizontalLayout.addWidget(qtw.QLabel('Рассчитать автоматически'), 1,
                                   alignment=Qt.AlignRight)
        horizontalLayout.addWidget(self.intervalsToggle, 1)
        horizontalLayout.addWidget(qtw.QLabel('Ввести вручную'), 2)
        return horizontalLayout

    def buttonBox(self):
        btnBox = qtw.QDialogButtonBox()

        btnBox.setStandardButtons(qtw.QDialogButtonBox.Open |
                                  qtw.QDialogButtonBox.Save |
                                  qtw.QDialogButtonBox.Cancel)
        btnBox.rejected.connect(self.close)

        self.openButton = btnBox.button(qtw.QDialogButtonBox.Open)
        self.openButton.clicked.connect(self.openFile)
        self.openButton.hide()

        saveButton = btnBox.button(qtw.QDialogButtonBox.Save)
        saveButton.clicked.connect(self.getReportEvent)
        return btnBox

    def addFormTxt(self):
        '''
        Метод для отображения окна ввода интервалов пользователем.
        '''
        if self.intervalsToggle.isChecked():
            self.intervalsTxt.show()
        else:
            self.intervalsTxt.hide()

    def updateAdrComboBox(self):
        current_category = self.categoryComboBox.currentText()
        adrs = self.controller.get_data()[current_category].keys()
        self.adrComboBox.clear()
        self.adrComboBox.addItems(adrs)

    def getReportEvent(self):
        '''
        Метод генерации отчёта по полету и сохранения его на диск.
        В зависимости от положения переключателя 
        отчет генерируется автоматически или по данным пользователя.
        '''
        text = self.intervalsTxt.toPlainText()
        if self.intervalsToggle.isChecked() and not text:
            self.parent.setNotify('предупреждение', "Need input intervals")
            return
        if not self.intervalsToggle.isChecked():
            text = ''
        options = qtw.QFileDialog.Options()
        filePath, _ = qtw.QFileDialog.getSaveFileName(
            self, "Save File", "", "xlsx Files (*.xlsx);;All Files(*)", options=options)
        if filePath:
            try:
                category = self.categoryComboBox.currentText()
                adr = self.adrComboBox.currentText()
                coef = self.parent.settings.value('koef_for_intervals')
                self.controller.save_report(filePath,
                                            category,
                                            adr,
                                            coef,
                                            text)
                self.filePath = filePath
                self.openButton.show()
                self.parent.setNotify(
                    'успех', f'xlsx file saved to {filePath}')
            except PermissionError:
                self.parent.setNotify(
                    'ошибка', 'File opened in another program')
            except AttributeError:
                self.parent.setNotify(
                    'предупреждение', 'check settings coefficient')
            except ValueError:
                self.parent.setNotify(
                    'предупреждение', 'JVD_H not found in data')
            except Exception as e:
                self.parent.setNotify('ошибка', str(e))

    def openFile(self):
        '''
        Метод открытия файла отчёта, если он был создан.
        '''
        startfile(self.filePath)
        self.close()
