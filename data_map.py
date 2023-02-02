import folium
from folium.plugins import MousePosition, TagFilterButton, BeautifyIcon
import branca.colormap as cm

class Map(object):

    def __init__(self, data) -> None:
        self.data = data
        self.data['group'] = self.data.name // 1000 * 1000
        self.start = self.data.name.iloc[0]
        self.finish = self.data.name.iloc[-1]
        self.map = folium.Map(location=[self.data.latitude.iloc[0], 
                                        self.data.longitude.iloc[0]],
                              icon='icon_circle',
                              zoom_start=6)
        self.tiles = ['openstreetmap',
                      'stamentoner',
                      'cartodbdark_matter',
                      'Stamen Watercolor']

    def _set_colormap(self):
        self.colormap = cm.LinearColormap(colors=['red',
                                                  'orange',
                                                  'yellow',
                                                  'green',
                                                  'cyan',
                                                  'blue',
                                                  'purple'],
                                          vmin=self.start,
                                          vmax=self.finish)
        self.map.add_child(self.colormap)

    @staticmethod
    def _set_lines(data, feature_group, colormap):
        positions = list(zip(data.latitude, data.longitude))
        folium.ColorLine(positions=positions,
                         colors=data.name,
                         colormap=colormap,
                         weight=5
                         ).add_to(feature_group)

    @staticmethod
    def _set_point(data, color, map):
        html = f'<h5><b>time:</b> {data.name}<br><b>JVD_H:</b> {round(data.JVD_H)}</h5>'
        icon = BeautifyIcon(icon='circle-o',
                            icon_shape='circle',
                            iconSize=[17,17],
                            background_color=color,
                            border_width=1)
        folium.Marker(location=[data.latitude, data.longitude],
                      tooltip=html,
                      icon=icon,
                      tags=[str(data.group)]).add_to(map)

    @staticmethod
    def _set_mouse_coordinates(map):
        formatter = "function(num) {return L.Util.formatNum(num, 5);};"
        mouse_position = MousePosition(position='topright',
                                       separator=' Long: ',
                                       empty_string='NaN',
                                       lng_first=False,
                                       num_digits=20,
                                       prefix='Lat:',
                                       lat_formatter=formatter,
                                       lng_formatter=formatter)
        map.add_child(mouse_position)

    @staticmethod
    def _set_tiles(map, tiles):
        for tile in tiles:
            folium.TileLayer(tile).add_to(map)

    def get_map(self):
        self._set_colormap()
        for row in self.data.itertuples():
            self._set_point(data=row,
                            color=self.colormap(row.name), 
                            map=self.map)

        self._set_mouse_coordinates(self.map)
        self._set_tiles(self.map, self.tiles)
        TagFilterButton(data=[str(i) for i in self.data.group.unique()], 
                        openPopupOnHover=True,
                        clear_text='сбросить').add_to(self.map)
        folium.LayerControl(collapsed=False).add_to(self.map)

    def save_map(self, filepath):
        self.map.save(filepath)
