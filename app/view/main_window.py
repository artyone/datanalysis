from app.controller import (
    Control, NoneJsonError, defaultSettings,
    getPalette, get_list_actions, get_menu_dict
)
from app.view.servicesWindows import (
    Graph_window, MapWindow, Report_window,
    ConsoleWindow, CalcWindow
)
from app.view.helpersWindows import (
    SettingsWindow, Save_csv_window,
    Open_file_window, Left_Menu_Tree
)
from PyQt5.QtGui import (
    QIcon, QColor, QPainter, QKeyEvent
)
from PyQt5.QtCore import (
    Qt, QSettings, QCoreApplication, QProcess
)
from PyQt5.QtWidgets import (
    QApplication, QMdiArea, QSplitter,
    QToolBar, QSpinBox, QAction, QFileDialog,
    QMainWindow, QMenu,
    QMessageBox
)
from PyQt5.sip import delete
from functools import partial
from notificator import notificator
from notificator.alingments import BottomRight
import app.resource.qrc_resources
import pyqtgraph as pg
import sys


class Main_window(QMainWindow):
    '''
    Класс основного окна. 
    При инициализаци создается контроллер и переменны для окон.
    Если настройки пустые или устарели - создаются настройки по-умолчанию.
    '''

    def __init__(self, app: QApplication) -> None:
        super().__init__()
        self.app = app
        self.map_window: MapWindow = None
        self.report_window: Report_window = None
        self.console_window: ConsoleWindow = None
        self.settings_window: SettingsWindow = None
        self.calc_window: CalcWindow = None
        self.save_csv_window: Save_csv_window = None
        self.open_file_window: Open_file_window = None
        self.controller: Control = Control()
        self.app_version = QCoreApplication.applicationVersion()
        self.app_name = QCoreApplication.applicationName()
        self.notify: notificator = notificator()
        self.settings: QSettings = QSettings()
        if (self.settings.allKeys() == [] or
                self.settings.value('version') != self.app_version):
            self.set_default_settings()
        self.initUI()
        self.setTheme()

        last_file = self.settings.value('lastFile')
        open_last_file = self.settings.value('mainSettings')['openLastFile']
        if last_file is not None and open_last_file:
            self.open_gzip_file(last_file['filePath'])

    def initUI(self) -> None:
        '''
        Создание основных элементов интерфейса.
        Создание Экшенов, меню, тулбара, статус бара, связей.
        Для уведомлений используется сторонняя библиотека.
        '''
        # self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle(f'{self.app_name} {self.app_version}')
        self.app.setWindowIcon(QIcon('icon.ico'))
        self.create_actions()
        self.generate_menu(self.menuBar(), get_menu_dict())
        self.create_tool_bar()
        self.create_status_bar()
        #self._connectActions()

        self.mdi = QMdiArea()
        self.mdi.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.mdi.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.splitter = QSplitter(Qt.Horizontal)

        self.tree_widget = Left_Menu_Tree(self)

        self.tree_widget.hide()

        self.splitter.addWidget(self.tree_widget)
        self.splitter.addWidget(self.mdi)

        self.setCentralWidget(self.splitter)
        self.showMaximized()

    def setTheme(self) -> None:
        theme = self.settings.value('mainSettings')['theme']
        if theme == 'light':
            return
        if theme == 'dark':
            self.mdi.setBackground(QColor(50, 50, 50))
        if theme == 'purple':
            self.mdi.setBackground(QColor(50, 50, 77))
        pallete = getPalette(theme)
        self.app.setPalette(pallete)
        self.setStyleSheet(
            "QTreeView::indicator {"
            "    border: 1px solid gray;"
            "}"
            "QTreeWidget::indicator:checked {"
            "    background-color: rgb(0, 191, 255);"
            "    border: 2px solid gray;"
            "}"
            "QMdiSubWindow {"
            "    color: black;"
            "}"
            "QMdiSubWindow:!active:title {"
            "    color: white;"
            "}"
        )

    def generate_menu(self, parent: QMenu, menu_dict: dict) -> None:
        """
        Метод генерации меню приложения. Описатель в app/controller/interface_data.py

        Args:
            - parent (QMenu): Родительское меню.
            - menu_dict (dict): Описатель элементов. Если задана не строка, вызываем себя снова.

        Returns:
            None
        """

        for menu, actions in menu_dict.items():
            submenu: QMenu = parent.addMenu(menu.title)
            if menu.icon:
                submenu.setIcon(self.getIcon(menu.icon))
            for action in actions:
                if isinstance(action, dict):
                    self.generate_menu(submenu, action)
                elif action is None:
                    submenu.addSeparator()
                else:
                    submenu.addAction(getattr(self, action))

    def create_tool_bar(self):
        '''
        Метод создания тулбара
        '''
        if self.settings.value('mainSettings')['toolBar'] == 'left':
            position = Qt.LeftToolBarArea
        else:
            position = Qt.TopToolBarArea
        self.addToolBar(position, self.file_tool_bar())
        self.addToolBar(position, self.service_tool_bar())
        self.addToolBar(position, self.view_tool_bar())

    def file_tool_bar(self) -> QToolBar:
        file_tool_bar: QMenu = QToolBar('File')
        file_tool_bar.addAction(self.open_txt_action)
        file_tool_bar.addAction(self.open_gzip_action)
        file_tool_bar.addAction(self.save_gzip_action)
        file_tool_bar.addSeparator()
        file_tool_bar.addAction(self.exit_action)
        file_tool_bar.setMovable(False)
        return file_tool_bar

    def service_tool_bar(self) -> QToolBar:
        service_tool_bar: QMenu = QToolBar('Service')
        service_tool_bar.addAction(self.calculate_data_action)
        service_tool_bar.addAction(self.python_console_action)
        service_tool_bar.setMovable(False)
        return service_tool_bar

    def view_tool_bar(self) -> QToolBar:
        view_tool_bar = QToolBar('View')
        view_tool_bar.addAction(self.hide_left_menu_action)
        view_tool_bar.addAction(self.create_graph_action)
        view_tool_bar.addAction(self.create_default_graph_action)
        self.spin_box = QSpinBox()
        self.spin_box.setMinimum(1)
        view_tool_bar.addWidget(self.spin_box)
        view_tool_bar.addSeparator()
        view_tool_bar.addAction(self.cascade_action)
        view_tool_bar.addAction(self.horizontal_action)
        view_tool_bar.addAction(self.vertical_action)
        view_tool_bar.addAction(self.track_graph_action)
        view_tool_bar.addSeparator()
        view_tool_bar.addAction(self.close_all_action)
        view_tool_bar.setMovable(False)
        return view_tool_bar

    def create_status_bar(self) -> None:
        '''
        Создание статус бара.
        '''
        self.statusbar = self.statusBar()
        self.statusbar.showMessage(
            'Привет, пользователь! Я за тобой слежу!', 30000
        )

    def create_actions(self) -> None:
        '''
        Создание Actions
        '''
        list_action = get_list_actions()
        for action in list_action:
            setattr(self, action.name, QAction(action.title, self))
            var: QAction = getattr(self, action.name)
            var.setIcon(self.getIcon(action.icon))
            var.setStatusTip(action.tip)
            if action.hotkey:
                var.setShortcut(action.hotkey)
            var.setCheckable(action.checkable)
            if isinstance(action.connect, str):
                var.triggered.connect(getattr(self, action.connect))
            if isinstance(action.connect, tuple):
                func, *args = action.connect
                func = getattr(self, func)
                var.triggered.connect(
                    partial(func, *args)
                )

    def center(self, obj=None) -> None:
        '''
        Метод для установки окна в центре экрана
        '''
        if obj is None:
            obj = self
        qr = obj.frameGeometry()
        cp = self.screen().geometry().center()
        qr.moveCenter(cp)
        obj.move(qr.topLeft())

    def clear_main_window(self) -> None:
        del self.controller
        self.controller = Control()
        self.tree_widget.clear()
        self.tree_widget.hide()
        self.mdi.closeAllSubWindows()
        self.destroy_child_window()
        self.check_positioning_windows()
        self.track_graph()
        self.settings.setValue('lastFile', None)

    def getIcon(self, name) -> QIcon:
        icon = QIcon(name)
        if self.settings.value('mainSettings')['theme'] == 'light':
            return icon
        pixmap = icon.pixmap(50, 50)
        color = QColor(255, 255, 255)
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), color)
        painter.end()
        return QIcon(pixmap)

    def open_gzip_file(self, filepath=None) -> None:
        '''
        Метод открытия файлов в зависимостиот параметра.
        Открывает любые бинарные, которые могут использоваться
        в программе.
        '''
        # TODO передалть на ласт файл на filepath открыть последний открытый
        if filepath:
            file, check = filepath, True
        else:
            file, check = QFileDialog.getOpenFileName(
                None,
                'Open file',
                '',
                f'Open File (*.gzip)'
            )
        if check:
            try:
                self.controller.load_gzip(file)
            except FileNotFoundError:
                self.setNotify('ошибка', 'Файл не найден')
            except TypeError as e:
                self.setNotify('ошибка', str(e))
            except Exception as e:
                self.setNotify('ошибка', str(e))
            else:
                self.tree_widget.update_check_box()
                self.settings.setValue(
                    'lastFile', {
                        'filePath': file,
                        'param': 'gzip'
                    }
                )
                if not filepath:
                    self.setNotify(
                        'успех', f'Файл {file} открыт')

    def get_open_file_window(self, filetype: str) -> None:
        if self.open_file_window is None:
            try:
                categories = self.controller.get_json_categories(
                    self.settings.value('mainSettings')['jsonDir']
                )
                self.open_file_window = Open_file_window(
                    self.controller, filetype, categories, self
                )
            except KeyError:
                self.setNotify(
                    'ошибка', 'Неверные данные в json файлах'
                )
                return
            except NoneJsonError:
                self.setNotify(
                    'ошибка', 'Нет json файлов в папке'
                )
                return
            except FileNotFoundError:
                self.setNotify(
                    'ошибка', 'Не найден путь к папке json'
                )
                return
            except Exception as e:
                self.setNotify(
                    'ошибка', str(e)
                )
                return
        else:
            self.open_file_window.hide()
        self.center(self.open_file_window)
        self.open_file_window.show()

    def destroy_child_window(self) -> None:
        '''
        Метод удаления дочерних окон.
        '''
        windows = [
            'settings_window',
            'report_window',
            'map_window',
            'calc_window',
            'open_file_window',
        ]
        for window in windows:
            if getattr(self, window):
                delete(getattr(self, window))
                setattr(self, window, None)

    #TODO есть 4 одинаковых вызова одного этого, подумать как исправить
    def save_csv_data(self) -> None:
        '''
        Сохранение данных в формате CSV
        '''
        if not self.check_data():
            return

        if self.save_csv_window is None:
            self.save_csv_window = Save_csv_window(self.controller, self)
        else:
            self.save_csv_window.hide()
        self.center(self.save_csv_window)
        self.save_csv_window.show()

    def save_gzip_data(self) -> None:
        '''
        Сохранение данных в формате pickle gzip 
        '''
        if not self.check_data():
            return

        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            "",
            "gzip Files (*.gzip);;All Files(*)",
            options=options
        )
        if file_path:
            try:
                self.controller.save_gzip(file_path)
            except PermissionError:
                self.setNotify(
                    'ошибка', 'Файл открыт в другой программе или занят.')
            except Exception as e:
                self.setNotify(
                    'ошибка', str(e)
                )
            else:
                self.setNotify(
                    'успех', f'gzip файл сохранен в {file_path}'
                )

    def calculate_data(self) -> None:
        '''
        Метод для расчета данных
        '''
        if not self.check_data():
            return

        if self.calc_window is None:
            self.calc_window = CalcWindow(self.controller, self)
        else:
            self.calc_window.hide()
        self.center(self.calc_window)
        self.calc_window.show()

    def make_map(self) -> None:
        '''
        Метод для открытия окна генерации карты
        '''
        if not self.check_data():
            return

        if self.map_window is None:
            self.map_window = MapWindow(self.controller, self)
        else:
            self.map_window.hide()
        self.center(self.map_window)
        self.map_window.show()

    def create_report(self) -> None:
        '''
        Метод для открытия окна создания отчёта
        '''
        # TODO обновить проверку на необходимые данные
        if not self.check_data():
            return

        if not self.controller.is_calculated():
            self.setNotify(
                'предупреждение',
                'Нужно получить расчетные данные.'
            )
            return
        if self.report_window is None:
            self.report_window = Report_window(self.controller, self)
        else:
            self.report_window.hide()
        self.center(self.report_window)
        self.report_window.show()

    def about(self):
        '''
        Метод для открытия окна about
        '''
        return

    def create_graph(self, custom_selected=None) -> None:
        '''
        Метод для создания окон графиков по чек-боксу бокового меню
        '''
        if custom_selected:
            tree_selected = custom_selected
        else:
            tree_selected = self.tree_widget.get_selected_elements()

        if self.spin_box.text() != '0':
            decimation = int(self.spin_box.text())
        else:
            decimation = 1
        try:
            graph_window = Graph_window(
                self.controller.get_data(),
                tree_selected,
                decimation,
                self
            )
        except AttributeError:
            self.setNotify(
                'предупреждение', 'Данные не в нужном формате.'
            )
        except KeyError:
            if custom_selected:
                self.setNotify(
                    'предупреждение',
                    'Проверьте настройки графиков по умолчанию'
                )
            else:
                self.setNotify(
                    'предупреждение',
                    'Указанный столбец не найден в данных'
                )
        except ValueError:
            if custom_selected:
                self.setNotify(
                    'предупреждение',
                    'Проверьте настройки графиков по умолчанию'
                )
            else:
                self.setNotify(
                    'предупреждение',
                    'Выберите элементы для графика в левом меню.'
                )
        except Exception as e:
            self.setNotify('предупреждение', e)
        else:
            self.mdi.addSubWindow(graph_window)
            graph_window.show()
            self.track_graph()
            self.check_positioning_windows()

    #TODO решить проблему с этим мемню и постройкой графиков по-умолчанию
    def createDropdownDefaultGraph(self) -> QMenu | None:
        menu = QMenu(self)
        if not self.settings.value('graphs')['default']:
            return
        for category in self.settings.value('graphs')['default']:
            menu.addAction(
                category['name'],
                partial(self.create_default_graph, category['rows']))
        return menu

    def create_default_graph(self, rows) -> None:
        '''
        Метод создания типовых графиков, которые задаются в настройках
        '''
        if not self.check_data():
            return
        rows = sorted(rows, key=lambda x: x['row'])
        for row in rows:
            graph = [
                (field['category'], field['adr'], field['column'])
                for field in row['fields']
            ]
            self.create_graph(graph)

        width = self.mdi.width()
        heigth = self.mdi.height()
        pnt = [0, 0]
        for row, window in zip(rows, self.mdi.subWindowList()):
            current_heigth = int(heigth * row['width'] * 0.01)
            window.showNormal()
            window.setGeometry(0, 0, width, current_heigth)
            window.move(pnt[0], pnt[1])
            pnt[1] += current_heigth

    def python_console(self) -> None:
        '''
        Метод для открытия окна консоли
        '''
        if not self.check_data():
            return

        if self.console_window is None:
            self.console_window = ConsoleWindow(self.controller, self)
        else:
            self.console_window.hide()
        self.center(self.console_window)
        self.console_window.show()

    def cascade_windows(self) -> None:
        '''
        Метод для построения окон в виде каскада.
        '''
        if not self.mdi.subWindowList():
            return
        self.vertical_action.setChecked(False)
        self.horizontal_action.setChecked(False)
        self.mdi.cascadeSubWindows()

    def horizontal_windows(self) -> None:
        '''
        Метод для построения окон в горизональном виде.
        '''
        if not self.mdi.subWindowList() or not self.horizontal_action.isChecked():
            self.horizontal_action.setChecked(False)
            return

        self.vertical_action.setChecked(False)
        width = self.mdi.width()
        heigth = self.mdi.height() // len(self.mdi.subWindowList())
        pnt = [0, 0]
        for window in self.mdi.subWindowList():
            window.setGeometry(pnt[0], pnt[1], width, heigth)
            pnt[1] += heigth

    def vertical_windows(self) -> None:
        '''
        Метод для построения окон в вертикальном виде.
        '''
        if not self.mdi.subWindowList() or not self.vertical_action.isChecked():
            self.vertical_action.setChecked(False)
            return

        self.horizontal_action.setChecked(False)
        width = self.mdi.width() // len(self.mdi.subWindowList())
        heigth = self.mdi.height()

        pnt = [0, 0]
        for window in self.mdi.subWindowList():
            window.setGeometry(pnt[0], pnt[1], width, heigth)
            pnt[0] += width

    def resize_horizontal_windows(self):
        '''
        Растягиваем окна, если они растянуты хотя бы на 80 %
        '''
        if self.mdi.width() == 0:
            return
        width = self.mdi.width() - (
            self.tree_widget.width() if self.tree_widget.isHidden() else 0
        )
        sizes = [
            True if window.width() / width > 0.8 else False
            for window in self.mdi.subWindowList()
        ]
        if all(sizes):
            for window in self.mdi.subWindowList():
                geometry = window.geometry()
                geometry.setWidth(self.mdi.width())
                window.setGeometry(geometry)
        return

    def check_positioning_windows(self) -> None:
        if not self.mdi.subWindowList():
            self.vertical_action.setChecked(False)
            self.horizontal_action.setChecked(False)
            return
        if self.vertical_action.isChecked():
            self.vertical_windows()
            return
        if self.horizontal_action.isChecked():
            self.horizontal_windows()
            return
        self.resize_horizontal_windows()

    def hide_left_menu(self) -> None:
        '''Метод скрытия левого меню'''
        if self.hide_left_menu_action.isChecked():
            self.hide_left_menu_action.setIcon(self.getIcon(':eye'))
            self.tree_widget.hide()
            QCoreApplication.processEvents()
            self.mdi.resize(self.splitter.width(), self.splitter.height())
        else:
            self.hide_left_menu_action.setIcon(self.getIcon(':eye-off'))
            self.tree_widget.show()
            QCoreApplication.processEvents()
            self.mdi.resize(
                self.splitter.width() - self.tree_widget.width() - 5,
                self.splitter.height()
            )
        self.check_positioning_windows()

    def track_graph(self) -> None:
        '''
        Метод для связи графиков по оси Ох.
        '''
        if not self.mdi.subWindowList():
            self.track_graph_action.setChecked(False)
            return
        if self.track_graph_action.isChecked():
            link = self.mdi.findChild(pg.PlotWidget)
            for child in self.mdi.subWindowList():
                child.findChild(pg.PlotWidget).setXLink(link)
        else:
            for child in self.mdi.subWindowList():
                child.findChild(pg.PlotWidget).setXLink(None)

    def close_all_windows(self) -> None:
        self.mdi.closeAllSubWindows()
        self.track_graph()
        self.check_positioning_windows()

    def closeEvent(self, event) -> None:
        '''
        Переназначение функции закрытия, для закрытия всех дочерних окон.
        '''
        QApplication.closeAllWindows()
        event.accept()

    #TODO этот метод надо осторожно менять
    def setNotify(self, type: str, txt: str) -> None:
        '''
        Метод отправки библиотеки
        '''
        notify = self.notify.info
        duration = 10
        if type == 'предупреждение':
            notify = self.notify.warning
        if type == 'успех':
            notify = self.notify.sucess
            duration = 5
        if type == 'ошибка':
            notify = self.notify.critical
        notify(
            Title=type.title(),
            Message=txt,
            Parent=self,
            Align=BottomRight,
            duracion=duration,
            onclick=None
        )

    def open_settings(self) -> None:
        '''
        Метод открытия окна настроек.
        '''
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self)
        else:
            self.settings_window.hide()
        self.center(self.settings_window)
        self.settings_window.show()


    # TODO вернуть функционал постройки графиков по умолчанию
    def updateInterfaceFromSettings(self, param) -> None:
        if param == 'graphs':
            self.menuDefaultGraphAction.setMenu(
                self.createDropdownDefaultGraph()
            )
        if param == 'left_menu_filters':
            self.tree_widget.update_check_box()

    def load_setting_from_file(self) -> None:
        '''
        Метод загрузки настроек из файла.
        '''
        filepath, check = QFileDialog.getOpenFileName(
            None,
            'Open file',
            '',
            'Json File (*.json)'
        )
        if check:
            try:
                data = self.controller.load_settings_json(filepath)
                self.settings.clear()
                for key, value in data.items():
                    self.settings.setValue(key, value)
                self.setNotify(
                    'успех', f'Настройки загружены.'
                )
                question = QMessageBox.question(
                    None,
                    "Вопрос",
                    "Настройки установлены, необходим перезапуск программы. Делаем?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if question == QMessageBox.Yes:
                    self.restart_app()
            except Exception as e:
                self.setNotify(
                    'ошибка', str(e)
                )

    def save_settings_to_file(self) -> None:
        '''
        Метод сохранения настроек в файл.
        '''
        options = QFileDialog.Options()
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save File", "",
            f"Json Files (*.json);;All Files(*)",
            options=options
        )
        data = {
            name: self.settings.value(name)
            for name in self.settings.allKeys()
        }
        if filepath:
            try:
                self.controller.save_settings_json(filepath, data)
                self.setNotify(
                    'успех', f'Настройки сохранены в {filepath}'
                )
            except PermissionError:
                self.setNotify(
                    'ошибка', 'Файл открыт в другой программе'
                )
            except Exception as e:
                self.setNotify('ошибка', str(e))

    def set_default_settings(self, need_restart=False) -> None:
        '''
        Метод очистки и установки стандартных настроек.
        '''
        self.settings.clear()
        defaultSettings(self.settings, self.app_version)
        if need_restart:
            question = QMessageBox.question(
                None,
                "Вопрос",
                "Стандартные настройки установлены, необходим перезапуск программы. Делаем?",
                QMessageBox.Yes | QMessageBox.No
            )
            if question == QMessageBox.Yes:
                self.restart_app()

    def restart_app(self) -> None:
        program = sys.executable
        QProcess.startDetached(program, sys.argv)
        QCoreApplication.quit()

    def check_data(self) -> bool:
        if self.controller.data_is_none():
            self.setNotify(
                'предупреждение', 'Нужно выбрать данные'
            )
            return False
        return True

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Escape:
            question = QMessageBox.question(
                None,
                "Вопрос",
                "Вы точно хотите выйти?",
                QMessageBox.Yes | QMessageBox.No
            )
            if question == QMessageBox.Yes:
                self.close()
        else:
            super().keyPressEvent(event)

    def update_child_windows(self) -> None:
        attr = [
            'calc_window', 'map_window',
            'report_window', 'settings_window',
            'save_csv_window'
        ]
        for attr_name in attr:
            if getattr(self, attr_name) is not None:
                getattr(self, attr_name).updateWidget()

    def hide_unhide_border_window(self) -> None:
        if not self.mdi.subWindowList():
            return
        for window in self.mdi.subWindowList():
            if window.windowFlags() & Qt.FramelessWindowHint:
                window.setWindowFlags(
                    Qt.Window
                )
            else:
                window.setWindowFlags(Qt.FramelessWindowHint)
