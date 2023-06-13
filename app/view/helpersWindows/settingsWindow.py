from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout,
    QCheckBox, QComboBox, QHBoxLayout,
    QTabWidget, QFileDialog, QLineEdit, 
    QPushButton, QScrollArea, QMessageBox
)
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtCore import Qt
from functools import partial
from .settingsWindowGraph import GraphTab, ValueErrorGraph
from .settingsWindowPlane import PlaneTab, ValueErrorPlanes


class SettingsWindow(QWidget):
    '''
    Класс окна настроек.
    settings - настройки приложения.
    list* - словари для сохранения объектов настроек.
    '''

    def __init__(self, parent) -> None:
        super().__init__()
        self.parent = parent
        self.settings = self.parent.settings
        self.listMainSettings = self.settings.value('mainSettings')
        self.listPlanes = self.settings.value('planes')
        self.listCorrections = self.settings.value('corrections')
        self.listGraphs = self.settings.value('graphs')
        self.listMenuFilters = []
        self.initUI()

    def initUI(self) -> None:
        '''
        Метод инициализации основных элементов окна.
        '''
        self.setGeometry(0, 0, 800, 600)
        self.setWindowTitle("Настройки")
        layout = QVBoxLayout()
        tabWidget = QTabWidget()
        tabWidget.addTab(self.mainTab(), 'Общие настройки')
        tabWidget.addTab(self.filterMenuTab(), 'Фильтр бокового меню')
        tabWidget.addTab(self.planeTab(), 'Самолёты')
        tabWidget.addTab(self.correctionTab(), 'Коррекция')
        tabWidget.addTab(self.graphTab(), 'Графики')
        self.saveButton = QPushButton('Сохранить')
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
        self.themeComboBox.addItems(['dark', 'purple', 'light'])
        self.themeComboBox.setCurrentText(self.listMainSettings['theme'])
        tabLayout.addRow('Тема:', self.themeComboBox)

        self.toolbarComboBox = QComboBox()
        self.toolbarComboBox.addItems(['left', 'top'])
        self.toolbarComboBox.setCurrentText(self.listMainSettings['toolBar'])
        tabLayout.addRow('Позиция кнопок:', self.toolbarComboBox)

        self.openLastCheckbox = QCheckBox()
        self.openLastCheckbox.setChecked(self.listMainSettings['openLastFile'])
        tabLayout.addRow('Открывать последний gzip:', self.openLastCheckbox)

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
        directoryPath = QFileDialog.getExistingDirectory(
            None,"Выберите папку"
        )
        if directoryPath:
            self.browseLineEdit.setText(directoryPath)

    def filterMenuTab(self) -> QWidget:
        '''
        Вкладка настройки фильтра бокового чек-бокс меню.
        '''
        scrollArea = QScrollArea()
        widget = QWidget()
        tabLayout = QVBoxLayout()
        for column in self.parent.tree_widget.get_all_columns():
            checkBox = QCheckBox(column)
            settings = self.settings.value('left_menu_filters')
            checkBox.setChecked(True if column in settings else False)
            tabLayout.addWidget(checkBox)
            self.listMenuFilters.append(checkBox)
        scrollArea.setWidgetResizable(True)
        widget.setLayout(tabLayout)
        scrollArea.setWidget(widget)
        return scrollArea

    def planeTab(self) -> QWidget:
        '''
        Вкладка настройки коэффициентов самолётов
        '''
        self.planeTabWidget = PlaneTab(self.listPlanes)
        return self.planeTabWidget

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
            if any((
                self.saveMainSettings(),
                self.savePlanesSettings(),
                self.saveCorrectionsSettings(),
                self.saveGraphSettings(),
                self.saveLeftMenuFilterSettings()
            )):
                self.parent.setNotify(
                    'успех', 'Настройки сохранены.'
                )
            else:
                self.parent.setNotify(
                    'информация', 'Вы не внесли изменения в настройки'
                )
        except (ValueErrorPlanes, ValueErrorGraph) as e:
            self.parent.setNotify(
                'ошибка', str(e)
            )
        except Exception as e:
            self.parent.setNotify(
                'ошибка', 'Настройки не сохранены, проверьте правильность введенных данных!'
            )

    def saveMainSettings(self) -> bool:
        newValueMainSettings = {
            'theme': self.themeComboBox.currentText(),
            'jsonDir': self.browseLineEdit.text(),
            'toolBar': self.toolbarComboBox.currentText(),
            'openLastFile': self.openLastCheckbox.isChecked()
        }
        if self.settings.value('mainSettings') == newValueMainSettings:
            return False
        #Устанавливаем фон для графиков под тему
        if newValueMainSettings['theme'] != 'light':
            self.graphTabWidget.backgroundCombo.setCurrentText('black')
        else: 
            self.graphTabWidget.backgroundCombo.setCurrentText('white')
        self.settings.setValue('mainSettings', newValueMainSettings)
        question = QMessageBox.question(
            None, "Вопрос", "Для применения настроек нужно перезапустить программу. Делаем?",
            QMessageBox.Yes | QMessageBox.No
        )
        if question == QMessageBox.Yes:
            self.parent.restartApp()
        return True

    def savePlanesSettings(self) -> None:
        newValuePlanes = self.planeTabWidget.getValues()
        if self.settings.value('planes') == newValuePlanes:
            return False
        self.settings.setValue('planes', newValuePlanes)
        return True

    def saveCorrectionsSettings(self) -> bool:
        newValueCorrections = {
            correction: float(widget.text())
            for correction, widget in self.listCorrections.items()
        }
        if self.settings.value('corrections') == newValueCorrections:
            return False
        self.settings.setValue('corrections', newValueCorrections)
        self.listCorrections = newValueCorrections
        return True

    def saveGraphSettings(self) -> bool:
        newGraphSettings = self.graphTabWidget.get_data()
        if self.settings.value('graphs') == newGraphSettings:
            return False
        self.settings.setValue('graphs', newGraphSettings)
        self.parent.updateInterfaceFromSettings('graphs')
        self.listGraphs = newGraphSettings
        return True

    def saveLeftMenuFilterSettings(self) -> bool:
        newValueFilters = [
            item.text() for item in self.listMenuFilters
            if item.isChecked()]
        if self.settings.value('left_menu_filters') == newValueFilters:
            return False
        self.settings.setValue('left_menu_filters', newValueFilters)
        self.parent.updateInterfaceFromSettings('left_menu_filters')
        return True

    def checkDigit(self, widget: QLineEdit):
        try:
            float(widget.text())
            widget.setStyleSheet("background:#1E1E1E;")
            self.saveButton.setDisabled(False)
        except ValueError:
            widget.setStyleSheet("background:#FA8072;")
            self.saveButton.setDisabled(True)

    def closeEvent(self, event):
        self.parent.settingsWindow = None
        self.deleteLater()
        event.accept()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
