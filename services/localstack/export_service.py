import json
import logging

from services.localstack.s3_service import S3Service
from services.localstack.sqs_service import SQSService
from services.localstack.dynamodb_service import DynamoDBService
from services.localstack.lambda_service import LambdaService
from services.localstack.apigateway_service import APIGatewayService

logger = logging.getLogger("[ExportService]")

class ExportService:
    """
    Gera um script bash com comandos AWS CLI para recriar
    todas as filas, buckets, tabelas, funções e APIs existentes.
    """
    def __init__(self, port_provider: callable):
        self.get_port = port_provider
        self.sqs = SQSService(self.get_port)
        self.s3 = S3Service(self.get_port)
        self.dynamodb = DynamoDBService(self.get_port)
        self.lambda_svc = LambdaService(self.get_port)
        self.apigw = APIGatewayService(self.get_port)

    def export_scripts(self) -> str:
        port = self.get_port()
        lines = [
            "#!/usr/bin/env bash",
            "set -e",
            f"export AWS_PAGER=''",
            f"export AWS_ENDPOINT=http://localhost:{port}",
            ""
        ]
        try:
            # SQS
            for url in self.sqs.list_queues():
                name = url.rstrip("/").split("/")[-1]
                lines.append(f"aws --endpoint-url $AWS_ENDPOINT sqs create-queue --queue-name {name}")
            lines.append("")

            for url in self.sqs.list_queues():
                name = url.rstrip("/").split("/")[-1]
                try:
                    msgs = self.sqs.receive_messages(url)
                except Exception:
                    continue

                if not msgs:
                    continue

                lines.append(f"# Mensagens da fila {name}")
                for msg in msgs:
                    body = msg.get("Body", "")
                    safe_body = body.replace("'", "'\"'\"'")
                    lines.append(
                        "aws --endpoint-url $AWS_ENDPOINT sqs send-message "
                        f"--queue-url {url} "
                        f"--message-body '{safe_body}'"
                    )
            lines.append("")

            # S3
            for bucket in self.s3.list_buckets():
                lines.append(f"aws --endpoint-url $AWS_ENDPOINT s3api create-bucket --bucket {bucket}")

                for key in self.s3.list_objects(bucket):
                    lines.append(
                        f"aws --endpoint-url $AWS_ENDPOINT s3 cp "
                        f"s3://{bucket}/{key} ./{bucket}/{key}"
                    )
            lines.append("")

            # DynamoDB
            for table in self.dynamodb.list_tables():
                lines.append(
                    "aws --endpoint-url $AWS_ENDPOINT dynamodb create-table "
                    f"--table-name {table} "
                    "--attribute-definitions AttributeName=id,AttributeType=S "
                    "--key-schema AttributeName=id,KeyType=HASH "
                    "--provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1"
                )
            lines.append("")

            # --- Exportando dados das tabelas ---
            for table in self.dynamodb.list_tables():
                items = self.dynamodb.scan_table(table)
                if not items:
                    continue
                lines.append(f"# Dados da tabela {table}")
                for item in items:
                    item_json = json.dumps(item, ensure_ascii=False)
                    lines.append(
                        "aws --endpoint-url $AWS_ENDPOINT dynamodb put-item "
                        f"--table-name {table} "
                        f"--item '{item_json}'"
                    )
            lines.append("")

            # Lambda
            for fn in self.lambda_svc.list_functions():
                lines.append(f"# Lambda function: {fn}")
                lines.append(f"aws --endpoint-url $AWS_ENDPOINT lambda get-function --function-name {fn} > {fn}.json")
            lines.append("")

            # API Gateway
            for api in self.apigw.list_apis():
                api_id = api["id"]
                name = api.get("name", api_id)
                lines.append(
                    f"aws --endpoint-url $AWS_ENDPOINT apigateway get-rest-api "
                    f"--rest-api-id {api_id} > {name}.json"
                )

        except Exception as e:
            logger.error(f"Erro ao montar scripts de exportação: {e}")
            raise

        return "\n".join(lines)
