import docker

class LocalStackService:
    """
    Gerencia apenas o container do LocalStack via Docker SDK.
    """
    def __init__(self):
        self.client = docker.from_env()
        self.container = None

    def start(self, host_port: int = 4566):
        """
        Inicia o container do LocalStack na porta informada, adicionando extra_hosts
        para mapear 'localhost' e 'host.docker.internal' ao gateway do Docker Host,
        e removendo em seguida os mapeamentos padrão gerados pelo Docker.
        """
        # Inicializa o container com extra_hosts para redirecionar ao gateway
        self.container = self.client.containers.run(
            "localstack/localstack:latest",
            detach=True,
            name="localstack_chatbot",
            remove=True,
            environment={"LAMBDA_EXECUTOR": "docker"},
            ports={"4566/tcp": host_port},
            extra_hosts={
                "localhost": "host-gateway",
                "host.docker.internal": "host-gateway"
            }
        )
        self.container.reload()
        self.container.exec_run("sh -c \"sed -i '/^127\\.0\\.0\\.1[[:space:]]\\+localhost/d' /etc/hosts\"")
        self.container.exec_run("sh -c \"sed -i '/^::1[[:space:]]\\+localhost/d' /etc/hosts\"")
        return self.container

    def stop(self) -> None:
        """
        Para o container LocalStack obtido pelo nome 'localstack_chatbot'.
        """
        try:
            container = self.client.containers.get("localstack_chatbot")
            container.stop()
        except docker.errors.NotFound:
            pass
        finally:
            self.container = None

    def is_running(self) -> bool:
        """
        Verifica se o container LocalStack está ativo.
        """
        try:
            c = self.client.containers.get("localstack_chatbot")
            return c.status == "running"
        except docker.errors.NotFound:
            return False