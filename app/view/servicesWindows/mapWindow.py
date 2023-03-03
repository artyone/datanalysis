from os import startfile
from PyQt5 import QtWidgets as qtw


class MapWindow(qtw.QWidget):
    '''
    Класс окна построения карты полёта
    parent - родительское окно
    controller - контроллер для получения данных.
    settings - настройки приложения.
    '''
    def __init__(self, controller, parent=None):
        super().__init__()
        self.parent = parent
        self.controller = controller
        self.settings = self.parent.settings
        self.initUI()

    def initUI(self):
        '''
        Метод отрисовки основных элементов окна.
        '''
        self.setGeometry(0, 0, 400, 200)
        self.setWindowTitle("Create map")
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

        self.formLayout.addRow('category', self.categoryComboBox)
        self.formLayout.addRow('adr', self.adrComboBox)


        self.jvdHMinLineEdit = qtw.QLineEdit(
            self.settings.value('map')['jvdHMin'])
        self.decimationLineEdit = qtw.QLineEdit(
            self.settings.value('map')['decimation'])
        self.formLayout.addRow('JVD_H min:', self.jvdHMinLineEdit)
        self.formLayout.addRow('decimation:', self.decimationLineEdit)
    
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
        saveButton.clicked.connect(self.getMap)

    def updateAdrComboBox(self):
        current_category = self.categoryComboBox.currentText()
        adrs = self.controller.get_data()[current_category].keys()
        self.adrComboBox.clear()
        self.adrComboBox.addItems(adrs)

    def getMap(self):
        '''
        Метод получения и сохранения карты по указанному пользователем пути.
        '''
        options = qtw.QFileDialog.Options()
        filePath, _ = qtw.QFileDialog.getSaveFileName(self,
            "Save File", "", "html Files (*.html);;All Files(*)", options=options)
        if filePath:
            try:
                self.controller.save_map(filePath,
                                         self.categoryComboBox.currentText(),
                                         self.adrComboBox.currentText(),
                                         self.jvdHMinLineEdit.text(),
                                         self.decimationLineEdit.text())
                self.settings.setValue('map', {
                    'jvdHMin': self.jvdHMinLineEdit.text(),
                    'decimation': self.decimationLineEdit.text()
                })
                self.parent.setNotify(
                    'success', f'html file saved to {filePath}')
                self.filePath = filePath
                self.openButton.show()

            except PermissionError:
                self.parent.setNotify(
                    'error', 'File opened in another program')
            except ValueError as e:
                self.parent.setNotify('error', str(e))
            except Exception as e:
                self.parent.setNotify('error', str(e))

    def openFile(self):
        '''
        Метод открытия файла карты, если она была создана
        '''
        startfile(self.filePath)
        self.close()
