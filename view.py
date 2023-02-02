import sys
import controller as ctlr
import qrc_resources
import pyqtgraph as pg
from PyQt5 import QtWidgets, sip
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import QCoreApplication, Qt, QEvent, QPoint
import PyQt5.QtCore as QtCore
from functools import partial
from PyQt5.QtWidgets import (
    QPushButton,
    QWidget,
    QMessageBox,
    QDesktopWidget,
    QLabel,
    QMdiSubWindow,
    QMdiArea,
    QApplication,
    QMainWindow,
    QAction,
    QFileDialog,
    QHBoxLayout,
    QSpacerItem,
    QCheckBox,
    QVBoxLayout,
    QSplitter,
    QFrame,
    QScrollArea,
    QTreeWidget,
    QTreeWidgetItem,
    QTreeWidgetItemIterator,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QErrorMessage,
    QMenu,
    QSpinBox,
    QSlider,
    QActionGroup,
    QDoubleSpinBox
)

class GraphWindow(QMdiSubWindow):

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
        self.mainWidget = QWidget()
        self.setWidget(self.mainWidget)
        self.mainLayout = QVBoxLayout()
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
        menu = QMenu()
        self.setBackgrounMenu(menu)
        self.setLineTypeMenu(menu)
        self.setTimeShiftMenu(menu)
        menu.addSeparator()
        
        closeAction = QAction('Clos&e')
        menu.addAction(closeAction)
        closeAction.triggered.connect(self.close)

        menu.exec(event.screenPos().toPoint())

    def setBackgrounMenu(self, parent):
        changeBackground = parent.addMenu('&Background')

        whiteBackgroundAction = QAction('&White ', self)
        whiteBackgroundAction.setCheckable(True)
        if getattr(self.plt, '_background') == 'white':
            whiteBackgroundAction.setChecked(True)
        else:
            whiteBackgroundAction.setChecked(False)
        changeBackground.addAction(whiteBackgroundAction)
        whiteBackgroundAction.triggered.connect(self.whiteBackground)

        blackBackgroundAction = QAction('&Black ', self)
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

            lineGraphAction = QAction('&Line', self)
            lineGraphAction.setCheckable(True)
            if data['curve'].opts['pen'] == data['pen']:
                lineGraphAction.setChecked(True)
            else:
                lineGraphAction.setChecked(False)
            nameLine.addAction(lineGraphAction)
            lineGraphAction.triggered.connect(partial(self.lineGraph, data))

            crossGraphAction = QAction('&Cross', self)
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
            timeShiftAction = QAction(name, self)
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
            sip.delete(self.shiftWidget)
        self.shiftWidget = QFrame()
        self.mainLayout.addWidget(self.shiftWidget)
        self.layoutShift = QHBoxLayout()
        self.shiftWidget.setLayout(self.layoutShift)
        max = self.data.name.max()
        self.slider = QSlider(Qt.Orientation.Horizontal, self)
        self.slider.setRange(-max, max)
        self.slider.setSingleStep(100)
        self.slider.setPageStep(100)
        self.slider.valueChanged.connect(partial(self.updateGraph, curve))
        self.spinBox = QDoubleSpinBox(self)
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


class MapWindow(QWidget):

    def __init__(self, controller):
        super().__init__()
        self.initUI()
        self.controller = controller

    def initUI(self):
        self.setGeometry(0, 0, 250, 150)
        self.center()
        self.setWindowTitle("Create map")
        dlgLayout = QVBoxLayout()
        formLayout = QFormLayout()
        formLayout.setVerticalSpacing(20)
        self.jvdHMin = QLineEdit('100')
        self.decimation = QLineEdit('20')
        formLayout.addRow("JVD_H min:", self.jvdHMin)
        formLayout.addRow("decimation:", self.decimation)
        btnBox = QDialogButtonBox()
        btnBox.setStandardButtons(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        btnBox.accepted.connect(self.createEvent)
        btnBox.rejected.connect(self.close)
        dlgLayout.addLayout(formLayout)
        dlgLayout.addWidget(btnBox)
        # Set the layout on the application's window
        self.setLayout(dlgLayout)

    def createEvent(self):
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getSaveFileName(self,
                                                  "Save File", "", "html Files (*.html);;All Files(*)", options=options)
        if filePath:
            try:
                self.controller.save_map(filePath,
                                         self.jvdHMin.text(),
                                         self.decimation.text())
                self.hide()
            except:
                QMessageBox.critical(self, "Error", "Error with save file")

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.data = None
        self.mapWindow = None
        self.controller = None
        self.filePathTxt = None
        self.filePathPdd = None
        self.initUI()

    def initUI(self):

        self.setGeometry(100, 100, 800, 600)
        self.center()
        self.setWindowTitle('Rp_datanalysis')
        self._createActions()
        self._createMenuBar()
        self._createToolBar()
        self._createStatusBar()
        self._connectActions()

        self.mdi = QMdiArea()
        self.mdi.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.mdi.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.splitter = QSplitter(Qt.Horizontal)
        self.setStyleSheet("QSplitter::handle{background: white;}")

        self.tree = QTreeWidget(self.splitter)
        self.tree.setHeaderHidden(True)
        self.tree.hide()
        self.splitter.addWidget(self.tree)

        self.splitter.addWidget(self.mdi)
        self.setCentralWidget(self.splitter)
        self.showMaximized()

    def _createMenuBar(self):
        menuBar = self.menuBar()

        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(self.newAction)

        openMenu = fileMenu.addMenu('&Open file')
        openMenu.setIcon(QIcon(':file-plus.svg'))
        openMenu.addAction(self.openTxtAction)
        openMenu.addAction(self.openPddAction)

        self.openRecentMenu = fileMenu.addMenu('Open Recent')
        self.openRecentMenu.setIcon(QIcon(':file-minus.svg'))

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
        serviceMenu.addAction(self.createMapAction)
        serviceMenu.addAction(self.createReport)

        settingsMenu = menuBar.addMenu('&Settings')

        helpMenu = menuBar.addMenu('&Help')
        helpMenu.addAction(self.aboutAction)

    def _createToolBar(self):
        fileToolBar = self.addToolBar('File')
        fileToolBar.addAction(self.openTxtAction)
        fileToolBar.addAction(self.openPddAction)
        fileToolBar.addSeparator()
        fileToolBar.addAction(self.exitAction)
        fileToolBar.setMovable(False)
        self.viewToolBar = self.addToolBar('View')
        self.viewToolBar.addAction(self.createGraphAction)
        self.spinBox = QSpinBox()
        self.viewToolBar.addWidget(self.spinBox)
        self.viewToolBar.addSeparator()
        self.viewToolBar.addAction(self.cascadeAction)
        self.viewToolBar.addAction(self.horizontalAction)
        self.viewToolBar.addAction(self.verticalAction)
        self.viewToolBar.addAction(self.trackGraphAction)
        self.viewToolBar.addSeparator()
        self.viewToolBar.addAction(self.closeAllAction)

    def _createStatusBar(self):
        self.statusbar = self.statusBar()
        self.statusbar.showMessage('Hello world!', 3000)
        self.openedFilesLabel = QLabel(
            f'File TXT: {self.filePathTxt}, File PDD: {self.filePathPdd}')
        self.statusbar.addPermanentWidget(self.openedFilesLabel)

    def _createActions(self):
        self.newAction = QAction('&New', self)
        self.newAction.setIcon(QIcon(':file.svg'))
        self.newAction.setStatusTip('Clear')

        self.openTxtAction = QAction('Open *.&txt...', self)
        self.openTxtAction.setIcon(QIcon(':file-text.svg'))
        self.openTxtAction.setStatusTip('Open file')
        self.openTxtAction.setShortcut('Ctrl+O')

        self.openPddAction = QAction('Open *.&pdd...', self)
        self.openPddAction.setIcon(QIcon(':file.svg'))
        self.openPddAction.setStatusTip('Open file')
        self.openPddAction.setShortcut('Ctrl+P')

        self.exitAction = QAction('&Exit', self)
        self.exitAction.setIcon(QIcon(':log-out.svg'))
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.setShortcut('Ctrl+Q')

        self.createGraphAction = QAction('&Create graph')
        self.createGraphAction.setIcon(QIcon(':trending-up.svg'))
        self.createGraphAction.setStatusTip('Create graph in new window')

        self.cascadeAction = QAction('Casca&de Windows')
        self.cascadeAction.setIcon(QIcon(':bar-chart.svg'))
        self.cascadeAction.setStatusTip('Cascade View Graph Windows')

        self.horizontalAction = QAction('&Horizontal Windows')
        self.horizontalAction.setIcon(QIcon(':more-vertical.svg'))
        self.horizontalAction.setStatusTip('Horizontal View Graph Windows')

        self.verticalAction = QAction('&Vertical Windows')
        self.verticalAction.setIcon(QIcon(':more-horizontal.svg'))
        self.verticalAction.setStatusTip('Vertical View Graph Windows')

        self.trackGraphAction = QAction('&Track graph')
        self.trackGraphAction.setIcon(QIcon(':move.svg'))
        self.trackGraphAction.setStatusTip('Track Grapth in all Windows')
        self.trackGraphAction.setCheckable(True)

        self.closeAllAction = QAction('Close &all Windows')
        self.closeAllAction.setIcon(QIcon(':x-circle.svg'))
        self.closeAllAction.setStatusTip('Close all opened Windows')

        self.createMapAction = QAction('&Create map', self)
        self.createMapAction.setIcon(QIcon(':map.svg'))
        self.createMapAction.setStatusTip('Create interactive map')

        self.createReport = QAction('&Create report', self)
        self.createReport.setIcon(QIcon(':mail.svg'))
        self.createReport.setStatusTip('Create cvv report')

        self.aboutAction = QAction('&About', self)
        self.aboutAction.setIcon(QIcon(':help-circle.svg'))
        self.aboutAction.setStatusTip('About programm')

    def _connectActions(self):
        self.newAction.triggered.connect(self.newFile)
        self.openTxtAction.triggered.connect(self.openFileTxt)
        self.openPddAction.triggered.connect(self.openFilePdd)
        self.openRecentMenu.aboutToShow.connect(self.populateOpenRecent)
        self.createMapAction.triggered.connect(self.createMap)
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
        if self.data is None:
            error_dialog = QtWidgets.QErrorMessage()
            error_dialog.showMessage('Oh no!')
            return

        it = QTreeWidgetItemIterator(self.tree)
        while it.value():
            item = it.value()
            if item.text(0) == param:
                sip.delete(item)
            it += 1

        parent = QTreeWidgetItem(self.tree)
        parent.setText(0, param)
        parent.setExpanded(True)
        for head in list(self.data.columns.values):
            item = QTreeWidgetItem(parent)
            item.setText(0, head)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Unchecked)
        self.tree.show()
        self.splitter.setSizes([100, 500])

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def newFile(self):
        self.centralWidget.setText('<b>File > New</b> clicked')

    def openFileTxt(self):
        self.filePathTxt, check = QFileDialog.getOpenFileName(
            None,
            'QFileDialog.getOpenFileName()',
            '', 'Text Files (*.txt)')
        if check:
            self.controller = ctlr.Control(self.filePathTxt)
            self.data = self.controller.get_data_calculate()
            self._createCheckBox('TXT')
            self._updateOpenedFiles()

    def openFilePdd(self):
        pass

    def createMap(self):
        if self.controller is None:
            QMessageBox.information(self, "Error", "Need to select the data")
            return
        if self.mapWindow is None:
            self.mapWindow = MapWindow(self.controller)
            self.mapWindow.show()
        else:
            self.mapWindow.hide()
            self.mapWindow.show()

    def about(self):
        self.centralWidget.setText('<b>Help > About</b> clicked')

    def openRecentFile(self, filename):
        # Logic for opening a recent file goes here...
        # self.centralWidget.setText(f'<b>{filename}</b> opened')
        pass

    def populateOpenRecent(self):
        pass
        # # Step 1. Remove the old options from the menu
        # self.openRecentMenu.clear()
        # # Step 2. Dynamically create the actions
        # actions = []
        # filenames = [f'File-{n}' for n in range(5)]
        # for filename in filenames:
        #     action = QAction(filename, self)
        #     action.triggered.connect(partial(self.openRecentFile, filename))
        #     actions.append(action)
        # # Step 3. Add the actions to the menu
        # self.openRecentMenu.addActions(actions)

    def createGraph(self):
        if self.data is None or self._getTreeSelected() == []:
            return
        decimation = int(self.spinBox.text())
        if decimation == 0:
            dataForGraph = self.data
        else:
            dataForGraph = self.data.iloc[::decimation]
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
        QApplication.closeAllWindows()
        event.accept()

    def _getTreeSelected(self):
        treeSelected = []
        iterator = QTreeWidgetItemIterator(
            self.tree, QTreeWidgetItemIterator.Checked)
        while iterator.value():
            item = iterator.value()
            treeSelected.append(item.text(0))
            iterator += 1
        return treeSelected

    def _updateOpenedFiles(self):
        self.openedFilesLabel.setText(
            f'File TXT: <b>{self.filePathTxt}</b>, File PDD: <b>{self.filePathPdd}</b>')


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    iface = MainWindow()
    iface.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
