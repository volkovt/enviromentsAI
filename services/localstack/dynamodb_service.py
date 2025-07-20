import logging
from decimal import Decimal

import boto3
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer

logger = logging.getLogger("[DynamoDBService]")

class DynamoDBService:
    """
    Serviço de baixo-nível para operações de DynamoDB no LocalStack.
    """
    def __init__(self, host_port: callable):
        self.get_port = host_port

    def _client(self):
        port = self.get_port()
        return boto3.client(
            "dynamodb",
            endpoint_url=f"http://localhost:{port}",
            region_name="us-east-1",
            aws_access_key_id="test",
            aws_secret_access_key="test"
        )

    def list_tables(self) -> list:
        resp = self._client().list_tables()
        return resp.get("TableNames", [])

    def scan_table(self, table_name: str) -> list[dict]:
        """
        Retorna todos os itens existentes na tabela DynamoDB.
        """
        try:
            paginator = self._client().get_paginator("scan")
            items = []
            for page in paginator.paginate(TableName=table_name):
                items.extend(page.get("Items", []))
            return items
        except Exception as e:
            logger.error(f"Erro ao escanear tabela {table_name}: {e}")
            raise

    def create_table(self, table_name: str) -> dict:
        """
        Cria uma tabela simples com chave primária 'id' (string).
        """
        return self._client().create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1}
        )

    def delete_table(self, table_name: str) -> dict:
        return self._client().delete_table(TableName=table_name)

    def put_item(self, table_name: str, item_id: str, data: str) -> dict:
        return self._client().put_item(
            TableName=table_name,
            Item={
                "id": {"S": item_id},
                "data": {"S": data}
            }
        )

    def list_items(self, table_name: str) -> list:
        """
        Lista todos os itens da tabela e desserializa dinamicamente
        cada atributo para tipos Python puros.
        """
        resp = self._client().scan(TableName=table_name)
        items = resp.get("Items", [])
        deserializer = TypeDeserializer()
        result = []
        for it in items:
            python_item = {k: deserializer.deserialize(v) for k, v in it.items()}
            result.append(python_item)
        return result

    def delete_item(self, table_name: str, item_id: str) -> dict:
        """
        Exclui um item pela chave primária.
        """
        return self._client().delete_item(
            TableName=table_name,
            Key={"id": {"S": item_id}}
        )

    def batch_put_items(self, table_name: str, items: list) -> None:
        """
        Insere múltiplos itens a partir de uma lista de dicts
        (cada dict pode ter qualquer estrutura aninhada, inclusive números).
        """
        client = self._client()
        serializer = TypeSerializer()

        for it in items:
            item_av = {}
            for key, value in it.items():
                if isinstance(value, float):
                    value = Decimal(str(value))
                item_av[key] = serializer.serialize(value)
            client.put_item(TableName=table_name, Item=item_av)