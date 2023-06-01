from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QStackedLayout,
    QLineEdit, QPushButton, QFormLayout,
    QComboBox
)
from functools import partial


class ValueErrorPlanes(Exception):
    pass


class InfoPlane(QStackedLayout):
    def __init__(self, data, parent):
        super().__init__()
        self.data: dict = data
        self.parent: PlaneTab = parent
        self.widgets: dict = {}
        self.initUI(self.data)

    def initUI(self, data):
        for planeName, values in data.items():
            widget = QWidget()
            layout = QFormLayout()
            planeNameEdit = QLineEdit(str(planeName))
            planeNameEdit.textEdited.connect(
                partial(self.changeName, planeNameEdit)
            )
            layout.addRow('Имя', planeNameEdit)
            widget.setLayout(layout)
            self.widgets[planeNameEdit] = {}
            for name, value in values.items():
                lineEdit = QLineEdit(str(value))
                layout.addRow(name, lineEdit)
                self.widgets[planeNameEdit][name] = lineEdit
            deleteButton = QPushButton('Удалить самолёт')
            deleteButton.clicked.connect(
                partial(self.deletePlane, widget, planeNameEdit)
            )
            layout.addRow(deleteButton)
            self.addWidget(widget)

    def deletePlane(self, widgetPlane: QWidget, planeNameEdit: QLineEdit):
        widgetPlane.deleteLater()
        del self.widgets[planeNameEdit]
        self.parent.comboBox.removeItem(self.currentIndex())

    def getValues(self):
        values = {}
        for planeNameWidget, coefWidgets in self.widgets.items():
            planeName = planeNameWidget.text()
            if planeName == '':
                raise ValueErrorPlanes(
                    'Не задано имя самолёта на вкладке настроек самолёта'
                )
            values[planeName] = {}
            for nameCoef, widget in coefWidgets.items():
                if widget.text() == '':
                    raise ValueErrorPlanes(
                        f'Не задан коэффициент для самолёта {planeName} на вкладке настроек самолёта'
                    )
                values[planeName][nameCoef] = widget.text()
        return values

    def changeName(self, textWidget: QLineEdit) -> None:
        text = textWidget.text()
        currentIndex = self.currentIndex()
        self.parent.comboBox.setItemText(currentIndex, text)

    def addPlane(self):
        try:
            self.initUI({
                '': {
                    name: '' for name in list(self.data.values())[0]
                }
            })
        except:
            headers = (
                'popr_prib_cor_V_cod',
                'popr_prib_cor_FI_cod',
                'popr_prib_cor_B_cod',
                'kurs_DISS_grad',
                'kren_DISS_grad',
                'tang_DISS_grad',
                'k',
                'k1'
            )
            self.initUI({
                '': {
                        name: '' for name in headers
                        }
            })


class PlaneTab(QWidget):
    def __init__(self, data) -> None:
        super().__init__()
        self.data = data

        layout = QVBoxLayout()
        addButton = QPushButton('Добавить самолёт')
        addButton.clicked.connect(self.addPlane)
        self.comboBox = QComboBox()
        self.comboBox.addItems(self.data)
        self.comboBox.currentIndexChanged.connect(self.changePage)
        layout.addWidget(addButton)
        layout.addWidget(self.comboBox)

        self.infoPlaneLayout = InfoPlane(self.data, self)
        layout.addLayout(self.infoPlaneLayout)

        self.setLayout(layout)

    def addPlane(self):
        self.comboBox.addItem('')
        self.infoPlaneLayout.addPlane()
        lastIndex = self.comboBox.count() - 1
        self.comboBox.setCurrentIndex(lastIndex)
        self.changePage(self.comboBox.currentIndex())

    def changePage(self, index):
        self.infoPlaneLayout.setCurrentIndex(index)

    def getValues(self):
        return self.infoPlaneLayout.getValues()


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    headers = (
        'popr_prib_cor_V_cod',
        'popr_prib_cor_FI_cod',
        'popr_prib_cor_B_cod',
        'kurs_DISS_grad',
        'kren_DISS_grad',
        'tang_DISS_grad',
        'k',
        'k1'
    )
    data = {
        'mdm': dict(zip(headers, (5, 14, 2, -0.62, 0.032, 3.33 - 0.032, 1, 1))),
        'm2': dict(zip(headers, (7, 6, 1, 0.2833, 0.032, 3.33 - 0.2, 1, 1))),
        'IL78m90a': dict(zip(headers, (7, 15, 1, 0.27, 0, 3.33, 1, 1))),
        'IL76md90a': dict(zip(headers, (6, 15, 1, 0 - 0.665, -0.144, 3.33, 1, 1))),
        'tu22': dict(zip(headers, (6, 6, 2, 0, 0, 0, 1 / 3.6, 0.00508))),
        'tu160': dict(zip(headers, (6, 10, 1, 0, 0, -2.5, 1, 1)))
    }
    app = QApplication(sys.argv)
    window = PlaneTab(data)
    window.show()
    print(window.getValues())
    sys.exit(app.exec_())
