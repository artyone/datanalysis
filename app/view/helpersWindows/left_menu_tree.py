from PyQt5.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QApplication, QMenu, QInputDialog,
    QTableWidget, QTableWidgetItem, QAction,
    QTreeWidgetItemIterator, QHeaderView, QFileDialog, QMainWindow
)
from PyQt5.QtGui import QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QPoint
from collections import defaultdict
import pandas as pd


class ViewDataWidget(QMainWindow):
    def __init__(self, parent, data: pd.DataFrame, category, adr, columns) -> None:
        super().__init__()
        self.parent = parent
        self.data: pd.DataFrame = data[category][adr][columns].round(3)
        self.category: str = category
        self.adr: str = adr
        self.columns: list = columns
        self.items_per_page = 5000
        self.current_page = 1

        self.table_widget = QTableWidget(self)
        self.setCentralWidget(self.table_widget)

        self.save_csv_action = QAction('&Сохранить *.csv...')
        self.save_csv_action.setIcon(QIcon(self.parent.get_icon(':save.svg')))
        self.save_csv_action.triggered.connect(self.save_csv)
        save_tool_bar = self.addToolBar('Save')
        save_tool_bar.addAction(self.save_csv_action)

        self.setup_table_widget()
        self.load_page(1)

        self.showMaximized()

    def setup_table_widget(self) -> None:
        """
        Инициализация таблицы
        """
        # Устанавливаем количество столбцов и их имена
        self.table_widget.setColumnCount(len(self.columns))
        self.table_widget.setHorizontalHeaderLabels(self.columns)

        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)

        scroll_bar = self.table_widget.verticalScrollBar()
        scroll_bar.valueChanged.connect(self.scroll_bar_value_changed)

    def save_csv(self) -> None:
        '''
        Метод сохранения данных в csv формат
        '''
        options = QFileDialog.Options()
        self.filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            "",
            f"csv files (*.csv);;All Files(*)",
            options=options
        )
        if self.filepath:
            try:
                self.parent.controller.save_csv(
                    self.filepath, self.category, self.adr, self.columns
                )
                self.parent.send_notify(
                    'успех', f'Csv файл сохранен в {self.filepath}'
                )
            except PermissionError:
                self.parent.send_notify(
                    'ошибка', 'Файл открыт в другой программе'
                )
            except Exception as e:
                self.parent.send_notify(
                    'ошибка', str(e)
                )

    def load_page(self, page_number: int) -> None:
        """
        Загрузка страницы просмотра.

        Args:
            page_number (int): Номер страницы для загрузки
        """
        start_index = (page_number - 1) * self.items_per_page
        end_index = start_index + self.items_per_page
        data_page = self.data.iloc[start_index:end_index]
        if len(data_page) <= 0:
            return
        self.table_widget.setRowCount(start_index + len(data_page))
        for row_index, row in data_page.iterrows():
            for column_index, column_name in enumerate(self.columns):
                column_item = QTableWidgetItem(str(row[column_name]))
                self.table_widget.setItem(row_index, column_index, column_item)

    def scroll_bar_value_changed(self) -> None:
        """
        Обработчик достижения конца таблицы
        """
        scroll_bar = self.table_widget.verticalScrollBar()

        if scroll_bar.sliderPosition() == scroll_bar.maximum():
            self.current_page += 1
            self.load_page(self.current_page)

    def closeEvent(self, event) -> None:
        event.accept()


class Left_Menu_Tree(QTreeWidget):
    def __init__(self, parent) -> None:
        super().__init__()
        self.parent = parent
        self.settings = self.parent.settings
        self.setColumnCount(2)
        self.setHeaderLabels(['Название', 'Количество'])
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.itemDoubleClicked.connect(self.handle_item_click)

    def update_check_box(self) -> None:
        """
        Обновляет виджет дерева с помощью данных полученных от контроллера.

        Returns:
            None
        """
        if not self.parent.controller.get_data():
            self.hide()
            self.parent.destroy_child_window()
            return
        self.clear()
        data = self.parent.controller.get_data()
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
        self.parent.splitter.setSizes([90, 500])
        self.parent.update_child_windows()


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
                self.parent.create_graph([(category, adr, element)])

    def show_context_menu(self, position: QPoint) -> None:
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
            hide_action.triggered.connect(self.hide_item_event)
            view_data_action = menu.addAction('Посмотреть данные')
            view_data_action.triggered.connect(self.view_data_event)

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
            self.parent.controller.change_column_name(
                info_item, new_name
            )
            self.update_check_box()
        except KeyError:
            self.parent.send_notify(
                'предупреждение', 'Элемент не найден в данных'
            )
        except Exception as e:
            self.parent.send_notify(
                'предупреждение', str(e)
            )

    def hide_item_event(self) -> None:
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
            self.parent.send_notify('успех', f'{name} скрыт.')

        except Exception as e:
            self.parent.send_notify('предупреждение', str(e))

    def view_data_event(self) -> None:
        """
        Посмотреть данные выбранного элемента
        """
        # Проверяем выбраны ли какие чек-боксы
        
        if self.get_selected_elements() != []:
            selected_elements = self.get_selected_elements()
            
        elif self.currentItem():
            # Проверяем правый клик был по элементу или категории
            current_item = self.currentItem()
            item_info = self.get_info_item(current_item)
            if len(item_info) != 3:  
                return
            else:
                selected_elements = [item_info]
        else: 
            return
        
        data = self.parent.controller.get_data()

        selected_categories = defaultdict(list)
        for element in selected_elements:
            selected_categories[(element[0], element[1])].append(element[2])

        self.child_window = []
        for key, columns in selected_categories.items():
            columns.insert(0, 'time')
            category, adr = key[0], key[1]
            self.child_window.append(ViewDataWidget(self.parent, data, category, adr, columns))
        




    def delete_item(self) -> None:
        """
        Удаляет выбранный элемент или категорию из данных.
        """
        selected_item = self.currentItem()
        if selected_item is None:
            return

        try:
            item_info = self.get_info_item(selected_item)
            self.parent.controller.delete_item(item_info)
            self.update_check_box()
        except KeyError:
            self.parent.send_notify(
                'предупреждение', 'Элемент не найден в данных'
            )
        except Exception as e:
            self.parent.send_notify('предупреждение', str(e))

    def addToOtherCategory(self):
        # TODO необходимо реализовать идею переноса каких-то данных в другие категории
        pass

    def get_all_columns(self) -> list:
        """
        Позволяет получить список уникальных имен всех элементов дерева.
        """
        data = self.parent.controller.get_data()
        columns = []
        for address in data.values():
            for dataframe in address.values():
                columns.extend(list(dataframe.columns))
        unique_columns = list(set(columns))
        sorted_columns = sorted(unique_columns)
        return sorted_columns
    
    def get_selected_elements(self) -> list:
        '''
        Фукнция для получения всех отмеченных чек-боксов.
        '''
        selected_elements = []
        iterator = QTreeWidgetItemIterator(
            self, QTreeWidgetItemIterator.Checked
        )
        while iterator.value():
            item = iterator.value()
            item_name = item.text(0)
            adr_name = item.parent().text(0)
            category_name = item.parent().parent().text(0)
            selected_elements.append((category_name, adr_name, item_name))
            iterator += 1
        return selected_elements