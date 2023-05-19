import sys
import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication, QMainWindow
import json as js
import pandas as pd
from functools import lru_cache
from time import perf_counter_ns
import struct
import numpy as np
import pickle
import gzip




def load_json(filepath: str):
    with open(filepath, 'r', encoding='utf8') as file:
        return js.load(file)


def graph(df: pd.DataFrame, column):

    filtered_df = df.dropna(subset=['time', column]).reset_index()

    x = filtered_df.time.to_list()
    y = filtered_df[column].to_list()

    app = QApplication(sys.argv)
    win = QMainWindow()

    plot_widget = pg.PlotWidget(title="freq", background='white')
    plot_widget.plot(x, y, pen='r')
    win.setCentralWidget(plot_widget)
    win.show()
    sys.exit(app.exec_())

def get_mask_shift_from_field(size):
    # получаем маску и смещение для побитового сравнения и получения данных
    start, stop = [int(i) for i in size.split(':')]
    number_mask = int('1' * (stop - start + 1), 2)
    shift = start
    return number_mask, shift

def get_unpacked_data_list(filepath):
    with open(filepath, 'rb') as file:
        string = file.read()
        unpacked_data_list = [
            i for i in struct.iter_unpack('>IH4x16H', string)]
        unpacked_data_list = np.array(unpacked_data_list)
    return unpacked_data_list


def unpack_element(byteswap, field_data, data_source: np.array):
    position = field_data['position'] + 2
    koef = field_data['koef']
    size = field_data['size']
    type = field_data['type']
    mask, shift = get_mask_shift_from_field(size)
    data_column = data_source[:, position]
    # if type == 'uint16' or type == 'pre':
    #     data_column = data_column.astype(np.uint16)

    if type == 'int16':
        data_column = data_column.astype(np.int16)

    if not byteswap:
        data_column = data_column.byteswap()
    if mask != 65535 or shift != 0:
        masked_data = np.bitwise_and(data_column, (mask << shift))
        masked_data = np.right_shift(masked_data, shift) * koef
    else:
        masked_data = data_column
    if type == 'int8':
        masked_data = masked_data.astype(np.int8)

    return masked_data


def unpack_group(byteswap, group_info, data_source, result_data):
    if type(group_info['fields']) == list:
        for field in group_info['fields']:
            column_name = field['name']
            column = unpack_element(byteswap, field, data_source)
            result_data[column_name] = column
    else:
        mask_condition, shift_condition = get_mask_shift_from_field(
            group_info['condition_bit'])
        condition_data = (data_source[:, group_info['condition_byte'] + 2]
                          & (mask_condition << shift_condition)) >> shift_condition
        for condition, fields in group_info['fields'].items():
            condition_mask = condition_data == int(condition)
            for field in fields:
                column_name = field['name']
                column = unpack_element(byteswap, field, data_source)
                column = np.where(condition_mask, column, np.nan)
                result_data[column_name] = column


def get_filtered_data_by_checksum(checksum, source_data):
    control_sum = source_data[:, 1].astype(np.uint16).byteswap()
    control_sum_mask = control_sum == checksum
    data_list = source_data[control_sum_mask]
    return data_list


def get_time_list(koef, source):
    time_list = source[:, 0].astype(np.uint32)
    time_list = time_list.byteswap() * koef
    return time_list


def unpack_fields(byteswap, fields, data_list, result_dict):
    for field in fields:
        if 'group' in field.keys() and field['group'] == True:
            unpack_group(byteswap, field, data_list, result_dict)
        else:
            column_name = field['name']
            column = unpack_element(byteswap, field, data_list)
            result_dict[column_name] = column
    return result_dict


def unpack_adr(adr, unpacked_data_list):
    checksum = int(adr['checksum'], base=16)
    data_list = get_filtered_data_by_checksum(checksum, unpacked_data_list)
    df_dict = {}
    df_dict['time'] = get_time_list(adr['time_koef'], data_list)
    df_dict = unpack_fields(
        adr['bytes_swap'], adr['fields'], data_list, df_dict)
    return df_dict


def load_pdd(filepath_pdd, filepath_json):
    json_data = load_json(filepath_json)
    unpacked_data_list = get_unpacked_data_list(filepath_pdd)
    result_dict = {}
    result_dict['name'] = json_data['name']
    result_dict['adr'] = {}

    for adr in json_data['adr']:
        adr_data = unpack_adr(adr, unpacked_data_list)
        result_dict['adr'][adr['adr_name']] = pd.DataFrame(adr_data)

    return result_dict


start = perf_counter_ns()

json_path = r'C:\Tikhonov\datanalysis\templates\d001.json'
# json_path = r'C:\Tikhonov\datanalysis\templates\default_pnk.json'
pdd_filepath = r"C:\Users\ONT\Downloads\RES.pdd"
# pdd_filepath = r"C:\Users\ONT\Downloads\данные_инс1_дисс.pdd"


# result = load_pdd(pdd_filepath, json_path)

# with gzip.open(r'C:\Tikhonov\datanalysis\temp\123.gz', 'wb', compresslevel=1) as file:
#     pickle.dump(result, file)

with gzip.open(r'C:\Tikhonov\datanalysis\temp\123.gz', 'rb') as file:
    loaded_data = pickle.load(file)

print(loaded_data)
print(perf_counter_ns() - start, 'finish')

# print(result)
# graph(result['ADR1'], 'CH_UPF')
