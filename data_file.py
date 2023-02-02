import pandas as pd
import chardet as cd


class Datas(object):

    def __init__(self, filepath: str) -> None:
        self.filepath = filepath

    def get_data(self) -> pd.DataFrame:
        return pd.read_csv(self.filepath, sep=self.get_sep(),
                           encoding=self.get_enc(), skiprows=[1])

    def get_sep(self) -> str:
        return '\t' if '.txt' in self.filepath else ','

    def get_enc(self) -> str | None:
        with open(self.filepath, 'br') as input:
            return cd.detect(input.read(1000))['encoding']

    def write_xlsx(self, dictionary: dict, filepath: str) -> None:
        result = pd.DataFrame(dictionary)
        result.to_excel(filepath, index=False)
