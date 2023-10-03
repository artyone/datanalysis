from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt


class BaseWidget(QWidget):
    def __init__(self, obj_name, parent, *args, **kwargs) -> None:
        super().__init__()
        self.parent = parent
        self.obj_name = obj_name

    def closeEvent(self, event):
        self.deleteLater()
        setattr(self.parent, self.obj_name, None)
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
