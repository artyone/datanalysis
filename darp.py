from sys import argv
from app.view import Main_window
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QApplication
from app.resource.constants import (
    ORGANIZATION_DOMAIN,
    ORGANIZATION_NAME,
    APPLICATION_NAME,
    APPLICATION_VERSION
)
# TODO продумать открытые файлы


def main() -> None:
    '''Точка входа в программу.'''
    QCoreApplication.setOrganizationName(ORGANIZATION_NAME)
    QCoreApplication.setOrganizationDomain(ORGANIZATION_DOMAIN)
    QCoreApplication.setApplicationName(APPLICATION_NAME)
    QCoreApplication.setApplicationVersion(APPLICATION_VERSION)

    app = QApplication(argv)
    app.setStyle('Fusion')
    iface = Main_window(app)
    iface.show()
    app.exec_()


if __name__ == '__main__':
    main()
