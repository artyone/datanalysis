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


class Line_choose_widget(QWidget):
    '''Виджет выбора категории и адр'''

    def __init__(self, text, categories) -> None:
        super().__init__()
        self.categories = categories
        layout = QHBoxLayout(self)

        text_label = QLabel(text, self)
        text_label.setFixedWidth(115)
        self.category_combo_box = QComboBox(self)
        self.category_combo_box.addItems(self.categories)
        self.adr_combo_box = QComboBox()
        self.category_combo_box.activated.connect(
            self.update_adr_combo_box
        )
        self.update_adr_combo_box()
        layout.addWidget(text_label)
        layout.addWidget(self.category_combo_box)
        layout.addWidget(self.adr_combo_box)

    def update_adr_combo_box(self) -> None:
        # обновляем адр при смене категории
        current_category = self.category_combo_box.currentText()
        self.adr_combo_box.clear()
        self.adr_combo_box.addItems(self.categories[current_category])

    def get_values(self) -> tuple:
        # получаем значения с виджета
        category = self.category_combo_box.currentText()
        adr = self.adr_combo_box.currentText()
        return {'category': category, 'adr': adr}
    
    def update_categories(self, new_categories: dict) -> None:
        self.categories = new_categories
        self.category_combo_box.clear()
        self.category_combo_box.addItems(self.categories)
        self.update_adr_combo_box()


class Choose_widget(QWidget):
    '''Виджет для выбора исходных и посчитаных данных'''

    def __init__(self, categories) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.line_source_widget = Line_choose_widget(
            'Исходные данные', categories
        )
        self.line_calc_widget = Line_choose_widget(
            'Посчитанные данные', categories
        )

        layout.addWidget(self.line_source_widget)
        layout.addWidget(self.line_calc_widget)

        self.hide()

    def get_values(self) -> dict:
        # получаем словарь данных с всех виджетов выбора
        source_values = self.line_source_widget.get_values()
        calc_values = self.line_calc_widget.get_values()
        return {'source': source_values, 'calc': calc_values}
    
    def update_categories(self, categories) -> None:
        self.line_source_widget.update_categories(categories)
        self.line_calc_widget.update_categories(categories)


class Report_window(QWidget):
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
        self.intervals_from_txt = None
        self.initUI()

    def initUI(self) -> None:
        self.setWindowTitle("Создание отчёта")
        layout = QFormLayout(self)

        self.plane_combo_box = QComboBox()  # выбор самолёта
        planes = self.parent.settings.value('planes').keys()
        self.plane_combo_box.addItems(planes)
        layout.addRow('Самолёт', self.plane_combo_box)

        categories = {
            name: value.keys()
            for name, value in self.controller.get_data().items()
        }

        self.pnk_check_box = QCheckBox('Добавить в отчёт даные ПНК')
        self.pnk_widget = Choose_widget(categories)
        self.pnk_check_box.stateChanged.connect(
            partial(self.widget_state_changed, self.pnk_widget)
        )
        layout.addRow(self.pnk_check_box)
        layout.addRow(self.pnk_widget)

        self.diss_check_box = QCheckBox('Добавить в отчёт даные ДИСС')
        self.diss_widget = Choose_widget(categories)
        self.diss_check_box.stateChanged.connect(
            partial(self.widget_state_changed, self.diss_widget)
        )
        # TODO убрать после реализации подсчёта дисс
        self.diss_check_box.hide()
        layout.addRow(self.diss_check_box)
        layout.addRow(self.diss_widget)
        layout.addRow(self.get_input_box())
        layout.addRow(self.intervals_from_txt)
        layout.addRow(self.get_button_box())

    def widget_state_changed(self, widget, state) -> None:
        # скрыть отобразить виджет при смене чекбоксов или тумблера
        if state:
            widget.show()
        else:
            widget.hide()
            self.adjustSize()
        if self.pnk_check_box.isChecked() or self.diss_check_box.isChecked():
            self.save_button.show()
        else:
            self.save_button.hide()

    def get_input_box(self) -> QHBoxLayout:
        # поле ввода интервалов
        self.toggle = AnimatedToggle()
        self.toggle.setChecked(True)
        self.intervals_from_txt = QPlainTextEdit()
        self.intervals_from_txt.setFixedHeight(300)
        self.toggle.stateChanged.connect(
            partial(self.widget_state_changed, self.intervals_from_txt)
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

    def get_button_box(self) -> QDialogButtonBox:
        # блок кнопок снизу
        button_box = QDialogButtonBox()
        button_box.setStandardButtons(
            QDialogButtonBox.Open |
            QDialogButtonBox.Save |
            QDialogButtonBox.Cancel
        )
        button_box.rejected.connect(self.close)

        self.open_button = button_box.button(QDialogButtonBox.Open)
        self.open_button.clicked.connect(self.open_file_event)
        self.open_button.hide()

        self.save_button = button_box.button(QDialogButtonBox.Save)
        self.save_button.clicked.connect(self.get_report_event)
        self.save_button.hide()
        return button_box

    def get_report_event(self) -> None:
        '''
        Метод генерации отчёта по полету и сохранения его на диск.
        В зависимости от положения переключателя 
        отчет генерируется автоматически или по данным пользователя.
        '''
        # TODO пока отчёт только по данным пнк
        text = self.intervals_from_txt.toPlainText()
        if self.toggle.isChecked() and not text:
            self.parent.send_notify(
                'предупреждение', 'Введите интервалы'
            )
            return
        if not self.toggle.isChecked():
            text = ''
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            "",
            "xlsx Files (*.xlsx);;All Files(*)",
            options=options)
        if file_path:
            try:
                # получаем данные виджетов выбора
                values = self.pnk_widget.get_values()
                # получаем общие коэффициенты
                coef = self.parent.settings.value('koef_for_intervals')
                plane = self.plane_combo_box.currentText()
                # формируем настройки самолёта
                plane_settings = {
                    'name': plane,
                    'values': self.parent.settings.value('planes')[plane]
                }
                self.controller.save_report(
                    file_path, values, plane_settings, coef, text
                )
                self.file_path = file_path
                self.open_button.show()
                self.parent.send_notify(
                    'успех', f'Отчёт сохранён в {self.file_path}'
                )
            except PermissionError:
                self.parent.send_notify(
                    'ошибка', 'Сохраняемый файл открыт в другой программе'
                )
            except FileNotFoundError:
                self.parent.send_notify(
                    'ошибка', 'Не найден шаблон xls_template.xlsx, проверьте его наличие'
                )
            except AttributeError:
                self.parent.send_notify(
                    'ошибка', 'Ошибка в данных или в коэффициентах'
                )
            except Exception as e:
                self.parent.send_notify('ошибка', str(e))

    def open_file_event(self) -> None:
        '''
        Метод открытия файла отчёта, если он был создан.
        '''
        startfile(self.file_path)
        self.close()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # закрыть по esc
        if event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)

    def updateWidget(self):
        new_categories = {
            name: value.keys()
            for name, value in self.controller.get_data().items()
        }
        self.pnk_widget.update_categories(new_categories)
        self.diss_widget.update_categories(new_categories)
        planes = self.parent.settings.value('planes').keys()
        self.plane_combo_box.clear()
        self.plane_combo_box.addItems(planes)


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = Report_window()
    window.show()
    sys.exit(app.exec_())
