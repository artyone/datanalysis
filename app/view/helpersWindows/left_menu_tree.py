from PyQt5.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QApplication, QMenu, QInputDialog
)
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt, QPoint


class Left_Menu_Tree(QTreeWidget):
    def __init__(self, mainWindow, parent=None) -> None:
        super().__init__()
        self.mainWindow = mainWindow
        self.settings = mainWindow.settings
        self.setColumnCount(2)
        self.setHeaderLabels(['Название', 'Количество'])
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.itemDoubleClicked.connect(self.handle_item_click)

    def update_check_box(self) -> None:
        """
        Обвноляет виджет дерева с помощью данных полученных от контроллера.

        Returns:
            None
        """
        if not self.mainWindow.controller.get_data():
            self.hide()
            return
        self.clear()
        data = self.mainWindow.controller.get_data()
        for category, adrs in sorted(data.items()):
            tree_category = QTreeWidgetItem(self)
            tree_category.setText(0, category)
            tree_category.setExpanded(True)
            for adr_name, adr_values in sorted(adrs.items()):
                tree_adr = QTreeWidgetItem(tree_category)
                tree_adr.setText(0, adr_name)
                tree_adr.setExpanded(True)
                for item_name in sorted(adr_values.columns):
                    if item_name in self.get_filters():
                        continue
                    self.add_tree_item(
                        tree_adr, item_name, len(adr_values[item_name])
                    )
        self.show()
        self.resize_columns_to_contents()
        self.mainWindow.splitter.setSizes([90, 500])

    def get_filters(self) -> list:
        return self.settings.value('left_menu_filters')

    def add_tree_item(self, parent: QTreeWidgetItem, item_name: str, count: int) -> None:
        """
        Добавляет новый элемент дерева с заданными именем и количеством.

        Args:
            - parent (QTreeWidgetItem): Родительский узел, к которому добавляется элемент.
            - item_name (str): Имя элемента.
            - count (int): Отображаемое количество.

        Returns:
            - None
        """
        tree_item = QTreeWidgetItem(parent)
        tree_item.setText(0, item_name)
        tree_item.setText(1, str(count))
        tree_item.setFont(1, QFont('Arial', 8, 1, True))
        if count:
            tree_item.setForeground(1, QColor('gray'))
        else:
            tree_item.setForeground(1, QColor('red'))
        tree_item.setFlags(tree_item.flags() | Qt.ItemIsUserCheckable)
        tree_item.setCheckState(0, Qt.Unchecked)

    def resize_columns_to_contents(self) -> None:
        self.resizeColumnToContents(0)
        self.resizeColumnToContents(1)

    @staticmethod
    def get_info_item(item: QTreeWidgetItem) -> list:
        """
        Возвращает информацию о элементе дерева.
        """
        info = []
        # Так как глубина дерева 3, то получаем максимум 3 элемента
        for _ in range(3):
            if item:
                info.append(item.text(0))
            else:
                break
            item = item.parent()
        return info[::-1]

    def handle_item_click(self, item: QTreeWidgetItem, _) -> None:
        """
        Обработка двойного клика на элементе дерева. 
        """
        mouse_event = QApplication.mouseButtons()
        if mouse_event == Qt.LeftButton:
            # Проверяем, что двойной клик по элементу, а не категории
            selected_item = self.get_info_item(item)
            if len(selected_item) == 3:
                category, adr, element = selected_item
                self.mainWindow.createGraph([(category, adr, element)])

    def showContextMenu(self, position: QPoint) -> None:
        """
        Отображает контекстное меню с различными действиями на основе текущего выбранного элемента.

        Args:
            - position (QPoint): Позиция курсора в дереве.

        Returns:
            - None.
        """
        menu = QMenu(self)
        uncheck_all_action = menu.addAction('Снять все отметки')
        uncheck_all_action.triggered.connect(self.update_check_box)
        rename_action = menu.addAction('Переименовать')
        rename_action.triggered.connect(self.rename_item)

        item = self.currentItem()
        if len(self.get_info_item(item)) == 3:
            hide_action = menu.addAction('Скрыть')
            hide_action.triggered.connect(self.hide_item)

        delete_action = menu.addAction('Удалить')
        delete_action.triggered.connect(self.delete_item)

        menu.exec_(self.viewport().mapToGlobal(position))

    def rename_item(self) -> None:
        """
        Переменовывает имя выбранного элемента.
        """
        selected_element = self.currentItem()

        if selected_element is None:
            return

        new_name, ok = QInputDialog.getText(
            self,
            'Переименовать элемент',
            'Введите новое имя:',
            text=selected_element.text(0)
        )
        if not ok:
            return

        try:
            info_item = self.get_info_item(selected_element)
            self.mainWindow.controller.change_column_name(
                info_item, new_name
            )
            self.update_check_box()
        except KeyError:
            self.mainWindow.setNotify(
                'предупреждение', 'Элемент не найден в данных'
            )
        except Exception as e:
            self.mainWindow.setNotify(
                'предупреждение', str(e)
            )

    def hide_item(self) -> None:
        """
        Скрывает элемент из отображения, добавляет его в настройки.
        """
        selected_item = self.currentItem()

        if selected_item is None:
            return

        try:
            _, _, name = self.get_info_item(selected_item)
            new_filter_value = self.settings.value('left_menu_filters')
            new_filter_value.append(name)
            self.settings.setValue('left_menu_filters', new_filter_value)
            self.update_check_box()
            self.mainWindow.setNotify('успех', f'{name} скрыт.')

        except Exception as e:
            self.mainWindow.setNotify('предупреждение', str(e))

    def delete_item(self) -> None:
        """
        Удаляет выбранный элемент или категорию из данных.
        """
        selected_item = self.currentItem()
        if selected_item is None:
            return

        try:
            item_info = self.get_info_item(selected_item)
            self.mainWindow.controller.delete_item(item_info)
            self.update_check_box()
        except KeyError:
            self.mainWindow.setNotify(
                'предупреждение', 'Элемент не найден в данных'
            )
        except Exception as e:
            self.mainWindow.setNotify('предупреждение', str(e))

    def addToOtherCategory(self):
        # TODO необходимо реализовать идею переноса каких-то данных в другие категории
        pass

    def get_all_columns(self) -> list:
        """
        Позволяет получить список уникальных имен всех элементов дерева.
        """
        data = self.mainWindow.controller.get_data()
        columns = []
        for address in data.values():
            for dataframe in address.values():
                columns.extend(list(dataframe.columns))
        unique_columns = list(set(columns))
        sorted_columns = sorted(unique_columns)
        return sorted_columns
