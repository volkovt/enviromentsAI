from services.localstack.sqs_service import SQSService


class SQSController:
    """
    Orquestra operações de SQS no LocalStack.
    """
    def __init__(self, port_provider: callable):
        self.service = SQSService(port_provider)

    def list_queues(self) -> list:
        try:
            return self.service.list_queues()
        except Exception as e:
            raise RuntimeError(f"Erro ao listar filas SQS: {e}")

    def create_queue(self, name: str) -> str:
        try:
            return self.service.create_queue(name)
        except Exception as e:
            raise RuntimeError(f"Erro ao criar fila SQS: {e}")

    def delete_queue(self, url: str) -> None:
        try:
            self.service.delete_queue(url)
        except Exception as e:
            raise RuntimeError(f"Erro ao excluir fila SQS: {e}")

    def send_message(self, url: str, body: str) -> str:
        try:
            return self.service.send_message(url, body)
        except Exception as e:
            raise RuntimeError(f"Erro ao enviar mensagem SQS: {e}")

    def receive_messages(self, url: str, max_number: int = 10, consume: bool = False) -> list:
        try:
            return self.service.receive_messages(url, max_number, consume)
        except Exception as e:
            raise RuntimeError(f"Erro ao receber mensagens SQS: {e}")
