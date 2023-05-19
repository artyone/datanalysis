from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QMdiSubWindow,
    QAction, QMenu, QHBoxLayout,
    QFrame, QSlider,
    QDoubleSpinBox, QPushButton
)
import app.resource.qrc_resources
import pyqtgraph as pg
from PyQt5.sip import delete
from PyQt5.QtCore import Qt
from functools import partial


class GraphWindow(QMdiSubWindow):
    '''
    Класс окон для построения графиков.
    parent - родительское окно
    data - данные для построения графика
    columns - колонки, необходимые для построения,
    график всегда строится Ох - time(время) Oy - выбранные колонки
    colors - цвета для графиков
    curves - словарь названия и объектов графиков.
    '''

    def __init__(self, data, treeSelected, decimation, parent) -> None:
        super().__init__()
        self.parent = parent
        self.data = data
        self.columns = treeSelected
        self.decimation = decimation
        self.colors = [
            'red', 'blue', 'green',
            'orange', 'black', 'purple', 'cyan'
        ]
        self.curves = dict()
        self.initUI()

    def initUI(self):
        '''
        Метод построения интерфейса окна.
        '''
        self.shiftWidget = None
        self.mainWidget = QWidget()
        self.setWidget(self.mainWidget)
        self.mainLayout = QVBoxLayout()
        self.mainWidget.setLayout(self.mainLayout)
        self.setWindowTitle('/'.join([i[2] for i in self.columns]))
        self.setStyleSheet("color: gray;")
        self.setGeometry(0, 0, 500, 300)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.createGraph()

    def createGraph(self):
        '''
        Метод построения непосредственно самого графика
        с использованием библиотеки pyqtgraph.
        Цвета берутся по кругу из массива цветов.
        Меню библиотеки выключено. 
        При перемещении курсора выводится информация о текущем его положении.
        При правом клике мыши вызывается кастомное контекстное меню.
        '''
        if self.data == {}:
            raise KeyError
        if self.columns == []:
            raise ValueError

        self.plt = pg.PlotWidget()
        self.plt.setBackground(
            self.parent.settings.value('graphs')['background']
        )
        self.plt.showGrid(x=True, y=True)
        self.plt.addLegend(pen='gray', offset=(0, 0))

        for category, adr, item in self.columns:
            dataForGraph = self.data[category][adr].dropna(subset=['time', item]).reset_index().iloc[::self.decimation]
            pen = pg.mkPen(color=self.colors[0])
            curve = pg.PlotDataItem(
                dataForGraph.time.to_list(),
                dataForGraph[item].to_list(),
                name=item,
                pen=pen
            )
            self.curves[f'{category}/{adr}/{item}'] = {
                'curve': curve, 'pen': pen, 'adr': adr, 'category': category
            }
            self.plt.addItem(curve)
            self.colors.append(self.colors.pop(0))
        self.plt.setMenuEnabled(False)
        self.mainLayout.addWidget(self.plt)
        self.plt.proxy = pg.SignalProxy(
            self.plt.scene().sigMouseMoved,
            rateLimit=30,
            slot=self.mouseMoved
        )
        self.plt.scene().sigMouseClicked.connect(self.mouseClickEvent)
        self.plt.setClipToView(True)

    def mouseMoved(self, e):
        '''
        Метод реализации высплывающей подсказки по координатам
        при перемещении мыши.
        '''
        pos = e[0]
        if self.plt.sceneBoundingRect().contains(pos):
            mousePoint = self.plt.getPlotItem().vb.mapSceneToView(pos)
            x = float(mousePoint.x())
            y = float(mousePoint.y())
            self.setWindowTitle(
                f'x: {round(x, 3)}, y: {round(y, 3)}'
            )
            self.setToolTip(
                f'x: <b>{round(x, 1)}</b>,<br> y: <b>{round(y, 1)}</b>'
            )

    def mouseClickEvent(self, event):
        '''
        Метод обработки событий нажатия мышки.
        '''
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
        '''
        Метод создания кастомного контекстного меню.
        '''
        menu = QMenu()
        self.setBackgrounMenu(menu)
        self.setLineTypeMenu(menu)
        self.setTimeShiftMenu(menu)
        menu.addSeparator()

        closeAction = QAction('&Закрыть')
        menu.addAction(closeAction)
        closeAction.triggered.connect(self.close)

        menu.exec(event.screenPos().toPoint())

    def setBackgrounMenu(self, parent):
        changeBackground = parent.addMenu('&Фон')

        whiteBackgroundAction = QAction('&Белый ', self)
        whiteBackgroundAction.setCheckable(True)
        if getattr(self.plt, '_background') == 'white':
            whiteBackgroundAction.setChecked(True)
        else:
            whiteBackgroundAction.setChecked(False)
        changeBackground.addAction(whiteBackgroundAction)
        whiteBackgroundAction.triggered.connect(self.whiteBackground)

        blackBackgroundAction = QAction('&Черный ', self)
        blackBackgroundAction.setCheckable(True)
        if getattr(self.plt, '_background') == 'black':
            blackBackgroundAction.setChecked(True)
        else:
            blackBackgroundAction.setChecked(False)
        changeBackground.addAction(blackBackgroundAction)
        blackBackgroundAction.triggered.connect(self.blackBackground)

    def setLineTypeMenu(self, parent):
        lineType = parent.addMenu('&Тип линии')
        for name, data in self.curves.items():
            nameLine = lineType.addMenu(name)

            lineGraphAction = QAction('&Линия', self)
            lineGraphAction.setCheckable(True)
            if data['curve'].opts['pen'] == data['pen']:
                lineGraphAction.setChecked(True)
            else:
                lineGraphAction.setChecked(False)
            nameLine.addAction(lineGraphAction)
            lineGraphAction.triggered.connect(partial(self.lineGraph, data))

            crossGraphAction = QAction('&Точки', self)
            crossGraphAction.setCheckable(True)
            if data['curve'].opts['symbol'] is None:
                crossGraphAction.setChecked(False)
            else:
                crossGraphAction.setChecked(True)
            nameLine.addAction(crossGraphAction)
            crossGraphAction.triggered.connect(partial(self.crossGraph, data))

    def setTimeShiftMenu(self, parent):
        timeShiftMenu = parent.addMenu('&Сдвиг графика')
        for name, data in self.curves.items():
            timeShiftAction = QAction(name, self)
            timeShiftMenu.addAction(timeShiftAction)
            timeShiftAction.triggered.connect(
                partial(self.timeShift, data)
            )

    def whiteBackground(self):
        '''
        Метод изменения цвета фона и запись его в настройки.
        '''
        self.plt.setBackground('white')
        settings = self.parent.settings.value('graphs')
        settings['background'] = 'white'
        self.parent.settings.setValue('graphs', settings)

    def blackBackground(self):
        '''
        Метод изменения цвета фона и запись его в настройки.
        '''
        self.plt.setBackground('black')
        settings = self.parent.settings.value('graphs')
        settings['background'] = 'black'
        self.parent.settings.setValue('graphs', settings)

    def lineGraph(self, data):
        '''
        Метод изменения линии графика.
        '''
        if data['curve'].opts['pen'] == data['pen']:
            data['curve'].setPen(None)
        else:
            data['curve'].setPen(data['pen'])

    def crossGraph(self, data):
        '''
        Метод изменения линии графика.
        '''
        if data['curve'].opts['symbol'] is None:
            data['curve'].setSymbol('+')
            data['curve'].setSymbolPen(data['pen'])
        else:
            data['curve'].setSymbol(None)

    def timeShift(self, curveData):
        '''
        Метод смещения графика по оси Ox.
        '''
        if self.shiftWidget is not None:
            delete(self.shiftWidget)
        self.shiftWidget = QFrame()
        self.mainLayout.addWidget(self.shiftWidget)
        self.layoutShift = QHBoxLayout()
        self.shiftWidget.setLayout(self.layoutShift)
        max = int(curveData['curve'].getData()[0].max()) * 2
        self.slider = QSlider(Qt.Orientation.Horizontal, self)
        self.slider.setRange(-max, max)
        self.slider.setSingleStep(50)
        self.slider.setPageStep(50)
        self.slider.valueChanged.connect(partial(self.updateGraph, curveData))
        self.spinBox = QDoubleSpinBox(self)
        self.spinBox.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.spinBox.setMinimumWidth(80)
        self.spinBox.setRange(-max, max)
        self.spinBox.setSingleStep(.1)
        self.spinBox.valueChanged.connect(
            partial(self.updateGraph, curveData))
        self.applyShiftButton = QPushButton('Применить смещение')
        self.applyShiftButton.clicked.connect(partial(self.applyShift, curveData))
        self.layoutShift.addWidget(self.applyShiftButton)
        self.layoutShift.addWidget(self.slider)
        self.layoutShift.addWidget(self.spinBox)

    def updateGraph(self, curveData, value):
        '''
        Метод перестроения графика после смещения данных.
        '''
        self.slider.setValue(int(value))
        self.spinBox.setValue(value)
        curve = curveData['curve']
        category = curveData['category']
        adr = curveData['adr']
        item = curve.name()
        dataForGraph = self.data[category][adr].iloc[::self.decimation]
        x = [i + value for i in dataForGraph.time]
        y = dataForGraph[item]
        curve.setData(x, y)

    def applyShift(self, curveData):
        value = self.spinBox.value(), 
        data = self.data[curveData['category']][curveData['adr']]
        print(data['time'])

        data['time'] = data['time'] + value
        print(data['time'])
        self.parent.setNotify('успех', 'Смещение задано. Не забудьте сохранить изменения')
