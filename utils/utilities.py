import os
import sys
from datetime import date, datetime
from functools import lru_cache


@lru_cache(maxsize=1)
def get_style_sheet(file_path: str = "styles/app_styles.qss") -> str:
    """
    Carrega o stylesheet QSS a partir de um arquivo.

    Se o aplicativo estiver empacotado (frozen), o caminho base será sys._MEIPASS;
    caso contrário, usa o diretório atual.

    :param file_path: Caminho relativo para o arquivo QSS.
    :return: Conteúdo do stylesheet ou string vazia se não encontrado.
    """
    try:
        if getattr(sys, 'frozen', False):
            BASE_PATH = sys._MEIPASS
            print('Base path:', BASE_PATH)
        else:
            BASE_PATH = os.path.dirname(os.path.abspath(__file__))
            BASE_PATH = os.path.join(BASE_PATH, "..")

        full_path = os.path.join(os.path.normpath(BASE_PATH), os.path.normpath(file_path))
        print(f"Loading stylesheet from: {full_path}")
        with open(full_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        print(f"Stylesheet file not found: {file_path}")
        return ""
    except UnicodeDecodeError as e:
        print(f"Error reading stylesheet: {e}")
        return ""

def ensure_date(val):
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val).date()
        except Exception:
            return date.today()
    return date.today()