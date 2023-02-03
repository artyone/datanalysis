import sys
import controller as ctlr
import qrc_resources
import pyqtgraph as pg
from os import startfile
from PyQt5.sip import delete
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from PyQt5 import QtCore
from PyQt5 import QtWidgets as qtw
from qtwidgets import AnimatedToggle
from functools import partial
from notificator import notificator
from notificator.alingments import BottomRight

class GraphWindow(qtw.QMdiSubWindow):

    def __init__(self, data, treeSelected) -> None:
        super().__init__()
        self.data = data
        self.columns = treeSelected
        self.colors = ['red', 'blue', 'green',
                       'orange', 'black', 'purple', 'cyan']
        self.curves = dict()
        self.initUI()

    def initUI(self):
        self.shiftWidget = None
        self.mainWidget = qtw.QWidget()
        self.setWidget(self.mainWidget)
        self.mainLayout = qtw.QVBoxLayout()
        self.mainWidget.setLayout(self.mainLayout)
        self.setWindowTitle('/'.join(self.columns))
        self.setGeometry(0, 0, 500, 300)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.createGraph()

    def createGraph(self):
        if self.data is None:
            return
        ox = self.data.name
        self.plt = pg.PlotWidget()
        self.plt.setBackground('black')
        self.plt.showGrid(x=True, y=True)
        self.plt.addLegend(pen='gray', offset=(0, 0))

        for column in self.columns:
            pen = pg.mkPen(color=self.colors[0])
            curve = pg.PlotDataItem(ox,
                                    self.data[column],
                                    name=column,
                                    pen=pen)
            self.curves[column] = {'curve': curve, 'pen': pen}
            self.plt.addItem(curve)
            self.colors.append(self.colors.pop(0))
        self.plt.setMenuEnabled(False)
        self.mainLayout.addWidget(self.plt)
        self.plt.proxy = pg.SignalProxy(self.plt.scene().sigMouseMoved,
                                        rateLimit=30,
                                        slot=self.mouseMoved)
        self.plt.scene().sigMouseClicked.connect(self.mouseClickEvent)
        self.plt.setClipToView(True)

    def mouseMoved(self, e):
        pos = e[0]
        if self.plt.sceneBoundingRect().contains(pos):
            mousePoint = self.plt.getPlotItem().vb.mapSceneToView(pos)
            self.setWindowTitle(
                f'x: {round(float(mousePoint.x()), 3)}, y: {round(float(mousePoint.y()), 3)}')
            self.setToolTip(
                f'x: <b>{round(float(mousePoint.x()), 1)}</b>,<br> y: <b>{round(float(mousePoint.y()), 1)}</b>')

    def mouseClickEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.RightButton:
            self.contextMenu(event)
            event.accept()
        if event.button() == QtCore.Qt.MouseButton.LeftButton and event.double():
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()
            event.accept()

    def contextMenu(self, event):
        menu = qtw.QMenu()
        self.setBackgrounMenu(menu)
        self.setLineTypeMenu(menu)
        self.setTimeShiftMenu(menu)
        menu.addSeparator()
        
        closeAction = qtw.QAction('Clos&e')
        menu.addAction(closeAction)
        closeAction.triggered.connect(self.close)

        menu.exec(event.screenPos().toPoint())

    def setBackgrounMenu(self, parent):
        changeBackground = parent.addMenu('&Background')

        whiteBackgroundAction = qtw.QAction('&White ', self)
        whiteBackgroundAction.setCheckable(True)
        if getattr(self.plt, '_background') == 'white':
            whiteBackgroundAction.setChecked(True)
        else:
            whiteBackgroundAction.setChecked(False)
        changeBackground.addAction(whiteBackgroundAction)
        whiteBackgroundAction.triggered.connect(self.whiteBackground)

        blackBackgroundAction = qtw.QAction('&Black ', self)
        blackBackgroundAction.setCheckable(True)
        if getattr(self.plt, '_background') == 'black':
            blackBackgroundAction.setChecked(True)
        else:
            blackBackgroundAction.setChecked(False)
        changeBackground.addAction(blackBackgroundAction)
        blackBackgroundAction.triggered.connect(self.blackBackground)

    def setLineTypeMenu(self, parent):
        lineType = parent.addMenu('&Line Type')
        for name, data in self.curves.items():
            nameLine = lineType.addMenu(name)

            lineGraphAction = qtw.QAction('&Line', self)
            lineGraphAction.setCheckable(True)
            if data['curve'].opts['pen'] == data['pen']:
                lineGraphAction.setChecked(True)
            else:
                lineGraphAction.setChecked(False)
            nameLine.addAction(lineGraphAction)
            lineGraphAction.triggered.connect(partial(self.lineGraph, data))

            crossGraphAction = qtw.QAction('&Cross', self)
            crossGraphAction.setCheckable(True)
            if data['curve'].opts['symbol'] is None:
                crossGraphAction.setChecked(False)
            else:
                crossGraphAction.setChecked(True)
            nameLine.addAction(crossGraphAction)
            crossGraphAction.triggered.connect(partial(self.crossGraph, data))

    def setTimeShiftMenu(self, parent):
        timeShiftMenu = parent.addMenu('&Time Shift')
        for name, data in self.curves.items():
            timeShiftAction = qtw.QAction(name, self)
            timeShiftMenu.addAction(timeShiftAction)
            timeShiftAction.triggered.connect(
                partial(self.timeShift, data['curve']))

    def whiteBackground(self):
        self.plt.setBackground('white')

    def blackBackground(self):
        self.plt.setBackground('black')

    def lineGraph(self, data):
        if data['curve'].opts['pen'] == data['pen']:
            data['curve'].setPen(None)
        else:
            data['curve'].setPen(data['pen'])

    def crossGraph(self, data):
        if data['curve'].opts['symbol'] is None:
            data['curve'].setSymbol('+')
            data['curve'].setSymbolPen(data['pen'])
        else:
            data['curve'].setSymbol(None)

    def timeShift(self, curve):
        if self.shiftWidget is not None:
            delete(self.shiftWidget)
        self.shiftWidget = qtw.QFrame()
        self.mainLayout.addWidget(self.shiftWidget)
        self.layoutShift = qtw.QHBoxLayout()
        self.shiftWidget.setLayout(self.layoutShift)
        max = self.data.name.max()
        self.slider = qtw.QSlider(Qt.Orientation.Horizontal, self)
        self.slider.setRange(-max, max)
        self.slider.setSingleStep(100)
        self.slider.setPageStep(100)
        self.slider.valueChanged.connect(partial(self.updateGraph, curve))
        self.spinBox = qtw.QDoubleSpinBox(self)
        self.spinBox.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.spinBox.setMinimumWidth(80)
        self.spinBox.setRange(-max, max)
        self.spinBox.setSingleStep(.1)
        self.spinBox.valueChanged.connect(partial(self.updateGraph, curve))
        self.layoutShift.addWidget(self.slider)
        self.layoutShift.addWidget(self.spinBox)

    def updateGraph(self, curve, value):
        self.slider.setValue(int(value))
        self.spinBox.setValue(value)
        x = [i + value for i in self.data['name']]
        y = self.data[curve.name()]
        curve.setData(x, y)


class MapWindow(qtw.QWidget):

    def __init__(self, controller, parent=None):
        super().__init__()
        self.parent = parent
        self.controller = controller
        self.initUI()
        
    def initUI(self):
        self.setGeometry(0, 0, 250, 150)
        self.setWindowTitle("Create map")
        dlgLayout = qtw.QVBoxLayout()
        formLayout = qtw.QFormLayout()
        formLayout.setVerticalSpacing(20)
        self.jvdHMin = qtw.QLineEdit('100')
        self.decimation = qtw.QLineEdit('20')
        formLayout.addRow("JVD_H min:", self.jvdHMin)
        formLayout.addRow("decimation:", self.decimation)
        self.btnBox = qtw.QDialogButtonBox()

        self.btnBox.setStandardButtons(qtw.QDialogButtonBox.Open |
                                       qtw.QDialogButtonBox.Save | 
                                       qtw.QDialogButtonBox.Cancel)
        self.btnBox.rejected.connect(self.close)

        self.openButton = self.btnBox.button(qtw.QDialogButtonBox.Open)
        self.openButton.clicked.connect(self.openFile)
        self.openButton.hide()

        saveButton = self.btnBox.button(qtw.QDialogButtonBox.Save)
        saveButton.clicked.connect(self.getMapEvent)
        dlgLayout.addLayout(formLayout)
        dlgLayout.addWidget(self.btnBox)
        self.setLayout(dlgLayout)

    def getMapEvent(self):
        options = qtw.QFileDialog.Options()
        self.filePath, _ = qtw.QFileDialog.getSaveFileName(self,
                    "Save File", "", "html Files (*.html);;All Files(*)", options=options)
        if self.filePath:
            try:
                self.controller.save_map(self.filePath,
                                         self.jvdHMin.text(),
                                         self.decimation.text())
                self.openButton.show()
                self.parent.setNotify('success', f'html file saved to {self.filePath}')
            except PermissionError:
                self.parent.setNotify('error', 'File opened in another program')
            except Exception as e:
                self.parent.setNotify('error', e)

    def openFile(self):
        startfile(self.filePath)
        self.close()


class ReportWindow(qtw.QWidget):

    def __init__(self, controller, parent=None) -> None:
        super().__init__()
        self.parent = parent
        self.controller = controller
        self.intervalsTxt = None
        self.initUI()

    def initUI(self):
        self.setGeometry(0, 0, 500, 500)
        self.setWindowTitle("Create report")
        self.setLayout(qtw.QVBoxLayout())

        formLayout = qtw.QFormLayout()
        horizontalLayout = qtw.QHBoxLayout()

        self.intervalsToggle = AnimatedToggle()
        self.intervalsToggle.setChecked(True)
        self.intervalsToggle.stateChanged.connect(self.addFormTxt)
        self.intervalsTxt = qtw.QPlainTextEdit()

        self.btnBox = qtw.QDialogButtonBox()

        self.btnBox.setStandardButtons(qtw.QDialogButtonBox.Open |
                                       qtw.QDialogButtonBox.Save | 
                                       qtw.QDialogButtonBox.Cancel)
        self.btnBox.rejected.connect(self.close)

        self.openButton = self.btnBox.button(qtw.QDialogButtonBox.Open)
        self.openButton.clicked.connect(self.openFile)
        self.openButton.hide()

        saveButton = self.btnBox.button(qtw.QDialogButtonBox.Save)
        saveButton.clicked.connect(self.getReportEvent)
        

        horizontalLayout.addWidget(qtw.QLabel('<b>Intervals:</b>'), 2)
        horizontalLayout.addWidget(qtw.QLabel('auto'), 1,
                                   alignment=Qt.AlignRight)
        horizontalLayout.addWidget(self.intervalsToggle, 1)
        horizontalLayout.addWidget(qtw.QLabel('manual'), 2)

        formLayout.addRow(horizontalLayout)
        formLayout.addRow(self.intervalsTxt)

        self.layout().addLayout(formLayout, 1)
        self.layout().addWidget(self.btnBox, 1)

    def addFormTxt(self):
        if self.intervalsToggle.isChecked():
            self.intervalsTxt.show()
        else: 
            self.intervalsTxt.hide()

    def getReportEvent(self):
        text = self.intervalsTxt.toPlainText()
        if self.intervalsToggle.isChecked() and not text:
            self.parent.setNotify('warning', "Need input intervals")
            return
        if not self.intervalsToggle.isChecked():
            text = ''
        options = qtw.QFileDialog.Options()
        self.filePath, _ = qtw.QFileDialog.getSaveFileName(self,
                    "Save File", "", "xlsx Files (*.xlsx);;All Files(*)",
                    options=options)
        if self.filePath:
            try:
                self.controller.save_report(self.filePath, text)
                self.openButton.show()
                self.parent.setNotify('success', f'xlsx file saved to {self.filePath}')
            except PermissionError:
                self.parent.setNotify('error', 'File opened in another program')
            except Exception as e:
                self.parent.setNotify('error', e)
    
    def openFile(self):
        startfile(self.filePath)
        self.close()




class MainWindow(qtw.QMainWindow):

    def __init__(self):
        super().__init__()
        self.mapWindow = None
        self.reportWindow = None
        self.controller = None
        self.filePathTxt = None
        self.filePathPdd = None
        self.initUI()

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
        menuBar = self.menuBar()

        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(self.newAction)

        openSourceMenu = fileMenu.addMenu('Open &source')
        openSourceMenu.setIcon(QIcon(':file-plus.svg'))
        openSourceMenu.addAction(self.openTxtAction)
        openSourceMenu.addAction(self.openPddAction)

        openDataMenu = fileMenu.addMenu('&Open data')
        openDataMenu.setIcon(QIcon(':database.svg'))

        saveMenu = fileMenu.addMenu('&Save as')
        saveMenu.setIcon(QIcon(':save'))
        saveMenu.addAction(self.saveParquetAction)
        saveMenu.addAction(self.saveCsvAction)

        fileMenu.addSeparator()
        fileMenu.addAction(self.exitAction)

        viewMenu = menuBar.addMenu('&View')
        viewMenu.addAction(self.createGraphAction)
        viewMenu.addAction(self.cascadeAction)
        viewMenu.addAction(self.horizontalAction)
        viewMenu.addAction(self.verticalAction)
        viewMenu.addAction(self.trackGraphAction)
        viewMenu.addSeparator()
        viewMenu.addAction(self.closeAllAction)

        serviceMenu = menuBar.addMenu('&Service')
        serviceMenu.addAction(self.calculateDataAction)
        serviceMenu.addAction(self.createMapAction)
        serviceMenu.addAction(self.createReportAction)

        settingsMenu = menuBar.addMenu('&Settings')

        helpMenu = menuBar.addMenu('&Help')
        helpMenu.addAction(self.aboutAction)

    def _createToolBar(self):
        fileToolBar = self.addToolBar('File')
        fileToolBar.addAction(self.openTxtAction)
        fileToolBar.addAction(self.openPddAction)
        fileToolBar.addAction(self.saveParquetAction)
        fileToolBar.addSeparator()
        fileToolBar.addAction(self.exitAction)
        fileToolBar.setMovable(False)
        serviceToolBar = self.addToolBar('Service')
        serviceToolBar.addAction(self.calculateDataAction)
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
        self.newAction = qtw.QAction('&New', self)
        self.newAction.setIcon(QIcon(':file.svg'))
        self.newAction.setStatusTip('Clear')

        self.openTxtAction = qtw.QAction('Open *.&txt...', self)
        self.openTxtAction.setIcon(QIcon(':file-text.svg'))
        self.openTxtAction.setStatusTip('Open file')
        self.openTxtAction.setShortcut('Ctrl+O')

        self.openPddAction = qtw.QAction('Open *.&pdd...', self)
        self.openPddAction.setIcon(QIcon(':file.svg'))
        self.openPddAction.setStatusTip('Open file')
        self.openPddAction.setShortcut('Ctrl+P')

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

        self.calculateDataAction = qtw.QAction('&Calculate data')
        self.calculateDataAction.setIcon(QIcon(':percent.svg'))
        self.calculateDataAction.setStatusTip('Calculate data from source')

        self.createMapAction = qtw.QAction('Create &map', self)
        self.createMapAction.setIcon(QIcon(':map.svg'))
        self.createMapAction.setStatusTip('Create interactive map')

        self.createReportAction = qtw.QAction('Create &report', self)
        self.createReportAction.setIcon(QIcon(':mail.svg'))
        self.createReportAction.setStatusTip('Create xlsx report')

        self.aboutAction = qtw.QAction('&About', self)
        self.aboutAction.setIcon(QIcon(':help-circle.svg'))
        self.aboutAction.setStatusTip('About programm')

    def _connectActions(self):
        self.newAction.triggered.connect(self.newFile)
        self.openTxtAction.triggered.connect(self.openFileTxt)
        self.openPddAction.triggered.connect(self.openFilePdd)
        self.saveParquetAction.triggered.connect(partial(self.saveData, 'snappy'))
        self.saveCsvAction.triggered.connect(partial(self.saveData, 'csv'))
        self.calculateDataAction.triggered.connect(self.calculateData)
        self.createMapAction.triggered.connect(self.createMap)
        self.createReportAction.triggered.connect(self.createReport)
        self.aboutAction.triggered.connect(self.about)
        self.exitAction.triggered.connect(self.close)
        self.createGraphAction.triggered.connect(self.createGraph)
        self.cascadeAction.triggered.connect(self.cascadeWindows)
        self.horizontalAction.triggered.connect(self.horizontalWindows)
        self.verticalAction.triggered.connect(self.verticalWindows)
        self.trackGraphAction.triggered.connect(self.trackGraph)
        self.trackGraphAction.toggled.connect(self.trackGraph)
        self.closeAllAction.triggered.connect(self._closeAllWindows)

    def _createCheckBox(self, param):
        if self.controller.get_data() is None:
            error_dialog = qtw.QErrorMessage()
            error_dialog.showMessage('Oh no!')
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


    def openFileTxt(self):
        self.filePathTxt, check = qtw.QFileDialog.getOpenFileName(
            None,
            'qtw.QFileDialog.getOpenFileName()',
            '', 'Text Files (*.txt)')
        if check:
            self.controller = ctlr.Control(self.filePathTxt)
            self._createCheckBox('TXT')
            self._updateOpenedFiles()
            self.setNotify('success', 'txt file opened')

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
        self.controller.set_calculate_data()
        self._createCheckBox('TXT')
        self._updateOpenedFiles()
        self.setNotify('success', 'data calculated')

    def createMap(self):
        if self.controller is None:
            self.setNotify('warning', 'Need to select the data')
            return
        if self.mapWindow is None:
            self.mapWindow = MapWindow(self.controller, self)
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
            self.reportWindow = ReportWindow(self.controller, self)
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
        graphWindow = GraphWindow(dataForGraph, self._getTreeSelected())
        self.mdi.addSubWindow(graphWindow)
        graphWindow.show()

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
