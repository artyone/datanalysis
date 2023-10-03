from os import startfile

from PyQt5.QtWidgets import (QComboBox, QDialogButtonBox, QFileDialog,
                             QFormLayout, QLineEdit, QVBoxLayout)

import app.controller as ctrl
import app.view as view
from app.view.helpersWindows import BaseWidget


class MapWindow(BaseWidget):
    '''
    Класс окна построения карты полёта
    parent - родительское окно
    controller - контроллер для получения данных.
    settings - настройки приложения.
    '''

    def __init__(self, name: str, controller: ctrl.Control, parent: "view.MainWindow") -> None:
        super().__init__(name, parent)
        self.controller = controller
        self.settings = self.parent.settings
        self.initUI()

    def initUI(self) -> None:
        '''
        Метод отрисовки основных элементов окна.
        '''

        self.setWindowTitle("Создание карты")
        dlgLayout = QVBoxLayout()

        self.initInputBlock()
        self.initButtonBlock()

        dlgLayout.addLayout(self.formLayout)
        dlgLayout.addWidget(self.btnBox)
        self.setLayout(dlgLayout)
        self.adjustSize()
        self.setGeometry(0, 0, 400, self.height())

    def initInputBlock(self) -> None:
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

        self.formLayout.addRow('Категория', self.categoryComboBox)
        self.formLayout.addRow('АДР', self.adrComboBox)

        self.jvdHMinLineEdit = QLineEdit(
            self.settings.value('map')['jvdHMin']
        )
        self.jvdHMinLineEdit.textChanged.connect(
            self.validateLineEdit
        )

        self.decimationLineEdit = QLineEdit(
            self.settings.value('map')['decimation']
        )
        self.decimationLineEdit.textChanged.connect(
            self.validateLineEdit
        )
        self.formLayout.addRow('JVD_H мин:', self.jvdHMinLineEdit)
        self.formLayout.addRow(
            'Прореживание:', self.decimationLineEdit
        )

    def initButtonBlock(self) -> None:
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

        self.saveButton = self.btnBox.button(QDialogButtonBox.Save)
        self.saveButton.clicked.connect(self.getMap)

    def updateAdrComboBox(self) -> None:
        '''Метод обновления адр при выборе категории'''
        current_category = self.categoryComboBox.currentText()
        adrs = self.controller.get_data()[current_category].keys()
        self.adrComboBox.clear()
        self.adrComboBox.addItems(adrs)

    def getMap(self) -> None:
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
        if filePath:  # если выбран путь
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
                )  # сохраняем в настройках последний выбор
                self.parent.send_notify(
                    'успех', f'Карта сохранена в: {filePath}'
                )
                self.filePath = filePath
                self.openButton.show()

            except PermissionError:
                self.parent.send_notify(
                    'ошибка', 'Файл открыт в другой программе'
                )
            except ValueError as e:
                self.parent.send_notify('ошибка', str(e))
            except Exception as e:
                self.parent.send_notify('ошибка', str(e))

    def openFile(self) -> None:
        '''
        Метод открытия файла карты, если она была создана
        '''
        startfile(self.filePath)
        self.close()

    def validateLineEdit(self) -> None:
        # проверка что введены цифры
        first = self.jvdHMinLineEdit.text().isdigit()
        second = self.decimationLineEdit.text().isdigit()
        if first and second:
            self.saveButton.setEnabled(True)
        else:
            self.saveButton.setEnabled(False)
        if not first:
            self.jvdHMinLineEdit.setStyleSheet("background-color: red")
        else:
            self.jvdHMinLineEdit.setStyleSheet("")
        if not second:
            self.decimationLineEdit.setStyleSheet("background-color: red")
        else:
            self.decimationLineEdit.setStyleSheet("")

    def updateWidget(self) -> None:
        categories = self.controller.get_data().keys()
        self.categoryComboBox.clear()
        self.categoryComboBox.addItems(categories)
        self.updateAdrComboBox()
