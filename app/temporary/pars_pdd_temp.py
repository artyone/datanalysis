from collections import defaultdict
import sys
from typing import Any
import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication, QMainWindow
import json as js
import pandas as pd
from functools import lru_cache
from time import perf_counter_ns
import struct
import numpy as np
import pickle


def load_json(filepath: str) -> Any:
    with open(filepath, 'r', encoding='utf8') as file:
        return js.load(file)


def graph(x, y):
    app = QApplication(sys.argv)
    win = QMainWindow()
    plot_widget = pg.PlotWidget(title="freq", background='white')
    plot_widget.plot(x, y, pen='r')
    win.setCentralWidget(plot_widget)
    win.show()
    sys.exit(app.exec_())


def get_mask(fields):
    structure = list(range(0, 32, 2))
    for elem in fields:
        type = elem['type']
        offset = elem['offset']
        if type == 'int':
            mask = 'h'
        elif type == 'uint':
            mask = 'H'
        elif type == 'pre':
            mask = 'H'
            # mask += '2s'
        else:
            raise ValueError('not find type')
        index = structure.index(offset)
        structure[index] = mask
    mask = '>' + ''.join(['xx' if isinstance(i, int)
                         else i for i in structure])
    return mask


def get_mask_shift_from_field(size):
    # получаем маску и смещение для побитового сравнения и получения данных
    start, stop = [int(i) for i in size.split(':')]
    number_mask = int('1' * (stop - start + 1), 2)
    shift = start
    return number_mask, shift

def unpack_groups(json_groups, result_df):

    for group in json_groups:
        masks_shifts = np.array([get_mask_shift_from_field(
            field['size']) for field in group['fields']])
        numbers = result_df[group['name']].values
        result_list = np.zeros(
            (len(numbers), len(masks_shifts)), dtype=np.int64)
        for i, (number_mask, shift) in enumerate(masks_shifts):
            result_list[:, i] = (numbers & (number_mask << shift)) >> shift
        columns = [field['name'] for field in group['fields']]
        new_df = pd.DataFrame(result_list, columns=columns)

        result_df = pd.concat(
            [result_df, new_df], axis=1)
    return result_df

def unpack_string(byte_str: bytes, adr: dict, result_data: dict):
    # контрольная сумма всегда в 4-5 байте (5-6)
    if adr['ks'] != byte_str[4:6]:
        return
    else:
        # время всегда в первых 4 байтах (0-3)
        time = struct.unpack('<I', byte_str[:4])[0]
        # данные всегда начинаются с 11 байта (10-42)
        data_byte = byte_str[10:]
        nums = struct.unpack(adr['group_mask'], data_byte)
        result_data['main'].append((time, *nums))
        if 'additionals' in adr.keys():
            for additional in adr['additionals']:
                condition = (data_byte[additional['offset']] & (
                    additional['number_mask'] << additional['shift']
                    )) >> additional['shift']

                if condition == additional['condition']:
                    nums = struct.unpack(additional['group_mask'], data_byte)
                    result_data['additionals'][additional['condition']].append((time, *nums))


def load_pdd(pddfilepath: str, json_filepath: str) -> dict:
    # загружаем описатель из json
    j_data = load_json(json_filepath)
    # приводим данные в json в порядок
    for adr in j_data['adr']:
        adr['fields'].sort(key=lambda x: x['offset'])
        adr['group_mask'] = get_mask(adr['fields'])
        adr['ks'] = int(adr['ks'], base=16).to_bytes(
            2, byteorder='little', signed=False)
        if 'additionals' in adr.keys():
            for additional in adr['additionals']:
                additional['fields'].sort(key=lambda x: x['offset'])
                additional['group_mask'] = get_mask(additional['fields'])
                additional['number_mask'], additional['shift'] = get_mask_shift_from_field(
                    additional['condition_address'])
    # начинаем формировать словарь, результатов
    result = {}
    result['name'] = j_data['name']
    # формируем разметку результирующего словаря
    for adr in j_data['adr']:
        result['adr'] = {adr['adr_name']: {'main': []}}
        if 'additionals' in adr.keys():
            result['adr'][adr['adr_name']]['additionals'] = []
            for _ in adr['additionals']:
                result['adr'][adr['adr_name']]['additionals'].append([])
    # result['adr'] = {
    #     adr['adr_name']: {'main':[]} for adr in j_data['adr']
    # }

    #читаем файл и распаковываем строки
    with open(pddfilepath, 'rb') as file:
        string = file.read(42)
        while len(string) == 42:
            for elem in j_data['adr']:
                unpack_string(
                    string, elem, result['adr'][elem['adr_name']]
                )
            string = file.read(42)

    print(perf_counter_ns() - a, 'файл прочитан')

    #формируем основной датафрейм и добавляем к нему группы условий
    for adr in j_data['adr']:
        columns = ['time'] + [field['name'] for field in adr['fields']]
        rows = np.array(result['adr'][adr['adr_name']]['main'])
        # result['adr'][adr['adr_name']] = pd.DataFrame(
        #     data=rows, columns=columns, dtype=int)
        main_df = pd.DataFrame(
            data=rows, columns=columns, dtype=int)
        for additional in adr['additionals']:
            columns = ['time'] + [field['name'] for field in additional['fields']]
            rows = np.array(result['adr'][adr['adr_name']]['additionals'][additional['condition']])
            df_additional = pd.DataFrame(data=rows, columns=columns, dtype=int)
            main_df = pd.merge(main_df, df_additional, on='time', how='left')

        #добавить умножение коэффициенто
        main_df.time = main_df.time * 0.0001

        result['adr'][adr['adr_name']] = main_df



    print(perf_counter_ns() - a, 'дф сформированы')

    #распаковываем группы
    for adr in j_data['adr']:
        result['adr'][adr['adr_name']] = unpack_groups(
            adr['groups'], result['adr'][adr['adr_name']])


    print(perf_counter_ns() - a, 'группы обработаны')

    # a = np.array(result['adr'][adr['adr_name']]['additionals'][1])
    # graph(a[::,0], a[::,1])
        

    return result

#решить вопрос с размером

a = perf_counter_ns()


result: pd.DataFrame = load_pdd(
    r"C:\Users\ONT\Downloads\RES.pdd",
    r'C:\Tikhonov\datanalysis\templates\default_d001_v1_11.json'
)


# with open('temp/pdd_diss.pkl', 'wb') as f:

#     pickle.dump({'DISS01': result['adr']}, f, protocol=4)

result = result['adr']['ADR1']


# print(result.group_otkaz)
#print(result)
graph(result.time, result.KorrUp_ch0)
