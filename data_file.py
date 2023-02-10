import pandas as pd
import chardet as cd
import json as js


class Datas(object):

    def __init__(self) -> None:
        pass

    def load_txt(self, filepath) -> pd.DataFrame:
        return pd.read_csv(filepath, sep=self.get_sep(filepath),
                           encoding=self.get_enc(filepath), skiprows=[1])

    def get_sep(self, filepath) -> str:
        return '\t' if '.txt' in filepath else ','

    def get_enc(self, filepath) -> str:
        with open(filepath, 'br') as input:
            return cd.detect(input.read(1000))['encoding']

    def write_xlsx(self, data: pd.DataFrame, filepath: str) -> None:
        data.to_excel(filepath, index=False)

    def write_parquet(self, data: pd.DataFrame, filepath: str):
        data.to_parquet(filepath)

    def write_csv(self, data: pd.DataFrame, filepath: str):
        data.to_csv(filepath, index=False)

    def load_parquet(self, filepath):
        return pd.read_parquet(filepath)

    def load_csv(self, filepath):
        return pd.read_csv(filepath)

    def load_python(self, filepath):
        with open(filepath, 'r', encoding='utf8') as file:
            return file.read()

    def load_json(self, filepath):
        with open(filepath, 'r', encoding='utf8') as file:
            return js.load(file)

    def save_python(self, filepath, data):
        with open(filepath, 'w', encoding='utf8') as file:
            file.write(data)

    def save_json(self, filepath, data):
        with open(filepath, 'w', encoding='utf-8') as file:
            js.dump(data, file)
