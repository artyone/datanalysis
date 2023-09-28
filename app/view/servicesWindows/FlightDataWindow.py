from PyQt5.QtWidgets import (
    QLineEdit, QLabel, QFormLayout, QDateTimeEdit,
    QPlainTextEdit, QComboBox, QDialogButtonBox
)
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtCore import Qt, QDate
from ..helpersWindows import BaseWidget


class FlightDataWindow(BaseWidget):
    def __init__(self, name, parent) -> None:
        super().__init__(name, parent)
        self.setWindowTitle("Данные полёта")
        self.correction_names = [
            'kren_DISS_grad', 'kurs_DISS_grad', 'tang_DISS_grad',
            'popr_prib_cor_B_cod', 'popr_prib_cor_V_cod', 'popr_prib_cor_FI_cod'
        ]
        self.initUI()

    def initUI(self) -> None:

        layout = QFormLayout(self)

        self.flight_date = QDateTimeEdit(self)
        self.flight_date.setDisplayFormat('dd.MM.yyyy')
        self.flight_date.setCalendarPopup(True)

        layout.addRow('Дата полёта: ', self.flight_date)

        self.plane_combo_box = QComboBox(self)
        planes = self.parent.settings.value('planes')
        self.plane_combo_box.addItems(planes)
        layout.addRow('Самолёт: ', self.plane_combo_box)

        self.frw_version_line_edit = QLineEdit(self)
        layout.addRow('Версия проши: ', self.frw_version_line_edit)

        self.intervals_text_edit = QPlainTextEdit(self)
        self.intervals_text_edit.setFixedHeight(200)
        layout.addRow('Участки: ', self.intervals_text_edit)

        self.comments_text_edit = QPlainTextEdit(self)
        self.comments_text_edit.setFixedHeight(200)
        layout.addRow('Комментарии: ', self.comments_text_edit)

        correction_label = QLabel('Поправки')
        correction_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(correction_label)

        for correction_name in self.correction_names:
            line_edit = QLineEdit(self)
            setattr(self, correction_name + '_line_edit', line_edit)
            layout.addRow(correction_name, line_edit)

        button_box = QDialogButtonBox()
        button_box.setStandardButtons(
            QDialogButtonBox.Save |
            QDialogButtonBox.Cancel
        )
        button_box.button(QDialogButtonBox.Save).setText('Сохранить')
        button_box.button(QDialogButtonBox.Cancel).setText('Отмена')
        button_box.rejected.connect(self.close)
        button_box.accepted.connect(self.save_event)

        layout.addWidget(button_box)

        self.setLayout(layout)
        self.set_current_values()
        self.adjustSize()
        self.setGeometry(0, 0, 800, self.height())

    def set_current_values(self):
        flight_data = self.parent.controller.get_data().get('FLIGHT_DATA', None)
        if flight_data is None:
            self.flight_date.setDate(QDate.currentDate())
            return

        if 'date' in flight_data:
            self.flight_date.setDate(
                QDate.fromString(flight_data['date'], 'dd.MM.yyyy')
            )
        else:
            self.flight_date.setDate(QDate.currentDate())

        if 'plane' in flight_data:
            self.plane_combo_box.setCurrentText(flight_data['plane'])

        if 'frw_version' in flight_data:
            self.frw_version_line_edit.setText(flight_data['frw_version'])

        if 'intervals' in flight_data:
            self.intervals_text_edit.setPlainText(flight_data['intervals'])

        if 'comments' in flight_data:
            self.comments_text_edit.setPlainText(flight_data['comments'])

        for correction_name in self.correction_names:
            if correction_name in flight_data:
                getattr(self, correction_name +
                        '_line_edit').setText(flight_data[correction_name])

    def save_event(self):
        data: dict = self.parent.controller.get_data()
        flight_data = data.get('FLIGHT_DATA', {})
        flight_data['date'] = self.flight_date.date().toString('dd.MM.yyyy')
        flight_data['plane'] = self.plane_combo_box.currentText()
        flight_data['frw_version'] = self.frw_version_line_edit.text()
        flight_data['intervals'] = self.intervals_text_edit.toPlainText()
        flight_data['comments'] = self.comments_text_edit.toPlainText()
        for correction_name in self.correction_names:
            flight_data[correction_name] = getattr(
                self, correction_name + '_line_edit').text()
        data['FLIGHT_DATA'] = flight_data
        self.parent.send_notify(
            'информация', 'Не забудьте сохранить данные в gzip'
        )
        self.close()