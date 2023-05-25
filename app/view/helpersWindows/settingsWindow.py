from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout,
    QCheckBox, QComboBox, QHBoxLayout,
    QTabWidget, QFileDialog,
    QLineEdit, QPushButton,
    QStackedLayout, QScrollArea,
    QPlainTextEdit
)
from PyQt5.QtCore import Qt
from functools import partial
from .settingsWindowGraph import GraphTab


class SettingsWindow(QWidget):
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
        self.setGeometry(0, 0, 800, 600)
        self.setWindowTitle("Settings menu")
        layout = QVBoxLayout()
        tabWidget = QTabWidget()
        tabWidget.addTab(self.mainTab(), 'Общие настройки')
        tabWidget.addTab(self.filterMenuTab(), 'Фильтр бокового меню')
        tabWidget.addTab(self.planeTab(), 'Самолёты')
        tabWidget.addTab(self.correctionTab(), 'Коррекция')
        tabWidget.addTab(self.graphTab(), 'Графики')
        self.saveButton = QPushButton('Save')
        self.saveButton.clicked.connect(self.saveSettings)
        layout.addWidget(tabWidget)
        layout.addWidget(self.saveButton)
        self.setLayout(layout)

    def mainTab(self):
        '''
        Вкладка основных настроек.
        '''
        tabWidget = QWidget()
        tabLayout = QFormLayout()

        lineEdit = self.initBrowseBlock()
        tabLayout.addRow('Путь к json папке:', lineEdit)

        self.themeComboBox = QComboBox()
        self.themeComboBox.addItems(['black', 'white'])
        self.themeComboBox.setCurrentText(self.listMainSettings['theme'])
        tabLayout.addRow('Тема:', self.themeComboBox)

        self.toolbarComboBox = QComboBox()
        self.toolbarComboBox.addItems(['left', 'top'])
        self.toolbarComboBox.setCurrentText(self.listMainSettings['toolBar'])
        tabLayout.addRow('Позиция кнопок:', self.toolbarComboBox)

        tabWidget.setLayout(tabLayout)
        return tabWidget

    def initBrowseBlock(self):
        horizontalLayer = QHBoxLayout()
        self.browseLineEdit = QLineEdit()
        self.browseLineEdit.setText(self.listMainSettings['jsonDir'])
        browseButton = QPushButton()
        browseButton.setText('...')
        browseButton.setFixedSize(40, 22)
        browseButton.clicked.connect(self.openDirectoryDialog)
        horizontalLayer.addWidget(self.browseLineEdit)
        horizontalLayer.addWidget(browseButton)
        horizontalLayer.setSpacing(15)
        return horizontalLayer

    def openDirectoryDialog(self):
        directoryPath = QFileDialog.getExistingDirectory(None,
                                                         "Выберите папку")
        if directoryPath:
            self.browseLineEdit.setText(directoryPath)

    def filterMenuTab(self):
        '''
        Вкладка настройки фильтра бокового чек-бокс меню.
        '''
        tabWidget = QWidget()
        tabLayout = QVBoxLayout()
        self.filtersComboBox = QComboBox()
        self.filtersComboBox.addItems(self.listMenuFilters['adrs'])

        tabLayout.addWidget(self.filtersComboBox, alignment=Qt.AlignTop)
        tabWidget.setLayout(tabLayout)
        self.filtersStackedLayout = QStackedLayout()
        for adr in self.listMenuFilters['adrs']:
            self.filtersStackedLayout.addWidget(self.pageFilterStacked(adr))
        self.filtersComboBox.activated.connect(
            partial(self.switchPage, self.filtersStackedLayout, self.filtersComboBox))

        self.unknownCheckBox = QCheckBox('Отображать неизвестные заголовки?')
        self.unknownCheckBox.setChecked(self.listMenuFilters['unknown'])
        tabLayout.addWidget(self.unknownCheckBox)

        tabLayout.addLayout(self.filtersStackedLayout)
        return tabWidget

    def pageFilterStacked(self, adr):
        pageWidget = QWidget()
        pageLayout = QFormLayout()
        for elements in self.settings.value('leftMenuFilters')['adrs'][adr]:
            checkBox = QCheckBox(str(elements))
            checkBox.setChecked(self.settings.value(
                'leftMenuFilters')['adrs'][adr][elements])
            pageLayout.addWidget(checkBox)
            self.listMenuFilters['adrs'][adr][elements] = checkBox
        pageWidget.setLayout(pageLayout)

        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setWidget(pageWidget)

        return scrollArea

    def planeTab(self):
        '''
        Вкладка настройки коэффициентов самолётов
        '''
        tabWidget = QWidget()
        tabLayout = QVBoxLayout()
        self.planesComboBox = QComboBox()
        self.planesComboBox.addItems(self.listPlanes)

        tabLayout.addWidget(self.planesComboBox, alignment=Qt.AlignTop)
        tabWidget.setLayout(tabLayout)
        self.planesStackedLayout = QStackedLayout()
        for plane in self.listPlanes:
            self.planesStackedLayout.addWidget(self.pagePlaneStacked(plane))
        self.planesComboBox.activated.connect(
            partial(self.switchPage, self.planesStackedLayout,
                    self.planesComboBox)
        )
        tabLayout.addLayout(self.planesStackedLayout)
        return tabWidget

    def pagePlaneStacked(self, plane):
        '''
        Создает страницу настроек для вкладки самолета.
        Значения берет из настроек и записывает объект в словарь listPlanes 
        для последующего быстрого получения данных объекта.
        '''
        pageWidget = QWidget()
        pageLayout = QFormLayout()
        for param, value in self.settings.value('planes')[plane].items():
            lineEdit = QLineEdit(str(value))
            lineEdit.textChanged.connect(partial(self.checkDigit, lineEdit))
            pageLayout.addRow(param, lineEdit)
            self.listPlanes[plane][param] = lineEdit
        pageWidget.setLayout(pageLayout)
        return pageWidget

    def correctionTab(self):
        '''
        Вкладка настройки корректировки коэффициентов
        '''
        tabWidget = QWidget()
        tabLayout = QFormLayout()
        for correction, value in self.listCorrections.items():
            lineEdit = QLineEdit(str(value))
            lineEdit.textChanged.connect(partial(self.checkDigit, lineEdit))
            tabLayout.addRow(correction, lineEdit)
            self.listCorrections[correction] = lineEdit
        tabWidget.setLayout(tabLayout)
        return tabWidget


    def graphTab(self):
        self.graphTabWidget = GraphTab(self.listGraphs)
        return self.graphTabWidget
    # def graphTab(self):
    #     '''
    #     Вкладка настроек графиков.
    #     '''
    #     tabWidget = QWidget()
    #     tabLayout = QFormLayout()
    #     bground = QComboBox()
    #     bground.addItems(
    #         ['black', 'white', 'red', 'green', 'pink', 'blue', 'gray']
    #     )
    #     bground.setCurrentText(self.listGraphs['background'])
    #     tabLayout.addRow('Фон графиков:', bground)
    #     self.listGraphs['background'] = bground
    #     string = '\n'.join(
    #         [
    #             ','.join([' '.join(x) for x in item])
    #             for item in self.listGraphs['default']
    #         ]
    #     )
    #     defaultTextEdit = QPlainTextEdit(string)
    #     tabLayout.addRow('Графики по умолчанию:', defaultTextEdit)
    #     self.listGraphs['default'] = defaultTextEdit
    #     tabWidget.setLayout(tabLayout)
    #     return tabWidget

    def switchPage(self, layout, widget):
        '''
        Метод переключения для изменения отображения в зависимости от индекса комбобокса.
        '''
        layout.setCurrentIndex(widget.currentIndex())

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
            'успех', 'Настройки сохранены, перезапустите приложение!'
        )
        self.parent.restartApp()

    def saveMainSettings(self):
        newValueMainSettings = {
            'theme': self.themeComboBox.currentText(),
            'jsonDir': self.browseLineEdit.text(),
            'toolBar': self.toolbarComboBox.currentText()
        }
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

    #TODO вернуть сохранение настроек
    # def saveGraphSettings(self):
    #     graphBackground = self.listGraphs['background'].currentText()
    #     graphDefault = [
    #         [tuple(x.split()) for x in row.split(',')]
    #         for row in self.listGraphs['default'].toPlainText().split('\n')
    #     ]

    #     graphSettings = {
    #         'background': graphBackground,
    #         'default': graphDefault
    #     }
    #     self.settings.setValue('graphs', graphSettings)

    def saveLeftMenuFilterSettings(self):
        newValueAdr = {
            adr: {
                name: widget.isChecked()
                for name, widget in data.items()
            }
            for adr, data in self.listMenuFilters['adrs'].items()
        }
        newValueFilters = {
            'unknown': self.unknownCheckBox.isChecked(),
            'adrs': newValueAdr
        }
        self.settings.setValue('leftMenuFilters', newValueFilters)

    def checkDigit(self, widget: QLineEdit):
        try:
            float(widget.text())
            widget.setStyleSheet("background:#1E1E1E;")
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
