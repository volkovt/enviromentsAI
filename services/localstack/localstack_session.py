# data/services/localstack_session.py

import os
import pickle

class LocalStackSession:
    """
    Persiste o estado dos componentes do LocalStack (API Gateway, SQS, S3, etc.)
    em um arquivo local (pickle).
    """
    def __init__(self, file_path="localstack_session.pkl"):
        self.file_path = file_path
        self.data = {
            "apigateway": {
                # ID da última API selecionada
                "selected_api": None,
                # Stage padrão a usar (ex: "dev")
                "stage": "dev",
                # Último caminho de OpenAPI importado
                "last_import_file": None,
                # Qualquer outra configuração específica...
            },
            # aqui poderíamos adicionar "sqs": {...}, "s3": {...}, etc.
        }
        self._load()

    def _load(self):
        """Tenta carregar o arquivo de sessão, se existir."""
        if os.path.exists(self.file_path):
            with open(self.file_path, "rb") as f:
                try:
                    saved = pickle.load(f)
                    # mescla somente chaves existentes, para manter defaults futuros
                    for k, v in saved.items():
                        if k in self.data:
                            self.data[k].update(v)
                        else:
                            self.data[k] = v
                except Exception:
                    pass

    def save(self):
        """Grava o estado atual em disco."""
        with open(self.file_path, "wb") as f:
            pickle.dump(self.data, f)

    def get(self, key: str) -> dict:
        """Retorna o sub-dicionário para o serviço indicado (ex: 'apigateway')."""
        return self.data.get(key, {})

    def update(self, key: str, partial: dict):
        """
        Atualiza apenas as chaves passadas em `partial` dentro de self.data[key]
        e persiste em disco imediatamente.
        """
        if key not in self.data:
            self.data[key] = {}
        self.data[key].update(partial)
        self.save()

    def get_api_session(self, api_id: str) -> dict:
        """
        Retorna o dicionário de sessão para a API `api_id`,
        contendo 'last_import_file' e 'endpoints'.
        """
        apis = self.data.setdefault("apigateway", {})
        sessions = apis.setdefault("sessions", {})
        return sessions.setdefault(api_id, {})

    def update_api_session(self, api_id: str, partial: dict) -> None:
        """
        Merge de `partial` no registro de sessão da API `api_id`
        e persiste em disco.
        """
        apis = self.data.setdefault("apigateway", {})
        sessions = apis.setdefault("sessions", {})
        api_sess = sessions.get(api_id, {})
        api_sess.update(partial)
        sessions[api_id] = api_sess
        self.save()