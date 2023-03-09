from app.model.calculate import Mathematical
from app.model.map import Map
from app.model.file import Datas as file_methods
import re

class NoneJsonError(Exception): pass

class Control(object):
    '''
    Класс контроллера для связи модели и интерфейса.
    data - данные полёта.
    data_calculated - признак были ли данные расчитаны или нет.
    '''

    needed_usred_diss, needed_usred_kbti, needed_usred_pnk = (
        False, False, False)

    def __init__(self) -> None:
        self.data = {}
        self.data_calculated = False

    def load_text(self, filepath: str, category: str, adr: str, type: str, load_unknown: bool):
        '''
        Загрузка данных из txt формата.
        '''
        #TODO добавить проверку load_unknown
        if type == 'txt':
            data_from_file = file_methods.load_txt(filepath)
        else:
            data_from_file = file_methods.load_csv(filepath)
        if 'name' in data_from_file.columns:
            data_from_file = data_from_file.rename(columns={'name': 'time'})

        self.data[category] = {adr:data_from_file}
        self.data_calculated = self._check_calculated()

    def load_csv(self, filepath):
        '''
        Загрузка данных из csv формата.
        '''
        data_from_file = file_methods.load_csv(filepath)
        self.data['PNK'] = {'ADR8':data_from_file}
        self.data_calculated = self._check_calculated()
    
    def load_pickle(self, filepath):
        '''
        Загрузка данных из pickle формата.
        '''
        data_from_file = file_methods.load_pickle(filepath)
        self.data = data_from_file
        self.data_calculated = self._check_calculated()

    @staticmethod
    def load_pytnon_script(filepath):
        '''
        Загрузка скрипта python.
        '''
        data_for_script = file_methods.load_python(filepath)
        return data_for_script

    @staticmethod
    def load_settings_json(filepath):
        '''
        Загрузка данных настроек из json формата.
        '''
        data_for_settings = file_methods.load_json(filepath)
        return data_for_settings

    def load_pdd(self, filepath):
        '''
        Загрузка данных из pdd формата.
        '''
        #TODO необходимо внедрить json файлы в настройки программы
        #временно пока json файл стандартный
        #добавить проверку jsona

        json_file = 'templates/default_pnk.json'
        data_from_file = file_methods.load_pdd(filepath, json_file)
        self.data[data_from_file['name']] = data_from_file['adr']

    @staticmethod
    def save_python_sript(filepath, data):
        '''
        Сохранение скрипта питона.
        '''
        file_methods.save_python(filepath, data)

    @staticmethod
    def save_settings_json(filepath, data):
        '''
        Сохранения данных настроек в json.
        '''
        file_methods.save_json(filepath, data)

    def set_calculate_data_pnk(self, category, adr, plane_corr, corrections):
        '''
        Метод расчета данных полёта.
        Содержит базовую проверку, содержат ли данные все 
        необходимые данные для расчетов.
        Последовательно рассчитывает данные.
        После всех расчетов обновляет данные в DataFrame.
        Если все прошло успешно, data_calculated - успешно.
        '''
        need_headers = {'time', 'DIS_Wx', 'DIS_Wy', 'DIS_Wz', 'I1_Kren',
                        'I1_Tang', 'I1_KursI', 'JVD_VN', 'JVD_VE', 'JVD_Vh'}
        headers = self.data[category][adr].columns
        if self.data == {} or not need_headers.issubset(headers):
            raise ValueError('Wrong data')
        self.worker = Mathematical(self.data[category][adr].copy())
        self.worker.apply_coefficient_w_diss(
            wx=corrections['koef_Wx_PNK'],
            wz=corrections['koef_Wz_PNK'],
            wy=corrections['koef_Wy_PNK'])
        self.worker.calc_angles(
            kren=corrections['kren_correct'],
            tang=corrections['tang_correct'],
            kurs=corrections['kurs_correct'])
        self.worker.calc_wg_kbti(plane_corr['k'], plane_corr['k1'])
        self.worker.calc_wc_kbti()
        self.worker.calc_wp()
        self.data['Calc'] = {'PNK':self.worker.get_only_calculated_data_pnk()}
        self.data_calculated = True

    def save_report(self, filepath, category, adr, koef_for_intervals, string):
        '''
        Метод расчета отчёта и его сохранения на диске.
        Создается объект класса рассчёта.
        Обязетально проверяется высота, если её нет в данных, то 
        автоматический рассчёт интервалов невозможен, только
        по пользовательскому вводу.
        Пользовательские данные регулярками обрабатываются,
        чтобы исключить возникновения ошибок.
        Расситываем данные с учетом коэффициентов, 
        записываем по указанному пути.
        '''
        data_source = self.data[category][adr]
        data_calc = self.data['Calc']['PNK']
        self.worker = Mathematical(data_source.merge(data_calc, on='time'))
        if string == '':
            if 'JVD_H' in self.data[category][adr].columns:
                intervals = self.worker.get_intervals(koef_for_intervals)
            else:
                raise ValueError('JVD_H not found in data')
        else:
            intervals = re.sub(r'[^\d\-\n]', '', string)
            intervals = re.findall(r'(\d+\-\d+)\n?', intervals)
            intervals = [i.split('-') for i in intervals]
            intervals = [(int(x), int(y)) for x, y in intervals]
        data_result = self.worker.get_calculated_data(intervals)

        file_methods.write_xlsx(data_result, filepath)

    def save_map(self, filepath, category, adr, jvd_h_min='', decimation=''):
        '''
        Метод построения карты и записи её на диск. 
        Три обязательных параметра указаны в need_headers.
        Если заданы decimation и jvd_h_min, они учитываются в данных
        для построения карты.
        '''
        need_headers = {'time', 'latitude', 'longitude'}
        if self.data == {}:
            raise ValueError('Wrong data')
        if not need_headers.issubset(self.data[category][adr].columns):
            raise ValueError('Wrong data, check time, latitude, longitude')
        data_for_map = self.data[category][adr].copy()
        if decimation != '':
            data_for_map = data_for_map.iloc[::int(decimation)]
        if jvd_h_min != '' and 'JVD_H' in data_for_map.columns:
            data_for_map = data_for_map.loc[data_for_map.JVD_H >= float(jvd_h_min),
                                            ['time', 'latitude', 'longitude', 'JVD_H']]
        map = Map(data_for_map)
        map.get_map()
        map.save_map(filepath)

    def save_csv(self, filepath, category, adr):
        '''
        Сохранение данных в формате csv.
        '''
        if self.data is None:
            raise Exception('Data must be not none')
        data_for_csv = self.data[category][adr]
        file_methods.write_csv(data_for_csv, filepath)

    def save_pickle(self, filepath):
        '''
        Сохранение данных в формате pickle.
        '''
        if self.data == {}:
            raise Exception('Data must be not none')
        file_methods.write_pickle(self.data, filepath)

    def get_data(self):
        '''
        Метод получения данных контроллера.
        '''
        return self.data

    def _check_calculated(self):
        '''
        Метод проверки были ли данные рассчитаны или нет.
        '''
        if 'Calc' in self.data:
            return True

    def is_calculated(self):
        '''
        Получение статуса рассчёта данных.
        '''
        return self.data_calculated

    @staticmethod
    def get_jsons_data(dirpath):
        json_list = file_methods.get_list_json_in_folder(dirpath)
        if json_list == []:
            raise NoneJsonError
        return file_methods.get_jsons_data(json_list)

    @classmethod
    def get_json_categories(cls, dirpath):
        json_categories = {json['name']:json['adr'] for json in cls.get_jsons_data(dirpath)}
        return json_categories

    def data_not_none(self):
        if self.data:
            return True
        return False



