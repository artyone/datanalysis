from typing import Any, Iterable
import pandas as pd
from pandas import DataFrame, Series
from math import pi, sin, cos, atan, radians


class Mathematical(object):
    '''
    Класс основных рассчётов данных.
    d - исходные данные, которые необходимо рассчитать.
    *_acc - средние величины.
    intervals_* - интервалы, получаемые рассчетным образом.
    '''

    def __init__(self, object: DataFrame) -> None:
        self.d = object
        self.Wxc_KBTIi_acc = 0
        self.Wzc_KBTIi_acc = 0
        self.Wyc_KBTIi_acc = 0
        self.Wp_KBTIi_acc = 0
        self.Wx_DISS_PNK_acc = 0
        self.Wz_DISS_PNK_acc = 0
        self.Wy_DISS_PNK_acc = 0
        self.Wp_diss_pnki_acc = 0
        self.USkbti = 0
        self.USpnk = 0
        self.intervals_tang = [set()]
        self.intervals_kren = [set()]
        self.intervals_h = [set()]
        self.intervals_wx = [set()]

    def apply_coefficient_w_diss(self, wx: float, wz: float, wy: float) -> None:
        '''
        Метод применения коэффициентов из настроек.
        '''
        self.d['Wx_DISS_PNK'] = self.d.DIS_Wx * wx
        self.d['Wz_DISS_PNK'] = self.d.DIS_Wz * wz
        self.d['Wy_DISS_PNK'] = self.d.DIS_Wy * wy

    def calc_angles(self, kren: float, tang: float, kurs: float) -> None:
        '''
        Метод расчета углов для рассчетов.
        '''
        self.d['Kren_sin'] = self.d.I1_Kren.apply(
            lambda x: sin(radians(x + kren))
        )
        self.d['Kren_cos'] = self.d.I1_Kren.apply(
            lambda x: cos(radians(x + kren))
        )
        self.d['Tang_sin'] = self.d.I1_Tang.apply(
            lambda x: sin(radians(x + tang))
        )
        self.d['Tang_cos'] = self.d.I1_Tang.apply(
            lambda x: cos(radians(x + tang))
        )
        self.d['Kurs_sin'] = self.d.I1_KursI.apply(
            lambda x: sin(radians(x + kurs))
        )
        self.d['Kurs_cos'] = self.d.I1_KursI.apply(
            lambda x: cos(radians(x + kurs))
        )

    def calc_wg_kbti(self, k: int, k1: int) -> None:
        '''
        Метод рассчёта с учётом коэффициента k.
        '''
        self.d['Wxg_KBTIi'] = (
            self.d.JVD_VN * k * 3.6 * self.d.Kurs_cos
            + self.d.JVD_VE * k * 3.6 * self.d.Kurs_sin
        )
        self.d['Wzg_KBTIi'] = (
            - self.d.JVD_VN * k * 3.6 * self.d.Kurs_sin
            + self.d.JVD_VE * k * 3.6 * self.d.Kurs_cos
        )
        self.d['Wyg_KBTIi'] = self.d.JVD_Vh * k1 * 3.6 * self.d.Kurs_sin

    def calc_wc_kbti(self) -> None:
        '''
        Метод рассчёта данных КБТИ.
        '''
        wxg, wyg, wzg = self.d.Wxg_KBTIi, self.d.Wyg_KBTIi, self.d.Wzg_KBTIi
        tang_cos, tang_sin, kren_cos, kren_sin = (
            self.d.Tang_cos, self.d.Tang_sin, self.d.Kren_cos, self.d.Kren_sin
        )
        
        self.d['Wxc_KBTIi'] = wxg * tang_cos + wyg * tang_sin
        self.d['Wyc_KBTIi'] = (
            -wxg * tang_sin * kren_cos + wyg * tang_cos * kren_cos + wzg * kren_sin
        )
        self.d['Wzc_KBTIi'] = (
            wxg * kren_sin * tang_sin - wyg * tang_cos * kren_sin + wzg * kren_cos
        )

    def calc_wp(self) -> None:
        '''
        Метод рассчёта путевой скорости.
        '''
        self.d['Wp_KBTIi'] = (self.d.Wxc_KBTIi**2 + self.d.Wzc_KBTIi**2)**0.5
        self.d['Wp_diss_pnki'] = (self.d.Wx_DISS_PNK**2 + self.d.Wz_DISS_PNK**2)**0.5

    def _get_interval(self, start: float, stop: float) -> DataFrame:
        '''
        Метод получения интервала от старта до финиша.
        '''
        return self.d[(self.d['time'] >= start) & (self.d['time'] <= stop)]

    def _get_height(self, start: int) -> Any:
        '''
        Метод получения высоты на старте интервала, если высота есть в данных.
        '''
        if not 'JVD_H' in self.d.columns:
            return 0
        result = self.d.loc[self.d['time'] == start, 'JVD_H'].values
        if len(result) > 0:
            return result[0]
        else:
            return 0

    def _get_percent(self, x: float, y: float) -> float:
        '''
        Метод получения процентных значений.
        '''
        if x:
            return (x - y) / x * 100
        return 0


    def _get_mean(self, start: int, stop: int) -> None:
        '''
        Метод получения средних данных для отчёта.
        '''
        interval = self._get_interval(start, stop)
        
        mean_columns = ['Wxc_KBTIi', 'Wzc_KBTIi', 'Wyc_KBTIi', 'Wp_KBTIi',
                        'Wx_DISS_PNK', 'Wz_DISS_PNK', 'Wy_DISS_PNK', 'Wp_diss_pnki']
        
        for column in mean_columns:
            mean_value = interval[column].mean()
            setattr(self, f'{column}_acc', mean_value)

    def _get_us(self) -> None:
        '''
        Метод рассчёта US.
        '''
        self.USkbti = (
            atan(self.Wzc_KBTIi_acc / self.Wxc_KBTIi_acc) / pi
        ) * 180
        self.USpnk = (
            atan(self.Wz_DISS_PNK_acc / self.Wx_DISS_PNK_acc) / pi
        ) * 180
        # USdiss=(math.atan(Wzc_DISS_r_acc/Wxc_DISS_r_acc)/math.pi)*180

    def get_calculated_data(self, start_stop: Iterable) -> pd.DataFrame:
        '''
        Метод возврата данных после рассчёта.
        '''
        data = []
        headers = [
            'length', 'JVD_H', 'start', 'stop',
            'counts', 'US', 'Wp', 'Wx', 'Wz', 'Wy'
        ]
        for start, stop in start_stop:
            self._get_mean(start, stop)
            self._get_us()
            counts = stop - start
            length = round((stop - start) * self.Wp_KBTIi_acc / 3600, 3)
            height = self._get_height(start)
            US = round(self.USpnk - self.USkbti, 3)
            # USdissms=(USdiss-USkbti)
            Wp = round(self._get_percent(
                self.Wp_diss_pnki_acc, self.Wp_KBTIi_acc), 3)
            Wx = round(self._get_percent(
                self.Wx_DISS_PNK_acc, self.Wxc_KBTIi_acc), 3)
            Wz = round(self._get_percent(
                self.Wz_DISS_PNK_acc, self.Wzc_KBTIi_acc), 3)
            Wy = round(self._get_percent(
                self.Wy_DISS_PNK_acc, self.Wyc_KBTIi_acc), 3)

            data.append((length, height, start,
                              stop, counts, US, Wp, Wx, Wz, Wy))
        result = pd.DataFrame(data, columns=headers)
        return result

    def _rolling_in_the_deep(self) -> Series:
        return self.d.DIS_Wx.rolling(50).mean()

    def get_intervals(self, koef):
        '''
        Метод автоматического получения интервалов по заданным
        коэффициентам.
        '''
        data = self._get_dataframe_for_intervals(koef)
        for row in data.itertuples():
            self._get_intervals_tang(
                time=row.time,
                raz=row.Tang_raz,
                tang=row.I1_Tang,
                h=row.JVD_H,
                k=koef
            )
            self._get_intervals_kren(
                time=row.time,
                raz=row.Kren_raz,
                kren=row.I1_Kren,
                h=row.JVD_H,
                k=koef
            )
            self._get_intervals_h(
                time=row.time,
                raz=row.h_raz,
                h=row.JVD_H,
                k=koef
            )
            self._get_intervals_wx(
                time=row.time,
                wx=row.DIS_Wx,
                raz_b=row.Wx_raz_b,
                h=row.JVD_H,
                k=koef
            )
        return self._calc_intervals(
            self.intervals_kren,
            self.intervals_h,
            self.intervals_wx
        )

    def _get_dataframe_for_intervals(self, k) -> DataFrame:
        '''
        Метод формирования датафрейма для получения интервалов 
        с разными смещениями среднего и коэффициентами.
        '''
        df = self.d.loc[self.d.time % 1 == 0,
                        ['time', 'I1_Tang', 'I1_Kren', 'JVD_H', 'DIS_Wx']]
        df['Tang_mean_5'] = df.I1_Tang.rolling(5).mean().shift().bfill()
        df['Kren_mean_5'] = df.I1_Kren.rolling(5).mean().shift().bfill()
        df['h_mean_25'] = df.JVD_H.rolling(25).mean().shift().bfill()
        df['Wx_mean_b'] = df.DIS_Wx.rolling(k['wx'][2]).mean().shift().bfill()
        df['Wx_mean_i'] = (df.DIS_Wx.rolling(k['wx'][3]).mean()
                                    .shift(- (k['wx'][3] - 1)).bfill())
        df['Tang_raz'] = abs(df.I1_Tang - df.Tang_mean_5)
        df['Kren_raz'] = abs(df.I1_Kren - df.Kren_mean_5)
        df['h_raz'] = abs(df.JVD_H - df.h_mean_25)
        df['Wx_raz_b'] = abs(1 - df.Wx_mean_b / df.Wx_mean_i)
        return df

    def _get_intervals_tang(self, time, raz, tang, h, k) -> None:
        '''
        Метод получения интервалов по тангажу.
        '''
        if raz < k['tang'][0] and tang < k['tang'][1] and h > k['h'][1]:
            self.intervals_tang[-1].add(time)
        elif len(self.intervals_tang[-1]) > 0:
            self.intervals_tang.append(set())

    def _get_intervals_kren(self, time, raz, kren, h, k) -> None:
        '''
        Метод получения интервалов по крену.
        '''
        if raz < k['kren'][0] and kren < k['kren'][1] and h > k['h'][1]:
            self.intervals_kren[-1].add(time)
        elif len(self.intervals_kren[-1]) > 0:
            self.intervals_kren.append(set())

    def _get_intervals_h(self, time, raz, h, k) -> None:
        '''
        Метод получения интервалов по высоте.
        '''
        if raz < k['h'][0] and h > k['h'][1]:
            self.intervals_h[-1].add(time)
        elif len(self.intervals_kren[-1]) > 0:
            self.intervals_h.append(set())

    def _get_intervals_wx(self, time, wx, raz_b, h, k) -> None:
        '''
        Метод получения интервалов по Wx.
        '''
        if (raz_b < k['wx'][0]) and wx > k['wx'][1] and h > k['h'][1]:
            self.intervals_wx[-1].add(time)
        elif len(self.intervals_wx[-1]) > 0:
            self.intervals_wx.append(set())

    def _calc_intervals(self, *args) -> list :
        '''
        Метод получения интервалов всем параметрам.
        '''
        arr = [i for i in args[0] if len(i) >= 310]
        for i in args[1:]:
            arr = [
                k
                for set1 in arr
                for set2 in i
                if len(k := set1 & set2) >= 310
            ]

        result = [(min(i) + 15, max(i) - 5) for i in arr]
        return result

    def get_only_calculated_data_pnk(self) -> DataFrame:
        '''
        Метод получения даты.
        '''
        headers = [
            'time',
            'Wx_DISS_PNK', 'Wz_DISS_PNK', 'Wy_DISS_PNK',
            'Wxg_KBTIi', 'Wzg_KBTIi', 'Wyg_KBTIi',
            'Wxc_KBTIi', 'Wyc_KBTIi', 'Wzc_KBTIi',
            'Wp_KBTIi', 'Wp_diss_pnki'
        ]
        return self.d[headers]
