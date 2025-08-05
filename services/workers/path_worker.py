import logging
import requests
from PyQt5.QtCore import QThread, pyqtSignal

from interface.environment_variables import EnvironmentVariable

logger = logging.getLogger("PathWorker")

class PathWorker(QThread):
    success  = pyqtSignal(object)
    error    = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, path: str, vars_list: list[EnvironmentVariable]):
        super().__init__()
        self.path      = path
        self.vars_list = vars_list

    def run(self):
        try:
            parts   = [p.strip() for p in self.path.split(".") if p.strip()]
            var_name = parts[0]

            var = next((v for v in self.vars_list if v.name == var_name), None)
            if var is None:
                raise ValueError(f"Variável '{var_name}' não encontrada")
            if not var.enabled:
                raise ValueError(f"Variável '{var_name}' está desabilitada")


            if var.type == "static":
                data = var.value
            elif var.type == "http":
                resp = requests.request(
                    method=var.method or "GET",
                    url=var.url,
                    params=var.params,
                    headers=var.headers,
                    data=var.body.encode("utf-8") if var.body else None,
                    timeout=10
                )
                resp.raise_for_status()
                try:
                    data = resp.json()
                except ValueError:
                    data = resp.text
            else:
                raise ValueError(f"Tipo '{var.type}' não suportado")

            for key in parts[1:]:
                if isinstance(data, dict) and key in data:
                    data = data[key]
                else:
                    raise KeyError(f"Chave '{key}' não encontrada em '{data}'")

            self.success.emit(data)
        except Exception as e:
            logger.error(f"[PathWorker] erro ao resolver '{self.path}': {e}")
            self.error.emit(str(e))
        finally:
            self.finished.emit()