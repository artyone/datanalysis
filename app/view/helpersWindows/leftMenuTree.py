from PyQt5.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QApplication, QMenu, QInputDialog
)
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt

class LeftMenuTree(QTreeWidget):
    def __init__(self, mainWindow, parent=None):
        super().__init__()
        self.mainWindow = mainWindow
        self.settings = mainWindow.settings
        self.setColumnCount(2)
        self.setHeaderLabels(['Название', 'Количество'])
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.itemDoubleClicked.connect(self.handleTreeItemDoubleClicked)


        #TODO сделать райт клик, переименовать и скрыть. 

    def updateCheckBox(self):
        '''
        Создание бокового чек-бокс дерева для построения графиков
        '''
        if not self.mainWindow.checkData():
            return

        self.clear()
        data = self.mainWindow.controller.get_data()
        for nameCategory, adrs in sorted(data.items(), key=lambda x: x[0]):
            treeCategory = QTreeWidgetItem(self)
            treeCategory.setText(0, nameCategory)
            treeCategory.setExpanded(True)
            for nameAdr, adrValues in sorted(adrs.items(), key=lambda x: x[0]):
                treeAdr = QTreeWidgetItem(treeCategory)
                treeAdr.setText(0, nameAdr)
                treeAdr.setExpanded(True)
                filters = self.settings.value('leftMenuFilters')
                for nameItem in sorted(adrValues.columns):
                    if nameItem in filters:
                        continue
                    treeItem = QTreeWidgetItem(treeAdr)
                    treeItem.setText(0, nameItem)
                    count = len(adrValues[nameItem])
                    treeItem.setText(1, str(count))
                    treeItem.setFont(1, QFont('Arial', 8, 1, True))
                    if count:
                        treeItem.setForeground(1, QColor('gray'))
                    else:
                        treeItem.setForeground(1, QColor('red'))
                    treeItem.setTextAlignment(1, Qt.AlignRight)
                    treeItem.setFlags(treeItem.flags() | Qt.ItemIsUserCheckable)
                    treeItem.setCheckState(0, Qt.Unchecked)
        self.show()
        self.resizeColumnToContents(0)
        self.resizeColumnToContents(1)
        self.mainWindow.splitter.setSizes([120, 500])

    @staticmethod
    def getInfoItem(item):
        info = []
        for _ in range(3):
            if item:
                info.append(item.text(0))
            else: break
            item = item.parent()
        if len(info) != 3:
            raise ValueError('Вы выбрали не элемент а категорию')
        return reversed(info)

    def handleTreeItemDoubleClicked(self, item, column):
        '''
        Обработка двойного клика на элементе дерева
        '''
        mouseEvent = QApplication.mouseButtons()
        if mouseEvent == Qt.LeftButton: 
            selectedItemTree = None
            try:
                selectedItemTree = self.getInfoItem(item)
            except Exception as e:
                self.mainWindow.setNotify('предупреждение', str(e))
            if selectedItemTree:
                category, adr, element  = selectedItemTree
                self.mainWindow.createGraph([(category, adr, element)])

    def showContextMenu(self, position):
        menu = QMenu(self)
        rename_action = menu.addAction("Переименовать")
        hide_action = menu.addAction("Скрыть")
        rename_action.triggered.connect(self.renameItem)
        hide_action.triggered.connect(self.hideItem)

        menu.exec_(self.viewport().mapToGlobal(position))

    def renameItem(self):
        item = self.currentItem()
        if item is not None:
            newName, ok = QInputDialog.getText(
                self, 
                "Переименовать элемент", 
                "Введите новое имя:", 
                text=item.text(0)
            )
            if ok:
                try:
                    selectedItemTree = self.getInfoItem(item)
                    self.mainWindow.controller.change_column_name(*selectedItemTree, newName)
                except Exception as e:
                    self.mainWindow.setNotify('предупреждение', str(e))
                self.updateCheckBox()


    def hideItem(self):
        item = self.currentItem()
        if item is not None:
            try:
                category, adr, name = self.getInfoItem(item)
                newFilterValue = self.settings.value('leftMenuFilters')
                if adr not in newFilterValue['adrs']:
                    newFilterValue['adrs'][adr] = {}
                newFilterValue['adrs'][adr][name] = False
                self.settings.setValue('leftMenuFilters', newFilterValue)
                self.updateCheckBox()
                self.mainWindow.setNotify('успех', f'{name} скрыт из {adr}')
     
            except Exception as e:
                self.mainWindow.setNotify('предупреждение', str(e))

    def addToOtherCategory(self):
        #TODO необходимо реализовать идею переноса каких-то данных в другие категории
        pass

    def getAllColumns(self) -> list:
        data = self.mainWindow.controller.get_data()
        result = []
        for adr in data.values():
            for df in adr.values():
                result.extend(list(df.columns))
        result = sorted(list(set(result)))
        return result