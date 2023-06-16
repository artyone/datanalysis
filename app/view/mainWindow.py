from app.controller import (
    Control, NoneJsonError, defaultSettings,
    getPalette
)
from app.view.servicesWindows import (
    GraphWindow, MapWindow, Report_window,
    ConsoleWindow, CalcWindow
)
from app.view.helpersWindows import (
    SettingsWindow, SaveCsvWindow,
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
    QTreeWidgetItemIterator, QMainWindow, QMenu,
    QMessageBox
)
from PyQt5.sip import delete
from functools import partial
from notificator import notificator
from notificator.alingments import BottomRight
import app.resource.qrc_resources
import pyqtgraph as pg
import sys


class MainWindow(QMainWindow):
    '''
    Класс основного окна. 
    При инициализаци создается контроллер и переменны для окон.
    Если настройки пустые или устарели - создаются настройки по-умолчанию.
    '''

    def __init__(self, app: QApplication) -> None:
        super().__init__()
        self.app = app
        self.mapWindow: MapWindow = None
        self.reportWindow: Report_window = None
        self.consoleWindow: ConsoleWindow = None
        self.settingsWindow: SettingsWindow = None
        self.calcWindow: CalcWindow = None
        self.saveCsvWindow: SaveCsvWindow = None
        self.openFileWindow: Open_file_window = None
        self.controller: Control = Control()
        self.appVersion = QCoreApplication.applicationVersion()
        self.appName = QCoreApplication.applicationName()
        self.notify: notificator = notificator()
        self.settings: QSettings = QSettings()
        if (self.settings.allKeys() == [] or
                self.settings.value('version') != self.appVersion):
            self.setDefaultSettings()
        self.initUI()
        self.setTheme()

        lastFile = self.settings.value('lastFile')
        openLastFile = self.settings.value('mainSettings')['openLastFile']
        if lastFile is not None and openLastFile:
            self.openBinaryFile(lastFile['filePath'])

    def initUI(self) -> None:
        '''
        Создание основных элементов интерфейса.
        Создание Экшенов, меню, тулбара, статус бара, связей.
        Для уведомлений используется сторонняя библиотека.
        '''
        # self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle(f'{self.appName} {self.appVersion}')
        self.app.setWindowIcon(QIcon('icon.ico'))
        self._createActions()
        self._createMenuBar()
        self._createToolBar()
        self._createStatusBar()
        self._connectActions()

        self.mdi = QMdiArea()
        self.mdi.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.mdi.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.splitter = QSplitter(Qt.Horizontal)

        self.tree_widget = Left_Menu_Tree(self, self.splitter)

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

    def _createMenuBar(self) -> None:
        '''
        Генерация меню
        '''
        self.menuBar = self.menuBar()
        self._createFileMenu()
        self._createViewMenu()
        self._createServiceMenu()
        self._createSettingsMenu()

    def _createFileMenu(self) -> None:
        fileMenu: QMenu = self.menuBar.addMenu('&Файл')
        fileMenu.addAction(self.clearAction)

        openSourceMenu: QMenu = fileMenu.addMenu(
            'Открыть txt или csv'
        )
        openSourceMenu.setIcon(self.getIcon(':file-plus.svg'))
        openSourceMenu.addAction(self.openTxtAction)
        openSourceMenu.addAction(self.openCsvAction)

        openDataMenu: QMenu = fileMenu.addMenu(
            '&Открыть gzip или pdd'
        )
        openDataMenu.setIcon(self.getIcon(':database.svg'))
        openDataMenu.addAction(self.openPddAction)
        openDataMenu.addAction(self.openGzipAction)

        saveMenu: QMenu = fileMenu.addMenu('&Сохранить как')
        saveMenu.setIcon(self.getIcon(':save'))
        saveMenu.addAction(self.saveGzipAction)
        saveMenu.addAction(self.saveCsvAction)

        fileMenu.addSeparator()
        fileMenu.addAction(self.exitAction)

    def _createViewMenu(self) -> None:
        viewMenu: QMenu = self.menuBar.addMenu('&Просмотр')
        viewMenu.addAction(self.hideLeftMenuAction)
        viewMenu.addAction(self.createGraphAction)
        viewMenu.addAction(self.menuDefaultGraphAction)
        viewMenu.addAction(self.cascadeAction)
        viewMenu.addAction(self.horizontalAction)
        viewMenu.addAction(self.verticalAction)
        viewMenu.addAction(self.trackGraphAction)
        viewMenu.addSeparator()
        viewMenu.addAction(self.closeAllAction)

    def _createServiceMenu(self):
        serviceMenu: QMenu = self.menuBar.addMenu('&Сервисы')
        serviceMenu.addAction(self.calculateDataAction)
        serviceMenu.addAction(self.createMapAction)
        serviceMenu.addAction(self.createReportAction)
        serviceMenu.addAction(self.pythonConsoleAction)

    def _createSettingsMenu(self):
        settingsMenu: QMenu = self.menuBar.addMenu('&Настройки')
        settingsMenu.addAction(self.openSettingsActions)
        settingsMenu.addAction(self.loadSettingsFromFileActions)
        settingsMenu.addAction(self.saveSettingsToFileActions)
        settingsMenu.addAction(self.setDefaultSettingsActions)
        settingsMenu.addAction(self.aboutAction)

    def _createToolBar(self):
        '''
        Создание тулбара.
        '''
        if self.settings.value('mainSettings')['toolBar'] == 'left':
            position = Qt.LeftToolBarArea
        else:
            position = Qt.TopToolBarArea
        self.addToolBar(position, self._fileToolBar())
        self.addToolBar(position, self._serviceToolBar())
        self.addToolBar(position, self._viewToolBar())

    def _fileToolBar(self) -> QToolBar:
        fileToolBar: QMenu = QToolBar('File')
        fileToolBar.addAction(self.openTxtAction)
        fileToolBar.addAction(self.openGzipAction)
        fileToolBar.addAction(self.saveGzipAction)
        fileToolBar.addSeparator()
        fileToolBar.addAction(self.exitAction)
        fileToolBar.setMovable(False)
        return fileToolBar

    def _serviceToolBar(self) -> QToolBar:
        serviceToolBar: QMenu = QToolBar('Service')
        serviceToolBar.addAction(self.calculateDataAction)
        serviceToolBar.addAction(self.pythonConsoleAction)
        serviceToolBar.setMovable(False)
        return serviceToolBar

    def _viewToolBar(self) -> QToolBar:
        viewToolBar = QToolBar('View')
        viewToolBar.addAction(self.hideLeftMenuAction)
        viewToolBar.addAction(self.createGraphAction)
        viewToolBar.addAction(self.menuDefaultGraphAction)
        self.spinBox = QSpinBox()
        self.spinBox.setMinimum(1)
        viewToolBar.addWidget(self.spinBox)
        viewToolBar.addSeparator()
        viewToolBar.addAction(self.cascadeAction)
        viewToolBar.addAction(self.horizontalAction)
        viewToolBar.addAction(self.verticalAction)
        viewToolBar.addAction(self.trackGraphAction)
        viewToolBar.addSeparator()
        viewToolBar.addAction(self.closeAllAction)
        viewToolBar.setMovable(False)
        return viewToolBar

    def _createStatusBar(self) -> None:
        '''
        Создание статус бара.
        '''
        self.statusbar = self.statusBar()
        self.statusbar.showMessage(
            'Привет, пользователь! Я за тобой слежу!', 30000
        )

    def _createActions(self) -> None:
        '''
        Создание Actions
        '''
        self._creteFileActions()
        self._creteServiceActions()
        self._createViewActions()
        self._createSettingsActions()

    def _creteFileActions(self) -> None:
        self.clearAction = QAction('&Очистить окно', self)
        self.clearAction.setIcon(self.getIcon(':x.svg'))
        self.clearAction.setStatusTip(
            'Очистить все данные в программе.'
        )

        self.openTxtAction = QAction('Открыть *.&txt...', self)
        self.openTxtAction.setIcon(self.getIcon(':file-plus.svg'))
        self.openTxtAction.setStatusTip(
            'Открыть txt файл с данными.'
        )

        self.openPddAction = QAction('Открыть *.&pdd...', self)
        self.openPddAction.setIcon(self.getIcon(':file.svg'))
        self.openPddAction.setStatusTip(
            'Открыть pdd файл с данными.'
        )

        self.openCsvAction = QAction('Открыть *.&csv...', self)
        self.openCsvAction.setIcon(self.getIcon(':file-text.svg'))
        self.openCsvAction.setStatusTip(
            'Открыть csv файл с данными.'
        )

        self.openGzipAction = QAction('Открыть *.&gzip...', self)
        self.openGzipAction.setIcon(self.getIcon(':file.svg'))
        self.openGzipAction.setStatusTip(
            'Открыть gzip файл с данными.'
        )
        self.openGzipAction.setShortcut('Ctrl+O')

        self.saveGzipAction = QAction(
            'Сохранить как *.gzip...', self
        )
        self.saveGzipAction.setIcon(self.getIcon(':save.svg'))
        self.saveGzipAction.setStatusTip(
            'Сохранить данные в формате gzip'
        )
        self.saveGzipAction.setShortcut('Ctrl+S')

        self.saveCsvAction = QAction(
            'Сохранить как *.csv...', self
        )
        self.saveCsvAction.setIcon(self.getIcon(':file-text.svg'))
        self.saveCsvAction.setStatusTip(
            'Сохранить данные в формате csv'
        )

        self.exitAction = QAction('&Закрыть приложение', self)
        self.exitAction.setIcon(self.getIcon(':log-out.svg'))
        self.exitAction.setStatusTip(
            'Закрыть приложение навсегда'
        )
        self.exitAction.setShortcut('Ctrl+Q')

    def _creteServiceActions(self) -> None:
        self.calculateDataAction = QAction(
            '&Рассчитать данные')
        self.calculateDataAction.setIcon(self.getIcon(':percent.svg'))
        self.calculateDataAction.setStatusTip(
            'Рассчитать данные для дальнейшего анализа'
        )

        self.createMapAction = QAction('Создать &карту', self)
        self.createMapAction.setIcon(self.getIcon(':map.svg'))
        self.createMapAction.setStatusTip(
            'Создать интерактивную карту полёта'
        )

        self.createReportAction = QAction('Создать &отчёт', self)
        self.createReportAction.setIcon(self.getIcon(':mail.svg'))
        self.createReportAction.setStatusTip(
            'Создать отчет по полету и сохранить его в xlsx'
        )

        self.pythonConsoleAction = QAction('&Python консоль', self)
        self.pythonConsoleAction.setIcon(self.getIcon(':terminal'))
        self.pythonConsoleAction.setStatusTip(
            'Открыть окно консоли'
        )

    def _createViewActions(self) -> None:
        self.hideLeftMenuAction = QAction('&Скрыть левое меню')
        self.hideLeftMenuAction.setIcon(self.getIcon(':eye-off'))
        self.hideLeftMenuAction.setStatusTip(
            'Скрыть/показать левое меню'
        )
        self.hideLeftMenuAction.setCheckable(True)

        self.createGraphAction = QAction('&Создать график')
        self.createGraphAction.setIcon(self.getIcon(':trending-up.svg'))
        self.createGraphAction.setStatusTip(
            'Создать график в новом окне'
        )

        self.menuDefaultGraphAction = QAction(
            '&Создать графики по умолчанию'
        )
        self.menuDefaultGraphAction.setMenu(self.createDropdownDefaultGraph())
        self.menuDefaultGraphAction.setIcon(self.getIcon(':shuffle.svg'))
        self.menuDefaultGraphAction.setStatusTip(
            'Создать графики по умолчанию в новых окнах'
        )

        self.cascadeAction = QAction(
            '&Каскадное расположение'
        )
        self.cascadeAction.setIcon(self.getIcon(':bar-chart.svg'))
        self.cascadeAction.setStatusTip(
            'Каскадное расположение окон графиков'
        )

        self.horizontalAction = QAction(
            '&Горизонтальное расположение'
        )
        self.horizontalAction.setIcon(self.getIcon(':more-vertical.svg'))
        self.horizontalAction.setStatusTip(
            'Горизонтальное расположение окон графиков'
        )
        self.horizontalAction.setCheckable(True)

        self.verticalAction = QAction(
            '&Вертикальное расположение'
        )
        self.verticalAction.setIcon(self.getIcon(':more-horizontal.svg'))
        self.verticalAction.setStatusTip(
            'Вертикальное расположение окон графиков'
        )
        self.verticalAction.setCheckable(True)

        self.trackGraphAction = QAction(
            '&Синхронизация графиков'
        )
        self.trackGraphAction.setIcon(self.getIcon(':move.svg'))
        self.trackGraphAction.setStatusTip(
            'Синхронизация всех графиков по оси Ох'
        )
        self.trackGraphAction.setCheckable(True)

        self.closeAllAction = QAction('Закрыть &все окна')
        self.closeAllAction.setIcon(self.getIcon(':x-circle.svg'))
        self.closeAllAction.setStatusTip(
            'Закрыть все открытые окна'
        )

    def _createSettingsActions(self) -> None:
        self.openSettingsActions = QAction('&Настройки')
        self.openSettingsActions.setIcon(self.getIcon(':settings.svg'))
        self.openSettingsActions.setStatusTip('Меню настроек')

        self.setDefaultSettingsActions = QAction(
            '&Установить стандартные настройки'
        )
        self.setDefaultSettingsActions.setIcon(self.getIcon(':sliders.svg'))
        self.setDefaultSettingsActions.setStatusTip(
            'Установить стандартные настройки'
        )

        self.loadSettingsFromFileActions = QAction(
            'Загрузить настройки из файла'
        )
        self.loadSettingsFromFileActions.setIcon(self.getIcon(':download.svg'))
        self.loadSettingsFromFileActions.setStatusTip(
            'Загрузить настройки из файла json'
        )

        self.saveSettingsToFileActions = QAction(
            '&Сохранить настройки в файл'
        )
        self.saveSettingsToFileActions.setIcon(self.getIcon(':save.svg'))
        self.saveSettingsToFileActions.setStatusTip(
            'Сохранить настройки в файл json'
        )

        self.aboutAction = QAction('&О программе')
        self.aboutAction.setIcon(self.getIcon(':help-circle.svg'))
        self.aboutAction.setStatusTip('О программе')

    def _connectActions(self) -> None:
        '''
        Соединение функций и Actions
        '''
        self._connectFileActions()
        self._connectServiceActions()
        self._connectViewActions()
        self._connectSettingsActions()

    def _connectFileActions(self) -> None:
        self.clearAction.triggered.connect(self.clearMainWindow)
        self.openTxtAction.triggered.connect(
            partial(self.getOpenFileWindow, 'txt')
        )
        self.openPddAction.triggered.connect(
            partial(self.getOpenFileWindow, 'pdd')
        )
        self.openGzipAction.triggered.connect(
            self.openBinaryFile
        )

        self.openCsvAction.triggered.connect(
            partial(self.getOpenFileWindow, 'csv'))
        self.saveGzipAction.triggered.connect(self.saveGzipData)
        self.saveCsvAction.triggered.connect(self.saveCsvData)
        self.exitAction.triggered.connect(self.close)

    def _connectServiceActions(self) -> None:
        self.calculateDataAction.triggered.connect(self.calculateData)
        self.createMapAction.triggered.connect(self.createMap)
        self.createReportAction.triggered.connect(self.createReport)
        self.pythonConsoleAction.triggered.connect(self.pythonConsole)

    def _connectViewActions(self) -> None:
        self.hideLeftMenuAction.triggered.connect(self.hideLeftMenuOnClick)
        self.createGraphAction.triggered.connect(self.createGraph)
        self.cascadeAction.triggered.connect(self.cascadeWindows)
        self.horizontalAction.triggered.connect(self.horizontalWindows)
        self.verticalAction.triggered.connect(self.verticalWindows)
        self.trackGraphAction.triggered.connect(self.trackGraph)
        self.closeAllAction.triggered.connect(self._closeAllWindows)

    def _connectSettingsActions(self) -> None:
        self.openSettingsActions.triggered.connect(self.openSettings)
        self.loadSettingsFromFileActions.triggered.connect(
            self.loadSettingFromFile
        )
        self.saveSettingsToFileActions.triggered.connect(
            self.saveSettingsToFile
        )
        self.setDefaultSettingsActions.triggered.connect(
            partial(self.setDefaultSettings, True))
        self.aboutAction.triggered.connect(self.about)

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

    def clearMainWindow(self) -> None:
        del self.controller
        self.controller = Control()
        self.tree_widget.clear()
        self.tree_widget.hide()
        self.mdi.closeAllSubWindows()
        self.destroyChildWindow()
        self.checkPositioningWindows()
        self.trackGraph()
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

    def openBinaryFile(self, filepath=None) -> None:
        '''
        Метод открытия файлов в зависимостиот параметра.
        Открывает любые бинарные, которые могут использоваться
        в программе.
        '''
        # TODO передалть на ласт файл на filepath открыть последний открытый
        if filepath:
            check = True
            file = filepath
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

    def getOpenFileWindow(self, filetype: str) -> None:
        if self.openFileWindow is None:
            try:
                categories = self.controller.get_json_categories(
                    self.settings.value('mainSettings')['jsonDir']
                )
                self.openFileWindow = Open_file_window(
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
            self.openFileWindow.hide()
        self.center(self.openFileWindow)
        self.openFileWindow.show()

    def destroyChildWindow(self) -> None:
        '''
        Метод удаления дочерних окон.
        '''
        windows = [
            'settingsWindow',
            'reportWindow',
            'mapWindow',
            'calcWindow',
            'openFileWindow',
        ]
        for window in windows:
            if getattr(self, window):
                delete(getattr(self, window))
                setattr(self, window, None)

    def saveCsvData(self) -> None:
        '''
        Сохранение данных в формате CSV
        '''
        if not self.checkData():
            return

        if self.saveCsvWindow is None:
            self.saveCsvWindow = SaveCsvWindow(self.controller, self)
        else:
            self.saveCsvWindow.hide()
        self.center(self.saveCsvWindow)
        self.saveCsvWindow.show()

    def saveGzipData(self) -> None:
        '''
        Сохранение данных в формате pickle gzip 
        '''
        if not self.checkData():
            return

        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            "",
            "gzip Files (*.gzip);;All Files(*)",
            options=options
        )
        if filePath:
            try:
                self.controller.save_gzip(filePath)
            except PermissionError:
                self.setNotify(
                    'ошибка', 'Файл открыт в другой программе или занят.')
            except Exception as e:
                self.setNotify(
                    'ошибка', str(e)
                )
            else:
                self.setNotify(
                    'успех', f'gzip файл сохранен в {filePath}'
                )

    def calculateData(self) -> None:
        '''
        Метод для расчета данных
        '''
        if not self.checkData():
            return

        if self.calcWindow is None:
            self.calcWindow = CalcWindow(self.controller, self)
        else:
            self.calcWindow.hide()
        self.center(self.calcWindow)
        self.calcWindow.show()

    def createMap(self) -> None:
        '''
        Метод для открытия окна генерации карты
        '''
        if not self.checkData():
            return

        if self.mapWindow is None:
            self.mapWindow = MapWindow(self.controller, self)
        else:
            self.mapWindow.hide()
        self.center(self.mapWindow)
        self.mapWindow.show()

    def createReport(self) -> None:
        '''
        Метод для открытия окна создания отчёта
        '''
        # TODO обновить проверку на необходимые данные
        if not self.checkData():
            return

        if not self.controller.is_calculated():
            self.setNotify(
                'предупреждение',
                'Нужно получить расчетные данные.'
            )
            return
        if self.reportWindow is None:
            self.reportWindow = Report_window(self.controller, self)
        else:
            self.reportWindow.hide()
        self.center(self.reportWindow)
        self.reportWindow.show()

    def about(self):
        '''
        Метод для открытия окна about
        '''
        return

    def bigWindow(self) -> None:
        from PyQt5.QtWidgets import QWidget, QVBoxLayout

        self.bigWindow = QWidget()
        self.bigWindow.showMaximized()
        self.bigLayer = QVBoxLayout()
        self.bigMdi = QMdiArea()
        for window in self.mdi.subWindowList():
            window.setParent(self.bigMdi)
            print(window.frameGeometry())
        self.bigLayer.addWidget(self.bigMdi)
        self.bigWindow.setLayout(self.bigLayer)
        return

    def createGraph(self, customSelected=None) -> None:
        '''
        Метод для создания окон графиков по чек-боксу бокового меню
        '''
        if customSelected:
            treeSelected = customSelected
        else:
            treeSelected = self._getTreeSelected()

        if self.spinBox.text() != '0':
            decimation = int(self.spinBox.text())
        else:
            decimation = 1
        try:
            graphWindow = GraphWindow(
                self.controller.get_data(),
                treeSelected,
                decimation,
                self
            )
        except AttributeError:
            self.setNotify(
                'предупреждение', 'Данные не в нужном формате.'
            )
        except KeyError:
            if customSelected:
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
            if customSelected:
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
            self.mdi.addSubWindow(graphWindow)
            graphWindow.show()
            self.trackGraph()
            self.checkPositioningWindows()

    def createDropdownDefaultGraph(self):
        menu = QMenu(self)
        if not self.settings.value('graphs')['default']:
            return
        for category in self.settings.value('graphs')['default']:
            menu.addAction(
                category['name'],
                partial(self.createDefaultGraph, category['rows']))
        return menu

    def createDefaultGraph(self, rows) -> None:
        '''
        Метод создания типовых графиков, которые задаются в настройках
        '''
        if not self.checkData():
            return
        rows = sorted(rows, key=lambda x: x['row'])
        for row in rows:
            graph = [
                (field['category'], field['adr'], field['column'])
                for field in row['fields']
            ]
            self.createGraph(graph)

        width = self.mdi.width()
        heigth = self.mdi.height()
        pnt = [0, 0]
        for row, window in zip(rows, self.mdi.subWindowList()):
            currentHeigth = int(heigth * row['width'] * 0.01)
            window.showNormal()
            window.setGeometry(0, 0, width, currentHeigth)
            window.move(pnt[0], pnt[1])
            pnt[1] += currentHeigth

    def pythonConsole(self) -> None:
        '''
        Метод для открытия окна консоли
        '''
        if not self.checkData():
            return

        if self.consoleWindow is None:
            self.consoleWindow = ConsoleWindow(self.controller, self)
        else:
            self.consoleWindow.hide()
        self.center(self.consoleWindow)
        self.consoleWindow.show()

    def cascadeWindows(self) -> None:
        '''
        Метод для построения окон в виде каскада.
        '''
        if not self.mdi.subWindowList():
            return
        self.verticalAction.setChecked(False)
        self.horizontalAction.setChecked(False)
        self.mdi.cascadeSubWindows()

    def horizontalWindows(self) -> None:
        '''
        Метод для построения окон в горизональном виде.
        '''
        if not self.mdi.subWindowList() or not self.horizontalAction.isChecked():
            self.horizontalAction.setChecked(False)
            return

        self.verticalAction.setChecked(False)
        width = self.mdi.width()
        heigth = self.mdi.height() // len(self.mdi.subWindowList())
        pnt = [0, 0]
        for window in self.mdi.subWindowList():
            window.setGeometry(pnt[0], pnt[1], width, heigth)
            pnt[1] += heigth

    def verticalWindows(self) -> None:
        '''
        Метод для построения окон в вертикальном виде.
        '''
        if not self.mdi.subWindowList() or not self.verticalAction.isChecked():
            self.verticalAction.setChecked(False)
            return

        self.horizontalAction.setChecked(False)
        width = self.mdi.width() // len(self.mdi.subWindowList())
        heigth = self.mdi.height()

        pnt = [0, 0]
        for window in self.mdi.subWindowList():
            window.setGeometry(pnt[0], pnt[1], width, heigth)
            pnt[0] += width

    def resizeHorizontalWindows(self):
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

    def checkPositioningWindows(self) -> None:
        if not self.mdi.subWindowList():
            self.verticalAction.setChecked(False)
            self.horizontalAction.setChecked(False)
            return
        if self.verticalAction.isChecked():
            self.verticalWindows()
            return
        if self.horizontalAction.isChecked():
            self.horizontalWindows()
            return
        self.resizeHorizontalWindows()

    def hideLeftMenuOnClick(self) -> None:
        '''Метод скрытия левого меню'''
        if self.hideLeftMenuAction.isChecked():
            self.hideLeftMenuAction.setIcon(self.getIcon(':eye'))
            self.tree_widget.hide()
            QCoreApplication.processEvents()
            self.mdi.resize(self.splitter.width(), self.splitter.height())
        else:
            self.hideLeftMenuAction.setIcon(self.getIcon(':eye-off'))
            self.tree_widget.show()
            QCoreApplication.processEvents()
            self.mdi.resize(
                self.splitter.width() - self.tree_widget.width() - 5,
                self.splitter.height()
            )
        self.checkPositioningWindows()

    def trackGraph(self) -> None:
        '''
        Метод для связи графиков по оси Ох.
        '''
        if not self.mdi.subWindowList():
            self.trackGraphAction.setChecked(False)
            return
        if self.trackGraphAction.isChecked():
            link = self.mdi.findChild(pg.PlotWidget)
            for child in self.mdi.subWindowList():
                child.findChild(pg.PlotWidget).setXLink(link)
        else:
            for child in self.mdi.subWindowList():
                child.findChild(pg.PlotWidget).setXLink(None)

    def _closeAllWindows(self) -> None:
        self.mdi.closeAllSubWindows()
        self.trackGraph()
        self.checkPositioningWindows()

    def closeEvent(self, event) -> None:
        '''
        Переназначение функции закрытия, для закрытия всех дочерних окон.
        '''
        QApplication.closeAllWindows()
        event.accept()

    def _getTreeSelected(self) -> list:
        '''
        Фукнция для получения всех отмеченных чек-боксов левого меню.
        '''
        treeSelected = []
        iterator = QTreeWidgetItemIterator(
            self.tree_widget, QTreeWidgetItemIterator.Checked)
        while iterator.value():
            item = iterator.value()
            itemName = item.text(0)
            adrName = item.parent().text(0)
            categoryName = item.parent().parent().text(0)
            treeSelected.append((categoryName, adrName, itemName))
            iterator += 1
        return treeSelected

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

    def openSettings(self) -> None:
        '''
        Метод открытия окна настроек.
        '''
        if self.settingsWindow is None:
            self.settingsWindow = SettingsWindow(self)
        else:
            self.settingsWindow.hide()
        self.center(self.settingsWindow)
        self.settingsWindow.show()

    def updateInterfaceFromSettings(self, param) -> None:
        if param == 'graphs':
            self.menuDefaultGraphAction.setMenu(
                self.createDropdownDefaultGraph()
            )
        if param == 'left_menu_filters':
            self.tree_widget.update_check_box()

    def loadSettingFromFile(self) -> None:
        '''
        Метод загрузки настроек из файла.
        '''
        filePath, check = QFileDialog.getOpenFileName(
            None,
            'Open file',
            '',
            'Json File (*.json)'
        )
        if check:
            try:
                data = self.controller.load_settings_json(filePath)
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
                    self.restartApp()
            except Exception as e:
                self.setNotify(
                    'ошибка', str(e)
                )

    def saveSettingsToFile(self) -> None:
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

    def setDefaultSettings(self, needRestart=False) -> None:
        '''
        Метод очистки и установки стандартных настроек.
        '''
        self.settings.clear()
        defaultSettings(self.settings, self.appVersion)
        if needRestart:
            question = QMessageBox.question(
                None,
                "Вопрос",
                "Стандартные настройки установлены, необходим перезапуск программы. Делаем?",
                QMessageBox.Yes | QMessageBox.No
            )
            if question == QMessageBox.Yes:
                self.restartApp()

    def restartApp(self) -> None:
        program = sys.executable
        QProcess.startDetached(program, sys.argv)
        QCoreApplication.quit()

    def checkData(self) -> bool:
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

    def updateChildWindows(self) -> None:
        attr = [
            'calcWindow', 'mapWindow',
            'reportWindow', 'settingsWindow'
        ]
        for attr_name in attr:
            if getattr(self, attr_name) is not None:
                getattr(self, attr_name).updateWidget()
