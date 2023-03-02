from os import startfile
from PyQt5 import QtWidgets as qtw


class OpenFileWindow(qtw.QWidget):
    '''
    Класс окна для выбора json для парсинга данных файла txt или csv
    parent - родительское окно
    controller - контроллер для получения данных.
    settings - настройки приложения.
    '''
    def __init__(self, controller, filetype, parent=None):
        super().__init__()
        self.parent = parent
        self.controller = controller
        self.filetype = filetype
        self.settings = self.parent.settings
        self.initUI()

    def initUI(self):
        '''
        Метод отрисовки основных элементов окна.
        '''
        self.setGeometry(0, 0, 400, 200)
        self.setWindowTitle(f'Open {self.filetype} file...')
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

        self.initCategoryBlock()



        self.loadUnknownCheckBox = qtw.QCheckBox()
        self.loadUnknownCheckBox.setChecked(True)
        self.loadUnknownCheckBox.setText('load unknown elements')

        self.formLayout.addRow('category', self.categoryComboBox)
        self.formLayout.addRow('adr', self.adrComboBox)
        self.formLayout.addRow('file', self.initBrowseBlock())
        self.formLayout.addRow(self.loadUnknownCheckBox)

    def initCategoryBlock(self):
        jsonDir = self.settings.value('mainSettings')['jsonDir']
        self.jsonsData = self.controller.get_jsons_data(jsonDir)

        self.categoryComboBox = qtw.QComboBox()
        categories = [json['name'] for json in self.jsonsData]
        self.categoryComboBox.addItems(categories)
        self.categoryComboBox.activated.connect(self.updateAdrComboBox)

        self.adrComboBox = qtw.QComboBox()
        current_category = self.jsonsData[self.categoryComboBox.currentIndex()]
        adrs = [adr['adr_name'] for adr in current_category['adr']]
        self.adrComboBox.addItems(adrs)

    def initBrowseBlock(self):
        horizontalLayer = qtw.QHBoxLayout()
        self.browseLineEdit = qtw.QLineEdit()
        browseButton = qtw.QPushButton()
        browseButton.setText('...')
        browseButton.setFixedSize(40, 22)
        browseButton.clicked.connect(self.openFileDialog)
        horizontalLayer.addWidget(self.browseLineEdit)
        horizontalLayer.addWidget(browseButton)
        horizontalLayer.setSpacing(15)
        return horizontalLayer
    
    def initButtonBlock(self):
        '''Метод инициализации кнопок на форме'''
        self.btnBox = qtw.QDialogButtonBox()
        self.btnBox.setStandardButtons(qtw.QDialogButtonBox.Open |
                                       qtw.QDialogButtonBox.Cancel)
        self.btnBox.rejected.connect(self.close)

        self.openButton = self.btnBox.button(qtw.QDialogButtonBox.Open)
        self.openButton.clicked.connect(self.openFile)


    def updateAdrComboBox(self):
        current_category = self.jsonsData[self.categoryComboBox.currentIndex()]
        adrs = [adr['adr_name'] for adr in current_category['adr']]
        self.adrComboBox.clear()
        self.adrComboBox.addItems(adrs)

    def openFileDialog(self):
        filePath, check = qtw.QFileDialog.getOpenFileName(None,
            'Open file', '', f'Open File (*.{self.filetype})')
        if check:
            self.browseLineEdit.setText(filePath)
    
    def openFile(self):
        pass

