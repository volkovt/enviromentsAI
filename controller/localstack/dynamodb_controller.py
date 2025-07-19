
from botocore.exceptions import ClientError
from services.localstack.dynamodb_service import DynamoDBService


class DynamoDBController:
    """
    Orquestra operações de DynamoDB e trata erros.
    """
    def __init__(self, port_provider: callable):
        self.service = DynamoDBService(port_provider)

    def list_tables(self) -> list:
        try:
            return self.service.list_tables()
        except ClientError as e:
            raise RuntimeError(f"Erro ao listar tabelas: {e}")

    def create_table(self, name: str) -> None:
        try:
            self.service.create_table(name)
        except ClientError as e:
            raise RuntimeError(f"Erro ao criar tabela: {e}")

    def delete_table(self, name: str) -> None:
        try:
            self.service.delete_table(name)
        except ClientError as e:
            raise RuntimeError(f"Erro ao excluir tabela: {e}")

    def put_item(self, table: str, item_id: str, data: str) -> None:
        try:
            self.service.put_item(table, item_id, data)
        except ClientError as e:
            raise RuntimeError(f"Erro ao inserir item: {e}")

    def list_items(self, table: str) -> list:
        try:
            return self.service.list_items(table)
        except ClientError as e:
            raise RuntimeError(f"Erro ao listar itens: {e}")

    def delete_item(self, table: str, item_id: str) -> None:
        try:
            self.service.delete_item(table, item_id)
        except ClientError as e:
            raise RuntimeError(f"Erro ao excluir item: {e}")

    def batch_put_items(self, table: str, items: list) -> None:
        try:
            self.service.batch_put_items(table, items)
        except ClientError as e:
            raise RuntimeError(f"Erro ao inserir itens em lote: {e}")