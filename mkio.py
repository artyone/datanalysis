import sys
from app.view.mainWindow import MainWindow
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QApplication


ORGANIZATION_NAME = 'Radiopribor'
ORGANIZATION_DOMAIN = 'zrp.ru'
APPLICATION_NAME = 'Radiopribor Mkio'
VERSION = '0.2023.02.27'


def main():
    '''Точка входа в программу.'''
    QCoreApplication.setApplicationName(ORGANIZATION_NAME)
    QCoreApplication.setOrganizationDomain(ORGANIZATION_DOMAIN)
    QCoreApplication.setApplicationName(APPLICATION_NAME)
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    iface = MainWindow()
    iface.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()