from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout,
    QLabel, QComboBox, QHBoxLayout,
    QDialogButtonBox, QFileDialog,
    QPlainTextEdit, QCheckBox
)
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtCore import Qt
from qtwidgets import AnimatedToggle
from os import startfile
from functools import partial


class LineChooseWidget(QWidget):
    def __init__(self, text, categories, parent=None) -> None:
        super().__init__()
        self.parent = parent
        self.categories = categories
        layout = QHBoxLayout()
        self.setLayout(layout)

        textLabel = QLabel(text)
        textLabel.setFixedWidth(115)
        self.categoryComboBox = QComboBox()
        self.categoryComboBox.addItems(self.categories.keys())
        self.adrComboBox = QComboBox()
        self.categoryComboBox.activated.connect(
            self.updateAdrComboBox
        )
        self.updateAdrComboBox()
        layout.addWidget(textLabel)
        layout.addWidget(self.categoryComboBox)
        layout.addWidget(self.adrComboBox)

    def updateAdrComboBox(self) -> None:
        currentCategory = self.categoryComboBox.currentText()
        self.adrComboBox.clear()
        self.adrComboBox.addItems(self.categories[currentCategory])

    def getValues(self) -> tuple:
        category = self.categoryComboBox.currentText()
        adr = self.adrComboBox.currentText()
        return {'category': category, 'adr': adr}


class ChooseWidget(QWidget):
    def __init__(self, categories, parent=None) -> None:
        super().__init__()
        self.parent = parent
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.lineSourceWidget = LineChooseWidget(
            'Исходные данные', categories
        )
        self.lineCalcWidget = LineChooseWidget(
            'Посчитанные данные', categories
        )

        layout.addWidget(self.lineSourceWidget)
        layout.addWidget(self.lineCalcWidget)

        self.hide()

    def getValues(self):
        sourceValues = self.lineSourceWidget.getValues()
        calcValues = self.lineCalcWidget.getValues()
        return {'source': sourceValues, 'calc': calcValues}


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

    def initUI(self) -> None:
        self.setWindowTitle("Создание отчёта")
        layout = QFormLayout()
        self.setLayout(layout)

        self.planeComboBox = QComboBox()
        planes = self.parent.settings.value('planes').keys()
        self.planeComboBox.addItems(planes)
        layout.addRow('Самолёт', self.planeComboBox)


        categories = {
            name: value.keys() 
            for name, value in self.controller.get_data().items()
        }

        self.pnkCheckBox = QCheckBox('Добавить в отчёт даные ПНК')
        self.pnkWidget = ChooseWidget(categories)
        self.pnkCheckBox.stateChanged.connect(
            partial(self.widgetStateChanged, self.pnkWidget)
        )
        layout.addRow(self.pnkCheckBox)
        layout.addRow(self.pnkWidget)

        self.dissCheckBox = QCheckBox('Добавить в отчёт даные ДИСС')
        self.dissWidget = ChooseWidget(categories)
        self.dissCheckBox.stateChanged.connect(
            partial(self.widgetStateChanged, self.dissWidget)
        )
        #TODO убрать после реализации подсчёта дисс
        self.dissCheckBox.hide()
        layout.addRow(self.dissCheckBox)
        layout.addRow(self.dissWidget)
        layout.addRow(self.inputBox())
        layout.addRow(self.intervalsTxt)
        layout.addRow(self.buttonBox())

    def widgetStateChanged(self, widget, state) -> None:
        if state:
            widget.show()
        else:
            widget.hide()
            self.adjustSize()
        if self.pnkCheckBox.isChecked() or self.dissCheckBox.isChecked():
            self.saveButton.show()
        else: self.saveButton.hide()


    def inputBox(self) -> QHBoxLayout:
        self.toggle = AnimatedToggle()
        self.toggle.setChecked(True)
        self.intervalsTxt = QPlainTextEdit()
        self.intervalsTxt.setFixedHeight(300)
        self.toggle.stateChanged.connect(
            partial(self.widgetStateChanged, self.intervalsTxt)
        )

        layout = QHBoxLayout()
        layout.addWidget(
            QLabel('<b>Интервалы:</b>'), 2
        )
        layout.addWidget(
            QLabel('Рассчитать автоматически'),
            1,
            alignment=Qt.AlignRight
        )
        layout.addWidget(self.toggle, 1)
        layout.addWidget(QLabel('Ввести вручную'), 2)
        return layout

    def buttonBox(self) -> QDialogButtonBox:
        buttonBox = QDialogButtonBox()
        buttonBox.setStandardButtons(
            QDialogButtonBox.Open |
            QDialogButtonBox.Save |
            QDialogButtonBox.Cancel
        )
        buttonBox.rejected.connect(self.close)

        self.openButton = buttonBox.button(QDialogButtonBox.Open)
        self.openButton.clicked.connect(self.openFileEvent)
        self.openButton.hide()

        self.saveButton = buttonBox.button(QDialogButtonBox.Save)
        self.saveButton.clicked.connect(self.getReportEvent)
        self.saveButton.hide()
        return buttonBox

    def getReportEvent(self) -> None:
        '''
        Метод генерации отчёта по полету и сохранения его на диск.
        В зависимости от положения переключателя 
        отчет генерируется автоматически или по данным пользователя.
        '''
        #TODO пока отчёт только по данным пнк
        text = self.intervalsTxt.toPlainText()
        if self.toggle.isChecked() and not text:
            self.parent.setNotify('предупреждение', "Введите интервалы.")
            return
        if not self.toggle.isChecked():
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
                values = self.pnkWidget.getValues()
                coef = self.parent.settings.value('koef_for_intervals')
                plane = self.planeComboBox.currentText()
                planeSettings = { 
                    'name': plane,
                    'values': self.parent.settings.value('planes')[plane]
                }
                self.controller.save_report(
                    filePath, values, planeSettings, coef, text
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

    def openFileEvent(self) -> None:
        '''
        Метод открытия файла отчёта, если он был создан.
        '''
        startfile(self.filePath)
        self.close()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = ReportWindow()
    window.show()
    sys.exit(app.exec_())
