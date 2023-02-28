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
        return pd.read_csv(filepath, sep=cls._get_sep(filepath),
                           encoding=cls._get_enc(filepath), skiprows=[1])

    @staticmethod
    def _get_sep(filepath) -> str:
        return '\t' if '.txt' in filepath else ','

    @staticmethod
    def _get_enc(filepath) -> str:
        with open(filepath, 'br') as input:
            return cd.detect(input.read(1000))['encoding']

    @staticmethod
    def write_xlsx(data: pd.DataFrame, filepath: str) -> None:
        data.to_excel(filepath, index=False)

    #TODO изменить с новым форматом данных
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
    def check_adr(data: dict) -> bool:
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
    def _convert_to_int(byte_num: bytes, koef: float = 1) -> int:
        '''Метод конвертации байткода (hex) в десятичную систему'''
        result = int.from_bytes(byte_num[::-1],
                                byteorder='big',
                                signed=True) * koef
        return result
    
    @classmethod
    def _convert_to_bin(cls, byte_num: int, koef: float, length: int) -> str:
        '''Метод конвертации байткода (hex) в двоичную систему'''
        int_number = cls._convert_to_int(byte_num, koef)
        result = bin(int_number)[2:].zfill(length)
        return result

    @classmethod
    def _unpack_elem(cls, byte_num: bytes, j_elem: dict):
        '''Метод распаковки элемента'''
        name = j_elem['name']
        koef = j_elem['koef']
        type = j_elem['type']
        if type == 'int':
            return cls._convert_to_int(byte_num, koef)
        if type == 'pr':
            return cls._convert_to_bin(byte_num, koef, j_elem['length'])

        raise ValueError(f'Unknown type in json: {name}, {type}, {j_elem["position"]}')


    @staticmethod
    def _unpack_group(value, members: list, data: dict):
        '''Метод распаковки группы'''
        for member in sorted(members, key=lambda x: x['position']):
            if member['length'] is None:
                continue
            name = member['name']
            length = member['length']
            data[name].append(value[:length])
            value = value[length:]

    @classmethod
    def _unpack_string(cls, byte_str: bytes, j_elems: dict, data: dict) -> None:
        '''
        Метод распаковки строки байткода
        0-3 байт - время
        4-5 байт - контрольная сумма
        6-9 байт - нулевые
        10-41 байт - данные
        '''
        if j_elems['ks'] != byte_str[4:6][::-1].hex():
            return
        data['time'].append(
            cls._convert_to_int(byte_str[:4], j_elems['time_koef']) * 0.001
        ) # 0.001 коэффициент подобранный именно для времени
        byte_str = byte_str[10:]
        for elem in sorted(j_elems['data_info'], key=lambda x: x['position']):
            if elem['length'] is None:
                continue
            
            length = elem['length'] // 8
            byte_num = byte_str[:length]
            value = cls._unpack_elem(byte_num, elem)
            byte_str = byte_str[length:]
            if not elem['group']:
                data[elem['name']].append(value)
            else:
                cls._unpack_group(value, elem['members'], data)
                
    @classmethod
    def load_pdd(cls, pddfilepath: str, json_filepath: str) -> dict:
        '''
        Метод считывание данных из файла pdd по 42 байта.
        '''
        j_data = cls.load_json(json_filepath)
        result = {}
        result['name'] = j_data['name']
        result['adr'] = {adr['adr_name']:defaultdict(list) for adr in j_data['adr']}
        with open(pddfilepath, 'rb') as file:
            string = file.read(42)
            while string:
                for elem in j_data['adr']:
                    cls._unpack_string(string, elem, result['adr'][elem['adr_name']])
                string = file.read(42)
        result['adr'] = {key: pd.DataFrame(value) for key, value in result['adr'].items()}
        return result