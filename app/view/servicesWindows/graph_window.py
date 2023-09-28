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
import pandas as pd
from ...controller.helpers import get_intervals_from_string


class Graph_window(QMdiSubWindow):
    '''
    Класс окон для построения графиков.
    parent - родительское окно
    data - данные для построения графика
    columns - колонки, необходимые для построения,
    график всегда строится Ох - time(время) Oy - выбранные колонки
    colors - цвета для графиков
    curves - словарь названия и объектов графиков.
    '''

    def __init__(self, data: pd.DataFrame, treeSelected, decimation, start_time, stop_time, parent) -> None:
        super().__init__()
        self.parent = parent
        self.data: dict = data
        self.columns: list = treeSelected
        self.title: str = '/'.join([i[2] for i in self.columns])
        self.decimation: int = decimation
        self.start_time: float | None = start_time
        self.stop_time: float | None = stop_time
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
        self.shift_widget = None
        self.main_widget: QWidget = QWidget()
        self.setWidget(self.main_widget)
        self.main_layout: QVBoxLayout = QVBoxLayout()
        self.main_widget.setLayout(self.main_layout)
        self.setWindowTitle(self.title)
        self.setGeometry(0, 0, 500, 300)
        self.setAttribute(Qt.WA_DeleteOnClose, True)  # type: ignore
        self.create_graph()

    def create_graph(self) -> None:
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

        self.plot = pg.PlotWidget()
        self.plot.setBackground(self.theme)
        self.plot.showGrid(x=True, y=True)

        legend_color = 'white' if self.theme == 'black' else 'black'
        self.legend: pg.LegendItem = self.plot.addLegend(
            pen=legend_color,
            labelTextColor=legend_color,
            offset=(0, 0)
        )
        pen = pg.mkPen(legend_color, width=1.3)
        self.plot.getAxis('bottom').setPen(pen)
        self.plot.getAxis('bottom').setTextPen(pen)
        self.plot.getAxis('left').setPen(pen)
        self.plot.getAxis('left').setTextPen(pen)

        for category, adr, item in self.columns:
            data_for_graph = self.data[category][adr].dropna(
                subset=['time', item]
            )
            data_for_graph = data_for_graph.reset_index().iloc[::self.decimation]
            if self.start_time and self.stop_time:
                data_for_graph = data_for_graph.loc[
                    (data_for_graph['time'] >= self.start_time) & (data_for_graph['time'] <= self.stop_time)
                ]
            pen = pg.mkPen(color=self.colors[0], width=1.5)
            curve = pg.PlotDataItem(
                data_for_graph.time.to_list(),
                data_for_graph[item].to_list(),
                name=item,
                pen=pen
            )
            self.curves[f'{category}/{adr}/{item}'] = {
                'curve': curve, 'pen': pen, 'adr': adr, 'category': category
            }
            self.plot.addItem(curve)
            self.colors.append(self.colors.pop(0))
        self.plot.setMenuEnabled(False)
        self.main_layout.addWidget(self.plot)
        self.plot.proxy = pg.SignalProxy(
            self.plot.scene().sigMouseMoved,
            rateLimit=30,
            slot=self.mouse_moved
        )
        self.plot.scene().sigMouseClicked.connect(self.mouse_click_event)
        self.plot.setClipToView(True)
        self.plot.setDownsampling(auto=True, mode='peak')

        flight_data = self.parent.controller.get_data().get('FLIGHT_DATA', {})
        if flight_data and 'intervals' in flight_data:
            intervals = get_intervals_from_string(flight_data['intervals'])
            for interval in intervals:
                roi = pg.LinearRegionItem(interval)  # отрезок [начало, конец]
                roi.setBrush(pg.mkBrush(192, 192, 50, 28))  # цвет фона с прозрачностью
                roi.setMovable(False)
                self.plot.addItem(roi)


    def mouse_moved(self, e) -> None:
        '''
        Метод реализации высплывающей подсказки по координатам
        при перемещении мыши.
        '''
        pos = e[0]
        if self.plot.sceneBoundingRect().contains(pos):
            mousePoint = self.plot.getPlotItem().vb.mapSceneToView(pos)  # type: ignore
            x = float(mousePoint.x())
            y = float(mousePoint.y())
            self.setWindowTitle(
                f'{self.title}       x: {round(x, 3)}, y: {round(y, 3)}                 '
            )
            self.setToolTip(
                f'x: <b>{round(x, 1)}</b>,<br> y: <b>{round(y, 1)}</b>'
            )

    def mouse_click_event(self, event) -> None:
        '''
        Метод обработки событий нажатия мышки.
        '''
        if event.button() == Qt.MouseButton.RightButton:
            self.context_menu(event)
            event.accept()
        if event.button() == Qt.MouseButton.LeftButton and event.double():
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()
            event.accept()
        if event.button() == Qt.MouseButton.MiddleButton:
            self.close()
            self.parent.check_positioning_windows()

    def context_menu(self, event) -> None:
        '''
        Метод создания кастомного контекстного меню.
        '''
        menu = QMenu()
        self.background_menu(menu)
        self.line_type_menu(menu)
        self.time_shift_menu(menu)

        hide_border_window_action = QAction(
            '&Скрыть/показать границы окна'
        )
        menu.addAction(hide_border_window_action)
        hide_border_window_action.triggered.connect(
            self.parent.hide_unhide_border_window
        )

        menu.addSeparator()

        close_action = QAction('&Закрыть')
        menu.addAction(close_action)
        close_action.triggered.connect(self.close)

        menu.exec(event.screenPos().toPoint())

    def background_menu(self, parent: QMenu) -> None:
        menu = parent.addMenu('&Фон')

        colors = {'white': 'Белый', 'black': 'Черный'}

        for encolor, rucolor in colors.items():
            action = QAction(rucolor, self)
            action.setCheckable(True)
            if getattr(self.plot, '_background') == encolor:
                action.setChecked(True)
            else:
                action.setChecked(False)
            menu.addAction(action)
            action.triggered.connect(
                partial(self.change_background_event, encolor)
            )

    def line_type_menu(self, parent: QMenu) -> None:
        line_type = parent.addMenu('&Тип линии')
        for name, data in self.curves.items():
            line_name: QMenu = line_type.addMenu(name)  # type: ignore

            line_graph_action = QAction('&Линия', self)
            line_graph_action.setCheckable(True)
            if data['curve'].opts['pen'] == data['pen']:
                line_graph_action.setChecked(True)
            else:
                line_graph_action.setChecked(False)
            line_name.addAction(line_graph_action)
            line_graph_action.triggered.connect(
                partial(self.line_graph_event, data))

            cross_graph_action = QAction('&Точки', self)
            cross_graph_action.setCheckable(True)
            if data['curve'].opts['symbol'] is None:
                cross_graph_action.setChecked(False)
            else:
                cross_graph_action.setChecked(True)
            line_name.addAction(cross_graph_action)
            cross_graph_action.triggered.connect(
                partial(self.cross_graph_event, data))

    def time_shift_menu(self, parent: QMenu) -> None:
        menu = parent.addMenu('&Сдвиг графика')
        for name, data in self.curves.items():
            action = QAction(name, self)
            menu.addAction(action)
            action.triggered.connect(
                partial(self.time_shift_event, data)
            )

    def change_background_event(self, color: str):
        '''
        Метод изменения цвета фона и запись его в настройки.
        '''
        self.plot.setBackground(color)
        settings = self.parent.settings.value('graphs')
        settings['background'] = color
        self.parent.settings.setValue('graphs', settings)
        legend_color = 'white' if color == 'black' else 'black'
        self.legend.setPen(legend_color)
        # setLabelTextColor не меняет цвет текста, видимо баг
        self.legend.setLabelTextColor(legend_color)

    def line_graph_event(self, data: dict) -> None:
        '''
        Метод изменения линии графика.
        '''
        if data['curve'].opts['pen'] == data['pen']:
            data['curve'].setPen(None)
        else:
            data['curve'].setPen(data['pen'])

    def cross_graph_event(self, data: dict) -> None:
        '''
        Метод изменения линии графика.
        '''
        if data['curve'].opts['symbol'] is None:
            data['curve'].setSymbol('+')
            data['curve'].setSymbolPen(data['pen'])
        else:
            data['curve'].setSymbol(None)

    def time_shift_event(self, curve_data: dict) -> None:
        '''
        Метод смещения графика по оси Ox.
        '''
        if self.shift_widget is not None:
            delete(self.shift_widget)
        self.shift_widget = QFrame()
        self.main_layout.addWidget(self.shift_widget)
        self.shift_layout = QHBoxLayout()
        self.shift_widget.setLayout(self.shift_layout)
        max = int(curve_data['curve'].getData()[0].max()) * 2
        self.slider = QSlider(Qt.Orientation.Horizontal, self)
        self.slider.setRange(-max, max)
        self.slider.setSingleStep(50)
        self.slider.setPageStep(50)
        self.slider.valueChanged.connect(
            partial(self.update_graph_event, curve_data))
        self.spin_box = QDoubleSpinBox(self)
        self.spin_box.setAlignment(
            Qt.AlignCenter | Qt.AlignVCenter
        )  # type: ignore
        self.spin_box.setMinimumWidth(80)
        self.spin_box.setRange(-max, max)
        self.spin_box.setSingleStep(.1)
        self.spin_box.valueChanged.connect(
            partial(self.update_graph_event, curve_data)
        )
        self.apply_shift_button = QPushButton(
            'Применить смещение'
        )
        self.apply_shift_button.clicked.connect(
            partial(self.apply_shift, curve_data)
        )
        self.shift_layout.addWidget(self.apply_shift_button)
        self.shift_layout.addWidget(self.slider)
        self.shift_layout.addWidget(self.spin_box)

    def update_graph_event(self, curve_data: dict, value: str) -> None:
        '''
        Метод перестроения графика после смещения данных.
        '''
        self.slider.setValue(int(value))
        self.spin_box.setValue(float(value))
        curve = curve_data['curve']
        category = curve_data['category']
        adr = curve_data['adr']
        item = curve.name()
        data_for_graph = self.data[category][adr].iloc[::self.decimation]
        x = [i + value for i in data_for_graph.time]
        y = data_for_graph[item]
        curve.setData(x, y)

    def apply_shift(self, curve_data) -> None:
        '''
        Применить смещение
        '''
        value = self.spin_box.value(),
        data = self.data[curve_data['category']][curve_data['adr']]
        data['time'] = data['time'] + value
        self.parent.send_notify(
            'успех', 'Смещение задано. Не забудьте сохранить изменения'
        )
