import boto3

class SecretManagerService:
    """
    Serviço de baixo-nível para operações de Secrets Manager no LocalStack.
    """
    def __init__(self, host_port: callable):
        self.get_port = host_port

    def _client(self):
        port = self.get_port()
        return boto3.client(
            "secretsmanager",
            endpoint_url=f"http://localhost:{port}",
            region_name="us-east-1",
            aws_access_key_id="test",
            aws_secret_access_key="test"
        )

    def list_secrets(self) -> list:
        resp = self._client().list_secrets()
        return [{"Name": s["Name"], "ARN": s.get("ARN")} for s in resp.get("SecretList", [])]

    def create_secret(self, name: str, secret_value: str) -> str:
        resp = self._client().create_secret(Name=name, SecretString=secret_value)
        return resp["ARN"]

    def get_secret_value(self, secret_id: str) -> str:
        resp = self._client().get_secret_value(SecretId=secret_id)
        return resp.get("SecretString", "")

    def update_secret(self, secret_id: str, secret_value: str) -> str:
        resp = self._client().put_secret_value(SecretId=secret_id, SecretString=secret_value)
        return resp["VersionId"]

    def delete_secret(self, secret_id: str, recovery_window_days: int = 7) -> dict:
        resp = self._client().delete_secret(SecretId=secret_id, RecoveryWindowInDays=recovery_window_days)
        return resp
