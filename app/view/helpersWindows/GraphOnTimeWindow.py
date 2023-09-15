import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout


class GraphOnTimeWidget(QWidget):
    def __init__(self, parent) -> None:
        super().__init__()
        self.parent = parent
        self.setWindowTitle('Выберите время')
        self.setGeometry(100, 100, 400, 200)

        start_label = QLabel('Старт:', self)
        stop_label = QLabel('Стоп:', self)

        self.start_input = QLineEdit(self)
        self.start_input.textChanged.connect(self.validate_inputs)

        self.stop_input = QLineEdit(self)
        self.stop_input.textChanged.connect(self.validate_inputs)

        self.ok_button = QPushButton('ОК', self)
        self.ok_button.setEnabled(False)
        self.ok_button.clicked.connect(self.create_graph)

        cancel_button = QPushButton('Отмена', self)
        cancel_button.clicked.connect(self.close)

        layout = QVBoxLayout()
        layout.addWidget(start_label)
        layout.addWidget(self.start_input)
        layout.addWidget(stop_label)
        layout.addWidget(self.stop_input)
        layout.addWidget(self.ok_button)
        layout.addWidget(cancel_button)

        self.setLayout(layout)

    def create_graph(self) -> None:
        start = float(self.start_input.text())
        stop = float(self.stop_input.text())
        self.parent.create_graph(start_time=start, stop_time=stop)
        self.parent.graph_on_time_window = None
        self.close()

    def validate_inputs(self):
        try:
            start = float(self.start_input.text())
            stop = float(self.stop_input.text())
            if start < stop:
                self.ok_button.setEnabled(True)
            else:
                self.ok_button.setEnabled(False)
        except:
            self.ok_button.setEnabled(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = QMainWindow()
    widget = GraphOnTimeWidget(window)
    window.setCentralWidget(widget)
    window.show()
    sys.exit(app.exec_())