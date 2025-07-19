from services.localstack.secret_manager_service import SecretManagerService


class SecretManagerController:
    """
    Orquestra operações de Secrets Manager e trata erros.
    """
    def __init__(self, port_provider: callable):
        self.service = SecretManagerService(port_provider)

    def list_secrets(self) -> list:
        try:
            return self.service.list_secrets()
        except Exception as e:
            raise RuntimeError(f"Erro ao listar segredos: {e}")

    def create_secret(self, name: str, value: str) -> str:
        try:
            return self.service.create_secret(name, value)
        except Exception as e:
            raise RuntimeError(f"Erro ao criar segredo: {e}")

    def get_secret_value(self, secret_id: str) -> str:
        try:
            return self.service.get_secret_value(secret_id)
        except Exception as e:
            raise RuntimeError(f"Erro ao obter valor do segredo: {e}")

    def update_secret(self, secret_id: str, value: str) -> str:
        try:
            return self.service.update_secret(secret_id, value)
        except Exception as e:
            raise RuntimeError(f"Erro ao atualizar segredo: {e}")

    def delete_secret(self, secret_id: str, recovery_window_days: int = 7) -> dict:
        try:
            return self.service.delete_secret(secret_id, recovery_window_days)
        except Exception as e:
            raise RuntimeError(f"Erro ao excluir segredo: {e}")
