import branca.colormap as cm
from folium import ColorLine, LayerControl, Map, Marker, TileLayer
from folium.plugins import BeautifyIcon, MousePosition, TagFilterButton


class FlightMap:
    '''
    Класс генерации карты полёта.
    '''

    def __init__(self, data) -> None:
        self.data = data
        self.jvd_h_in = 'JVD_H' in list(data.columns)
        self.data['group'] = self.data.time // 1000 * 1000
        self.start = self.data.time.iloc[0]
        self.finish = self.data.time.iloc[-1]
        self.map = Map(
            location=[
                self.data.latitude.iloc[25],
                self.data.longitude.iloc[25]
            ],
            icon='icon_circle',
            zoom_start=6,
            control_scale=True
        )
        self.tiles = [
            'openstreetmap',
            'stamentoner',
            'cartodbdark_matter',
            'Stamen Watercolor'
        ]

    def _set_colormap(self):
        self.colormap = cm.LinearColormap(
            colors=[
                'red', 'orange',
                'yellow', 'green',
                'cyan', 'blue',
                'purple'
            ],
            vmin=self.start,
            vmax=self.finish
        )
        self.map.add_child(self.colormap)

    @staticmethod
    def _set_lines(data, feature_group, colormap):
        positions = list(zip(data.latitude, data.longitude))
        ColorLine(
            positions=positions,
            colors=data.time,
            colormap=colormap,
            weight=5
        ).add_to(feature_group)

    @staticmethod
    def _set_point(data, color, map, jvd_h_in):
        html = f'<h5><b>Время:</b> {data.time}</h5>'
        if jvd_h_in:
            html += f'<h5><br><b>JVD_H:</b> {round(data.JVD_H)}</h5>'
        icon = BeautifyIcon(
            icon='circle-o',
            icon_shape='circle',
            iconSize=[17, 17],
            background_color=color,
            border_width=1
        )
        Marker(
            location=[data.latitude, data.longitude],
            tooltip=html,
            icon=icon,
            tags=[str(data.group)]
        ).add_to(map)

    @staticmethod
    def _set_mouse_coordinates(map):
        formatter = "function(num) {return L.Util.formatNum(num, 5);};"
        mouse_position = MousePosition(
            position='topright',
            separator=' Long: ',
            empty_string='NaN',
            lng_first=False,
            num_digits=20,
            prefix='Lat:',
            lat_formatter=formatter,
            lng_formatter=formatter
        )
        map.add_child(mouse_position)

    @staticmethod
    def _set_tiles(map, tiles):
        # TODO реворк этого
        for tile in tiles:
            TileLayer(tile).add_to(map)
        custom_tiles = TileLayer(
            # Укажите URL к вашим кастомным тайлам
            tiles='https://{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png',
            attr='&copy; OpenStreetMap France | &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            # Укажите имя для отображения в легенде (по желанию)
            name='OpenStreetMap France',
        )
        custom_tiles.add_to(map)
        custom_tiles = TileLayer(
            # Укажите URL к вашим кастомным тайлам
            tiles='https://tile.openstreetmap.de/{z}/{x}/{y}.png',
            attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            # Укажите имя для отображения в легенде (по желанию)
            name='OpenStreetMap DE',
        )
        custom_tiles.add_to(map)
        custom_tiles = TileLayer(
            # Укажите URL к вашим кастомным тайлам
            tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
            attr='Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)',
            # Укажите имя для отображения в легенде (по желанию)
            name='OpenTopoMap',
        )
        custom_tiles.add_to(map)
        custom_tiles = TileLayer(
            # Укажите URL к вашим кастомным тайлам
            tiles='https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png',
            attr='<a href="https://github.com/cyclosm/cyclosm-cartocss-style/releases" title="CyclOSM - Open Bicycle render">CyclOSM</a> | Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            # Укажите имя для отображения в легенде (по желанию)
            name='CyclOSM',
        )
        custom_tiles.add_to(map)
        custom_tiles = TileLayer(
            # Укажите URL к вашим кастомным тайлам
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Specialty/DeLorme_World_Base_Map/MapServer/tile/{z}/{y}/{x}',
            attr='Tiles &copy; Esri &mdash; Copyright: &copy;2012 DeLorme',
            # Укажите имя для отображения в легенде (по желанию)
            name='Esri.DeLorme',
        )
        custom_tiles.add_to(map)

    def get_map(self):
        self._set_colormap()
        for row in self.data.itertuples():
            self._set_point(
                data=row,
                color=self.colormap(row.time),
                map=self.map,
                jvd_h_in=self.jvd_h_in
            )

        self._set_mouse_coordinates(self.map)
        self._set_tiles(self.map, self.tiles)
        TagFilterButton(
            data=[str(i) for i in self.data.group.unique()],
            openPopupOnHover=True,
            clear_text='сбросить'
        ).add_to(self.map)
        LayerControl(collapsed=True).add_to(self.map)

    def save_map(self, filepath):
        self.map.save(filepath)
