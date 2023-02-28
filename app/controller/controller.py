from app.model.calculate import Mathematical
from app.model.map import Map
from app.model.file import Datas as file_methods
import re

class Control(object):
    '''
    Класс контроллера для связи модели и интерфейса.
    fly - модель полёта.
    data - данные полёта.
    data_calculated - признак были ли данные расчитаны или нет.
    '''

    needed_usred_diss, needed_usred_kbti, needed_usred_pnk = (
        False, False, False)

    def __init__(self) -> None:
        self.data = None
        self.data_calculated = False

    def load_txt(self, filepath):
        '''
        Загрузка данных из txt формата.
        '''
        data_from_file = file_methods.load_txt(filepath)
        self.data = data_from_file
        self.data_calculated = self.check_calculated()

    def load_csv(self, filepath):
        '''
        Загрузка данных из csv формата.
        '''
        data_from_file = file_methods.load_csv(filepath)
        self.data = data_from_file
        self.data_calculated = self.check_calculated()

    def load_parquet(self, filepath):
        '''
        Загрузка данных из parquet формата.
        '''
        data_from_file = file_methods.load_parquet(filepath)
        self.data = data_from_file
        self.data_calculated = self.check_calculated()

    @staticmethod
    def load_pytnon_script(filepath):
        '''
        Загрузка скрипта python.
        '''
        data_from_script = file_methods.load_python(filepath)
        return data_from_script

    @staticmethod
    def load_settings_json(filepath):
        '''
        Загрузка данных настроек из json формата.
        '''
        data_from_settings = file_methods.load_json(filepath)
        return data_from_settings

    def load_pdd(self, filepath):
        '''
        Загрузка данных из pdd формата.
        '''
        #TODO необходимо внедрить json файлы в настройки программы
        #временно пока json файл стандартный
        #временно пока только один адр
        #добавить проверку jsona

        json_file = 'templates/default_adr8.json'
        data_from_file = file_methods.load_pdd(filepath, json_file)
        self.data = data_from_file['adr']['ADR8']

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

    def set_calculate_data(self, plane_corr, corrections):
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
        if self.data is None or not need_headers.issubset(self.data.columns):
            raise ValueError('Wrong data')
        self.worker = Mathematical(self.data)
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
        self.data = self.worker.get_data()
        self.data_calculated = True

    def save_report(self, filepath, koef_for_intervals, string):
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
        self.worker = Mathematical(self.data)
        if string == '':
            if 'JVD_H' in self.data.columns:
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

    def save_map(self, filepath, jvd_h_min='', decimation=''):
        '''
        Метод построения карты и записи её на диск. 
        Три обязательных параметра указаны в need_headers.
        Если заданы decimation и jvd_h_min, они учитываются в данных
        для построения карты.
        '''
        need_headers = {'time', 'latitude', 'longitude'}
        if self.data is None or not need_headers.issubset(self.data.columns):
            raise ValueError('Wrong data')
        data_for_map = self.data.copy()
        if decimation != '':
            data_for_map = data_for_map.iloc[::int(decimation)]
        if jvd_h_min != '' and 'JVD_H' in data_for_map.columns:
            data_for_map = data_for_map.loc[self.data.JVD_H >= float(jvd_h_min),
                                            ['time', 'latitude', 'longitude', 'JVD_H']]
        map = Map(data_for_map)
        map.get_map()
        map.save_map(filepath)

    def save_csv(self, filepath):
        '''
        Сохранение данных в формате csv.
        '''
        if self.data is None:
            raise Exception('Data must be not none')
        file_methods.write_csv(self.data, filepath)

    def save_parquet(self, filepath):
        '''
        Сохранение данных в формате parquiet.
        '''
        if self.data is None:
            raise Exception('Data must be not none')
        file_methods.write_parquet(self.data, filepath)

    def get_data(self):
        '''
        Метод получения данных контроллера.
        '''
        return self.data

    def check_calculated(self):
        '''
        Метод проверки были ли данные рассчитаны или нет.
        '''
        if 'Wp_diss_pnki' in self.data.columns:
            return True

    def is_calculated(self):
        '''
        Получение статуса рассчёта данных.
        '''
        return self.data_calculated
