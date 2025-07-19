from services.localstack.lambda_service import LambdaService


class LambdaController:
    """
    Controller que orquestra list, deploy e invoke para Lambdas via LambdaService.
    """
    def __init__(self, port_provider: callable):
        self.service = LambdaService(port_provider)

    def list_functions(self) -> list:
        try:
            return self.service.list_functions()
        except Exception as e:
            raise RuntimeError(f"Erro ao listar funções Lambda: {e}")

    def deploy(self, function_name: str, directory_path: str) -> None:
        try:
            self.service.deploy(function_name, directory_path)
        except Exception as e:
            raise RuntimeError(f"Erro ao deploy da função Lambda: {e}")

    def invoke(self, function_name: str, payload: dict = None) -> str:
        try:
            return self.service.invoke(function_name, payload)
        except Exception as e:
            raise RuntimeError(f"Erro ao invocar a função Lambda: {e}")

    def delete(self, function_name: str) -> None:
        try:
            self.service.delete_function(function_name)
        except Exception as e:
            raise RuntimeError(f"Erro ao excluir função Lambda: {e}")

    def get_configuration(self, function_name: str) -> dict:
        try:
            return self.service.get_configuration(function_name)
        except Exception as e:
            raise RuntimeError(f"Erro ao obter configuração da função Lambda: {e}")