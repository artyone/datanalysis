from PyQt5.QtWidgets import (
    QVBoxLayout, QFormLayout,
    QCheckBox, QComboBox,
    QDialogButtonBox, QInputDialog
)
from ..helpersWindows import BaseWidget


class CalcWindow(BaseWidget):
    '''
    Класс окна рассчета данных.
    parent - родительское окно
    controller - контроллер для получения данных.
    '''

    def __init__(self, name, controller, parent) -> None:
        super().__init__(name, parent)
        self.controller = controller
        self.initUI()

    def initUI(self) -> None:
        '''
        Метод отрисовки основных элементов окна.
        '''
        self.setGeometry(0, 0, 400, 300)
        self.setWindowTitle("Рассчитать данные")
        dlgLayout = QVBoxLayout()

        self.initInputBlock()
        self.initButtonBlock()

        dlgLayout.addLayout(self.formLayout)
        dlgLayout.addWidget(self.btnBox)
        self.setLayout(dlgLayout)
        self.checkAnyChoice()

    def initInputBlock(self) -> None:
        '''Метод инициализации элементов выбора пользователя'''
        self.formLayout = QFormLayout()
        self.formLayout.setVerticalSpacing(20)

        self.planeComboBox = QComboBox()
        planes = self.parent.settings.value('planes')
        self.planeComboBox.addItems(planes)
        self.planeComboBox.setCurrentText(
            self.parent.settings.value('planeComboBox')
        )
        self.planeComboBox.activated.connect(self.saveComboBoxValue)

        self.initPnkBlock()
        self.initDissBlock()
        self.initUnchBlock()

        self.formLayout.addRow('Самолёт:', self.planeComboBox)
        self.formLayout.addRow('Рассчитать ПНК:', self.calcPnkCheckBox)
        self.formLayout.addRow(self.categoryPnkComboBox)
        self.formLayout.addRow(self.adrPnkComboBox)
        self.formLayout.addRow('Рассчитать ДИСС:', self.calcDissCheckBox)
        # TODO вернуть отображение, при релизе подсчётов дисс
        self.calcDissCheckBox.hide()

        self.formLayout.addRow(self.categoryDissComboBox)
        self.formLayout.addRow(self.adrDissComboBox)

        
        self.formLayout.addRow('Объединить UNCH: ', self.unchCheckBox)
        self.formLayout.addRow(self.categoryUnchComboBox)

    def initPnkBlock(self) -> None:
        '''Метод инициализации блока пнк'''
        self.calcPnkCheckBox = QCheckBox()
        self.calcPnkCheckBox.stateChanged.connect(self.handlerPnk)

        self.categoryPnkComboBox = QComboBox()
        categories = self.controller.get_data().keys()
        self.categoryPnkComboBox.addItems(categories)
        self.categoryPnkComboBox.activated.connect(self.updateAdrPnkComboBox)

        self.adrPnkComboBox = QComboBox()
        current_category = self.categoryPnkComboBox.currentText()
        adrs = self.controller.get_data()[current_category].keys()
        self.adrPnkComboBox.addItems(adrs)

        self.categoryPnkComboBox.hide()
        self.adrPnkComboBox.hide()

    def initDissBlock(self) -> None:
        '''Метод инициализации блока дисс'''
        self.calcDissCheckBox = QCheckBox()
        self.calcDissCheckBox.stateChanged.connect(self.handlerDiss)

        self.categoryDissComboBox = QComboBox()
        categories = self.controller.get_data().keys()
        self.categoryDissComboBox.addItems(categories)
        self.categoryDissComboBox.activated.connect(self.updateAdrDissComboBox)

        self.adrDissComboBox = QComboBox()
        current_category = self.categoryDissComboBox.currentText()
        adrs = self.controller.get_data()[current_category].keys()
        self.adrDissComboBox.addItems(adrs)

        self.categoryDissComboBox.hide()
        self.adrDissComboBox.hide()

    def initUnchBlock(self) -> None:
        '''Метод инициализации блока UNCH'''
        self.unchCheckBox = QCheckBox()
        self.unchCheckBox.stateChanged.connect(self.handlerUnch)
        self.categoryUnchComboBox = QComboBox()
        categories = self.controller.get_data().keys()
        self.categoryUnchComboBox.addItems(categories)
        self.categoryUnchComboBox.hide()

    def initButtonBlock(self) -> None:
        '''Метод инициализации кнопок на форме'''
        self.btnBox = QDialogButtonBox()
        self.btnBox.setStandardButtons(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.btnBox.rejected.connect(self.close)  # type: ignore
        self.okButton = self.btnBox.button(QDialogButtonBox.Ok)
        self.okButton.clicked.connect(self.calculateEvent)
        self.okButton.setText('Рассчитать')
        self.btnBox.button(QDialogButtonBox.Cancel).setText(
            'Отмена'
        )

    def handlerUnch(self) -> None:
        '''Метод скрытия/отображения выбора категории и адр'''
        if self.unchCheckBox.isChecked():
            self.checkAnyChoice()
            self.calcPnkCheckBox.setChecked(False)
            self.calcDissCheckBox.setChecked(False)
            self.categoryUnchComboBox.show()
        else: 
            self.categoryUnchComboBox.hide()
    def handlerPnk(self) -> None:
        '''Метод скрытия/отображения выбора категории и адр пнк'''
        if self.calcPnkCheckBox.isChecked():
            self.categoryPnkComboBox.show()
            self.adrPnkComboBox.show()
            self.unchCheckBox.setChecked(False)
        else:
            self.categoryPnkComboBox.hide()
            self.adrPnkComboBox.hide()
            self.calcDissCheckBox.setChecked(False)
        self.checkAnyChoice()

    def handlerDiss(self) -> None:
        '''Метод скрытия/отображения выбора категории и адр дисс'''
        if self.calcDissCheckBox.isChecked():
            self.categoryPnkComboBox.show()
            self.adrPnkComboBox.show()
            self.categoryDissComboBox.show()
            self.adrDissComboBox.show()
            self.calcPnkCheckBox.setChecked(True)
            self.unchCheckBox.setChecked(False)
        else:
            self.categoryDissComboBox.hide()
            self.adrDissComboBox.hide()
        self.checkAnyChoice()

    def updateAdrPnkComboBox(self) -> None:
        '''Метод обновления пнк адр комбобокса'''
        current_category = self.categoryPnkComboBox.currentText()
        adrs = self.controller.get_data()[current_category].keys()
        self.adrPnkComboBox.clear()
        self.adrPnkComboBox.addItems(adrs)

    def updateAdrDissComboBox(self) -> None:
        '''Метод обновления дисс адр комбобокса'''
        current_category = self.categoryDissComboBox.currentText()
        adrs = self.controller.get_data()[current_category].keys()
        self.adrDissComboBox.clear()
        self.adrDissComboBox.addItems(adrs)

    def saveComboBoxValue(self) -> None:
        '''
        Метод для сохранения в настройках самолета по умолчанию.
        '''
        self.parent.settings.setValue(
            'planeComboBox', self.planeComboBox.currentText()
        )

    def calculateEvent(self) -> None:
        '''
        Метод по нажатию кнопки ОК, который непосредственно запускает
        рассчет значений с их последующей передачей в главное окно
        '''
        # TODO в дальнейшейм необходимо будет добавить рассчеты
        # дисс, пока только пнк, продумать решение красивее
        if self.unchCheckBox.isChecked():
            self.calculateUnch('UNCH')
            return

        targetAdr, ok = QInputDialog.getText(
            self, 'Ввод данных', 'Введите название адр:'
        )
        if not ok:
            return

        if self.calcDissCheckBox.isChecked():
            self.calculateDiss(targetAdr)

        if self.calcPnkCheckBox.isChecked():
            self.calculatePnk(targetAdr)


    def calculateUnch(self, target_adr) -> None:
        try:
            category = self.categoryUnchComboBox.currentText()
            self.controller.concatenate_unch(category, 'ADR2', target_adr)
            self.parent.tree_widget.update_check_box()
            self.parent.send_notify(
                'успех', 'Данные подсчитаны.'
            )
            self.close()
        except ValueError:
            self.parent.send_notify(
                'предупреждение', 'Нет данных в adr2'
            )
        except KeyError:
            self.parent.send_notify(
                'предупреждение', 'Нет указанной категории, возможно вы её переименовали'
            )
        except Exception as e:
            self.parent.send_notify(
                'предупреждение', str(e)
            )


    def calculateDiss(self, target_adr) -> None:
        pass

    def calculatePnk(self, target_adr) -> None:
        planeCorr = self.parent.settings.value(
            'planes')[self.planeComboBox.currentText()]
        corrections = self.parent.settings.value('corrections')
        categoryPnk = self.categoryPnkComboBox.currentText()
        adrPnk = self.adrPnkComboBox.currentText()
        try:
            self.controller.set_calculate_data_pnk(
                category=categoryPnk,
                adr=adrPnk,
                plane_correct=planeCorr,
                corrections=corrections,
                target_adr=target_adr
            )
            self.parent.tree_widget.update_check_box()
            self.parent.send_notify('успех', 'Данные подсчитаны.')
            self.close()
        except Exception as e:
            self.parent.send_notify('предупреждение', str(e))

    def checkAnyChoice(self) -> None:
        if any([
            self.calcPnkCheckBox.isChecked(),
            self.calcDissCheckBox.isChecked(),
            self.unchCheckBox.isChecked()
        ]):
            self.okButton.setEnabled(True)
        else:
            self.okButton.setEnabled(False)

    def updateWidget(self) -> None:
        '''Метод обновления списка категорий'''
        categories = self.controller.get_data().keys()
        self.categoryUnchComboBox.clear()
        self.categoryUnchComboBox.addItems(categories)
        self.categoryDissComboBox.clear()
        self.categoryDissComboBox.addItems(categories)
        self.categoryPnkComboBox.clear()
        self.categoryPnkComboBox.addItems(categories)
        self.updateAdrDissComboBox()
        self.updateAdrPnkComboBox()
        planes = self.parent.settings.value('planes')
        self.planeComboBox.clear()
        self.planeComboBox.addItems(planes)
        self.planeComboBox.setCurrentText(
            self.parent.settings.value('planeComboBox')
        )