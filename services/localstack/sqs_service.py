import logging

import boto3
from botocore.config import Config

logger = logging.getLogger("[SQSService]")

class SQSService:
    """
    Serviço de baixo-nível para operações de SQS no LocalStack.
    """
    def __init__(self, host_port: callable):
        """
        host_port: função que retorna a porta configurada para o LocalStack.
        """
        self.get_port = host_port

    def _client(self):
        port = self.get_port()
        return boto3.client(
            "sqs",
            endpoint_url=f"http://localhost:{port}",
            region_name="us-east-1",
            aws_access_key_id="test",
            aws_secret_access_key="test",
            config=Config(retries={"max_attempts": 0})
        )

    def receive_messages(self, queue_url: str) -> list[dict]:
        """
        Retorna até 10 mensagens da fila (não as deleta).
        """
        try:
            resp = self.client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=0,
                VisibilityTimeout=0
            )
            return resp.get("Messages", [])
        except Exception as e:
            logger.error(f"Erro ao receber mensagens da fila {queue_url}: {e}")
            raise

    def list_queues(self) -> list:
        resp = self._client().list_queues()
        return resp.get("QueueUrls", [])

    def create_queue(self, queue_name: str) -> str:
        resp = self._client().create_queue(QueueName=queue_name)
        return resp["QueueUrl"]

    def delete_queue(self, queue_url: str) -> None:
        self._client().delete_queue(QueueUrl=queue_url)

    def send_message(self, queue_url: str, body: str) -> str:
        resp = self._client().send_message(QueueUrl=queue_url, MessageBody=body)
        return resp["MessageId"]

    def receive_messages(self, queue_url: str, max_number: int = 10, consume: bool = False) -> list:
        client = self._client()
        resp = client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=max_number,
            WaitTimeSeconds=0
        )
        msgs = resp.get("Messages", [])
        if consume:
            for m in msgs:
                client.delete_message(QueueUrl=queue_url, ReceiptHandle=m["ReceiptHandle"])
        else:
            for m in msgs:
                client.change_message_visibility(
                    QueueUrl=queue_url,
                    ReceiptHandle=m["ReceiptHandle"],
                    VisibilityTimeout=0
                )
        return msgs
