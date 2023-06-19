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
        self.data: dict = data
        self.columns: list = treeSelected
        self.title: str = '/'.join([i[2] for i in self.columns])
        self.decimation: int = decimation
        self.colors: list = [
            'red', 'blue', 'green', 'orange',
            'gray', 'purple', 'cyan', 'yellow',
            'pink'
        ]

        self.curves: dict = dict()
        self.theme: str = self.parent.settings.value('graphs')['background']
        self.initUI()

    def initUI(self) -> None:
        '''
        Метод построения интерфейса окна.
        '''
        self.shiftWidget = None
        self.mainWidget: QWidget = QWidget()
        self.setWidget(self.mainWidget)
        self.mainLayout: QVBoxLayout = QVBoxLayout()
        self.mainWidget.setLayout(self.mainLayout)
        self.setWindowTitle(self.title)
        self.setGeometry(0, 0, 500, 300)
        self.setAttribute(Qt.WA_DeleteOnClose, True)  # type: ignore
        self.createGraph()

    def createGraph(self) -> None:
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
        self.plt.setBackground(self.theme)
        self.plt.showGrid(x=True, y=True)

        legendColor = 'white' if self.theme == 'black' else 'black'
        self.legend: pg.LegendItem = self.plt.addLegend(
            pen=legendColor,
            labelTextColor=legendColor,
            offset=(0, 0)
        )

        for category, adr, item in self.columns:
            dataForGraph = self.data[category][adr].dropna(
                subset=['time', item]
            )
            dataForGraph = dataForGraph.reset_index().iloc[::self.decimation]
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

    def mouseMoved(self, e) -> None:
        '''
        Метод реализации высплывающей подсказки по координатам
        при перемещении мыши.
        '''
        pos = e[0]
        if self.plt.sceneBoundingRect().contains(pos):
            mousePoint = self.plt.getPlotItem().vb.mapSceneToView(pos)  # type: ignore
            x = float(mousePoint.x())
            y = float(mousePoint.y())
            self.setWindowTitle(
                f'{self.title}       x: {round(x, 3)}, y: {round(y, 3)}                 '
            )
            self.setToolTip(
                f'x: <b>{round(x, 1)}</b>,<br> y: <b>{round(y, 1)}</b>'
            )

    def mouseClickEvent(self, event) -> None:
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
            self.parent.checkPositioningWindows()

    def contextMenu(self, event) -> None:
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
        closeAction.triggered.connect(self.close)  # type: ignore

        menu.exec(event.screenPos().toPoint())

    def setBackgrounMenu(self, parent: QMenu) -> None:
        menu = parent.addMenu('&Фон')

        colors = {'white': 'Белый', 'black': 'Черный'}

        for encolor, rucolor in colors.items():
            action = QAction(rucolor, self)
            action.setCheckable(True)
            if getattr(self.plt, '_background') == encolor:
                action.setChecked(True)
            else:
                action.setChecked(False)
            menu.addAction(action)
            action.triggered.connect(
                partial(self.changeBackground, encolor)
            )

    def setLineTypeMenu(self, parent: QMenu) -> None:
        lineType = parent.addMenu('&Тип линии')
        for name, data in self.curves.items():
            nameLine: QMenu = lineType.addMenu(name)  # type: ignore

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

    def setTimeShiftMenu(self, parent: QMenu) -> None:
        timeShiftMenu = parent.addMenu('&Сдвиг графика')
        for name, data in self.curves.items():
            timeShiftAction = QAction(name, self)
            timeShiftMenu.addAction(timeShiftAction)
            timeShiftAction.triggered.connect(
                partial(self.timeShift, data)
            )

    def changeBackground(self, color: str):
        '''
        Метод изменения цвета фона и запись его в настройки.
        '''
        self.plt.setBackground(color)
        settings = self.parent.settings.value('graphs')
        settings['background'] = color
        self.parent.settings.setValue('graphs', settings)
        legendColor = 'white' if color == 'black' else 'black'
        self.legend.setPen(legendColor)
        # setLabelTextColor не меняет цвет текста, видимо баг
        self.legend.setLabelTextColor(legendColor)

    def lineGraph(self, data: dict) -> None:
        '''
        Метод изменения линии графика.
        '''
        if data['curve'].opts['pen'] == data['pen']:
            data['curve'].setPen(None)
        else:
            data['curve'].setPen(data['pen'])

    def crossGraph(self, data: dict) -> None:
        '''
        Метод изменения линии графика.
        '''
        if data['curve'].opts['symbol'] is None:
            data['curve'].setSymbol('+')
            data['curve'].setSymbolPen(data['pen'])
        else:
            data['curve'].setSymbol(None)

    def timeShift(self, curveData: dict) -> None:
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
        self.spinBox.setAlignment(
            Qt.AlignCenter | Qt.AlignVCenter)  # type: ignore
        self.spinBox.setMinimumWidth(80)
        self.spinBox.setRange(-max, max)
        self.spinBox.setSingleStep(.1)
        self.spinBox.valueChanged.connect(
            partial(self.updateGraph, curveData))
        self.applyShiftButton = QPushButton('Применить смещение')
        self.applyShiftButton.clicked.connect(
            partial(self.applyShift, curveData))
        self.layoutShift.addWidget(self.applyShiftButton)
        self.layoutShift.addWidget(self.slider)
        self.layoutShift.addWidget(self.spinBox)

    def updateGraph(self, curveData: dict, value: str) -> None:
        '''
        Метод перестроения графика после смещения данных.
        '''
        self.slider.setValue(int(value))
        self.spinBox.setValue(float(value))
        curve = curveData['curve']
        category = curveData['category']
        adr = curveData['adr']
        item = curve.name()
        dataForGraph = self.data[category][adr].iloc[::self.decimation]
        x = [i + value for i in dataForGraph.time]
        y = dataForGraph[item]
        curve.setData(x, y)

    def applyShift(self, curveData) -> None:
        '''
        Применить смещение
        '''
        value = self.spinBox.value(),
        data = self.data[curveData['category']][curveData['adr']]
        data['time'] = data['time'] + value
        self.parent.setNotify(
            'успех', 'Смещение задано. Не забудьте сохранить изменения'
        )
