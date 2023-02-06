import pandas as pd
import chardet as cd


class Datas(object):

    def __init__(self, filepath: str) -> None:
        self.filepath = filepath

    def load_txt(self) -> pd.DataFrame:
        return pd.read_csv(self.filepath, sep=self.get_sep(),
                           encoding=self.get_enc(), skiprows=[1])

    def get_sep(self) -> str:
        return '\t' if '.txt' in self.filepath else ','

    def get_enc(self) -> str | None:
        with open(self.filepath, 'br') as input:
            return cd.detect(input.read(1000))['encoding']

    def write_xlsx(self, data: pd.DataFrame, filepath: str) -> None:
        data.to_excel(filepath, index=False)

    def write_parquet(self, data: pd.DataFrame, filepath: str):
        data.to_parquet(filepath)

    def write_csv(self, data: pd.DataFrame, filepath: str):
        data.to_csv(filepath, index=False)

    def load_parquet(self):
        return pd.read_parquet(self.filepath)

    def load_csv(self):
        return pd.read_csv(self.filepath)

    def load_python(self, filepath):
        with open(filepath, 'r', encoding='utf8') as file:
            return file.read()

    def save_python(self, filepath, data):
        with open(filepath, 'w', encoding='utf8') as file:
            file.write(data)
    
