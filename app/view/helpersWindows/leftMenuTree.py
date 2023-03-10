from select import select
from PyQt5 import QtWidgets as qtw, QtGui as qtg, QtCore as qtc

class LeftMenuTree(qtw.QTreeWidget):
    def __init__(self, mainWindow, parent=None):
        super().__init__()
        self.mainWindow = mainWindow
        self.settings = mainWindow.settings
        self.setColumnCount(2)
        self.setHeaderLabels(['Название', 'Количество'])
        self.setContextMenuPolicy(qtc.Qt.CustomContextMenu)
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
            treeCategory = qtw.QTreeWidgetItem(self)
            treeCategory.setText(0, nameCategory)
            treeCategory.setExpanded(True)
            for nameAdr, adrValues in adrs.items():
                treeAdr = qtw.QTreeWidgetItem(treeCategory)
                treeAdr.setText(0, nameAdr)
                treeAdr.setExpanded(True)
                filters = self.settings.value('leftMenuFilters')
                adrFilters = filters['adrs'].get(nameAdr, {})
                for nameItem in adrValues.columns:
                    if adrFilters.get(nameItem, filters['unknown']):
                        treeItem = qtw.QTreeWidgetItem(treeAdr)
                        treeItem.setText(0, nameItem)
                        count = len(adrValues[nameItem])
                        treeItem.setText(1, str(count))
                        treeItem.setFont(1, qtg.QFont('Arial', 8, 1, True))
                        if count:
                            treeItem.setForeground(1, qtg.QColor('gray'))
                        else:
                            treeItem.setForeground(1, qtg.QColor('red'))
                        treeItem.setTextAlignment(1, qtc.Qt.AlignRight)
                        treeItem.setFlags(treeItem.flags() | qtc.Qt.ItemIsUserCheckable)
                        treeItem.setCheckState(0, qtc.Qt.Unchecked)
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
        mouseEvent = qtw.QApplication.mouseButtons()
        if mouseEvent == qtc.Qt.LeftButton: 
            selectedItemTree = None
            try:
                selectedItemTree = self.getInfoItem(item)
            except Exception as e:
                self.mainWindow.setNotify('предупреждение', str(e))
            if selectedItemTree:
                category, adr, element  = selectedItemTree
                self.mainWindow.createGraph([(category, adr, element)])

    def showContextMenu(self, position):
        menu = qtw.QMenu(self)
        rename_action = menu.addAction("Переименовать")
        hide_action = menu.addAction("Скрыть")
        rename_action.triggered.connect(self.renameItem)
        hide_action.triggered.connect(self.hideItem)

        menu.exec_(self.viewport().mapToGlobal(position))

    def renameItem(self):
        item = self.currentItem()
        if item is not None:
            newName, ok = qtw.QInputDialog.getText(self, "Переименовать элемент", "Введите новое имя:", text=item.text(0))
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
                print(category, adr, name)
                newFilterValue = self.settings.value('leftMenuFilters')
                if adr not in newFilterValue['adrs']:
                    newFilterValue['adrs'][adr] = {}
                newFilterValue['adrs'][adr][name] = False
                self.settings.setValue('leftMenuFilters', newFilterValue)
                print(self.settings.value('leftMenuFilters')['adrs']['PNK'])
                self.updateCheckBox()
     
            except Exception as e:
                self.mainWindow.setNotify('предупреждение', str(e))

    def addToOtherCategory(self):
        #TODO необходимо реализовать идею переноса каких-то данных в другие категории
        pass