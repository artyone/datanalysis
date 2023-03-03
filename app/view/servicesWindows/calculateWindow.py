from PyQt5 import QtWidgets as qtw


class CalcWindow(qtw.QWidget):
    '''
    Класс окна рассчета данных.
    parent - родительское окно
    controller - контроллер для получения данных.
    '''
    def __init__(self, controller, parent=None):
        super().__init__()
        self.parent = parent
        self.controller = controller
        self.initUI()

    def initUI(self):
        '''
        Метод отрисовки основных элементов окна.
        '''
        self.setGeometry(0, 0, 400, 300)
        self.setWindowTitle("Calculate data")
        dlgLayout = qtw.QVBoxLayout()

        self.initInputBlock()
        self.initButtonBlock()

        dlgLayout.addLayout(self.formLayout)
        dlgLayout.addWidget(self.btnBox)
        self.setLayout(dlgLayout)

    def initInputBlock(self):
        '''Метод инициализации элементов выбора пользователя'''
        self.formLayout = qtw.QFormLayout()
        self.formLayout.setVerticalSpacing(20)

        self.planeComboBox = qtw.QComboBox()
        self.planeComboBox.addItems(self.parent.settings.value('planes'))
        self.planeComboBox.setCurrentText(self.parent.settings.value('planeComboBox'))
        self.planeComboBox.activated.connect(self.saveComboBoxValue)

        self.initPnkBlock()
        self.initDissBlock()

        self.formLayout.addRow('plane:', self.planeComboBox)
        self.formLayout.addRow('calc pnk:', self.calcPnkCheckBox)
        self.formLayout.addRow(self.categoryPnkComboBox)
        self.formLayout.addRow(self.adrPnkComboBox)
        self.formLayout.addRow('calc diss:', self.calcDissCheckBox)
        self.formLayout.addRow(self.categoryDissComboBox)
        self.formLayout.addRow(self.adrDissComboBox)

    def initPnkBlock(self):
        '''Метод инициализации блока пнк'''
        self.calcPnkCheckBox = qtw.QCheckBox()
        self.calcPnkCheckBox.stateChanged.connect(self.hideUnhidePnk)

        self.categoryPnkComboBox = qtw.QComboBox()
        categories = self.controller.get_data().keys()
        self.categoryPnkComboBox.addItems(categories)
        self.categoryPnkComboBox.activated.connect(self.updateAdrPnkComboBox)

        self.adrPnkComboBox = qtw.QComboBox()
        current_category = self.categoryPnkComboBox.currentText()
        adrs = self.controller.get_data()[current_category].keys()
        self.adrPnkComboBox.addItems(adrs)

        self.categoryPnkComboBox.hide()
        self.adrPnkComboBox.hide()

    def initDissBlock(self):
        '''Метод инициализации блока дисс'''
        self.calcDissCheckBox = qtw.QCheckBox()
        self.calcDissCheckBox.stateChanged.connect(self.hideUnhideDiss)

        self.categoryDissComboBox = qtw.QComboBox()
        categories = self.controller.get_data().keys()
        self.categoryDissComboBox.addItems(categories)
        self.categoryDissComboBox.activated.connect(self.updateAdrDissComboBox)

        self.adrDissComboBox = qtw.QComboBox()
        current_category = self.categoryDissComboBox.currentText()
        adrs = self.controller.get_data()[current_category].keys()
        self.adrDissComboBox.addItems(adrs)

        self.categoryDissComboBox.hide()
        self.adrDissComboBox.hide()
    
    def initButtonBlock(self):
        '''Метод инициализации кнопок на форме'''
        self.btnBox = qtw.QDialogButtonBox()
        self.btnBox.setStandardButtons(qtw.QDialogButtonBox.Ok |
                                       qtw.QDialogButtonBox.Cancel)
        self.btnBox.rejected.connect(self.close)
        self.btnBox.accepted.connect(self.calculate)

    def hideUnhidePnk(self):
        '''Метод скрытия/отображения выбора категории и адр пнк'''
        if self.calcPnkCheckBox.isChecked():
            self.categoryPnkComboBox.show()
            self.adrPnkComboBox.show()
        else:
            self.categoryPnkComboBox.hide()
            self.adrPnkComboBox.hide()
            self.calcDissCheckBox.setChecked(False)

    def hideUnhideDiss(self):
        '''Метод скрытия/отображения выбора категории и адр дисс'''
        if self.calcDissCheckBox.isChecked():
            self.categoryPnkComboBox.show()
            self.adrPnkComboBox.show()
            self.categoryDissComboBox.show()
            self.adrDissComboBox.show()
            self.calcPnkCheckBox.setChecked(True)
        else:
            self.categoryDissComboBox.hide()
            self.adrDissComboBox.hide()

    def updateAdrPnkComboBox(self):
        '''Метод обновления пнк адр комбобокса'''
        current_category = self.categoryPnkComboBox.currentText()
        adrs = self.controller.get_data()[current_category].keys()
        self.adrPnkComboBox.clear()
        self.adrPnkComboBox.addItems(adrs)

    def updateAdrDissComboBox(self):
        '''Метод обновления дисс адр комбобокса'''
        current_category = self.categoryDissComboBox.currentText()
        adrs = self.controller.get_data()[current_category].keys()
        self.adrDissComboBox.clear()
        self.adrDissComboBox.addItems(adrs)

    def saveComboBoxValue(self):
        '''
        Метод для сохранения в настройках самолета по умолчанию.
        '''
        self.parent.settings.setValue(
            'planeComboBox', self.planeComboBox.currentText())

    def calculate(self):
        '''
        Метод по нажатию кнопки ОК, который непосредственно запускает
        рассчет значений с их последующей передачей в главное окно
        '''
        #TODO в дальнейшейм необходимо будет добавить рассчеты
        # дисс, пока только пнк
        if not self.calcPnkCheckBox.isChecked():
            self.parent.setNotify('warning', 'pnk checkbox required')

        plane_corr = self.parent.settings.value(
            'planes')[self.planeComboBox.currentText()]
        corrections = self.parent.settings.value('corrections')
        categoryPnk = self.categoryPnkComboBox.currentText()
        adrPnk = self.adrPnkComboBox.currentText()
        try:
            self.controller.set_calculate_data_pnk(categoryPnk,
                                                   adrPnk,
                                                   plane_corr,
                                                   corrections)
            self.parent.createCheckBox()
            self.parent.updateOpenedFiles()
            self.parent.setNotify('success', 'data calculated')
            self.close()
        except ValueError:
            self.parent.setNotify('warning', 'Wrong data file')
    