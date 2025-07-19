import boto3

class S3Service:
    """
    Serviço de baixo-nível para operações de S3 no LocalStack.
    """
    def __init__(self, host_port: callable):
        self.get_port = host_port

    def _client(self):
        port = self.get_port()
        return boto3.client(
            "s3",
            endpoint_url=f"http://localhost:{port}",
            region_name="us-east-1",
            aws_access_key_id="test",
            aws_secret_access_key="test"
        )

    def list_buckets(self) -> list:
        resp = self._client().list_buckets()
        return [b["Name"] for b in resp.get("Buckets", [])]

    def create_bucket(self, name: str) -> None:
        self._client().create_bucket(Bucket=name)

    def delete_bucket(self, name: str) -> None:
        self._client().delete_bucket(Bucket=name)

    def list_objects(self, bucket: str) -> list:
        resp = self._client().list_objects_v2(Bucket=bucket)
        return [o["Key"] for o in resp.get("Contents", [])]

    def upload_object(self, bucket: str, file_path: str, key: str) -> None:
        self._client().upload_file(Filename=file_path, Bucket=bucket, Key=key)

    def download_object(self, bucket: str, key: str, dest: str) -> None:
        self._client().download_file(Bucket=bucket, Key=key, Filename=dest)

    def delete_object(self, bucket: str, key: str) -> None:
        """
        Exclui o objeto especificado dentro de um bucket.
        """
        self._client().delete_object(Bucket=bucket, Key=key)