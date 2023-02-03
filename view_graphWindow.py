import pyqtgraph as pg
from PyQt5.sip import delete
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets as qtw
from functools import partial

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
        if event.button() == Qt.MouseButton.RightButton:
            self.contextMenu(event)
            event.accept()
        if event.button() == Qt.MouseButton.LeftButton and event.double():
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()
            event.accept()
        if event.button() == Qt.MouseButton.MiddleButton:
            self.close()

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