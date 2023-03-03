from app.controller.controller import Control, NoneJsonError
from app.view.graphWindow import GraphWindow
from app.view.mapWindow import MapWindow
from app.view.reportWindow import ReportWindow
from app.view.consoleWindow import ConsoleWindow
from app.view.settingsWindow import SettingsWindow
from app.view.calculateWindow import CalcWindow
from app.view.saveCsvWindow import SaveCsvWindow
from app.view.openFileWindow import OpenFileWindow
import app.view.qrc_resources
import pyqtgraph as pg
from PyQt5.sip import delete
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette, QPainter
from PyQt5.QtCore import Qt, QSettings, QCoreApplication
from PyQt5 import QtWidgets as qtw
from functools import partial
from notificator import notificator
from notificator.alingments import BottomRight


class MainWindow(qtw.QMainWindow):
    '''
    Класс основного окна. 
    При инициализаци создается контроллер и переменны для окон.
    Если настройки пустые или устарели - создаются настройки по-умолчанию.
    '''
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.mapWindow = None
        self.reportWindow = None
        self.consoleWindow = None
        self.settingsWindow = None
        self.calcWindow = None
        self.saveCsvWindow = None
        self.openFileWindow = None
        self.controller = Control()
        self.filePath = None
        self.filePathPdd = None
        self.notify = None
        self.app_version = QCoreApplication.applicationVersion()
        self.app_name = QCoreApplication.applicationName()

        self.settings = QSettings()
        if (self.settings.allKeys() == [] or 
            self.settings.value('version') != self.app_version):
            self.setDefaultSettings()
        self.setTheme()
        self.initUI()

        # TODO удалить на релизе
        if self.settings.value('lastFile') is not None:
            lastFile = self.settings.value('lastFile')
            self.openFile(lastFile['param'], lastFile['filePath'])

    def initUI(self):
        '''
        Создание основных элементов интерфейса.
        Создание Экшенов, меню, тулбара, статус бара, связей.
        Для уведомлений используется сторонняя библиотека.
        '''
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle(f'{self.app_name} {self.app_version}')
        self._createActions()
        self._createMenuBar()
        self._createToolBar()
        self._createStatusBar()
        self._connectActions()
        self.notify = notificator()

        self.mdi = qtw.QMdiArea()
        self.mdi.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.mdi.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.splitter = qtw.QSplitter(Qt.Horizontal)
        self.setStyleSheet("qtw.QSplitter::handle{background: white;}")

        self.tree = qtw.QTreeWidget(self.splitter)
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(['name', 'count'])
        self.tree.hide()

        self.splitter.addWidget(self.tree)
        self.splitter.addWidget(self.mdi)

        self.setCentralWidget(self.splitter)
        self.center()
        self.showMaximized()

    @staticmethod
    def getPalette():
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        return palette

    def setTheme(self):
        if self.settings.value('mainSettings')['theme'] == 'black':
            self.app.setPalette(self.getPalette())

    def _createMenuBar(self):
        '''
        Генерация меню
        '''
        self.menuBar = self.menuBar()
        self._createFileMenu()
        self._createViewMenu()
        self._createServiceMenu()
        self._createSettingsMenu()

    def _createFileMenu(self):
        fileMenu = self.menuBar.addMenu('&File')
        fileMenu.addAction(self.clearAction)

        openSourceMenu = fileMenu.addMenu('Open &source')
        openSourceMenu.setIcon(self.getIcon(':file-plus.svg'))
        openSourceMenu.addAction(self.openTxtAction)
        openSourceMenu.addAction(self.openPddAction)

        openDataMenu = fileMenu.addMenu('&Open data')
        openDataMenu.setIcon(self.getIcon(':database.svg'))
        openDataMenu.addAction(self.openPickleAction)
        openDataMenu.addAction(self.openCsvAction)

        saveMenu = fileMenu.addMenu('&Save as')
        saveMenu.setIcon(self.getIcon(':save'))
        saveMenu.addAction(self.savePickleAction)
        saveMenu.addAction(self.saveCsvAction)

        fileMenu.addSeparator()
        fileMenu.addAction(self.exitAction)

    def _createViewMenu(self):
        viewMenu = self.menuBar.addMenu('&View')
        viewMenu.addAction(self.hideLeftMenuAction)
        viewMenu.addAction(self.createGraphAction)
        viewMenu.addAction(self.createDefaultGraphAction)
        viewMenu.addAction(self.cascadeAction)
        viewMenu.addAction(self.horizontalAction)
        viewMenu.addAction(self.verticalAction)
        viewMenu.addAction(self.trackGraphAction)
        viewMenu.addSeparator()
        viewMenu.addAction(self.closeAllAction)

    def _createServiceMenu(self):
        serviceMenu = self.menuBar.addMenu('&Service')
        serviceMenu.addAction(self.calculateDataAction)
        serviceMenu.addAction(self.createMapAction)
        serviceMenu.addAction(self.createReportAction)
        serviceMenu.addAction(self.pythonConsoleAction)

    def _createSettingsMenu(self):
        settingsMenu = self.menuBar.addMenu('&Settings')
        settingsMenu.addAction(self.openSettingsActions)
        settingsMenu.addAction(self.loadSettingsFromFileActions)
        settingsMenu.addAction(self.saveSettingsToFileActions)
        settingsMenu.addAction(self.setDefaultSettingsActions)
        settingsMenu.addAction(self.aboutAction)

    def _createToolBar(self):
        '''
        Создание тулбара.
        '''
        self._createFileToolBar()
        self._createServiceToolBar()
        self._createViewToolBar()

    def _createFileToolBar(self):
        fileToolBar = self.addToolBar('File')
        fileToolBar.addAction(self.openTxtAction)
        fileToolBar.addAction(self.openPickleAction)
        fileToolBar.addAction(self.savePickleAction)
        fileToolBar.addSeparator()
        fileToolBar.addAction(self.exitAction)
        fileToolBar.setMovable(False)

    def _createServiceToolBar(self):
        serviceToolBar = self.addToolBar('Service')
        serviceToolBar.addAction(self.calculateDataAction)
        serviceToolBar.addAction(self.pythonConsoleAction)

    def _createViewToolBar(self):
        viewToolBar = self.addToolBar('View')
        viewToolBar.addAction(self.hideLeftMenuAction)
        viewToolBar.addAction(self.createGraphAction)
        viewToolBar.addAction(self.createDefaultGraphAction)
        self.spinBox = qtw.QSpinBox()
        self.spinBox.setMinimum(1)
        viewToolBar.addWidget(self.spinBox)
        viewToolBar.addSeparator()
        viewToolBar.addAction(self.cascadeAction)
        viewToolBar.addAction(self.horizontalAction)
        viewToolBar.addAction(self.verticalAction)
        viewToolBar.addAction(self.trackGraphAction)
        viewToolBar.addSeparator()
        viewToolBar.addAction(self.closeAllAction)

    def _createStatusBar(self):
        '''
        Создание статус бара.
        '''
        self.statusbar = self.statusBar()
        self.statusbar.showMessage('Hello world!', 3000)
        self.openedFilesLabel = qtw.QLabel(
            f'File TXT: {self.filePath}, File PDD: {self.filePathPdd}')
        self.statusbar.addPermanentWidget(self.openedFilesLabel)

    def _createActions(self):
        '''
        Создание Actions
        '''
        self._creteFileActions()
        self._creteServiceActions()
        self._createViewActions()
        self._createSettingsActions()

    def _creteFileActions(self):
        self.clearAction = qtw.QAction('Clea&r', self)
        self.clearAction.setIcon(self.getIcon(':x.svg'))
        self.clearAction.setStatusTip('Clear')

        self.openTxtAction = qtw.QAction('Open *.&txt...', self)
        self.openTxtAction.setIcon(self.getIcon(':file-plus.svg'))
        self.openTxtAction.setStatusTip('Open TXT file')

        self.openPddAction = qtw.QAction('Open *.&pdd...', self)
        self.openPddAction.setIcon(self.getIcon(':file.svg'))
        self.openPddAction.setStatusTip('Open file')

        self.openCsvAction = qtw.QAction('Open *.&csv...', self)
        self.openCsvAction.setIcon(self.getIcon(':file-text.svg'))
        self.openCsvAction.setStatusTip('Open CSV file')

        self.openPickleAction = qtw.QAction('Open *.&pickle...', self)
        self.openPickleAction.setIcon(self.getIcon(':file.svg'))
        self.openPickleAction.setStatusTip(
            'Open pickle file')

        self.savePickleAction = qtw.QAction('Save as *.pickle...', self)
        self.savePickleAction.setIcon(self.getIcon(':save.svg'))
        self.savePickleAction.setStatusTip(
            'Save data to pickle file')
        self.savePickleAction.setShortcut('Ctrl+S')

        self.saveCsvAction = qtw.QAction('Save as *.csv...', self)
        self.saveCsvAction.setIcon(self.getIcon(':file-text.svg'))
        self.saveCsvAction.setStatusTip('Save data to csv file')

        self.exitAction = qtw.QAction('&Exit', self)
        self.exitAction.setIcon(self.getIcon(':log-out.svg'))
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.setShortcut('Ctrl+Q')

    def _creteServiceActions(self):
        self.calculateDataAction = qtw.QAction('&Calculate data')
        self.calculateDataAction.setIcon(self.getIcon(':percent.svg'))
        self.calculateDataAction.setStatusTip('Calculate data from source')

        self.createMapAction = qtw.QAction('Create &map', self)
        self.createMapAction.setIcon(self.getIcon(':map.svg'))
        self.createMapAction.setStatusTip('Create interactive map')

        self.createReportAction = qtw.QAction('Create &report', self)
        self.createReportAction.setIcon(self.getIcon(':mail.svg'))
        self.createReportAction.setStatusTip('Create xlsx report')

        self.pythonConsoleAction = qtw.QAction('&Python Console', self)
        self.pythonConsoleAction.setIcon(self.getIcon(':terminal'))
        self.createReportAction.setStatusTip('Open python console window')

    def _createViewActions(self):
        self.hideLeftMenuAction = qtw.QAction('&Hide left menu')
        self.hideLeftMenuAction.setIcon(self.getIcon(':eye-off'))
        self.hideLeftMenuAction.setStatusTip('Hide/Unhide left menu')
        self.hideLeftMenuAction.setCheckable(True)

        self.createGraphAction = qtw.QAction('&Create graph')
        self.createGraphAction.setIcon(self.getIcon(':trending-up.svg'))
        self.createGraphAction.setStatusTip('Create graph in new window')

        self.createDefaultGraphAction = qtw.QAction('&Create default graphs')
        self.createDefaultGraphAction.setIcon(self.getIcon(':shuffle.svg'))
        self.createDefaultGraphAction.setStatusTip(
            'Create default graph in new window')

        self.cascadeAction = qtw.QAction('Casca&de Windows')
        self.cascadeAction.setIcon(self.getIcon(':bar-chart.svg'))
        self.cascadeAction.setStatusTip('Cascade View Graph Windows')

        self.horizontalAction = qtw.QAction('&Horizontal Windows')
        self.horizontalAction.setIcon(self.getIcon(':more-vertical.svg'))
        self.horizontalAction.setStatusTip('Horizontal View Graph Windows')

        self.verticalAction = qtw.QAction('&Vertical Windows')
        self.verticalAction.setIcon(self.getIcon(':more-horizontal.svg'))
        self.verticalAction.setStatusTip('Vertical View Graph Windows')

        self.trackGraphAction = qtw.QAction('&Track graph')
        self.trackGraphAction.setIcon(self.getIcon(':move.svg'))
        self.trackGraphAction.setStatusTip('Track Grapth in all Windows')
        self.trackGraphAction.setCheckable(True)

        self.closeAllAction = qtw.QAction('Close &all Windows')
        self.closeAllAction.setIcon(self.getIcon(':x-circle.svg'))
        self.closeAllAction.setStatusTip('Close all opened Windows')

    def _createSettingsActions(self):
        self.openSettingsActions = qtw.QAction('&Settings')
        self.openSettingsActions.setIcon(self.getIcon(':settings.svg'))
        self.openSettingsActions.setStatusTip('Settings menu')

        self.setDefaultSettingsActions = qtw.QAction('Set &default settings')
        self.setDefaultSettingsActions.setIcon(self.getIcon(':sliders.svg'))
        self.setDefaultSettingsActions.setStatusTip('Set default settings')

        self.loadSettingsFromFileActions = qtw.QAction(
            'Load settings from file')
        self.loadSettingsFromFileActions.setIcon(self.getIcon(':download.svg'))
        self.loadSettingsFromFileActions.setStatusTip(
            'Save settings to file json')

        self.saveSettingsToFileActions = qtw.QAction('Sa&ve settings to file')
        self.saveSettingsToFileActions.setIcon(self.getIcon(':save.svg'))
        self.saveSettingsToFileActions.setStatusTip(
            'Save settings to file json')

        self.aboutAction = qtw.QAction('&About')
        self.aboutAction.setIcon(self.getIcon(':help-circle.svg'))
        self.aboutAction.setStatusTip('About programm')

    def _connectActions(self):
        '''
        Соединение функций и Actions
        '''
        self._connectFileActions()
        self._connectServiceActions()
        self._connectViewActions()
        self._connectSettingsActions()

    def _connectFileActions(self):
        self.clearAction.triggered.connect(self.clearMainWindow)
        self.openTxtAction.triggered.connect(partial(self.openTextFile, 'txt'))
        self.openPddAction.triggered.connect(partial(self.openFile, 'pdd'))
        self.openPickleAction.triggered.connect(
            partial(self.openFile, 'pkl'))
        self.openCsvAction.triggered.connect(partial(self.openTextFile, 'csv'))
        self.savePickleAction.triggered.connect(self.savePickleData)
        self.saveCsvAction.triggered.connect(self.saveCsvData)
        self.exitAction.triggered.connect(self.close)

    def _connectServiceActions(self):
        self.calculateDataAction.triggered.connect(self.calculateData)
        self.createMapAction.triggered.connect(self.createMap)
        self.createReportAction.triggered.connect(self.createReport)
        self.pythonConsoleAction.triggered.connect(self.pythonConsole)

    def _connectViewActions(self):
        self.hideLeftMenuAction.triggered.connect(self.hideLeftMenu)
        self.createGraphAction.triggered.connect(self.createGraph)
        self.createDefaultGraphAction.triggered.connect(
            self.createDefaultGraph)
        self.cascadeAction.triggered.connect(self.cascadeWindows)
        self.horizontalAction.triggered.connect(self.horizontalWindows)
        self.verticalAction.triggered.connect(self.verticalWindows)
        self.trackGraphAction.triggered.connect(self.trackGraph)
        self.trackGraphAction.toggled.connect(self.trackGraph)
        self.closeAllAction.triggered.connect(self._closeAllWindows)

    def _connectSettingsActions(self):
        self.openSettingsActions.triggered.connect(self.openSettings)
        self.loadSettingsFromFileActions.triggered.connect(
            self.loadSettingFromFile)
        self.saveSettingsToFileActions.triggered.connect(
            self.saveSettingsToFile)
        self.setDefaultSettingsActions.triggered.connect(
            self.setDefaultSettings)
        self.aboutAction.triggered.connect(self.about)

    def createCheckBox(self):
        '''
        Создание бокового чек-бокс дерева для построения графиков
        '''
        if self.controller.get_data() == {}:
            self.setNotify('warning', 'Need to select the data')
            return

        self.tree.clear()
        data = self.controller.get_data()
        for nameCategory, adrs in sorted(data.items(), key=lambda x: x[0]):
            treeCategory = qtw.QTreeWidgetItem(self.tree)
            treeCategory.setText(0, nameCategory)
            treeCategory.setExpanded(True)
            for nameAdr, adrValues in adrs.items():
                treeAdr = qtw.QTreeWidgetItem(treeCategory)
                treeAdr.setText(0, nameAdr)
                treeAdr.setExpanded(True)
                filters = self.settings.value('leftMenuFilters')
                for nameItem in list(adrValues.columns.values):
                    if filters.get(nameItem, filters['unknown']):
                        treeItem = qtw.QTreeWidgetItem(treeAdr)
                        treeItem.setText(0, nameItem)
                        count = len(adrValues[nameItem])
                        treeItem.setText(1, str(count))
                        treeItem.setFont(1, QFont('Arial', 8, 1, True))
                        if count:
                            treeItem.setForeground(1, QColor('gray'))
                        else:
                            treeItem.setForeground(1, QColor('red'))
                        treeItem.setTextAlignment(1, 2)
                        treeItem.setFlags(treeItem.flags() | Qt.ItemIsUserCheckable)
                        treeItem.setCheckState(0, Qt.Unchecked)
        self.tree.show()
        self.tree.resizeColumnToContents(0)
        self.tree.resizeColumnToContents(1)
        self.splitter.setSizes([120, 500])

    def center(self, obj=None):
        '''
        Метод для установки окна в центре экрана
        '''
        if obj is None:
            obj = self
        qr = obj.frameGeometry()
        cp = self.screen().geometry().center()
        qr.moveCenter(cp)
        obj.move(qr.topLeft())

    def clearMainWindow(self):
        del self.controller
        self.controller = Control()
        self.tree.clear()
        self.tree.hide()
        self.mdi.closeAllSubWindows()
        self._destroyChildWindow()
        self.trackGraph()

    def hideLeftMenu(self):
        if self.hideLeftMenuAction.isChecked():
            self.hideLeftMenuAction.setIcon(self.getIcon(':eye'))
            self.tree.hide()
        else: 
            self.hideLeftMenuAction.setIcon(self.getIcon(':eye-off'))
            self.tree.show()

    def getIcon(self, name):
        icon = QIcon(name)
        if self.settings.value('mainSettings')['theme'] == 'white':
            return icon
        pixmap = icon.pixmap(50,50)
        color = QColor(255, 255, 255)
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), color)
        painter.end()
        return QIcon(pixmap)
    def openFile(self, filetype, filepath=None):
        '''
        Метод открытия файлов в зависимостиот параметра.
        Открывает любые типы файлов, которые могут использоваться
        в программе.
        '''
        # TODO передалть на ласт файл на filepath открыть последний открытый
        if filepath:
            self.filePath = filepath
            check = True
        else:
            self.filePath, check = qtw.QFileDialog.getOpenFileName(None,
                                                                   'Open file', '', f'Open File (*.{filetype})')
        if check:
            try:
                # if param == 'txt':
                #     self.controller.load_txt(self.filePath)
                # if param == 'csv':
                #     self.controller.load_csv(self.filePath)
                if filetype == 'pkl':
                    self.controller.load_pickle(self.filePath)
                if filetype == 'pdd':
                    self.controller.load_pdd(self.filePath)
                self.createCheckBox()
                self.updateOpenedFiles()
                self._destroyChildWindow()
                self.settings.setValue('lastFile',
                                       {'filePath': self.filePath,
                                        'param': filetype})
                self.setNotify('success', f'{self.filePath} file opened')
            except ValueError as e:
                self.setNotify('error', str(e))

    def openTextFile(self, filetype):
        if self.openFileWindow is None:
            try:
                categories = self.controller.get_json_categories(
                    self.settings.value('mainSettings')['jsonDir'])
                self.openFileWindow = OpenFileWindow(self.controller, filetype, categories, self)
            except KeyError:
                self.setNotify('error', 'bad json data in json folder')
                return
            except NoneJsonError:
                self.setNotify('error', 'not json in folder')
                return
            except Exception as e:
                self.setNotify('error', str(e))
                return
        else:
            self.openFileWindow.hide()
        self.center(self.openFileWindow)
        self.openFileWindow.show()
    
    def _destroyChildWindow(self):
        '''
        Метод удаления дочерних окон.
        Необходим для обновления информации в них. Временное решение.
        '''
        #TODO на подумать, можно в этих окнах реализовать апдейт
        #при открытии нового файла
        if self.reportWindow: 
            delete(self.reportWindow)
            self.reportWindow = None
        if self.mapWindow: 
            delete(self.mapWindow)
            self.mapWindow = None
        if self.calcWindow:
            delete(self.calcWindow)
            self.calcWindow = None
        if self.openFileWindow:
            delete(self.openFileWindow)
            self.openFileWindow = None

    def saveCsvData(self):
        '''
        Сохранение данных в формате CSV
        '''
        if self.controller.get_data() == {}:
            self.setNotify('warning', 'Need to select the data')
            return

        if self.saveCsvWindow is None:
            self.saveCsvWindow = SaveCsvWindow(self.controller, self)
        else:
            self.saveCsvWindow.hide()
        self.center(self.saveCsvWindow)
        self.saveCsvWindow.show()

    def savePickleData(self):
        '''
        Сохранение данных в формате pickle
        '''
        if self.controller.get_data() == {}:
            self.setNotify('warning', 'Need to select the data')
            return
        options = qtw.QFileDialog.Options()
        filePath, _ = qtw.QFileDialog.getSaveFileName(self,
            "Save File", "", "Pickle Files (*.pkl);;All Files(*)",
                                                      options=options)
        if filePath:
            try:
                self.controller.save_pickle(filePath)
                self.setNotify('success', f'Pickle file saved to {filePath}')
            except PermissionError:
                self.setNotify('error', 'File opened in another program')
            except Exception as e:
                self.setNotify('error', str(e))

    def calculateData(self):
        '''
        Метод для расчета данных
        '''
        if self.controller.get_data() == {}:
            self.setNotify('warning', 'Need to select the data')
            return

        if self.calcWindow is None:
            self.calcWindow = CalcWindow(self.controller, self)
        else:
            self.calcWindow.hide()
        self.center(self.calcWindow)
        self.calcWindow.show()

    def createMap(self):
        '''
        Метод для открытия окна генерации карты
        '''
        if self.controller.get_data() == {}:
            self.setNotify('warning', 'Need to select the data')
            return
        if self.mapWindow is None:
            self.mapWindow = MapWindow(self.controller, self)
        else:
            self.mapWindow.hide()
        self.center(self.mapWindow)
        self.mapWindow.show()

    def createReport(self):
        '''
        Метод для открытия окна создания отчёта
        '''
        #TODO обновить проверку на необходимые данные
        if self.controller.get_data() == {}:
            self.setNotify('warning', 'Need to select the data')
            return
        if not self.controller.is_calculated():
            self.setNotify('warning', 'Need to calcuclate the data')
            return
        if self.reportWindow is None:
            self.reportWindow = ReportWindow(self.controller, self)
        else:
            self.reportWindow.hide()
        self.center(self.reportWindow)
        self.reportWindow.show()

    def about(self):
        '''
        Метод для открытия окна about
        '''
        pass

    def createGraph(self):
        '''
        Метод для создания окон графиков по чек-боксу бокового меню
        '''
        selectedTree = self._getTreeSelected()
        if self.controller.get_data() == {} or selectedTree == []:
            self.setNotify(
                'warning', 'Need to select the data or data for graph')
            return
        
        if self.spinBox.text() != '0':
            decimation = int(self.spinBox.text())
        else: decimation = 1
        
        graphWindow = GraphWindow(self.controller.get_data(), selectedTree, decimation, self)
        self.mdi.addSubWindow(graphWindow)
        graphWindow.show()
        self.trackGraph()

    def createDefaultGraph(self):
        '''
        Метод создания типовых графиков, которые задаются в настройках
        '''
        #TODO исправить отрисовку стандратных графиков с новым форматом данных
        if self.controller.get_data() == {} or self.settings.value('graphs')['default'] == []:
            self.setNotify(
                'warning', 'Need to select the data or check settings graphs')
            return

        if self.spinBox.text() != '0':
            decimation = int(self.spinBox.text())
        else: decimation = 1

        for graph in self.settings.value('graphs')['default']:
            if not set(graph).issubset(self.controller.get_data().columns):
                self.setNotify('warning', f'{graph} not find in data')
                continue
            graphWindow = GraphWindow(self.controller.get_data(), graph, decimation, self)
            self.mdi.addSubWindow(graphWindow)
            graphWindow.show()
        self.horizontalWindows()
        self.trackGraph()

    def createGraphForConsole(self, data, *args):
        '''
        Вспомогательный Метод для создания графика из консоли.
        '''
        #TODO продумать и изменить метод для консоли из-за нового формата данных
        if data is None:
            return
        graphWindow = GraphWindow(data, args, self)
        self.mdi.addSubWindow(graphWindow)
        graphWindow.show()

    def pythonConsole(self):
        '''
        Метод для открытия окна консоли
        '''
        if self.controller.get_data() == {}:
            self.setNotify('warning', 'Need to select the data')
            return
        if self.consoleWindow is None:
            self.consoleWindow = ConsoleWindow(self.controller, self)
        else:
            self.consoleWindow.hide()
        self.center(self.consoleWindow)
        self.consoleWindow.show()

    def cascadeWindows(self):
        '''
        Метод для построения окон в виде каскада.
        '''
        self.mdi.cascadeSubWindows()

    def horizontalWindows(self):
        '''
        Метод для построения окон в горизональном виде.
        '''
        if not self.mdi.subWindowList():
            return
        width = self.mdi.width()
        heigth = self.mdi.height() // len(self.mdi.subWindowList())
        pnt = [0, 0]
        for window in self.mdi.subWindowList():
            window.showNormal()
            window.setGeometry(0, 0, width, heigth)
            window.move(pnt[0], pnt[1])
            pnt[1] += heigth

    def verticalWindows(self):
        '''
        Метод для построения окон в вертикальном виде.
        '''
        if not self.mdi.subWindowList():
            return
        width = self.mdi.width() // len(self.mdi.subWindowList())
        heigth = self.mdi.height()
        pnt = [0, 0]
        for window in self.mdi.subWindowList():
            window.showNormal()
            window.setGeometry(0, 0, width, heigth)
            window.move(pnt[0], pnt[1])
            pnt[0] += width

    def trackGraph(self):
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

    def _closeAllWindows(self):
        self.mdi.closeAllSubWindows()
        self.trackGraph()

    def closeEvent(self, event):
        '''
        Переназначение функции закрытия, для закрытия всех дочерних окон.
        '''
        qtw.QApplication.closeAllWindows()
        event.accept()

    def _getTreeSelected(self):
        '''
        Фукнция для получения всех отмеченных чек-боксов левого меню.
        '''
        treeSelected = []
        iterator = qtw.QTreeWidgetItemIterator(
            self.tree, qtw.QTreeWidgetItemIterator.Checked)
        while iterator.value():
            item = iterator.value()
            item_name = item.text(0)
            adr_name = item.parent().text(0)
            category_name = item.parent().parent().text(0) 
            treeSelected.append((category_name, adr_name, item_name))
            iterator += 1
        return treeSelected

    def updateOpenedFiles(self):
        '''
        Метод обновления открытых файлов.
        '''
        #TODO необходимо продумать как отображать открытые файлы и надо ли это вообще
        self.openedFilesLabel.setText(
            f'File TXT: <b>{self.filePath}</b>, File PDD: <b>{self.filePathPdd}</b>')

    def setNotify(self, type, txt):
        '''
        Метод отправки библиотеки
        '''
        notify = self.notify.info
        if type == 'warning':
            notify = self.notify.warning
        if type == 'success':
            notify = self.notify.sucess
        if type == 'error':
            notify = self.notify.critical
        notify(type.title(), txt, self, Align=BottomRight, duracion=6)

    def defaultSettings(self):
        '''
        Метод установки стандартных настроек.
        '''
        self.settings.setValue('version', self.app_version)
        self.settings.setValue('koef_for_intervals',
                               {
                                   # макс разница, макс значение
                                   'tang': [4, 10],
                                   # макс разница, макс значение
                                   'kren': [1.4, 10],
                                   # макс разница, макс значение
                                   'h': [20, 200],
                                   # макс отношение, макс значение,усредение до, усреднение в моменте
                                   'wx': [0.025, 200, 150, 50]
                               })
        headers = ('popr_prib_cor_V_cod',
                   'popr_prib_cor_FI_cod',
                   'popr_prib_cor_B_cod',
                   'kurs_DISS_grad',
                   'kren_DISS_grad',
                   'tang_DISS_grad',
                   'k',
                   'k1')
        planesParams = {
            'mdm': dict(zip(headers, (5, 14, 2, -0.62, 0.032, 3.33 - 0.032, 1, 1))),
            'm2': dict(zip(headers, (7, 6, 1, 0.2833, 0.032, 3.33 - 0.2, 1, 1))),
            'IL78m90a': dict(zip(headers, (7, 15, 1, 0.27, 0, 3.33, 1, 1))),
            'IL76md90a': dict(zip(headers, (6, 15, 1, 0 - 0.665, -0.144, 3.33, 1, 1))),
            'tu22': dict(zip(headers, (6, 6, 2, 0, 0, 0, 1 / 3.6, 0.00508))),
            'tu160': dict(zip(headers, (6, 10, 1, 0, 0, -2.5, 1, 1)))
        }
        self.settings.setValue('planes', planesParams)
        self.settings.setValue('map', {'jvdHMin': '100', 'decimation': '20'})
        self.settings.setValue('lastFile', None)
        corrections = {'koef_Wx_PNK': 1, 'koef_Wy_PNK': 1, 'koef_Wz_PNK': 1,
                       'kurs_correct': 1, 'kren_correct': 1, 'tang_correct': 1}
        self.settings.setValue('corrections', corrections)
        #TODO изменить формат хранения стандартных графиков под новый вид даты
        #добавить возможность настройки цветов графиков
        graphs = {
            'background': 'black',
            'default': [['I1_Kren', 'I1_Tang'], ['JVD_H'], ['Wp_KBTIi', 'Wp_diss_pnki']]}
        self.settings.setValue('graphs', graphs)
        headers = [
            'time', 'latitude', 'longitude', 'JVD_H', 'JVD_VN', 'JVD_VE',
            'JVD_Vh', 'DIS_S266', 'DIS_Wx30', 'DIS_Wx31', 'DIS_S264', 'DIS_Wy30',
            'DIS_Wy31', 'DIS_S267', 'DIS_Wz30', 'DIS_Wz31', 'DIS_S206', 'DIS_US30',
            'DIS_US31', 'DIS_TIME', 'DIS_Wx', 'DIS_Wy', 'DIS_Wz', 'DIS_W', 'DIS_US',
            'I1_KursI', 'I1_Tang', 'I1_Kren', 'Wx_DISS_PNK', 'Wz_DISS_PNK',
            'Wy_DISS_PNK', 'Kren_sin', 'Kren_cos', 'Tang_sin', 'Tang_cos',
            'Kurs_sin', 'Kurs_cos', 'Wxg_KBTIi', 'Wzg_KBTIi', 'Wyg_KBTIi',
            'Wxc_KBTIi', 'Wyc_KBTIi', 'Wzc_KBTIi', 'Wp_KBTIi', 'Wp_diss_pnki', 'unknown'
        ]
        leftMenuFilters = {head: True for head in headers}
        self.settings.setValue('leftMenuFilters', leftMenuFilters)
        mainSettings = {'theme':'black', 'jsonDir':'templates'}
        self.settings.setValue('mainSettings', mainSettings)


    def openSettings(self):
        '''
        Метод открытия окна настроек.
        '''
        if self.settingsWindow is None:
            self.settingsWindow = SettingsWindow(self.controller, self)
        else:
            self.settingsWindow.hide()
        self.center(self.settingsWindow)
        self.settingsWindow.show()

    def loadSettingFromFile(self):
        '''
        Метод загрузки настроек из файла.
        '''
        filePath, check = qtw.QFileDialog.getOpenFileName(None,
                                                          'Open file', '', 'Json File (*.json)')
        if check:
            try:
                data = self.controller.load_settings_json(filePath)
                self.settings.clear()
                for key, value in data.items():
                    self.settings.setValue(key, value)
                self.setNotify('success', f'Settings updated. Restart program.')
            except Exception as e:
                self.setNotify('error', str(e))

    def saveSettingsToFile(self):
        '''
        Метод сохранения настроек в файл.
        '''
        options = qtw.QFileDialog.Options()
        filepath, _ = qtw.QFileDialog.getSaveFileName(self,
                                                      "Save File", "", f"Json Files (*.json);;All Files(*)",
                                                      options=options)
        data = {name: self.settings.value(name)
                for name in self.settings.allKeys()}
        if filepath:
            try:
                self.controller.save_settings_json(filepath, data)
                self.setNotify('success', f'Settings file saved to {filepath}')
            except PermissionError:
                self.setNotify('error', 'File opened in another program')
            except Exception as e:
                self.setNotify('error', str(e))

    def setDefaultSettings(self):
        '''
        Метод очистки и установки стандартных настроек.
        '''
        self.settings.clear()
        self.defaultSettings()
        if self.notify:
            self.setNotify(
                'success', 'Default settings are set. Restart program.')



