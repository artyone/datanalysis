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

    def updateCheckBox(self):
        '''
        Создание бокового чек-бокс дерева для построения графиков
        '''
        if self.mainWindow.controller.get_data() == {}:
            self.hide()
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
                    #treeItem.setTextAlignment(1, Qt.AlignRight)
                    treeItem.setFlags(treeItem.flags() | Qt.ItemIsUserCheckable)
                    treeItem.setCheckState(0, Qt.Unchecked)
        self.show()
        self.resizeColumnToContents(0)
        self.resizeColumnToContents(1)
        self.mainWindow.splitter.setSizes([90, 500])

    @staticmethod
    def getInfoItem(item: QTreeWidgetItem) -> list:
        info = []
        for _ in range(3):
            if item:
                info.append(item.text(0))
            else: break
            item = item.parent()
        return info[::-1]

    def handleTreeItemDoubleClicked(self, item: QTreeWidgetItem, _) -> None:
        '''
        Обработка двойного клика на элементе дерева
        '''
        mouseEvent = QApplication.mouseButtons()
        if mouseEvent == Qt.LeftButton: 
            selectedItemTree = self.getInfoItem(item)
            if len(selectedItemTree) == 3:
                category, adr, element  = selectedItemTree
                self.mainWindow.createGraph([(category, adr, element)])

    def showContextMenu(self, position) -> None:
        menu = QMenu(self)
        uncheckAllAction = menu.addAction('Снять все отметки')
        renameAction = menu.addAction('Переименовать')
        renameAction.triggered.connect(self.renameItem)
        uncheckAllAction.triggered.connect(self.updateCheckBox)

        item = self.currentItem()
        if len(self.getInfoItem(item)) == 3:
            hideAction = menu.addAction('Скрыть')
            hideAction.triggered.connect(self.hideItem)

        delAction = menu.addAction('Удалить')
        delAction.triggered.connect(self.deleteItem)

        menu.exec_(self.viewport().mapToGlobal(position))

    def renameItem(self) -> None:
        item = self.currentItem()
        if item is not None:
            newName, ok = QInputDialog.getText(
                self, 
                'Переименовать элемент', 
                'Введите новое имя:', 
                text=item.text(0)
            )
            if ok:
                try:
                    selectedItemTree = self.getInfoItem(item)
                    self.mainWindow.controller.change_column_name(selectedItemTree, newName)
                    self.updateCheckBox()
                except KeyError:
                    self.mainWindow.setNotify('предупреждение', 'Элемент не найден в данных')
                except Exception as e:
                    self.mainWindow.setNotify('предупреждение', str(e))

    def hideItem(self) -> None:
        item = self.currentItem()
        if item is not None:
            try:
                _, _, name = self.getInfoItem(item)
                newFilterValue = self.settings.value('leftMenuFilters')
                newFilterValue.append(name)
                self.settings.setValue('leftMenuFilters', newFilterValue)
                self.updateCheckBox()
                self.mainWindow.setNotify('успех', f'{name} скрыт.')
     
            except Exception as e:
                self.mainWindow.setNotify('предупреждение', str(e))

    def deleteItem(self) -> None:
        item = self.currentItem()
        if item is not None:
            try:
                selectedItemTree = self.getInfoItem(item)
                self.mainWindow.controller.delete_item(selectedItemTree)
                self.updateCheckBox()
            except KeyError:
                self.mainWindow.setNotify('предупреждение', 'Элемент не найден в данных')
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