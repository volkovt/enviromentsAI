import docker

from services.localstack.export_service import ExportService
from services.localstack.localstack_service import LocalStackService

class LocalStackController:
    """
    Orquestra start/stop do container LocalStack.
    """
    def __init__(self, port_provider: callable):
        self.service = LocalStackService()
        self.export_service = None
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

    def export_scripts(self) -> str:
        try:
            if not self.is_running():
                raise RuntimeError("LocalStack não está rodando. Inicie o serviço antes de exportar scripts.")
            if self.export_service is None:
                self.export_service = ExportService(self.get_port)
                return self.export_service.export_scripts()
            else:
                return self.export_service.export_scripts()
        except Exception as e:
            raise RuntimeError(f"Erro ao exportar scripts: {e}")