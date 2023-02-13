from app.model.calculate import Mathematical
from app.model.map import Map
from app.model.file import Datas
import re


class Control(object):

    needed_usred_diss, needed_usred_kbti, needed_usred_pnk = (
        False, False, False)

    def __init__(self) -> None:
        self.fly = Datas()
        self.data = None
        self.data_calculated = False

    def load_txt(self, filepath):
        data_from_file = self.fly.load_txt(filepath)
        self.data = data_from_file
        self.data_calculated = self.check_calculated()

    def load_csv(self, filepath):
        data_from_file = self.fly.load_csv(filepath)
        self.data = data_from_file
        self.data_calculated = self.check_calculated()

    def load_parquet(self, filepath):
        data_from_file = self.fly.load_parquet(filepath)
        self.data = data_from_file
        self.data_calculated = self.check_calculated()

    def load_pytnon_script(self, filepath):
        data_from_script = self.fly.load_python(filepath)
        return data_from_script

    def load_settings_json(self, filepath):
        data_from_settings = self.fly.load_json(filepath)
        return data_from_settings

    def save_python_sript(self, filepath, data):
        self.fly.save_python(filepath, data)

    def save_settings_json(self, filepath, data):
        self.fly.save_json(filepath, data)

    def set_calculate_data(self, plane_corr, corrections):
        # TODO реализовать проверку на недостающие данные для расчета
        need_headers = {'name', 'DIS_Wx', 'DIS_Wy', 'DIS_Wz', 'I1_Kren',
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

        self.fly.write_xlsx(data_result, filepath)

    def save_map(self, filepath, jvd_h_min='', decimation=''):
        need_headers = {'name', 'latitude', 'longitude'}
        if self.data is None or not need_headers.issubset(self.data.columns):
            raise ValueError('Wrong data')
        data_for_map = self.data.copy()
        if decimation != '':
            data_for_map = data_for_map.iloc[::int(decimation)]
        if jvd_h_min != '' and 'JVD_H' in data_for_map.columns:
            data_for_map = data_for_map.loc[self.data.JVD_H >= float(jvd_h_min),
                                            ['name', 'latitude', 'longitude', 'JVD_H']]
        map = Map(data_for_map)
        map.get_map()
        map.save_map(filepath)

    def save_csv(self, filepath):
        if self.data is None:
            raise Exception('Data must be not none')
        self.fly.write_csv(self.data, filepath)

    def save_parquet(self, filepath):
        if self.data is None:
            raise Exception('Data must be not none')
        self.fly.write_parquet(self.data, filepath)

    def get_data(self):
        return self.data

    def check_calculated(self):
        if 'Wp_diss_pnki' in self.data.columns:
            return True

    def is_calculated(self):
        return self.data_calculated
