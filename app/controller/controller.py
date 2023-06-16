from app.model import Mathematical, Flight_map
from app.model import file_methods
from pandas import DataFrame
import re
import numpy as np
import pandas as pd
from itertools import zip_longest


class NoneJsonError(Exception):
    pass


class Control(object):
    '''
    Класс контроллера для связи модели и интерфейса.
    data - данные полёта.
    data_calculated - признак были ли данные расчитаны или нет.
    '''

    needed_usred_diss, needed_usred_kbti, needed_usred_pnk = (
        False, False, False
    )

    def __init__(self) -> None:
        self.data: dict = {}
        self.data_calculated: bool = False

    def load_text(
        self,
        filepath: str,
        category: str,
        adr: str,
        type: str,
        category_info: dict,
        load_unknown: bool = True
    ) -> None:
        '''
        Загрузка данных из txt формата.
        '''
        if type == 'txt':
            data_from_file = file_methods.load_txt(filepath)
        else:
            data_from_file = file_methods.load_csv(filepath)
        if 'name' in data_from_file.columns:
            data_from_file = data_from_file.rename(columns={'name': 'time'})

        if not load_unknown:
            category_headers = []
            for elem in category_info:
                if elem['adr_name'] == adr:
                    category_headers = [field['name']
                                        for field in elem['fields']]
                    category_headers.extend(['time', 'latitude', 'longitude'])
                    break
            if not category_headers:
                raise ValueError('Не найдены заголовки в json файле')
            for column_name in data_from_file:
                if column_name not in category_headers:
                    del data_from_file[column_name]

        self.data[category] = {adr: data_from_file}
        self.data_calculated = self._check_calculated()

    def load_gzip(self, filepath: str) -> None:
        '''
        Загрузка данных из pickle gzip формата.
        '''
        data_from_file = file_methods.load_gzip(filepath)
        for category in data_from_file:
            self.data[category] = data_from_file[category]
        self.data_calculated = self._check_calculated()

    @staticmethod
    def load_pytnon_script(filepath: str) -> str:
        '''
        Загрузка скрипта python.
        '''
        data_for_script = file_methods.load_python_script(filepath)
        return data_for_script

    @staticmethod
    def load_settings_json(filepath: str) -> dict:
        '''
        Загрузка данных настроек из json формата.
        '''
        data_for_settings = file_methods.load_json(filepath)
        return data_for_settings

    def load_pdd(self, filepath: str, category, json_data) -> None:
        '''
        Загрузка данных из pdd формата.
        '''
        # TODO добавить проверку json_data

        data_from_file = file_methods.load_pdd(filepath, json_data)
        self.data[category] = data_from_file

    @staticmethod
    def save_python_sript(filepath: str, data: DataFrame) -> None:
        '''
        Сохранение скрипта питона.
        '''
        file_methods.save_python(filepath, data)

    @staticmethod
    def save_settings_json(filepath: str, data: DataFrame) -> None:
        '''
        Сохранения данных настроек в json.
        '''
        file_methods.save_json(filepath, data)

    def set_calculate_data_pnk(
        self,
        category: str,
        adr: str,
        plane_correct: dict,
        corrections: dict,
        target_adr: str
    ) -> None:
        '''
        Метод расчета данных полёта.
        Содержит базовую проверку, содержат ли данные все 
        необходимые данные для расчетов.
        Последовательно рассчитывает данные.
        После всех расчетов обновляет данные в DataFrame.
        Если все прошло успешно, data_calculated - успешно.
        '''
        need_headers = {
            'time', 'DIS_Wx', 'DIS_Wy', 'DIS_Wz', 'I1_Kren',
            'I1_Tang', 'I1_KursI', 'JVD_VN', 'JVD_VE', 'JVD_Vh'
        }
        headers = self.data[category][adr].columns
        if self.data_is_none() or not need_headers.issubset(headers):
            not_found_headers = set(need_headers) - set(headers)
            raise ValueError(
                f'В данных не хватает: {", ".join(not_found_headers)}')
        self.worker = Mathematical(self.data[category][adr].copy())
        self.worker.apply_coefficient_w_diss(
            wx=corrections['koef_Wx_PNK'],
            wz=corrections['koef_Wz_PNK'],
            wy=corrections['koef_Wy_PNK'])
        self.worker.calc_angles(
            kren=corrections['kren_correct'],
            tang=corrections['tang_correct'],
            kurs=corrections['kurs_correct'])
        self.worker.calc_wg_kbti(plane_correct['k'], plane_correct['k1'])
        self.worker.calc_wc_kbti()
        self.worker.calc_wp()
        if 'CALC' in self.data:
            self.data['CALC'][target_adr] = self.worker.get_only_calculated_data_pnk()
        else:
            self.data['CALC'] = {
                target_adr: self.worker.get_only_calculated_data_pnk()
            }
        self.data_calculated = True

    def save_report(
        self,
        filepath: str,
        categories: dict,
        plane_koef: dict,
        koef_for_intervals: dict,
        string: str
    ) -> None:
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
        category_source = categories['source']['category']
        adr_source = categories['source']['adr']
        data_source = self.data[category_source][adr_source]
        category_calc = categories['calc']['category']
        adr_calc = categories['calc']['adr']
        data_calc = self.data[category_calc][adr_calc]
        self.worker = Mathematical(data_source.merge(data_calc, on='time'))
        if string == '':
            if 'JVD_H' in data_source.columns:
                intervals = self.worker.get_intervals(koef_for_intervals)
            else:
                raise ValueError(
                    'JVD_H не найден в данных, автоматически подбор недоступен'
                )
        else:
            intervals = re.sub(r'[^\d\-\n]', '', string)
            intervals = re.findall(r'(\d+\-\d+)\n?', intervals)
            intervals = [i.split('-') for i in intervals]
            intervals = [(int(x), int(y)) for x, y in intervals]
        data_result = self.worker.get_calculated_data(intervals)

        file_methods.write_xlsx(data_result, plane_koef, filepath)

    def save_map(
        self,
        filepath: str,
        category: str,
        adr: str,
        jvd_h_min: str = '',
        decimation: str = ''
    ) -> None:
        '''
        Метод построения карты и записи её на диск. 
        Три обязательных параметра указаны в need_headers.
        Если заданы decimation и jvd_h_min, они учитываются в данных
        для построения карты.
        '''
        need_headers = {'time', 'latitude', 'longitude'}
        if self.data_is_none():
            raise ValueError('Wrong data')
        if not need_headers.issubset(self.data[category][adr].columns):
            raise ValueError(
                'Wrong data, check time, latitude, longitude')
        data_for_map = self.data[category][adr].copy()
        if decimation != '':
            data_for_map = data_for_map.iloc[::int(decimation)]
        if jvd_h_min != '' and 'JVD_H' in data_for_map.columns:
            data_for_map = data_for_map.loc[
                data_for_map.JVD_H >= float(jvd_h_min),
                ['time', 'latitude', 'longitude', 'JVD_H']
            ]
        map = Flight_map(data_for_map)
        map.get_map()
        map.save_map(filepath)

    def save_csv(self, filepath: str, category: str, adr: str) -> None:
        '''
        Сохранение данных в формате csv.
        '''
        if self.data_is_none():
            raise Exception('Data must be not none')
        data_for_csv = self.data[category][adr]
        file_methods.write_csv(data_for_csv, filepath)

    def save_gzip(self, filepath: str) -> None:
        '''
        Сохранение данных в формате pickle gzip.
        '''
        if self.data_is_none():
            raise Exception('Data must be not none')
        file_methods.write_gzip(self.data, filepath)

    def get_data(self) -> dict:
        '''
        Метод получения данных контроллера.
        '''
        return self.data

    def _check_calculated(self) -> bool:
        '''
        Метод проверки были ли данные рассчитаны или нет.
        '''
        if 'CALC' in self.data:
            return True
        return False

    def is_calculated(self):
        '''
        Получение статуса рассчёта данных.
        '''
        return self.data_calculated

    @staticmethod
    def get_jsons_data(dirpath: str) -> list:
        json_list = file_methods.get_list_json_in_folder(dirpath)
        if json_list == []:
            raise NoneJsonError
        return file_methods.get_jsons_data(json_list)

    @classmethod
    def get_json_categories(cls, dirpath: str) -> dict:
        json_categories = {
            json['name']: json['adr']
            for json in cls.get_jsons_data(dirpath)
        }
        return json_categories

    def data_is_none(self) -> bool:
        if self.data:
            return False
        return True

    def change_column_name(self, item_info: list, new_name: str) -> None:
        if self.data_is_none():
            raise ValueError('Нет данных')
        if len(item_info) == 1:
            category = item_info[0]
            self.data[new_name] = self.data[category]
            del self.data[category]
            return
        if len(item_info) == 2:
            category, adr = item_info
            self.data[category][new_name] = self.data[category][adr]
            del self.data[category][adr]
            return
        category, adr, column = item_info
        self.data[category][adr] = self.data[category][adr].rename(
            columns={column: new_name}
        )

    def delete_item(self, item_info: list) -> None:
        if self.data_is_none():
            raise ValueError('Нет данных')
        if len(item_info) == 1:
            category = item_info[0]
            del self.data[category]
            return
        if len(item_info) == 2:
            category, adr = item_info
            del self.data[category][adr]
            return
        category, adr, column = item_info
        self.data[category][adr].drop(column, axis=1, inplace=True)

    def concatenate_unch(self, input_category: str, input_adr: str, target_adr: str):
        # TODO убрать это в модель
        if self.data_is_none():
            raise ValueError('Нет данных')
        data = self.data[input_category][input_adr]

        result = {
            'Ch1_UNCH1': [],
            'Ch1_UNCH2': [],
            'Ch2_UNCH1': [],
            'Ch2_UNCH2': [],
            'Ch3_UNCH1': [],
            'Ch3_UNCH2': [],
        }
        for i in data:
            if i == 'time':
                continue
            channel, unch, number = i.split('_')
            result[f'{channel}_{unch}'].append(data[i].dropna().values)

        for name in result:
            result[name] = np.column_stack(result[name]).ravel()

        min_length = min(
            len(result['Ch1_UNCH1']),
            len(result['Ch1_UNCH2']),
            len(result['Ch2_UNCH1']),
            len(result['Ch2_UNCH2']),
            len(result['Ch3_UNCH1']),
            len(result['Ch3_UNCH2'])
        )
        for name in result:
            result[name] = result[name][:min_length]
        result['time'] = np.arange(min_length)

        result = pd.DataFrame(result)
        if 'CALC' in self.data:
            self.data['CALC'][target_adr] = result
        else:
            self.data['CALC'] = {target_adr: result}
