from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout,
    QLabel, QComboBox, QHBoxLayout,
    QDialogButtonBox, QFileDialog,
    QPlainTextEdit
)
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtCore import Qt
from qtwidgets import AnimatedToggle
from os import startfile


class ReportWindow(QWidget):
    '''
    Класс окна получения отчета по полету.
    parent - родительское окно.
    controller - контроллер.
    intervalsTxt - текст пользовательских интервалов.
    '''

    def __init__(self, controller, parent) -> None:
        super().__init__()
        self.parent = parent
        self.controller = controller
        self.intervalsTxt = None
        self.initUI()

    def initUI(self):
        '''
        Метод инциализации главных элементов окна.
        '''
        self.setGeometry(0, 0, 500, 500)
        self.setWindowTitle("Создание отчёта")
        self.setLayout(QVBoxLayout())

        formLayout = QFormLayout()

        self.initCategoryBlock()
        inputBox = self.inputBox()
        btnBox = self.buttonBox()

        formLayout.addRow('Категория', self.categoryComboBox)
        formLayout.addRow('АДР', self.adrComboBox)
        formLayout.addRow('Самолёт', self.planeComboBox)
        formLayout.addRow(inputBox)
        formLayout.addRow(self.intervalsTxt)

        self.layout().addLayout(formLayout, 1)
        self.layout().addWidget(btnBox, 1)

    def initCategoryBlock(self) -> None:
        self.categoryComboBox = QComboBox()
        categories = self.controller.get_data().keys()
        self.categoryComboBox.addItems(categories)
        self.categoryComboBox.activated.connect(self.updateAdrComboBox)

        self.adrComboBox = QComboBox()
        current_category = self.categoryComboBox.currentText()
        adrs = self.controller.get_data()[current_category].keys()
        self.adrComboBox.addItems(adrs)

        self.planeComboBox = QComboBox()
        self.planeComboBox.addItems(
            self.parent.settings.value('planes').keys()
        )

    def inputBox(self) -> QHBoxLayout:
        self.intervalsToggle = AnimatedToggle()
        self.intervalsToggle.setChecked(True)
        self.intervalsToggle.stateChanged.connect(self.addFormTxt)
        self.intervalsTxt = QPlainTextEdit()

        horizontalLayout = QHBoxLayout()
        horizontalLayout.addWidget(QLabel('<b>Интервалы:</b>'), 2)
        horizontalLayout.addWidget(
            QLabel('Рассчитать автоматически'),
            1,
            alignment=Qt.AlignRight
        )
        horizontalLayout.addWidget(self.intervalsToggle, 1)
        horizontalLayout.addWidget(QLabel('Ввести вручную'), 2)
        return horizontalLayout

    def buttonBox(self) -> QDialogButtonBox:
        btnBox = QDialogButtonBox()

        btnBox.setStandardButtons(
            QDialogButtonBox.Open |
            QDialogButtonBox.Save |
            QDialogButtonBox.Cancel
        )
        btnBox.rejected.connect(self.close)

        self.openButton = btnBox.button(QDialogButtonBox.Open)
        self.openButton.clicked.connect(self.openFile)
        self.openButton.hide()

        saveButton = btnBox.button(QDialogButtonBox.Save)
        saveButton.clicked.connect(self.getReportEvent)
        return btnBox

    def addFormTxt(self) -> None:
        '''
        Метод для отображения окна ввода интервалов пользователем.
        '''
        if self.intervalsToggle.isChecked():
            self.intervalsTxt.show()
        else:
            self.intervalsTxt.hide()

    def updateAdrComboBox(self) -> None:
        current_category = self.categoryComboBox.currentText()
        adrs = self.controller.get_data()[current_category].keys()
        self.adrComboBox.clear()
        self.adrComboBox.addItems(adrs)

    def getReportEvent(self) -> None:
        '''
        Метод генерации отчёта по полету и сохранения его на диск.
        В зависимости от положения переключателя 
        отчет генерируется автоматически или по данным пользователя.
        '''
        text = self.intervalsTxt.toPlainText()
        if self.intervalsToggle.isChecked() and not text:
            self.parent.setNotify('предупреждение', "Need input intervals")
            return
        if not self.intervalsToggle.isChecked():
            text = ''
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            "",
            "xlsx Files (*.xlsx);;All Files(*)",
            options=options)
        if filePath:
            try:
                category = self.categoryComboBox.currentText()
                adr = self.adrComboBox.currentText()
                coef = self.parent.settings.value('koef_for_intervals')
                plane = self.planeComboBox.currentText()
                planeSettings = { 
                    'name': plane,
                    'values': self.parent.settings.value('planes')[plane]
                }
                self.controller.save_report(
                    filePath, category, adr, planeSettings, coef, text
                )
                self.filePath = filePath
                self.openButton.show()
                self.parent.setNotify(
                    'успех', f'Отчёт сохранён в {filePath}')
            except PermissionError:
                self.parent.setNotify(
                    'ошибка', 'Сохраняемый файл открыт в другой программе')
            except FileNotFoundError:
                self.parent.setNotify(
                    'ошибка', 'Не найден шаблон xls_template.xlsx, проверьте его наличие')
            except AttributeError:
                self.parent.setNotify(
                    'ошибка', 'Ошибка в данных или в коэффициентах')
            except Exception as e:
                self.parent.setNotify('ошибка', str(e))

    def openFile(self):
        '''
        Метод открытия файла отчёта, если он был создан.
        '''
        startfile(self.filePath)
        self.close()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)
