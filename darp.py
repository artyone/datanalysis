import sys
from app.view.mainWindow import MainWindow
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QApplication
from app.resource.constants import (
    ORGANIZATION_DOMAIN, 
    ORGANIZATION_NAME, 
    APPLICATION_NAME, 
    VERSION, 
    EXIT_CODE_REBOOT
    )


def main():
    '''Точка входа в программу.'''
    QCoreApplication.setOrganizationName(ORGANIZATION_NAME)
    QCoreApplication.setOrganizationDomain(ORGANIZATION_DOMAIN)
    QCoreApplication.setApplicationName(APPLICATION_NAME)
    QCoreApplication.setApplicationVersion(VERSION)

    while True:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        iface = MainWindow(app)
        iface.show()
        exit_code = app.exec_()
        if exit_code != EXIT_CODE_REBOOT:
            break


if __name__ == '__main__':
    main()