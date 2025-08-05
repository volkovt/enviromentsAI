import json
import os
import logging
from threading import Lock
from typing import List

from interface.environment_variables import EnvironmentVariable

logger = logging.getLogger("VariableService")

class VariableService:
    def __init__(self, file_path="environment_variables.json"):
        self.file_path = file_path
        self.lock = Lock()
        try:
            self._ensure_file()
        except Exception as e:
            logger.error(f"Falha ao garantir arquivo de variáveis: {e}")

    def _ensure_file(self):
        try:
            if not os.path.exists(self.file_path):
                with open(self.file_path, "w", encoding="utf-8") as f:
                    json.dump([], f)
                logger.info(f"Arquivo criado: {self.file_path}")
        except Exception as e:
            logger.error(f"Erro ao criar arquivo de variáveis: {e}")

    def load_all(self) -> List[EnvironmentVariable]:
        try:
            with self.lock, open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            vars_list = [EnvironmentVariable(**item) for item in data]
            return vars_list
        except Exception as e:
            logger.error(f"Falha ao carregar variáveis de {self.file_path}: {e}")
            return []

    def save_all(self, vars: List[EnvironmentVariable]):
        tmp = self.file_path + ".tmp"
        try:
            with self.lock, open(tmp, "w", encoding="utf-8") as f:
                json.dump([v.__dict__ for v in vars], f, indent=2, ensure_ascii=False)
            os.replace(tmp, self.file_path)
            #logger.info(f"{len(vars)} variáveis salvas em {self.file_path}")
        except Exception as e:
            logger.error(f"Falha ao salvar variáveis em {self.file_path}: {e}")
