from sys import argv
from PyQt5.QtCore import QCoreApplication, QSettings
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPlainTextEdit,
    QWidget, QPushButton, QVBoxLayout,
    QMessageBox
)
import json


ORGANIZATION_NAME: str = 'Radiopribor'
ORGANIZATION_DOMAIN: str = 'zrp.ru'
APPLICATION_NAME: str = 'DARP'


class MainWindow(QMainWindow):

    def __init__(self) -> None:
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setGeometry(400, 300, 400, 600)
        self.qsettings = QSettings()

        string = self.getStringFromSettings(self.qsettings)
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        self.plainText = QPlainTextEdit()
        self.plainText.setPlainText(string)
        layout.addWidget(self.plainText)

        saveButton = QPushButton('Сохранить')
        saveButton.clicked.connect(self.save)
        layout.addWidget(saveButton)

        delButton = QPushButton('Удалить настройки')
        delButton.clicked.connect(self.delete)
        layout.addWidget(delButton)

        self.setCentralWidget(widget)

    @staticmethod
    def getStringFromSettings(qsettings: QSettings) -> str:
        settings = {
            key: qsettings.value(key)
            for key in qsettings.allKeys()
        }
        string = json.dumps(settings, indent=4, ensure_ascii=False)
        return string

    def save(self) -> None:
        string = self.plainText.toPlainText()
        settings = json.loads(string)
        for key, value in settings.items():
            self.qsettings.setValue(key, value)
        QMessageBox.information(self, "Уведомление", "Настройки сохранены")

    def delete(self) -> None:
        self.qsettings.clear()
        self.plainText.clear()
        QMessageBox.information(self, "Уведомление", "Настройки удалены")

if __name__ == "__main__":
    QCoreApplication.setOrganizationName(ORGANIZATION_NAME)
    QCoreApplication.setOrganizationDomain(ORGANIZATION_DOMAIN)
    QCoreApplication.setApplicationName(APPLICATION_NAME)

    app = QApplication(argv)
    app.setStyle('Fusion')
    iface = MainWindow()

    iface.show()
    app.exec_()
