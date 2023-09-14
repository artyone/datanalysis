from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout,
    QCheckBox, QComboBox, QHBoxLayout,
    QDialogButtonBox, QFileDialog,
    QLineEdit, QPushButton
)
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtCore import Qt


class Open_file_window(QWidget):
    '''
    Класс окна для выбора json для парсинга данных файла txt или csv
    parent - родительское окно
    controller - контроллер для получения данных.
    settings - настройки приложения.
    '''

    def __init__(self, controller, filetype, categories, parent=None):
        super().__init__()
        self.parent = parent
        self.controller = controller
        self.filetype = filetype
        self.categories = categories
        self.settings = self.parent.settings
        self.initUI()

    def initUI(self):
        '''
        Метод отрисовки основных элементов окна.
        '''
        self.setGeometry(0, 0, 400, 200)
        self.setWindowTitle(f'Открыть {self.filetype} файл...')
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        layout = QVBoxLayout(self)

        self.init_input_block()
        self.init_button_block()

        layout.addLayout(self.form_layout)
        layout.addWidget(self.button_box)

    def init_input_block(self) -> None:
        '''Метод инициализации элементов ввода и выбора пользователя'''
        self.form_layout = QFormLayout()
        self.form_layout.setVerticalSpacing(20)

        self.init_category_block()

        self.load_unknown_check_box = QCheckBox()
        self.load_unknown_check_box.setChecked(True)
        self.load_unknown_check_box.setText(
            'загружать незвестные элементы'
        )

        self.form_layout.addRow('Категория', self.category_combo_box)
        if self.filetype != 'pdd':
            self.form_layout.addRow('АДР', self.adr_combo_box)
        else:
            self.load_unknown_check_box.hide()
        self.form_layout.addRow('Файл', self.init_browse_block())
        self.form_layout.addRow(self.load_unknown_check_box)

    def init_category_block(self) -> None:
        self.category_combo_box = QComboBox()
        self.category_combo_box.addItems(self.categories.keys())
        self.adr_combo_box = QComboBox()
        adrs = self.categories[self.category_combo_box.currentText()]
        self.adr_combo_box.addItems([adr['adr_name'] for adr in adrs])
        self.category_combo_box.activated.connect(self.update_adr_comboBox)

    def init_browse_block(self) -> QHBoxLayout:
        horizontal_layer = QHBoxLayout()
        self.filepath_line_edit = QLineEdit()
        browse_button = QPushButton()
        browse_button.setText('...')
        browse_button.setFixedSize(40, 22)
        browse_button.clicked.connect(self.open_file_dialog)
        horizontal_layer.addWidget(self.filepath_line_edit)
        horizontal_layer.addWidget(browse_button)
        horizontal_layer.setSpacing(15)
        return horizontal_layer

    def init_button_block(self) -> None:
        '''Метод инициализации кнопок на форме'''
        self.button_box = QDialogButtonBox()
        self.button_box.setStandardButtons(
            QDialogButtonBox.Open | QDialogButtonBox.Cancel
        )
        self.button_box.rejected.connect(self.close)

        self.openButton = self.button_box.button(QDialogButtonBox.Open)
        self.openButton.clicked.connect(
            self.open_file_pdd if self.filetype == 'pdd' else self.open_file_txt
        )

    def update_adr_comboBox(self) -> None:
        adrs = self.categories[self.category_combo_box.currentText()]
        self.adr_combo_box.clear()
        self.adr_combo_box.addItems([adr['adr_name'] for adr in adrs])

    def open_file_dialog(self) -> None:
        filePath, check = QFileDialog.getOpenFileName(
            None,
            'Open file',
            '',
            f'Open File (*.{self.filetype})'
        )
        if check:
            self.filepath_line_edit.setText(filePath)

    def open_file_txt(self) -> None:
        category = self.category_combo_box.currentText()
        adr = self.adr_combo_box.currentText()
        filepath = self.filepath_line_edit.text()
        try:
            self.controller.load_text(
                filepath,
                category,
                adr,
                self.filetype,
                self.categories[category],
                self.load_unknown_check_box.isChecked()
            )
            self.parent.tree_widget.update_check_box()
            self.parent.send_notify(
                'успех', f'Файл {filepath} открыт'
            )
            self.parent.last_file_label.setText(
                    f'Последний открытый файл: {filepath}   '
            )
            self.parent.destroy_child_window()
        except Exception as e:
            self.parent.send_notify('ошибка', str(e))

    def open_file_pdd(self) -> None:
        category = self.category_combo_box.currentText()
        json_data = self.categories[category]
        filepath = self.filepath_line_edit.text()
        try:
            self.controller.load_pdd(
                filepath,
                category,
                json_data
            )
            self.parent.tree_widget.update_check_box()
            self.parent.send_notify(
                'успех', f'Файл {filepath} открыт'
            )
            self.parent.last_file_label.setText(
                    f'Последний открытый файл: {filepath}   '
                )
            self.parent.destroy_child_window()
        except Exception as e:
            self.parent.send_notify('ошибка', str(e))

    def closeEvent(self, event) -> None:
        '''
        Переназначение функции закрытия, для уничтожение окна.
        '''
        self.deleteLater()
        self.parent.open_file_window = None
        event.accept()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
