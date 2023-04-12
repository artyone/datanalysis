from os import startfile
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout,
    QComboBox, QLineEdit, QFileDialog,
    QDialogButtonBox
)


class MapWindow(QWidget):
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
        dlgLayout = QVBoxLayout()

        self.initInputBlock()
        self.initButtonBlock()

        dlgLayout.addLayout(self.formLayout)
        dlgLayout.addWidget(self.btnBox)
        self.setLayout(dlgLayout)

    def initInputBlock(self):
        '''Метод инициализации элементов ввода и выбора пользователя'''
        self.formLayout = QFormLayout()
        self.formLayout.setVerticalSpacing(20)

        self.categoryComboBox = QComboBox()
        categories = self.controller.get_data().keys()
        self.categoryComboBox.addItems(categories)
        self.categoryComboBox.activated.connect(self.updateAdrComboBox)

        self.adrComboBox = QComboBox()
        current_category = self.categoryComboBox.currentText()
        adrs = self.controller.get_data()[current_category].keys()
        self.adrComboBox.addItems(adrs)

        self.formLayout.addRow('category', self.categoryComboBox)
        self.formLayout.addRow('adr', self.adrComboBox)

        self.jvdHMinLineEdit = QLineEdit(
            self.settings.value('map')['jvdHMin']
        )
        self.decimationLineEdit = QLineEdit(
            self.settings.value('map')['decimation']
        )
        self.formLayout.addRow('JVD_H min:', self.jvdHMinLineEdit)
        self.formLayout.addRow('decimation:', self.decimationLineEdit)

    def initButtonBlock(self):
        '''Метод инициализации кнопок на форме'''
        self.btnBox = QDialogButtonBox()
        self.btnBox.setStandardButtons(
            QDialogButtonBox.Open |
            QDialogButtonBox.Save |
            QDialogButtonBox.Cancel
        )
        self.btnBox.rejected.connect(self.close)

        self.openButton = self.btnBox.button(QDialogButtonBox.Open)
        self.openButton.clicked.connect(self.openFile)
        self.openButton.hide()

        saveButton = self.btnBox.button(QDialogButtonBox.Save)
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
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            "",
            "html Files (*.html);;All Files(*)",
            options=options
        )
        if filePath:
            try:
                self.controller.save_map(
                    filePath,
                    self.categoryComboBox.currentText(),
                    self.adrComboBox.currentText(),
                    self.jvdHMinLineEdit.text(),
                    self.decimationLineEdit.text()
                )
                self.settings.setValue(
                    'map',
                    {
                        'jvdHMin': self.jvdHMinLineEdit.text(),
                        'decimation': self.decimationLineEdit.text()
                    }
                )
                self.parent.setNotify(
                    'успех', f'html file saved to {filePath}')
                self.filePath = filePath
                self.openButton.show()

            except PermissionError:
                self.parent.setNotify(
                    'ошибка', 'File opened in another program')
            except ValueError as e:
                self.parent.setNotify('ошибка', str(e))
            except Exception as e:
                self.parent.setNotify('ошибка', str(e))

    def openFile(self):
        '''
        Метод открытия файла карты, если она была создана
        '''
        startfile(self.filePath)
        self.close()
