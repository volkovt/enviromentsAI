import os
from io import BytesIO
import zipfile
import boto3
import json

class LambdaService:
    """
    Serviço de baixo-nível para operações de AWS Lambda no LocalStack.
    """
    def __init__(self, host_port: callable):
        self.get_port = host_port

    def _client(self):
        port = self.get_port()
        return boto3.client(
            'lambda',
            endpoint_url=f'http://localhost:{port}',
            aws_access_key_id='test',
            aws_secret_access_key='test',
            region_name='us-east-1'
        )

    def _package_directory(self, directory_path: str) -> bytes:
        buf = BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
            for root, _, files in os.walk(directory_path):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    archive_name = os.path.relpath(filepath, start=directory_path)
                    z.write(filepath, archive_name)
        buf.seek(0)
        return buf.read()

    def list_functions(self) -> list:
        """
        Lista nomes de funções Lambda existentes.
        """
        client = self._client()
        resp = client.list_functions()
        return [f['FunctionName'] for f in resp.get('Functions', [])]

    def deploy(self, function_name: str, directory_path: str) -> None:
        """
        Cria ou atualiza o código da função Lambda.
        """
        client = self._client()
        zip_bytes = self._package_directory(directory_path)
        try:
            client.create_function(
                FunctionName=function_name,
                Runtime='python3.8',
                Role='arn:aws:iam::000000000000:role/lambda-role',
                Handler='lambda_function.lambda_handler',
                Code={'ZipFile': zip_bytes},
                Publish=True
            )
        except client.exceptions.ResourceConflictException:
            client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_bytes,
                Publish=True
            )

    def invoke(self, function_name: str, payload: dict = None) -> str:
        """
        Invoca a função Lambda e retorna o resultado em string.
        """
        client = self._client()
        if payload is None:
            payload = {}
        resp = client.invoke(
            FunctionName=function_name,
            Payload=json.dumps(payload)
        )
        result = resp['Payload'].read().decode()
        return result

    def delete_function(self, function_name: str) -> None:
        """
        Exclui a função Lambda especificada.
        """
        client = self._client()
        client.delete_function(FunctionName=function_name)

    def get_configuration(self, function_name: str) -> dict:
        client = self._client()
        return client.get_function_configuration(FunctionName=function_name)