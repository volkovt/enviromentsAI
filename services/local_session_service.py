# data/services/local/session_service.py

import json
import os
from threading import Lock

class LocalSessionService:
    """
    Serviço simples para CRUD de itens numa lista persistida em JSON.
    Usa file‐lock para evitar condições de corrida.
    """
    def __init__(self, file_path: str | None = None):
        if file_path:
            self.file_path = file_path
        else:
            self.file_path = "chatbot_tasks.json"
        self.lock = Lock()
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def read_all(self) -> list[dict]:
        with self.lock, open(self.file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def write_all(self, items: list[dict]):
        tmp = self.file_path + ".tmp"
        with self.lock, open(tmp, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, default=str)
        os.replace(tmp, self.file_path)

    def scan(self) -> list[dict]:
        """Retorna todas as tasks."""
        return self.read_all()

    def put_item(self, item: dict):
        """Adiciona uma nova task."""
        data = self.read_all()
        data.append(item)
        self.write_all(data)

    def update_item(self, item_id: str, item: dict):
        """Substitui a task cujo id bate com item_id."""
        data = self.read_all()
        data = [item if i.get("id")==item_id else i for i in data]
        self.write_all(data)

    def delete_item(self, item_id: str):
        """Remove a task pelo id."""
        data = self.read_all()
        data = [i for i in data if i.get("id")!=item_id]
        self.write_all(data)

    def _get_pref_file(self):
        return self.file_path + ".prefs.json"

    def write_session_data(self, key, value):
        prefs_file = self._get_pref_file()
        try:
            if not os.path.exists(prefs_file):
                data = {}
            else:
                with open(prefs_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            data[key] = value
            with open(prefs_file, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"[LocalSessionService] Erro ao salvar preferências: {e}")

    def read_session_data(self, key, default=None):
        prefs_file = self._get_pref_file()
        try:
            if not os.path.exists(prefs_file):
                return default
            with open(prefs_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get(key, default)
        except Exception as e:
            print(f"[LocalSessionService] Erro ao ler preferências: {e}")
            return default
