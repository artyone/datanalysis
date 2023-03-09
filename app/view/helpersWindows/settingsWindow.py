from PyQt5 import QtWidgets as qtw
from PyQt5.QtCore import Qt
from functools import partial


class SettingsWindow(qtw.QWidget):
    '''
    Класс окна настроек.
    settings - настройки приложения.
    list* - словари для сохранения объектов настроек.
    controller - контроллер.
    '''

    def __init__(self, controller, parent=None):
        super().__init__()
        self.parent = parent
        self.settings = self.parent.settings
        self.listMainSettings = self.settings.value('mainSettings')
        self.listPlanes = self.settings.value('planes')
        self.listCorrections = self.settings.value('corrections')
        self.listGraphs = self.settings.value('graphs')
        self.listMenuFilters = self.settings.value('leftMenuFilters')
        self.controller = controller
        self.initUI()

    def initUI(self):
        '''
        Метод инициализации основных элементов окна.
        '''
        self.setGeometry(0, 0, 700, 500)
        self.setWindowTitle("Settings menu")
        layout = qtw.QVBoxLayout()
        tabWidget = qtw.QTabWidget()
        tabWidget.addTab(self.mainTab(), 'Общие настройки')
        tabWidget.addTab(self.filterMenuTab(), 'Фильтр бокового меню')
        tabWidget.addTab(self.planeTab(), 'Самолёты')
        tabWidget.addTab(self.correctionTab(), 'Коррекция')
        tabWidget.addTab(self.graphTab(), 'Графики')
        self.saveButton = qtw.QPushButton('Save')
        self.saveButton.clicked.connect(self.saveSettings)
        layout.addWidget(tabWidget)
        layout.addWidget(self.saveButton)
        self.setLayout(layout)

    def mainTab(self):
        '''
        Вкладка основных настроек.
        '''
        tabWidget = qtw.QWidget()
        tabLayout = qtw.QFormLayout()

        lineEdit = self.initBrowseBlock()
        tabLayout.addRow('Путь к json папке:', lineEdit)

        self.themeComboBox = qtw.QComboBox()
        self.themeComboBox.addItems(['black', 'white'])
        self.themeComboBox.setCurrentText(self.listMainSettings['theme'])
        tabLayout.addRow('Тема:', self.themeComboBox)

        tabWidget.setLayout(tabLayout)
        return tabWidget

    def initBrowseBlock(self):
        horizontalLayer = qtw.QHBoxLayout()
        self.browseLineEdit = qtw.QLineEdit()
        self.browseLineEdit.setText(self.listMainSettings['jsonDir'])
        browseButton = qtw.QPushButton()
        browseButton.setText('...')
        browseButton.setFixedSize(40, 22)
        browseButton.clicked.connect(self.openDirectoryDialog)
        horizontalLayer.addWidget(self.browseLineEdit)
        horizontalLayer.addWidget(browseButton)
        horizontalLayer.setSpacing(15)
        return horizontalLayer

    def openDirectoryDialog(self):
        directoryPath = qtw.QFileDialog.getExistingDirectory(None,
                                                             "Выберите папку")
        if directoryPath:
            self.browseLineEdit.setText(directoryPath)

    def filterMenuTab(self):
        '''
        Вкладка настройки фильтра бокового чек-бокс меню.
        '''
        tabScrollArea = qtw.QScrollArea()
        tabWidget = qtw.QWidget()
        tabLayout = qtw.QVBoxLayout()
        self.uncheckButton = qtw.QPushButton('Снять все отметки')
        self.uncheckButton.setMaximumWidth(100)
        self.uncheckButton.clicked.connect(self.uncheckAllCheckBox)
        tabLayout.addWidget(self.uncheckButton)
        for key, value in self.settings.value('leftMenuFilters').items():
            checkBox = qtw.QCheckBox(key)
            checkBox.setChecked(value)
            tabLayout.addWidget(checkBox)
            self.listMenuFilters[key] = checkBox
        tabScrollArea.setWidgetResizable(True)
        tabWidget.setLayout(tabLayout)
        tabScrollArea.setWidget(tabWidget)
        return tabScrollArea

    def planeTab(self):
        '''
        Вкладка настройки коэффициентов самолётов
        '''
        tabWidget = qtw.QWidget()
        tabLayout = qtw.QVBoxLayout()
        self.planesComboBox = qtw.QComboBox()
        self.planesComboBox.addItems(self.listPlanes)
        self.planesComboBox.activated.connect(self.switchPage)
        tabLayout.addWidget(self.planesComboBox, alignment=Qt.AlignTop)
        tabWidget.setLayout(tabLayout)
        self.stackedLayout = qtw.QStackedLayout()
        for plane in self.listPlanes:
            self.stackedLayout.addWidget(self.pagePlaneStacked(plane))

        tabLayout.addLayout(self.stackedLayout)
        return tabWidget

    def pagePlaneStacked(self, plane):
        '''
        Создает страницу настроек для вкладки самолета.
        Значения берет из настроек и записывает объект в словарь listPlanes 
        для последующего быстрого получения данных объекта.
        '''
        pageWidget = qtw.QWidget()
        pageLayout = qtw.QFormLayout()
        for param, value in self.settings.value('planes')[plane].items():
            lineEdit = qtw.QLineEdit(str(value))
            lineEdit.textChanged.connect(partial(self.checkDigit, lineEdit))
            pageLayout.addRow(param, lineEdit)
            self.listPlanes[plane][param] = lineEdit
        pageWidget.setLayout(pageLayout)
        return pageWidget

    def correctionTab(self):
        '''
        Вкладка настройки корректировки коэффициентов
        '''
        tabWidget = qtw.QWidget()
        tabLayout = qtw.QFormLayout()
        for correction, value in self.listCorrections.items():
            lineEdit = qtw.QLineEdit(str(value))
            lineEdit.textChanged.connect(partial(self.checkDigit, lineEdit))
            tabLayout.addRow(correction, lineEdit)
            self.listCorrections[correction] = lineEdit
        tabWidget.setLayout(tabLayout)
        return tabWidget

    def graphTab(self):
        '''
        Вкладка настроек графиков.
        '''
        tabWidget = qtw.QWidget()
        tabLayout = qtw.QFormLayout()
        bground = qtw.QComboBox()
        bground.addItems(
            ['black', 'white', 'red', 'green', 'pink', 'blue', 'gray'])
        bground.setCurrentText(self.listGraphs['background'])
        tabLayout.addRow('Фон графиков:', bground)
        self.listGraphs['background'] = bground
        string = '\n'.join([','.join([' '.join(x) for x in item]) for item in self.listGraphs['default']])
        defaultTextEdit = qtw.QPlainTextEdit(string)
        tabLayout.addRow('Графики по умолчанию:', defaultTextEdit)
        self.listGraphs['default'] = defaultTextEdit
        tabWidget.setLayout(tabLayout)
        return tabWidget

    def switchPage(self):
        '''
        Метод переключения для изменения отображения во вкладке самолётов.
        '''
        self.stackedLayout.setCurrentIndex(self.planesComboBox.currentIndex())

    def saveSettings(self):
        '''
        Метод сохранения всех настроек.
        '''
        self.saveMainSettings()
        self.savePlanesSettings()
        self.saveCorrectionsSettings()
        self.saveGraphSettings()
        self.saveLeftMenuFilterSettings()
        self.parent.setNotify(
            'успех', 'Настройки сохранены, перезапустите приложение!')
        self.parent.restartApp()

    def saveMainSettings(self):
        newValueMainSettings = {'theme': self.themeComboBox.currentText(),
                                'jsonDir': self.browseLineEdit.text()}
        self.settings.setValue('mainSettings', newValueMainSettings)

    def savePlanesSettings(self):
        newValuePlanes = {
            plane: {
                param: float(widget.text())
                for param, widget in value.items()
            }
            for plane, value in self.listPlanes.items()
        }
        self.settings.setValue('planes', newValuePlanes)

    def saveCorrectionsSettings(self):
        newValueCorrections = {
            correction: float(widget.text())
            for correction, widget in self.listCorrections.items()
        }
        self.settings.setValue('corrections', newValueCorrections)

    def saveGraphSettings(self):
        graphBackground = self.listGraphs['background'].currentText()
        graphDefault = [[tuple(x.split()) for x in row.split(',')] 
                         for row in self.listGraphs['default'].toPlainText().split('\n')]

        graphSettings = {'background': graphBackground,
                         'default': graphDefault}
        self.settings.setValue('graphs', graphSettings)

    def saveLeftMenuFilterSettings(self):
        newValueFilters = {
            key: widget.isChecked()
            for key, widget in self.listMenuFilters.items()
        }
        self.settings.setValue('leftMenuFilters', newValueFilters)

    def checkDigit(self, widget: qtw.QLineEdit):
        try:
            float(widget.text())
            widget.setStyleSheet("background:#FFFFFF;")
            self.saveButton.setDisabled(False)
        except ValueError:
            widget.setStyleSheet("background:#FA8072;")
            self.saveButton.setDisabled(True)

    def uncheckAllCheckBox(self):
        '''
        Метод снятия всех чек-боксов.
        '''
        if self.uncheckButton.text() == 'Снять все отметки':
            for widget in self.listMenuFilters.values():
                widget.setChecked(False)
            self.uncheckButton.setText('Отметить всё')
        else:
            for widget in self.listMenuFilters.values():
                widget.setChecked(True)
            self.uncheckButton.setText('Снять все отметки')
