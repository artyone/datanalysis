import pandas as pd
import chardet as cd
import json as js
from collections import defaultdict


class Datas(object):
    '''
    Класс модели для работы с файлами.
    '''
    def __init__(self) -> None:
        pass
    
    @classmethod
    def load_txt(cls, filepath) -> pd.DataFrame:
        return pd.read_csv(filepath, sep=cls.get_sep(filepath),
                           encoding=cls.get_enc(filepath), skiprows=[1])

    @staticmethod
    def get_sep(filepath) -> str:
        return '\t' if '.txt' in filepath else ','

    @staticmethod
    def get_enc(filepath) -> str:
        with open(filepath, 'br') as input:
            return cd.detect(input.read(1000))['encoding']

    @staticmethod
    def write_xlsx(data: pd.DataFrame, filepath: str) -> None:
        data.to_excel(filepath, index=False)

    @staticmethod
    def write_parquet(data: pd.DataFrame, filepath: str):
        data.to_parquet(filepath)

    @staticmethod
    def write_csv(data: pd.DataFrame, filepath: str):
        data.to_csv(filepath, index=False)

    @staticmethod
    def load_parquet(filepath):
        return pd.read_parquet(filepath)

    @staticmethod
    def load_csv(filepath):
        return pd.read_csv(filepath)

    @staticmethod
    def load_python(filepath):
        with open(filepath, 'r', encoding='utf8') as file:
            return file.read()

    @staticmethod
    def load_json(filepath):
        with open(filepath, 'r', encoding='utf8') as file:
            return js.load(file)

    @staticmethod
    def save_python(filepath, data):
        with open(filepath, 'w', encoding='utf8') as file:
            file.write(data)

    @staticmethod
    def save_json(filepath, data):
        with open(filepath, 'w', encoding='utf-8') as file:
            js.dump(data, file)

    @staticmethod
    def check_adr(data: dict):
        '''
        Метод проверки словаря, загруженного из json файла.
        Так как 10 байт для всех явлюятся обязательными и одинаковыми,
        то проверка осуществляется только, что данных в словаре не более
        32 байт
        '''
        summ = sum(elem['length'] for elem in data['data_info'])
        if summ < 33:
            return True
        return False

    @staticmethod
    def convert_to_dec(bytecode, koef):
        '''Метод конвертации байткода в 10ичную систему'''
        result = int.from_bytes(bytecode[::-1],
                                byteorder='big',
                                signed=True) * koef
        return result

    @classmethod
    def unpack_string(cls, bytedata, j_elem, data):
        '''
        Метод распаковки строки байткода
        0-3 байт - время
        4-5 байт - контрольная сумма
        6-9 байт - нулевые
        10-41 байт - данные
        '''
        if j_elem['ks'] != bytedata[4:6][::-1].hex():
            return
        data['time'].append(
            cls.convert_to_dec(bytedata[:4], j_elem['time_koef']) * 0.001
        ) # 0.001 коэффициент подобранный именно для времени
        bytedata = bytedata[10:]
        for value in sorted(j_elem['data_info'], key=lambda x: x['position']):
            if not value['group'] and value['length'] is not None:
                name = value['name']
                length = value['length'] // 8
                koef = value['koef']
                data[name].append(cls.convert_to_dec(bytedata[:length], koef))
                bytedata = bytedata[length:]

    @classmethod
    def load_pdd(cls, pddfilepath, json_filepath):
        '''
        Метод считывание данных из файла pdd по 42 байта.
        '''
        j_data = cls.load_json(json_filepath)
        result = {adr['adr']: defaultdict(list) for adr in j_data}
        with open(pddfilepath, 'rb') as file:
            string = file.read(42)
            while string:
                for elem in j_data:
                    cls.unpack_string(string, elem, result[elem['adr']])
                string = file.read(42)
        return {key: pd.DataFrame(value) for key, value in result.items()}