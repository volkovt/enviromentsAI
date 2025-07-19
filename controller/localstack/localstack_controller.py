import docker

from services.localstack.localstack_service import LocalStackService

class LocalStackController:
    """
    Orquestra start/stop do container LocalStack.
    """
    def __init__(self, port_provider: callable):
        self.service = LocalStackService()
        self.get_port = port_provider

    def start(self):
        port = self.get_port()
        try:
            return self.service.start(port)
        except docker.errors.DockerException as e:
            raise RuntimeError(f"Não foi possível iniciar o LocalStack: {e}")

    def stop(self):
        try:
            self.service.stop()
        except docker.errors.DockerException as e:
            raise RuntimeError(f"Não foi possível parar o LocalStack: {e}")

    def is_running(self) -> bool:
        try:
            return self.service.is_running()
        except docker.errors.DockerException as e:
            raise RuntimeError(f"Erro ao verificar status do LocalStack: {e}")