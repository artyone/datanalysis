from os import startfile, path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout,
    QComboBox, QDialogButtonBox,
    QFileDialog
)
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtCore import Qt


class Save_csv_window(QWidget):
    '''
    Класс окна выбора категории и адр для сохранения csv файла
    parent - родительское окно
    controller - контроллер для получения данных.
    '''

    def __init__(self, controller, parent) -> None:
        super().__init__()
        self.parent = parent
        self.controller = controller
        self.initUI()

    def initUI(self) -> None:
        '''Метод отрисовки основных элементов окна.'''
        self.setGeometry(0, 0, 360, 130)
        self.setWindowTitle("Сохранить в CSV...")
        layout = QVBoxLayout(self)

        input_box = self.get_input_box()
        button_box = self.get_button_box()

        layout.addLayout(input_box)
        layout.addWidget(button_box)

    def get_input_box(self) -> QFormLayout:
        '''Метод инициализации элементов ввода и выбора пользователя'''
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(20)

        self.category_combo_box = QComboBox()
        categories = self.controller.get_data().keys()
        self.category_combo_box.addItems(categories)
        self.category_combo_box.activated.connect(self.update_adr_combo_box)

        self.adr_combo_box = QComboBox()
        current_category = self.category_combo_box.currentText()
        adrs = self.controller.get_data()[current_category].keys()
        self.adr_combo_box.addItems(adrs)

        form_layout.addRow('Категория', self.category_combo_box)
        form_layout.addRow('АДР', self.adr_combo_box)
        return form_layout

    def get_button_box(self) -> QDialogButtonBox:
        '''Метод инициализации кнопок на форме'''
        button_box = QDialogButtonBox()
        button_box.setStandardButtons(
            QDialogButtonBox.Open |
            QDialogButtonBox.Save |
            QDialogButtonBox.Cancel
        )
        button_box.rejected.connect(self.close)

        self.open_button = button_box.button(QDialogButtonBox.Open)
        self.open_button.clicked.connect(self.open_dir_event)
        self.open_button.hide()
        self.open_button.setText('Открыть папку')

        save_button = button_box.button(QDialogButtonBox.Save)
        save_button.clicked.connect(self.save_csv_event)
        save_button.setText('Сохранить')

        button_box.button(QDialogButtonBox.Cancel).setText('Отмена')
        return button_box

    def update_adr_combo_box(self) -> None:
        current_category = self.category_combo_box.currentText()
        adrs = self.controller.get_data()[current_category].keys()
        self.adr_combo_box.clear()
        self.adr_combo_box.addItems(adrs)

    def save_csv_event(self):
        category = self.category_combo_box.currentText()
        adr = self.adr_combo_box.currentText()
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            "",
            f"CSV Files (*.csv);;All Files(*)",
            options=options
        )
        if file_path:
            try:
                self.controller.save_csv(file_path, category, adr)
                self.parent.setNotify(
                    'успех', f'CSV файл сохранен {file_path}')
                self.open_button.show()
                self.filePath = file_path
            except PermissionError:
                self.parent.setNotify(
                    'ошибка', 'Файл отркрыт в другой программе')
            except Exception as e:
                self.parent.setNotify('ошибка', str(e))

    def open_dir_event(self):
        '''
        Метод открытия папки с файлом, если файл был сохранён
        '''
        folder_path = path.dirname(self.filePath)
        startfile(folder_path)
        self.close()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)

    def updateWidget(self):
        new_categories = {
            name: value.keys()
            for name, value in self.controller.get_data().items()
        }
        self.category_combo_box.clear()
        self.category_combo_box.addItems(new_categories.keys())
        self.update_adr_combo_box()
