from services.localstack.s3_service import S3Service


class S3Controller:
    """
    Orquestra operações de S3 no LocalStack.
    """
    def __init__(self, port_provider: callable):
        self.service = S3Service(port_provider)

    def list_buckets(self) -> list:
        try:
            return self.service.list_buckets()
        except Exception as e:
            raise RuntimeError(f"Erro ao listar buckets S3: {e}")

    def create_bucket(self, name: str) -> None:
        try:
            self.service.create_bucket(name)
        except Exception as e:
            raise RuntimeError(f"Erro ao criar bucket S3: {e}")

    def delete_bucket(self, name: str) -> None:
        try:
            self.service.delete_bucket(name)
        except Exception as e:
            raise RuntimeError(f"Erro ao excluir bucket S3: {e}")

    def list_objects(self, bucket: str) -> list:
        try:
            return self.service.list_objects(bucket)
        except Exception as e:
            raise RuntimeError(f"Erro ao listar objetos S3: {e}")

    def upload_object(self, bucket: str, file_path: str, key: str) -> None:
        try:
            self.service.upload_object(bucket, file_path, key)
        except Exception as e:
            raise RuntimeError(f"Erro ao fazer upload para S3: {e}")

    def download_object(self, bucket: str, key: str, dest: str) -> None:
        try:
            self.service.download_object(bucket, key, dest)
        except Exception as e:
            raise RuntimeError(f"Erro ao fazer download de S3: {e}")

    def delete_object(self, bucket: str, key: str) -> None:
        """
        Exclui o objeto especificado dentro de um bucket.
        """
        try:
            self.service.delete_object(bucket, key)
        except Exception as e:
            raise RuntimeError(f"Erro ao excluir objeto S3: {e}")