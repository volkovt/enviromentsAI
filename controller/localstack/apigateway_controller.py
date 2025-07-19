from services.localstack.apigateway_service import APIGatewayService

class APIGatewayController:
    """
    Controller que orquestra list/import/create/delete de APIs e
    também expõe list_endpoints para obter recursos e métodos.
    """
    def __init__(self, port_provider: callable):
        self.service = APIGatewayService(port_provider)

    def list_apis(self) -> list:
        try:
            return self.service.list_apis()
        except Exception as e:
            raise RuntimeError(f"Erro ao listar APIs: {e}")

    def import_api(self, file_content: str) -> dict:
        try:
            return self.service.import_api(file_content)
        except Exception as e:
            raise RuntimeError(f"Erro ao importar API: {e}")

    def create_api(self, name: str, description: str = "") -> dict:
        try:
            return self.service.create_api(name, description)
        except Exception as e:
            raise RuntimeError(f"Erro ao criar API: {e}")

    def delete_api(self, api_id: str) -> None:
        try:
            self.service.delete_api(api_id)
        except Exception as e:
            raise RuntimeError(f"Erro ao excluir API: {e}")

    def list_endpoints(self, api_id: str) -> list:
        try:
            return self.service.list_endpoints(api_id)
        except Exception as e:
            raise RuntimeError(f"Erro ao listar endpoints da API: {e}")

    def get_method(self, api_id: str, resource_id: str, http_method: str) -> dict:
        """
        Encapsula o get_method do service, para uso no Component.
        """
        try:
            return self.service.get_method(api_id, resource_id, http_method)
        except Exception as e:
            raise RuntimeError(f"Erro ao obter método da API: {e}")

    def create_deployment(self, api_id: str, stage_name: str = "dev") -> dict:
        """
        Encapsula create_deployment do service.
        """
        try:
            return self.service.create_deployment(api_id, stage_name)
        except Exception as e:
            raise RuntimeError(f"Erro ao criar deployment da API: {e}")

    def ensure_integrations(self, api_id: str):
        try:
            self.service.ensure_integrations(api_id)
        except Exception as e:
            raise RuntimeError(f"Erro em ensure_integrations: {e}")

    def create_endpoint(self, api_id: str, path: str, http_method: str) -> None:
        """
        Orquestra a criação de um endpoint (resource+method).
        """
        try:
            self.service.create_endpoint(api_id, path, http_method)
        except Exception as e:
            raise RuntimeError(f"Erro ao criar endpoint: {e}")

    def create_path(self, api_id: str, path: str, path_item: dict) -> None:
        """
        Cria um path completo (OpenAPI style) numa API já existente.
        """
        try:
            self.service.put_path_item(api_id, path, path_item)
            self.service.create_deployment(api_id, "dev")
        except Exception as e:
            raise RuntimeError(f"Erro ao criar path '{path}': {e}")

    def update_integration(self,
                           api_id: str,
                           resource_id: str,
                           http_method: str,
                           integration_type: str,
                           uri: str,
                           enable_proxy: bool = False) -> None:
        """
        Orquestra a atualização da integração de um método.
        Se enable_proxy=True, habilita o greedy proxy ({proxy}) no path.
        """
        try:
            self.service.update_integration(
                api_id,
                resource_id,
                http_method,
                integration_type,
                uri,
                enable_proxy
            )
        except Exception as e:
            raise RuntimeError(f"Erro ao atualizar integração: {e}")

    def get_api_definition(self,
                           api_id: str,
                           stage_name: str = "dev",
                           export_type: str = "oas30") -> str:
        """
        Repassa a chamada de exportação à camada de serviço.
        """
        try:
            return self.service.get_api_definition(api_id, stage_name, export_type)
        except Exception as e:
            raise RuntimeError(f"Erro ao obter definição da API: {e}")

    def get_integration(self, api_id: str, resource_id: str, http_method: str) -> dict:
        try:
            return self.service.get_integration(api_id, resource_id, http_method)
        except Exception as e:
            raise RuntimeError(f"Erro ao obter integração da API: {e}")

    def import_complex_api(self, file_path: str) -> dict:
       """
       Orquestra importação de OpenAPI complexo com referências.
       """
       try:
           return self.service.import_complex_api(file_path)
       except Exception as e:
           raise RuntimeError(f"Erro ao importar API complexa: {e}")


    def update_parameters(
        self,
        api_id: str,
        resource_id: str,
        http_method: str,
        parameters: list
    ) -> None:
        """
        Controlador para criar/remover requestParameters no método.
        """
        self.service.update_method_request_parameters(
            api_id, resource_id, http_method, parameters
        )

    def delete_endpoint(
            self,
            api_id: str,
            resource_id: str,
            http_method: str
    ) -> None:
        """
        Controlador para excluir um endpoint e redeploy.
        """
        self.service.delete_method(api_id, resource_id, http_method)
        self.create_deployment(api_id, "dev")