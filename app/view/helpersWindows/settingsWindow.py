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
        self.listMainSettings = self.settings.value('main_settings')
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
        tabWidget.addTab(
            self.mainTab(), 'Общие настройки'
        )
        tabWidget.addTab(
            self.filterMenuTab(), 'Фильтр бокового меню'
        )
        tabWidget.addTab(
            self.planeTab(), 'Самолёты'
        )
        tabWidget.addTab(
            self.correctionTab(), 'Коррекция'
        )
        tabWidget.addTab(
            self.graphTab(), 'Графики'
        )
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
        tabLayout.addRow(
            'Путь к json папке:', lineEdit
        )

        self.themeComboBox = QComboBox()
        self.themeComboBox.addItems(['dark', 'purple', 'light'])
        self.themeComboBox.setCurrentText(self.listMainSettings['theme'])
        tabLayout.addRow(
            'Тема:', self.themeComboBox
        )

        self.toolbarComboBox = QComboBox()
        self.toolbarComboBox.addItems(['left', 'top'])
        self.toolbarComboBox.setCurrentText(self.listMainSettings['tool_bar'])
        tabLayout.addRow(
            'Позиция кнопок:', self.toolbarComboBox
        )

        self.openLastCheckbox = QCheckBox()
        self.openLastCheckbox.setChecked(
            self.listMainSettings['open_last_file']
        )
        tabLayout.addRow(
            'Открывать последний gzip:', self.openLastCheckbox
        )

        tabWidget.setLayout(tabLayout)
        return tabWidget

    def initBrowseBlock(self) -> QHBoxLayout:
        horizontalLayer = QHBoxLayout()
        self.browseLineEdit = QLineEdit()
        self.browseLineEdit.setText(self.listMainSettings['json_dir'])
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
            None, "Выберите папку"
        )
        if directoryPath:
            self.browseLineEdit.setText(directoryPath)

    def filterMenuTab(self) -> QWidget:
        '''
        Вкладка настройки фильтра бокового чек-бокс меню.
        '''
        scrollArea = QScrollArea()
        widget = QWidget()
        self.filterTabLayout = QVBoxLayout()
        self.addFilterCheckBox(self.filterTabLayout)
        scrollArea.setWidgetResizable(True)
        widget.setLayout(self.filterTabLayout)
        scrollArea.setWidget(widget)
        return scrollArea

    def addFilterCheckBox(self, layout: QVBoxLayout) -> None:
        self.listMenuFilters = []
        for column in self.parent.tree_widget.get_all_columns():
            checkBox = QCheckBox(column)
            settings = self.settings.value('left_menu_filters')
            checkBox.setChecked(True if column in settings else False)
            layout.addWidget(checkBox)

            self.listMenuFilters.append(checkBox)

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
                self.parent.send_notify(
                    'успех', 'Настройки сохранены.'
                )
            else:
                self.parent.send_notify(
                    'информация', 'Вы не внесли изменения в настройки'
                )
        except (ValueErrorPlanes, ValueErrorGraph) as e:
            self.parent.send_notify(
                'ошибка', str(e)
            )
        except Exception as e:
            self.parent.send_notify(
                'ошибка', 'Настройки не сохранены, проверьте правильность введенных данных!'
            )

    def saveMainSettings(self) -> bool:
        newValueMainSettings = {
            'theme': self.themeComboBox.currentText(),
            'json_dir': self.browseLineEdit.text(),
            'tool_bar': self.toolbarComboBox.currentText(),
            'open_last_file': self.openLastCheckbox.isChecked()
        }
        if self.settings.value('main_settings') == newValueMainSettings:
            return False
        # Устанавливаем фон для графиков под тему
        if newValueMainSettings['theme'] != 'light':
            self.graphTabWidget.backgroundCombo.setCurrentText('black')
        else:
            self.graphTabWidget.backgroundCombo.setCurrentText('white')
        self.settings.setValue('main_settings', newValueMainSettings)
        question = QMessageBox.question(
            self, "Вопрос", "Для применения настроек нужно перезапустить программу. Делаем?",
            QMessageBox.Yes | QMessageBox.No
        )
        if question == QMessageBox.Yes:
            self.parent.restart_app()
        return True

    def savePlanesSettings(self) -> bool:
        newValuePlanes = self.planeTabWidget.getValues()
        if self.settings.value('planes') == newValuePlanes:
            return False
        self.settings.setValue('planes', newValuePlanes)
        self.parent.update_child_windows()
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
        self.parent.update_interface_from_settings('graphs')
        self.listGraphs = newGraphSettings
        return True

    def saveLeftMenuFilterSettings(self) -> bool:
        newValueFilters = [
            item.text() for item in self.listMenuFilters
            if item.isChecked()]
        if self.settings.value('left_menu_filters') == newValueFilters:
            return False
        self.settings.setValue('left_menu_filters', newValueFilters)
        self.parent.update_interface_from_settings('left_menu_filters')
        return True

    def checkDigit(self, widget: QLineEdit) -> None:
        try:
            float(widget.text())
            widget.setStyleSheet("background:#1E1E1E;")
            self.saveButton.setEnabled(True)
        except ValueError:
            widget.setStyleSheet("background:#FA8072;")
            self.saveButton.setEnabled(False)

    def closeEvent(self, event) -> None:
        self.parent.settings_window = None
        self.deleteLater()
        event.accept()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def updateWidget(self) -> None:
        layout = self.filterTabLayout
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.addFilterCheckBox(layout)
