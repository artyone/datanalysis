import data_calculate as dc
import data_map as dm
import data_file as df

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
        self.data_from_file = self.set_data_from_file(self.filepath)
        self.data_calculate = self.set_calculate_data()

    def set_data_from_file(self, filepath):
        self.fly = df.Datas(filepath)
        try:
            data_from_file = self.fly.get_data()
            return data_from_file
        except Exception as error:
            print('Ошибка чтения файла\n', error)
            exit()

    def set_calculate_data(self):
        if self.data_from_file is None:
            raise Exception('Data must be not none')
        self.worker = dc.Mathematical(self.data_from_file)
        self.worker.apply_coefficient_w_diss(
            wx=self.koef_Wx_PNK, wz=self.koef_Wz_PNK, wy=self.koef_Wy_PNK)
        self.worker.calc_angles(kren=self.kren_correct,
                                tang=self.tang_correct, kurs=self.kurs_correct)
        self.worker.calc_wg_kbti(tu22=self.tu22)
        self.worker.calc_wc_kbti()
        self.worker.calc_wp()
        return self.worker.get_data()

    def get_intervals(self):
        # intervals = self.worker.get_intervals(self.koef_for_intervals)
        intervals = '25475-25952,29000-29451,30450-30883,36900-37432,37432-37967,37967-38320,47400-47921,47921-48440,48440-48960'
        intervals = [i.split('-') for i in intervals.split(',')]
        intervals = [(int(x), int(y)) for x, y in intervals]
        data_result = self.worker.get_calculated_data(intervals)
        try:
            self.fly.write_xlsx(data_result, '26122022_ДИСС_по_эталону.xlsx')
        except Exception as e:
            print('Ошибка записи файла\n', e)
            exit()

    def save_map(self, filepath, jvd_h_min='', decimation=''):
        if self.data_calculate is None:
            raise Exception('Data must be not none')
        if decimation == '':
            decimation = 1
        if jvd_h_min == '':
            jvd_h_min = 0
        map = dm.Map(self.data_calculate.loc
                     [(self.data_calculate.JVD_H > float(jvd_h_min))
                      & (self.data_calculate.name % float(decimation) == 0),
                      ['name', 'latitude', 'longitude', 'JVD_H']])
        map.get_map()
        map.save_map(filepath)

    def get_data_from_file(self):
        return self.data_from_file

    def get_data_calculate(self):
        return self.data_calculate


# new = Control('26122022_ДИСС_по_эталону.txt')
# new.save_map('26122022_ДИСС_по_эталону.html', '100', '20')
