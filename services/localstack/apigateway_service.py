import json
from typing import Any

import boto3
import yaml

from services.openapi.openapi_loader import OpenAPIResolver

class APIGatewayService:
    """
    Serviço de baixo-nível para operações de API Gateway no LocalStack.
    """
    def __init__(self, host_port: callable):
        self.get_port = host_port

    def _client(self):
        port = self.get_port()
        return boto3.client(
            "apigateway",
            endpoint_url=f"http://localhost:{port}",
            aws_access_key_id="test",
            aws_secret_access_key="test",
            region_name="us-east-1",
            config=boto3.session.Config(
                retries={
                    'max_attempts': 0,
                    'mode': 'standard'
                }
            )
        )

    def create_deployment(self, api_id: str, stage_name: str = "dev") -> dict:
        """
        Cria um deployment (stage) para a API, permitindo invocação HTTP.
        """
        client = self._client()
        return client.create_deployment(
            restApiId=api_id,
            stageName=stage_name
        )

    def list_apis(self) -> list:
        resp = self._client().get_rest_apis()
        return resp.get("items", [])

    def _clean_nulls(self, obj):
        """
        Remove recursivamente todos os valores None de dicionários e listas.
        """
        if isinstance(obj, dict):
            return {
                k: self._clean_nulls(v)
                for k, v in obj.items()
                if v is not None
            }
        elif isinstance(obj, list):
            return [self._clean_nulls(v) for v in obj if v is not None]
        else:
            return obj

    def create_api(self, name: str, description: str = "") -> dict:
        return self._client().create_rest_api(
            name=name,
            description=description
        )

    def delete_api(self, api_id: str) -> None:
        self._client().delete_rest_api(restApiId=api_id)

    def list_endpoints(self, api_id: str) -> list:
        """
        Retorna uma lista de dicionários com cada par (resource, método)
        de toda a hierarquia de recursos da API.
        """
        resp = self._client().get_resources(restApiId=api_id)
        endpoints = []
        for res in resp.get("items", []):
            path = res.get("path")
            for method in res.get("resourceMethods", {}).keys():
                endpoints.append({
                    "resourceId": res["id"],
                    "path": path,
                    "method": method
                })
        return endpoints

    def get_method(self, api_id: str, resource_id: str, http_method: str) -> dict:
        """
        Retorna a configuração do método (incluindo requestParameters)
        para um dado recurso e método HTTP.
        """
        client = self._client()
        return client.get_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method
        )

    def get_integration(self, api_id: str, resource_id: str, http_method: str) -> Any | None:
        """
        Retorna None ou dicionário da integração se existir.
        """
        client = self._client()
        try:
            return client.get_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method
            )
        except client.exceptions.NotFoundException:
            return None

    def ensure_integrations(self, api_id: str):
        """
        Para cada resource-method, se não existir requestTemplates,
        cria uma integração MOCK mínima (com requestTemplates) para evitar NoneType.
        """
        client = self._client()
        resources = client.get_resources(restApiId=api_id).get("items", [])
        for res in resources:
            rid = res["id"]
            for m in res.get("resourceMethods", {}):
                try:
                    integration = client.get_integration(
                        restApiId=api_id,
                        resourceId=rid,
                        httpMethod=m
                    )
                except client.exceptions.NotFoundException:
                    integration = None

                has_templates = bool(
                    integration
                    and isinstance(integration.get("requestTemplates"), dict)
                    and integration["requestTemplates"]
                )

                if not has_templates:
                    client.put_integration(
                        restApiId=api_id,
                        resourceId=rid,
                        httpMethod=m,
                        type="MOCK",
                        requestTemplates={
                            "application/json": '{ "statusCode": 200 }'
                        }
                    )
                    client.put_method_response(
                        restApiId=api_id,
                        resourceId=rid,
                        httpMethod=m,
                        statusCode="200",
                        responseModels={"application/json": "Empty"}
                    )
                    client.put_integration_response(
                        restApiId=api_id,
                        resourceId=rid,
                        httpMethod=m,
                        statusCode="200",
                        responseTemplates={
                            "application/json": '{ "message": "OK" }'
                        }
                    )

    def create_endpoint(self, api_id: str, path: str, http_method: str) -> None:
        """
        Cria (ou recupera) cada segmento de recurso para o path informado,
        depois cria o método HTTP associado.
        """
        client = self._client()
        # 1) obtém todos os resources atuais
        resources = client.get_resources(restApiId=api_id)["items"]
        # 2) rootResourceId
        root_id = next(r["id"] for r in resources if r["path"] == "/")
        parent_id = root_id

        # 3) cria/navega cada segmento de path
        for seg in path.strip("/").split("/"):
            found = next(
                (r for r in resources if r.get("parentId") == parent_id and r["pathPart"] == seg),
                None
            )
            if not found:
                new = client.create_resource(
                    restApiId=api_id,
                    parentId=parent_id,
                    pathPart=seg
                )
                parent_id = new["id"]
                resources.append({**new, "path": f"{new['path']}/{seg}"})
            else:
                parent_id = found["id"]

        client.put_method(
            restApiId=api_id,
            resourceId=parent_id,
            httpMethod=http_method,
            authorizationType="NONE"
        )

    def update_integration(self,
                           api_id: str,
                           resource_id: str,
                           http_method: str,
                           integration_type: str,
                           uri: str,
                           enable_proxy: bool = False) -> None:
        """
        Atualiza a integração de um método.
        Se enable_proxy=True, habilita greedy proxy ({proxy});
        senão, registra URI estática e remove qualquer mapeamento de proxy.
        """
        client = self._client()

        # proxy dinâmico?
        request_params = None
        if enable_proxy:
            client.update_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                patchOperations=[{
                    "op": "add",
                    "path": "/requestParameters/method.request.path.proxy",
                    "value": "true"
                }]
            )
            request_params = {
                "integration.request.path.proxy": "method.request.path.proxy"
            }
        else:
            # remove proxy para não aparecer campo na UI
            try:
                client.update_method(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod=http_method,
                    patchOperations=[{
                        "op": "remove",
                        "path": "/requestParameters/method.request.path.proxy"
                    }]
                )
            except client.exceptions.NotFoundException:
                pass

        params = {
            "restApiId": api_id,
            "resourceId": resource_id,
            "httpMethod": http_method,
            "type": integration_type,
            "integrationHttpMethod": http_method,
            "uri": uri,
            "connectionType": "INTERNET",
            "passthroughBehavior": "WHEN_NO_MATCH"
        }
        if request_params:
            params["requestParameters"] = request_params

        client.put_integration(**params)

    def get_api_definition(self,
                           api_id: str,
                           stage_name: str = "dev",
                           export_type: str = "oas30") -> str:
        """
        Exporta a definição da API (OpenAPI 3.0 JSON) já com integrações.
        """
        client = self._client()
        resp = client.get_export(
            restApiId=api_id,
            stageName=stage_name,
            exportType=export_type,
            parameters={"extensions": "integrations"},
            accepts="application/json"
        )
        return resp["body"].read().decode("utf-8")


    def import_api(self, file_content: str) -> dict:
        """
        Importa um arquivo OpenAPI ou uma definição completa exportada.
        """
        try:
            spec = yaml.safe_load(file_content)
        except Exception:
            spec = json.loads(file_content)

        if all(key in spec for key in ["api", "resources"]):
            return self._import_full_api(spec)

        clean_spec = self._clean_nulls(spec)
        body = json.dumps(clean_spec, default=str)
        return self._client().import_rest_api(
            failOnWarnings=False,
            body=body
        )

    def import_complex_api(self, file_path: str) -> dict:
        """
        Importa OpenAPI com referências ou uma exportação completa da API.
        """

        def _json_default(obj):
            from datetime import date, datetime
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, date):
                return obj.isoformat()

            return str(obj)

        resolver = OpenAPIResolver()
        spec = resolver.load(file_path)

        if all(key in spec for key in ["api", "resources"]):
            return self._import_full_api(spec)

        with open("output.log", "w", encoding="utf-8") as log_file:
            # expected type 'SupportsWrite(str)' but got 'TextIOWrapper'
            json.dump(spec, log_file, indent=2, default=_json_default)

        return self._client().import_rest_api(
            failOnWarnings=False,
            body=json.dumps(spec, default=_json_default)
        )

    def _export_full_api(self, api_id: str) -> dict:
        client = self._client()

        api = client.get_rest_api(restApiId=api_id)
        resources = client.get_resources(restApiId=api_id).get("items", [])
        stages = client.get_stages(restApiId=api_id).get("item", [])
        validators = client.get_request_validators(restApiId=api_id).get("items", [])
        models = client.get_models(restApiId=api_id).get("items", [])
        authorizers = client.get_authorizers(restApiId=api_id).get("items", [])

        full = {
            "api": api,
            "resources": [],
            "stages": stages,
            "validators": validators,
            "models": models,
            "authorizers": authorizers,
            "policy": api.get("policy")
        }

        for res in resources:
            res_data = {"resource": res, "methods": []}
            if "resourceMethods" in res:
                for method in res["resourceMethods"]:
                    try:
                        m = client.get_method(api_id, res["id"], method)
                        try:
                            i = client.get_integration(api_id, res["id"], method)
                        except client.exceptions.NotFoundException:
                            i = None
                        res_data["methods"].append({"method": m, "integration": i})
                    except Exception:
                        continue
            full["resources"].append(res_data)

        return full

    def _import_full_api(self, full: dict) -> dict:
        client = self._client()

        api = client.create_rest_api(
            name=full["api"]["name"],
            description=full["api"].get("description", "")
        )
        api_id = api["id"]

        if full.get("policy"):
            client.update_rest_api(
                restApiId=api_id,
                patchOperations=[
                    {
                        "op": "replace",
                        "path": "/policy",
                        "value": full["policy"]
                    }
                ]
            )

        id_map = {}
        root_id = client.get_resources(restApiId=api_id)["items"][0]["id"]

        for r in full["resources"]:
            path_parts = r["resource"]["path"].strip("/").split("/") if r["resource"]["path"] != "/" else []
            parent_id = root_id
            for part in path_parts:
                key = f"{parent_id}/{part}"
                if key not in id_map:
                    created = client.create_resource(
                        restApiId=api_id,
                        parentId=parent_id,
                        pathPart=part
                    )
                    id_map[key] = created["id"]
                    parent_id = created["id"]
                else:
                    parent_id = id_map[key]

            res_id = parent_id

            for m in r["methods"]:
                method = m["method"]["httpMethod"]
                client.put_method(
                    restApiId=api_id,
                    resourceId=res_id,
                    httpMethod=method,
                    authorizationType="NONE",
                    requestParameters=m["method"].get("requestParameters", {})
                )

                if m.get("integration"):
                    integ = m["integration"]
                    client.put_integration(
                        restApiId=api_id,
                        resourceId=res_id,
                        httpMethod=method,
                        type=integ["type"],
                        integrationHttpMethod=integ.get("httpMethod", "POST"),
                        uri=integ.get("uri"),
                        passthroughBehavior=integ.get("passthroughBehavior", "WHEN_NO_MATCH"),
                        requestTemplates=integ.get("requestTemplates", {}),
                        timeoutInMillis=integ.get("timeoutInMillis", 29000)
                    )

                client.put_method_response(
                    restApiId=api_id,
                    resourceId=res_id,
                    httpMethod=method,
                    statusCode="200",
                    responseModels={"application/json": "Empty"}
                )
                client.put_integration_response(
                    restApiId=api_id,
                    resourceId=res_id,
                    httpMethod=method,
                    statusCode="200",
                    responseTemplates={"application/json": '{"message": "OK"}'}
                )

        # Models
        for model in full.get("models", []):
            client.create_model(
                restApiId=api_id,
                name=model["name"],
                description=model.get("description", ""),
                schema=model.get("schema", "{}"),
                contentType=model.get("contentType", "application/json")
            )

        # Validators
        for val in full.get("validators", []):
            client.create_request_validator(
                restApiId=api_id,
                name=val["name"],
                validateRequestBody=val.get("validateRequestBody", False),
                validateRequestParameters=val.get("validateRequestParameters", False)
            )

        # Deployment
        client.create_deployment(
            restApiId=api_id,
            stageName="dev"
        )

        return api


    def _get_or_create_resource(self, api_id: str, path: str) -> str:
        """
        Garante que cada segmento de 'path' exista e retorna o resourceId final.
        """
        client = self._client()
        resp = client.get_resources(restApiId=api_id)
        resources = resp["items"]
        root = next(r for r in resources if r["path"] == "/")
        parent_id = root["id"]

        for seg in path.strip("/").split("/"):
            found = next(
                (r for r in resources
                 if r.get("parentId")==parent_id and r.get("pathPart")==seg),
                None
            )
            if not found:
                new = client.create_resource(
                    restApiId=api_id,
                    parentId=parent_id,
                    pathPart=seg
                )
                resources.append(new)
                parent_id = new["id"]
            else:
                parent_id = found["id"]
        return parent_id

    def put_path_item(self, api_id: str, path: str, path_item: dict) -> None:
        """
        Cria recurso+método e configura parâmetros,
        integração e responses seguindo a spec OpenAPI do path_item.
        """
        client = self._client()
        resource_id = self._get_or_create_resource(api_id, path)

        for method_name, op in path_item.items():
            http_method = method_name.upper()

            client.put_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                authorizationType="NONE"
            )

            for param in op.get("parameters", []):
                if isinstance(param, dict) and "name" in param:
                    name = param["name"]
                    in_ = param["in"]
                    required = param.get("required", False)
                    client.update_method(
                        restApiId=api_id,
                        resourceId=resource_id,
                        httpMethod=http_method,
                        patchOperations=[{
                            "op": "add",
                            "path": f"/requestParameters/method.request.{in_}.{name}",
                            "value": "true" if required else "false"
                        }]
                    )

            integ = op.get("x-amazon-apigateway-integration", {})
            uri   = integ.get("uri")
            itype = integ.get("type")
            imeth = integ.get("httpMethod")
            if uri and itype and imeth:
                self.update_integration(api_id, resource_id, http_method, itype, uri)

            for status, resp_def in op.get("responses", {}).items():
                client.put_method_response(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod=http_method,
                    statusCode=status,
                    responseModels={ct: "Empty" for ct in resp_def.get("content", {}).keys()}
                )
                for ct, details in resp_def.get("content", {}).items():
                    tmpl = json.dumps(details.get("schema", {}))
                    client.put_integration_response(
                        restApiId=api_id,
                        resourceId=resource_id,
                        httpMethod=http_method,
                        statusCode=status,
                        responseTemplates={ct: tmpl}
                    )

    def update_method_request_parameters(
            self,
            api_id: str,
            resource_id: str,
            http_method: str,
            parameters: list
    ) -> None:
        """
        Sincroniza os requestParameters do método com a lista `parameters`.
        - Adiciona ou atualiza cada parâmetro (value "true" ou "false").
        - Remove quaisquer parâmetros que já existam no método mas não estejam na lista.
        """
        client = self._client()

        resp = client.get_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method
        )
        existing = resp.get("requestParameters", {}) or {}
        existing_keys = set(existing.keys())

        desired_keys = set()
        ops = []

        for p in parameters:
            name = p["name"]
            kind = p["in"]
            required = p.get("required", False)
            aws_in = "querystring" if kind == "query" else kind
            key = f"method.request.{aws_in}.{name}"
            desired_keys.add(key)

            path = f"/requestParameters/{key}"
            value = "true" if required else "false"
            ops.append({
                "op": "add",
                "path": path,
                "value": value
            })

        for key in existing_keys - desired_keys:
            path = f"/requestParameters/{key}"
            ops.append({
                "op": "remove",
                "path": path
            })

        if ops:
            client.update_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                patchOperations=ops
            )

    def delete_method(self, api_id: str, resource_id: str, http_method: str) -> None:
        """
        Remove o método (endpoint) do recurso.
        """
        client = self._client()
        client.delete_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method
        )