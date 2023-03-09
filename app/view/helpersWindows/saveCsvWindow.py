from os import startfile
from PyQt5 import QtWidgets as qtw


class SaveCsvWindow(qtw.QWidget):
    '''
    Класс окна выбора категории и адр для сохранения csv файла
    parent - родительское окно
    controller - контроллер для получения данных.
    '''

    def __init__(self, controller, parent=None):
        super().__init__()
        self.parent = parent
        self.controller = controller
        self.initUI()

    def initUI(self):
        '''Метод отрисовки основных элементов окна.'''
        self.setGeometry(0, 0, 350, 200)
        self.setWindowTitle("Сохранить в CSV...")
        dlgLayout = qtw.QVBoxLayout()

        self.initInputBlock()
        self.initButtonBlock()

        dlgLayout.addLayout(self.formLayout)
        dlgLayout.addWidget(self.btnBox)
        self.setLayout(dlgLayout)

    def initInputBlock(self):
        '''Метод инициализации элементов ввода и выбора пользователя'''
        self.formLayout = qtw.QFormLayout()
        self.formLayout.setVerticalSpacing(20)

        self.categoryComboBox = qtw.QComboBox()
        categories = self.controller.get_data().keys()
        self.categoryComboBox.addItems(categories)
        self.categoryComboBox.activated.connect(self.updateAdrComboBox)

        self.adrComboBox = qtw.QComboBox()
        current_category = self.categoryComboBox.currentText()
        adrs = self.controller.get_data()[current_category].keys()
        self.adrComboBox.addItems(adrs)

        self.formLayout.addRow('Категория', self.categoryComboBox)
        self.formLayout.addRow('АДР', self.adrComboBox)

    def initButtonBlock(self):
        '''Метод инициализации кнопок на форме'''
        self.btnBox = qtw.QDialogButtonBox()
        self.btnBox.setStandardButtons(qtw.QDialogButtonBox.Open |
                                       qtw.QDialogButtonBox.Save |
                                       qtw.QDialogButtonBox.Cancel)
        self.btnBox.rejected.connect(self.close)

        self.openButton = self.btnBox.button(qtw.QDialogButtonBox.Open)
        self.openButton.clicked.connect(self.openFile)
        self.openButton.hide()

        saveButton = self.btnBox.button(qtw.QDialogButtonBox.Save)
        saveButton.clicked.connect(self.saveCsv)

    def updateAdrComboBox(self):
        current_category = self.categoryComboBox.currentText()
        adrs = self.controller.get_data()[current_category].keys()
        self.adrComboBox.clear()
        self.adrComboBox.addItems(adrs)

    def saveCsv(self):
        category = self.categoryComboBox.currentText()
        adr = self.adrComboBox.currentText()
        options = qtw.QFileDialog.Options()
        filePath, _ = qtw.QFileDialog.getSaveFileName(self,
                                                      "Save File", "", f"CSV Files (*.csv);;All Files(*)",
                                                      options=options)
        if filePath:
            try:
                self.controller.save_csv(filePath, category, adr)
                self.parent.setNotify(
                    'успех', f'CSV файл сохранен {filePath}')
                self.openButton.show()
                self.filePath = filePath
            except PermissionError:
                self.parent.setNotify(
                    'ошибка', 'Файл отркрыт в другой программе')
            except Exception as e:
                self.parent.setNotify('ошибка', str(e))

    def openFile(self):
        '''
        Метод открытия файла csv, если она был сохранён
        '''
        startfile(self.filePath)
        self.close()
