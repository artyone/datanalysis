import sys
import controller as ctlr
import view_graphWindow as graph
import view_mapWindow as map
import view_reportWindow as report
import view_pythonConsole as console
import qrc_resources
import pyqtgraph as pg
from PyQt5.sip import delete
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets as qtw
from functools import partial
from notificator import notificator
from notificator.alingments import BottomRight


class MainWindow(qtw.QMainWindow):

    def __init__(self):
        super().__init__()
        self.mapWindow = None
        self.reportWindow = None
        self.consoleWindow = None
        self.controller = None
        self.filePathTxt = None
        self.filePathPdd = None
        self.initUI()

        #TODO удалить на релизе
        self.openFile('snappy', 'output/123.snappy')

    def initUI(self):
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('Rp_datanalysis')
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
        self.tree.setHeaderHidden(True)
        self.tree.hide()

        self.splitter.addWidget(self.tree)
        self.splitter.addWidget(self.mdi)

        self.setCentralWidget(self.splitter)
        self.center()
        self.showMaximized()

    def _createMenuBar(self):
        self.menuBar = self.menuBar()
        self._createFileMenu()
        self._createViewMenu()
        self._createServiceMenu()
        self._createSettingsMenu()
        self._createHelpMenu()

    def _createFileMenu(self):
        fileMenu = self.menuBar.addMenu('&File')
        fileMenu.addAction(self.newAction)

        openSourceMenu = fileMenu.addMenu('Open &source')
        openSourceMenu.setIcon(QIcon(':file-plus.svg'))
        openSourceMenu.addAction(self.openTxtAction)
        openSourceMenu.addAction(self.openPddAction)

        openDataMenu = fileMenu.addMenu('&Open data')
        openDataMenu.setIcon(QIcon(':database.svg'))
        openDataMenu.addAction(self.openParquetAction)
        openDataMenu.addAction(self.openCsvAction)

        saveMenu = fileMenu.addMenu('&Save as')
        saveMenu.setIcon(QIcon(':save'))
        saveMenu.addAction(self.saveParquetAction)
        saveMenu.addAction(self.saveCsvAction)

        fileMenu.addSeparator()
        fileMenu.addAction(self.exitAction)
    
    def _createViewMenu(self):
        viewMenu = self.menuBar.addMenu('&View')
        viewMenu.addAction(self.createGraphAction)
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
    
    def _createHelpMenu(self):
        helpMenu = self.menuBar.addMenu('&Help')
        helpMenu.addAction(self.aboutAction)

    def _createToolBar(self):
        self._createFileToolBar()
        self._createServiceToolBar()
        self._createViewToolBar()

    def _createFileToolBar(self):
        fileToolBar = self.addToolBar('File')
        fileToolBar.addAction(self.openTxtAction)
        fileToolBar.addAction(self.openParquetAction)
        fileToolBar.addAction(self.saveParquetAction)
        fileToolBar.addSeparator()
        fileToolBar.addAction(self.exitAction)
        fileToolBar.setMovable(False)

    def _createServiceToolBar(self):
        serviceToolBar = self.addToolBar('Service')
        self.planeComboBox = qtw.QComboBox()
        self.planeComboBox.addItems(['mdm', 'm2', 'IL78m90a', 'IL76md90a', 'tu22', 'tu160'])
        serviceToolBar.addWidget(self.planeComboBox)
        serviceToolBar.addAction(self.calculateDataAction)
        serviceToolBar.addAction(self.pythonConsoleAction)
        
    def _createViewToolBar(self):
        viewToolBar = self.addToolBar('View')
        viewToolBar.addAction(self.createGraphAction)
        self.spinBox = qtw.QSpinBox()
        viewToolBar.addWidget(self.spinBox)
        viewToolBar.addSeparator()
        viewToolBar.addAction(self.cascadeAction)
        viewToolBar.addAction(self.horizontalAction)
        viewToolBar.addAction(self.verticalAction)
        viewToolBar.addAction(self.trackGraphAction)
        viewToolBar.addSeparator()
        viewToolBar.addAction(self.closeAllAction)

    def _createStatusBar(self):
        self.statusbar = self.statusBar()
        self.statusbar.showMessage('Hello world!', 3000)
        self.openedFilesLabel = qtw.QLabel(
            f'File TXT: {self.filePathTxt}, File PDD: {self.filePathPdd}')
        self.statusbar.addPermanentWidget(self.openedFilesLabel)

    def _createActions(self):
        self._creteFileActions()
        self._creteServiceActions()
        self._createViewActions()

        self.aboutAction = qtw.QAction('&About', self)
        self.aboutAction.setIcon(QIcon(':help-circle.svg'))
        self.aboutAction.setStatusTip('About programm')

    def _creteFileActions(self):
        self.newAction = qtw.QAction('&New', self)
        self.newAction.setIcon(QIcon(':file.svg'))
        self.newAction.setStatusTip('Clear')

        self.openTxtAction = qtw.QAction('Open *.&txt...', self)
        self.openTxtAction.setIcon(QIcon(':file-text.svg'))
        self.openTxtAction.setStatusTip('Open TXT file')

        self.openPddAction = qtw.QAction('Open *.&pdd...', self)
        self.openPddAction.setIcon(QIcon(':file.svg'))
        self.openPddAction.setStatusTip('Open file')

        self.openCsvAction = qtw.QAction('Open *.&csv...', self)
        self.openCsvAction.setIcon(QIcon(':file-text.svg'))
        self.openCsvAction.setStatusTip('Open CSV file')

        self.openParquetAction = qtw.QAction('Open *.&snappy...', self)
        self.openParquetAction.setIcon(QIcon(':file.svg'))
        self.openParquetAction.setStatusTip('Open Parquet with compression snappy file')

        self.saveParquetAction = qtw.QAction('Save as *.snappy...', self)
        self.saveParquetAction.setIcon(QIcon(':save.svg'))
        self.saveParquetAction.setStatusTip('Save data to parquet file with compression snappy')
        self.saveParquetAction.setShortcut('Ctrl+S')

        self.saveCsvAction = qtw.QAction('Save as *.csv...', self)
        self.saveCsvAction.setIcon(QIcon(':file-text.svg'))
        self.saveCsvAction.setStatusTip('Save data to csv file')

        self.exitAction = qtw.QAction('&Exit', self)
        self.exitAction.setIcon(QIcon(':log-out.svg'))
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.setShortcut('Ctrl+Q')

    def _creteServiceActions(self):
        self.calculateDataAction = qtw.QAction('&Calculate data')
        self.calculateDataAction.setIcon(QIcon(':percent.svg'))
        self.calculateDataAction.setStatusTip('Calculate data from source')

        self.createMapAction = qtw.QAction('Create &map', self)
        self.createMapAction.setIcon(QIcon(':map.svg'))
        self.createMapAction.setStatusTip('Create interactive map')

        self.createReportAction = qtw.QAction('Create &report', self)
        self.createReportAction.setIcon(QIcon(':mail.svg'))
        self.createReportAction.setStatusTip('Create xlsx report')

        self.pythonConsoleAction = qtw.QAction('&Python Console', self)
        self.pythonConsoleAction.setIcon(QIcon(':terminal'))
        self.createReportAction.setStatusTip('Open python console window')

    def _createViewActions(self):
        self.createGraphAction = qtw.QAction('&Create graph')
        self.createGraphAction.setIcon(QIcon(':trending-up.svg'))
        self.createGraphAction.setStatusTip('Create graph in new window')

        self.cascadeAction = qtw.QAction('Casca&de Windows')
        self.cascadeAction.setIcon(QIcon(':bar-chart.svg'))
        self.cascadeAction.setStatusTip('Cascade View Graph Windows')

        self.horizontalAction = qtw.QAction('&Horizontal Windows')
        self.horizontalAction.setIcon(QIcon(':more-vertical.svg'))
        self.horizontalAction.setStatusTip('Horizontal View Graph Windows')

        self.verticalAction = qtw.QAction('&Vertical Windows')
        self.verticalAction.setIcon(QIcon(':more-horizontal.svg'))
        self.verticalAction.setStatusTip('Vertical View Graph Windows')

        self.trackGraphAction = qtw.QAction('&Track graph')
        self.trackGraphAction.setIcon(QIcon(':move.svg'))
        self.trackGraphAction.setStatusTip('Track Grapth in all Windows')
        self.trackGraphAction.setCheckable(True)

        self.closeAllAction = qtw.QAction('Close &all Windows')
        self.closeAllAction.setIcon(QIcon(':x-circle.svg'))
        self.closeAllAction.setStatusTip('Close all opened Windows')

    def _connectActions(self):
        self._connectFileActions()
        self._connectServiceActions()
        self._connectViewActions()
        self.aboutAction.triggered.connect(self.about)
        
    def _connectFileActions(self):
        self.newAction.triggered.connect(self.newFile)
        self.openTxtAction.triggered.connect(partial(self.openFile, 'txt'))
        self.openPddAction.triggered.connect(self.openFilePdd)
        self.openParquetAction.triggered.connect(partial(self.openFile, 'snappy'))
        self.openCsvAction.triggered.connect(partial(self.openFile, 'csv'))
        self.saveParquetAction.triggered.connect(partial(self.saveData, 'snappy'))
        self.saveCsvAction.triggered.connect(partial(self.saveData, 'csv'))
        self.exitAction.triggered.connect(self.close)
        
    def _connectServiceActions(self):
        self.calculateDataAction.triggered.connect(self.calculateData)
        self.createMapAction.triggered.connect(self.createMap)
        self.createReportAction.triggered.connect(self.createReport)
        self.pythonConsoleAction.triggered.connect(self.pythonConsole)

    def _connectViewActions(self):
        self.createGraphAction.triggered.connect(self.createGraph)
        self.cascadeAction.triggered.connect(self.cascadeWindows)
        self.horizontalAction.triggered.connect(self.horizontalWindows)
        self.verticalAction.triggered.connect(self.verticalWindows)
        self.trackGraphAction.triggered.connect(self.trackGraph)
        self.trackGraphAction.toggled.connect(self.trackGraph)
        self.closeAllAction.triggered.connect(self._closeAllWindows)

    def _createCheckBox(self, param):
        if self.controller.get_data() is None:
            self.setNotify('warning', 'Need to select the data')
            return
            
        it = qtw.QTreeWidgetItemIterator(self.tree)
        while it.value():
            item = it.value()
            if item.text(0) == param:
                delete(item)
            it += 1

        parent = qtw.QTreeWidgetItem(self.tree)
        parent.setText(0, param)
        parent.setExpanded(True)
        for head in list(self.controller.get_data().columns.values):
            item = qtw.QTreeWidgetItem(parent)
            item.setText(0, head)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Unchecked)
        self.tree.show()
        self.splitter.setSizes([100, 500])

    def center(self, obj=None):
        if obj is None:
            obj = self
        qr = obj.frameGeometry()
        cp = self.screen().geometry().center()
        qr.moveCenter(cp)
        obj.move(qr.topLeft())

    def newFile(self):
        pass
        

    def openFile(self, param, filepath = None):
        #TODO передалть на ласт файл на filepath открыть последний открытый
        if filepath:
            self.filePathTxt = filepath
            check = True
        else:
            self.filePathTxt, check = qtw.QFileDialog.getOpenFileName(None, 
                                    'Open file', '', f'Open File (*.{param})')
        if check:
            try:
                self.controller = ctlr.Control(self.filePathTxt)
                if param == 'txt':
                    self.controller.load_txt()
                if param == 'csv':
                    self.controller.load_csv()
                if param == 'snappy':
                    self.controller.load_parquet()
                self._createCheckBox('Data')
                self._updateOpenedFiles()
                self.setNotify('success', f'{param} file opened')
            except Exception as e:
                self.setNotify('error', e)

    def openFilePdd(self):
        pass

    def saveData(self, param):
        if self.controller is None:
            self.setNotify('warning', 'Need to select the data')
            return
        options = qtw.QFileDialog.Options()
        filePath, _ = qtw.QFileDialog.getSaveFileName(self,
                    "Save File", "", f"{param} Files (*.{param});;All Files(*)",
                    options=options)
        if filePath:
            try:
                if param == 'snappy':
                    self.controller.save_parquet(filePath)
                else:
                    self.controller.save_csv(filePath)
                self.setNotify('success', f'{param} file saved to {filePath}')
            except PermissionError:
                self.setNotify('error', 'File opened in another program')
            except Exception as e:
                self.setNotify('error', e)

    def calculateData(self):
        if self.controller is None:
            self.setNotify('warning', 'Need to select the data')
            return

        #TODO добавить считывание с self.planeComboBox модель самолета
        print(self.planeComboBox.currentText())

        self.controller.set_calculate_data()
        self._createCheckBox('Data')
        self._updateOpenedFiles()
        self.setNotify('success', 'data calculated')

    def createMap(self):
        if self.controller is None:
            self.setNotify('warning', 'Need to select the data')
            return
        if self.mapWindow is None:
            self.mapWindow = map.MapWindow(self.controller, self)
        else:
            self.mapWindow.hide()
        self.center(self.mapWindow)
        self.mapWindow.show()

    def createReport(self):
        if self.controller is None:
            self.setNotify('warning', 'Need to select the data')
            return
        if not self.controller.is_calculated():
            self.setNotify('warning', 'Need to calcuclate the data')
            return
        if self.reportWindow is None:
            self.reportWindow = report.ReportWindow(self.controller, self)
        else:
            self.reportWindow.hide()
        self.center(self.reportWindow)
        self.reportWindow.show()

    def about(self):
        self.setNotify('warning', 'Need to select the data')

    def createGraph(self):
        if self.controller is None or self._getTreeSelected() == []:
            self.setNotify('warning', 'Need to select the data or data for graph')
            return
        decimation = int(self.spinBox.text())
        if decimation == 0:
            dataForGraph = self.controller.get_data()
        else:
            dataForGraph = self.controller.get_data().iloc[::decimation]
        graphWindow = graph.GraphWindow(dataForGraph, self._getTreeSelected())
        self.mdi.addSubWindow(graphWindow)
        graphWindow.show()

    def createGraphForConsole(self, data, *args):
        if data is None:
            return
        graphWindow = graph.GraphWindow(data, args)
        self.mdi.addSubWindow(graphWindow)
        graphWindow.show()
            

    def pythonConsole(self):
        if self.controller is None:
            self.setNotify('warning', 'Need to select the data')
            return
        if self.consoleWindow is None:
            self.consoleWindow = console.ConsoleWindow(self.controller, self)
        else:
            self.consoleWindow.hide()
        self.center(self.consoleWindow)
        self.consoleWindow.show()


    def cascadeWindows(self):
        self.mdi.cascadeSubWindows()

    def horizontalWindows(self):
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

    def closeEvent(self, event):
        qtw.QApplication.closeAllWindows()
        event.accept()

    def _getTreeSelected(self):
        treeSelected = []
        iterator = qtw.QTreeWidgetItemIterator(
            self.tree, qtw.QTreeWidgetItemIterator.Checked)
        while iterator.value():
            item = iterator.value()
            treeSelected.append(item.text(0))
            iterator += 1
        return treeSelected

    def _updateOpenedFiles(self):
        self.openedFilesLabel.setText(
            f'File TXT: <b>{self.filePathTxt}</b>, File PDD: <b>{self.filePathPdd}</b>')

    def setNotify(self, type, txt):
        notify = self.notify.info
        if type == 'warning':
            notify = self.notify.warning
        if type == 'success':
            notify = self.notify.sucess
        if type == 'error':
            notify = self.notify.critical
        notify(type.title(), txt, self, Align=BottomRight, duracion=6)


def main():
    app = qtw.QApplication(sys.argv)
    app.setStyle('Fusion')
    iface = MainWindow()
    iface.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
