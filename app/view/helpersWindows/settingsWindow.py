from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout,
    QCheckBox, QComboBox, QHBoxLayout,
    QTabWidget, QFileDialog,
    QLineEdit, QPushButton,
    QStackedLayout, QScrollArea,
    QMessageBox
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

    def __init__(self, controller, parent=None) -> None:
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

    def initUI(self) -> None:
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

    def mainTab(self) -> QWidget:
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

    def initBrowseBlock(self) -> QHBoxLayout:
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

    def openDirectoryDialog(self) -> None:
        directoryPath = QFileDialog.getExistingDirectory(None,
                                                         "Выберите папку")
        if directoryPath:
            self.browseLineEdit.setText(directoryPath)

    def filterMenuTab(self) -> QWidget:
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

    def pageFilterStacked(self, adr: str) -> QScrollArea:
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

    def planeTab(self) -> QWidget:
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

    def pagePlaneStacked(self, plane: str) -> QWidget:
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

    def correctionTab(self) -> QWidget:
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

    def graphTab(self) -> GraphTab:
        self.graphTabWidget = GraphTab(self.listGraphs)
        return self.graphTabWidget

    def switchPage(self, layout, widget) -> None:
        '''
        Метод переключения для изменения отображения в зависимости от индекса комбобокса.
        '''
        layout.setCurrentIndex(widget.currentIndex())

    def saveSettings(self) -> None:
        '''
        Метод сохранения всех настроек.
        '''
        # TODO придумать контроль ошибок при сохранении, особенно графиков
        try:
            self.saveMainSettings()
            self.savePlanesSettings()
            self.saveCorrectionsSettings()
            self.saveGraphSettings()
            self.saveLeftMenuFilterSettings()
            self.parent.setNotify(
                'успех', 'Настройки сохранены.'
            )
        except:
            self.parent.setNotify(
                'ошибка', 'Настройки не сохранены, проверьте правильность введенных данных!'
            )

    def saveMainSettings(self) -> None:
        newValueMainSettings = {
            'theme': self.themeComboBox.currentText(),
            'jsonDir': self.browseLineEdit.text(),
            'toolBar': self.toolbarComboBox.currentText()
        }
        if self.settings.value('mainSettings') == newValueMainSettings:
            return
        self.settings.setValue('mainSettings', newValueMainSettings)
        question = QMessageBox.question(
            None, "Вопрос", "Для применения настроек нужно перезапустить программу. Делаем?",
            QMessageBox.Yes | QMessageBox.No
        )
        if question == QMessageBox.Yes:
            self.parent.restartApp()

    def savePlanesSettings(self) -> None:
        newValuePlanes = {
            plane: {
                param: float(widget.text())
                for param, widget in value.items()
            }
            for plane, value in self.listPlanes.items()
        }
        if self.settings.value('planes') == newValuePlanes:
            return
        self.settings.setValue('planes', newValuePlanes)

    def saveCorrectionsSettings(self) -> None:
        newValueCorrections = {
            correction: float(widget.text())
            for correction, widget in self.listCorrections.items()
        }
        if self.settings.value('corrections') == newValueCorrections:
            return
        self.settings.setValue('corrections', newValueCorrections)
        self.listCorrections = newValueCorrections

    def saveGraphSettings(self) -> None:
        newGraphSettings = self.graphTabWidget.get_data()
        if self.settings.value('graphs') == newGraphSettings:
            return
        self.settings.setValue('graphs', newGraphSettings)
        self.parent.updateInterfaceFromSettings('graphs')
        self.listGraphs = newGraphSettings

    def saveLeftMenuFilterSettings(self) -> None:
        # TODO добавить заголовки и вообще продумать это всё
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
        if self.settings.value('leftMenuFilters') == newValueFilters:
            return
        self.settings.setValue('leftMenuFilters', newValueFilters)
        self.listMenuFilters = newValueFilters
        self.parent.updateInterfaceFromSettings('leftMenuFilters')

    def checkDigit(self, widget: QLineEdit):
        try:
            float(widget.text())
            widget.setStyleSheet("background:#1E1E1E;")
            self.saveButton.setDisabled(False)
        except ValueError:
            widget.setStyleSheet("background:#FA8072;")
            self.saveButton.setDisabled(True)

    def uncheckAllCheckBox(self) -> None:
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
