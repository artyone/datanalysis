from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout,
    QCheckBox, QComboBox, QHBoxLayout,
    QDialogButtonBox, QFileDialog,
    QLineEdit, QPushButton
)


class OpenFileWindow(QWidget):
    '''
    Класс окна для выбора json для парсинга данных файла txt или csv
    parent - родительское окно
    controller - контроллер для получения данных.
    settings - настройки приложения.
    '''

    def __init__(self, controller, filetype, categories, parent=None):
        super().__init__()
        self.parent = parent
        self.controller = controller
        self.filetype = filetype
        self.categories = categories
        self.settings = self.parent.settings
        self.initUI()

    def initUI(self):
        '''
        Метод отрисовки основных элементов окна.
        '''
        self.setGeometry(0, 0, 400, 200)
        self.setWindowTitle(f'Открыть {self.filetype} файл...')
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

        self.initCategoryBlock()

        self.loadUnknownCheckBox = QCheckBox()
        self.loadUnknownCheckBox.setChecked(True)
        self.loadUnknownCheckBox.setText('загружать незвестные элементы')

        self.formLayout.addRow('Категория', self.categoryComboBox)
        self.formLayout.addRow('АДР', self.adrComboBox)
        self.formLayout.addRow('Файл', self.initBrowseBlock())
        self.formLayout.addRow(self.loadUnknownCheckBox)

    def initCategoryBlock(self):
        self.categoryComboBox = QComboBox()
        self.categoryComboBox.addItems(self.categories.keys())
        self.adrComboBox = QComboBox()
        adrs = self.categories[self.categoryComboBox.currentText()]
        self.adrComboBox.addItems([adr['adr_name'] for adr in adrs])
        self.categoryComboBox.activated.connect(self.updateAdrComboBox)

    def initBrowseBlock(self):
        horizontalLayer = QHBoxLayout()
        self.browseLineEdit = QLineEdit()
        browseButton = QPushButton()
        browseButton.setText('...')
        browseButton.setFixedSize(40, 22)
        browseButton.clicked.connect(self.openFileDialog)
        horizontalLayer.addWidget(self.browseLineEdit)
        horizontalLayer.addWidget(browseButton)
        horizontalLayer.setSpacing(15)
        return horizontalLayer

    def initButtonBlock(self):
        '''Метод инициализации кнопок на форме'''
        self.btnBox = QDialogButtonBox()
        self.btnBox.setStandardButtons(
            QDialogButtonBox.Open | QDialogButtonBox.Cancel
        )
        self.btnBox.rejected.connect(self.close)

        self.openButton = self.btnBox.button(QDialogButtonBox.Open)
        self.openButton.clicked.connect(self.openFile)

    def updateAdrComboBox(self):
        adrs = self.categories[self.categoryComboBox.currentText()]
        self.adrComboBox.clear()
        self.adrComboBox.addItems([adr['adr_name'] for adr in adrs])

    def openFileDialog(self):
        filePath, check = QFileDialog.getOpenFileName(
            None,
            'Open file',
            '',
            f'Open File (*.{self.filetype})'
        )
        if check:
            self.browseLineEdit.setText(filePath)

    def openFile(self):
        try:
            self.controller.load_text(
                self.browseLineEdit.text(),
                self.categoryComboBox.currentText(),
                self.adrComboBox.currentText(),
                self.filetype,
                self.loadUnknownCheckBox.isChecked()
            )
            self.parent.tree.updateCheckBox()
            self.parent.setNotify(
                'успех', f'Файл {self.browseLineEdit.text()} открыт'
            )
            self.parent.destroyChildWindow()
        except ValueError as e:
            self.setNotify('ошибка', str(e))
