import data_calculate as dc
import data_map as dm
import data_file as df
import re

class Control(object):

    IL78m90a = False
    IL76md90a = False
    mdm = False
    m2 = True
    tu22 = False
    tu160 = False

    needed_usred_diss, needed_usred_kbti, needed_usred_pnk = (
        False, False, False)

    kurs_DISS_grad = 0
    kren_DISS_grad = 0
    tang_DISS_grad = 0

    if mdm:
        kurs_DISS_grad = -0.62  # -0°37'
        kren_DISS_grad = 0.032  # +0°02’
        tang_DISS_grad = 3.33 - 0.032  # 3°20’-0°02’
    if m2:
        kurs_DISS_grad = 0.2833  # 0°17’  #18 в частоте
        kren_DISS_grad = 0.032
        tang_DISS_grad = 3.33 - 0.2  # -0.032  #3.33 #3°20'
    if IL78m90a:
        kurs_DISS_grad = 0.27  # 0°16’
        kren_DISS_grad = 0
        tang_DISS_grad = 3.33  # 3.33   #3°20'
    if IL76md90a:
        kurs_DISS_grad = 0 - 0.665   # -0°39’
        kren_DISS_grad = -0.144  # 0
        tang_DISS_grad = 3.33  # 3°20'+0°7'
    if tu22:  # 45.03
        kurs_DISS_grad = 0  # 0.45
        kren_DISS_grad = 0
        tang_DISS_grad = 0  # -4°00' (-4.0), но пока в прошивке 1.4 ДИСС 0
    if tu160:  # 70m
        kurs_DISS_grad = 0
        kren_DISS_grad = 0
        tang_DISS_grad = -2.5  # 2.5  #-2°30'

    # добавляется к I1_KursI, I1_Kren, I1_Tang из *.txt-данных от КБТИ (поворот оси): тут подбираем, сообщаем что ввести, знак тот же, в скрипте влияют только на данные КБТИ
    kurs_correct = 0
    kren_correct = 0
    tang_correct = 0

    # Поправки прибора коррекции, вводятся у нас на заводе, влияют на наши данные
    work_popr_typ = 1  # Если 0, то работаем по градусам, если 1 - по кодам
    popr_prib_cor_V = 72.57  # угол v градусы
    popr_prib_cor_FI = 72.57  # угол фи градусы
    popr_prib_cor_B = 65.05  # угол В градусы

    # Поправки прибора коррекции, вводятся у нас на заводе, влияют на наши данные
    work_popr_typ = 1  # Если 0, то работаем по градусам, если 1 - по кодам
    popr_prib_cor_V = 72.57  # угол v градусы
    popr_prib_cor_FI = 72.57  # угол фи градусы
    popr_prib_cor_B = 65.05  # угол В градусы

    popr_prib_cor_V_cod = 0
    popr_prib_cor_FI_cod = 0
    popr_prib_cor_B_cod = 0
    if mdm:
        popr_prib_cor_V_cod = 5  # Код поправки угла v,  от 0 до 15 Wx
        popr_prib_cor_FI_cod = 14  # Код поправки угла фи,  от 0 до 15 Wz
        popr_prib_cor_B_cod = 2  # Код поправки угла В,  от 0 до 3 Wy
    if m2:
        popr_prib_cor_V_cod = 7  # Код поправки угла v,  от 0 до 15 Wx, влияет на Wпутевую и Wx
        popr_prib_cor_FI_cod = 6  # Код поправки угла фи,  от 0 до 15 Wz
        # Код поправки угла В,  от 0 до 3 Wy (читается справа налево)
        popr_prib_cor_B_cod = 1
    if tu22:
        popr_prib_cor_V_cod = 6  # Код поправки угла v,  от 0 до 15 Wx, влияет на Wпутевую и Wx
        popr_prib_cor_FI_cod = 6  # Код поправки угла фи,  от 0 до 15 Wz
        # Код поправки угла В,  от 0 до 3 Wy (читается справа налево)
        popr_prib_cor_B_cod = 2
    if IL78m90a:
        # Код поправки угла v,  от 0 до 15 Wx, влияет на Wпутевую и Wx (читается справа налево)
        popr_prib_cor_V_cod = 7
        popr_prib_cor_FI_cod = 15  # Код поправки угла фи,  от 0 до 15 Wz
        # Код поправки угла В,  от 0 до 3 Wy (читается справа налево)
        popr_prib_cor_B_cod = 1
    if IL76md90a:
        # Код поправки угла v,  от 0 до 15 Wx, влияет на Wпутевую и Wx (читается справа налево)
        popr_prib_cor_V_cod = 6
        popr_prib_cor_FI_cod = 15  # Код поправки угла фи,  от 0 до 15 Wz
        # Код поправки угла В,  от 0 до 3 Wy (читается справа налево)
        popr_prib_cor_B_cod = 1
    if tu160:  # 70m
        # Код поправки угла v,  от 0 до 15 Wx, влияет на Wпутевую и Wx (читается справа налево)
        popr_prib_cor_V_cod = 6
        popr_prib_cor_FI_cod = 10  # Код поправки угла фи,  от 0 до 15 Wz
        # Код поправки угла В,  от 0 до 3 Wy (читается справа налево)
        popr_prib_cor_B_cod = 2

    # вывод ошибок
    b_sravnenie_rasch_s_pnk = True  # сравнение данных КБТИ с  выдаваемыми в пнк
    # обычно они не нужны, сравнение расч данных с данными КБТИ
    b_sravnenie_rasch_s_kbti = True
    b_sravnenie_pnk_s_rasch = True  # сравнение расч данных с данными, выдаваемыми в пнк

    koef_Wx_PNK = 0.997
    koef_Wz_PNK = 1.005  # 0.935
    koef_Wy_PNK = 1.038

    if True:
        koef_Wx_PNK = 1
        koef_Wz_PNK = 1
        koef_Wy_PNK = 1

    koef_for_intervals = {
        # макс разница, макс значение
        'tang': [4, 10],
        # макс разница, макс значение
        'kren': [1.4, 10],
        # макс разница, макс значение
        'h': [20, 200],
        # макс отношение, макс значение,усредение до, усреднение в моменте
        'wx': [0.025, 200, 150, 50]
    }

    def __init__(self, file) -> None:
        self.filepath = file
        self.fly = df.Datas(self.filepath)
        self.data = None
        self.data_calculated = False

    def load_txt(self):
        data_from_file = self.fly.load_txt()
        self.data = data_from_file
        self.data_calculated = self.check_calculated()

    def load_csv(self):
        data_from_file = self.fly.load_csv()
        self.data = data_from_file
        self.data_calculated = self.check_calculated()
    
    def load_parquet(self):
        data_from_file = self.fly.load_parquet()
        self.data = data_from_file
        self.data_calculated = self.check_calculated()

    def load_pytnon_script(self, filepath):
        data_from_script = self.fly.load_python(filepath)
        return data_from_script

    def save_python_sript(self, filepath, data):
        self.fly.save_python(filepath, data)

    def set_calculate_data(self, plane_corr, koef_Wxyz_PNK, corr_kkt):
        #TODO реализовать проверку на недостающие данные для расчета
        need_headers = {'name', 'DIS_Wx', 'DIS_Wy', 'DIS_Wz', 'I1_Kren', 
                        'I1_Tang', 'I1_KursI', 'JVD_VN', 'JVD_VE', 'JVD_Vh'}
        if self.data is None or not need_headers.issubset(self.data.columns):
            raise ValueError('Wrong data')
        self.worker = dc.Mathematical(self.data)
        self.worker.apply_coefficient_w_diss(
            wx=koef_Wxyz_PNK['koef_Wx_PNK'], 
            wz=koef_Wxyz_PNK['koef_Wz_PNK'], 
            wy=koef_Wxyz_PNK['koef_Wy_PNK'])
        self.worker.calc_angles(
            kren=corr_kkt['kren_correct'], 
            tang=corr_kkt['tang_correct'], 
            kurs=corr_kkt['kurs_correct'])
        self.worker.calc_wg_kbti(plane_corr['k'], plane_corr['k1'])
        self.worker.calc_wc_kbti()
        self.worker.calc_wp()
        self.data = self.worker.get_data()
        self.data_calculated = True

    def save_report(self, filepath, string):
        self.worker = dc.Mathematical(self.data)
        if string == '':
            intervals = self.worker.get_intervals(self.koef_for_intervals)
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
        map = dm.Map(data_for_map)
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

