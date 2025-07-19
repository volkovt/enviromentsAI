import json

import requests
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QTreeWidget, QTreeWidgetItem,
    QTextEdit, QFileDialog, QMessageBox, QFormLayout, QWidget, QScrollArea, QSizePolicy, QDialog, QMenu
)
import qtawesome as qta
import os

from presentation.components.localstack.create_path_dialog import NewPathDialog
from presentation.components.json_text_edit import JSONTextEdit
from presentation.components.localstack.params_dialog import ParamsDialog
from services.localstack.localstack_session import LocalStackSession


class APIGatewayComponent(QWidget):
    HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD", "ANY"}
    """
    Componente de UI para gerir API Gateways:
      • Importar via OpenAPI
      • Criar manualmente (nome + descrição)
      • Listar APIs existentes
      • Excluir APIs
      • Exibir todos os endpoints em árvore
    """
    def __init__(self, controller, port_input, lambda_controller):
        super().__init__()
        self._current_integration_type = None
        self.current_uri = None
        self.controller = controller
        self.lambda_controller = lambda_controller
        self.get_port = port_input.value
        self.selected_file = None
        self.api_map = {}
        self.path_param_inputs = {}
        self.query_param_inputs = {}
        self.header_param_inputs = {}

        self._build_ui()
        self._refresh_apis()
        self._refresh_lambdas()

        self.session = LocalStackSession()
        saved = self.session.get("apigateway").get("selected_api")
        if saved and saved in self.api_map.values():
            name = next(n for n, i in self.api_map.items() if i == saved)
            idx = self.api_combo.findText(name)
            if idx >= 0:
                self.api_combo.setCurrentIndex(idx)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        content = QWidget()
        layout = QVBoxLayout(content)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)
        header_layout.setAlignment(Qt.AlignLeft)
        file_layout = QHBoxLayout()
        file_layout.setContentsMargins(0, 0, 0, 0)
        file_layout.setSpacing(5)
        file_layout.setAlignment(Qt.AlignRight)
        self.file_label = QLabel("No file selected")
        self.file_label.setToolTip("Selected OpenAPI file")
        select_btn = QPushButton()
        select_btn.setIcon(qta.icon("fa5s.folder-open", color="orange"))
        select_btn.setToolTip("Select OpenAPI file to import")
        select_btn.setIconSize(QSize(24, 24))
        select_btn.setFixedWidth(30)
        select_btn.clicked.connect(self._select_file)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(select_btn)
        import_btn = QPushButton()
        import_btn.setToolTip("Import API from OpenAPI file")
        import_btn.setIcon(qta.icon("fa5s.upload", color="orange"))
        import_btn.setIconSize(QSize(24, 24))
        import_btn.setFixedWidth(30)
        import_btn.clicked.connect(self._on_import_api)
        file_layout.addWidget(import_btn)

        import_complex_btn = QPushButton()
        import_complex_btn.setToolTip("Import complex API with references")
        import_complex_btn.setIcon(qta.icon("fa5s.file-code", color="orange"))
        import_btn.setIconSize(QSize(24, 24))
        import_complex_btn.setFixedWidth(30)
        import_complex_btn.clicked.connect(self._on_import_complex_api)
        file_layout.addWidget(import_complex_btn)

        manual_layout = QHBoxLayout()

        create_btn = QPushButton(qta.icon("fa5s.plus", color="orange"), "Create API")
        create_btn.setToolTip("Create API manually")
        create_btn.setIconSize(QSize(24, 24))
        create_btn.clicked.connect(self._on_create_api)
        manual_layout.addWidget(create_btn)

        name_label = QLabel("Name:")
        name_label.setToolTip("Nome da API")
        name_label.setFixedWidth(100)
        manual_layout.addWidget(name_label)
        self.name_input = QLineEdit()
        manual_layout.addWidget(self.name_input)
        description_label = QLabel("Description:")
        description_label.setToolTip("Descrição opcional da API")
        description_label.setFixedWidth(150)
        manual_layout.addWidget(description_label)
        self.desc_input = QLineEdit()
        manual_layout.addWidget(self.desc_input)

        header_layout.addLayout(manual_layout)
        header_layout.addStretch()
        header_layout.addLayout(file_layout)

        layout.addLayout(header_layout)

        sel_layout = QHBoxLayout()
        api_selection_label = QLabel("APIs:")
        api_selection_label.setToolTip("Selecione uma API para ver detalhes")
        api_selection_label.setFixedWidth(100)
        sel_layout.addWidget(api_selection_label)
        self.api_combo = QComboBox()
        self.api_combo.setPlaceholderText("Select an API")
        self.api_combo.currentIndexChanged.connect(self._on_api_change)
        sel_layout.addWidget(self.api_combo)

        refresh_btn = QPushButton(qta.icon("fa5s.sync", color="orange"), "")
        refresh_btn.setIconSize(QSize(24, 24))
        refresh_btn.setFixedWidth(30)
        refresh_btn.setToolTip("Refresh APIs")
        refresh_btn.clicked.connect(self._refresh_apis)
        sel_layout.addWidget(refresh_btn)

        delete_btn = QPushButton(qta.icon("fa5s.trash", color="red"), "")
        delete_btn.setIconSize(QSize(24, 24))
        delete_btn.setFixedWidth(30)
        delete_btn.setToolTip("Delete API")
        delete_btn.clicked.connect(self._on_delete_api)
        sel_layout.addWidget(delete_btn)

        layout.addLayout(sel_layout)

        background_color = "background-color: #1C1C1C; border: 2px solid #462E0F;"

        self.api_definition_label = QLabel("API Definition (JSON)")
        self.api_definition_label.setToolTip("Selecione uma API para ver detalhes")
        layout.addWidget(self.api_definition_label)
        self.detail_view = QTextEdit()
        self.detail_view.setToolTip("Definição da API selecionada")
        self.detail_view.setAcceptRichText(False)
        self.detail_view.setStyleSheet(background_color)
        self.detail_view.setFontFamily("Courier New")
        self.detail_view.setFontPointSize(10)
        self.detail_view.setLineWrapMode(QTextEdit.NoWrap)
        self.detail_view.setTabChangesFocus(True)
        self.detail_view.setPlaceholderText("API definition will be shown here...")
        self.detail_view.setMinimumHeight(300)
        self.detail_view.setReadOnly(True)
        layout.addWidget(self.detail_view)

        ep_layout = QHBoxLayout()
        ep_label = QLabel("New Path:")
        ep_label.setToolTip("Informe o path do novo endpoint")
        ep_label.setFixedWidth(150)
        ep_layout.addWidget(ep_label)
        self.new_path_input = QLineEdit()
        self.new_path_input.setPlaceholderText("/contratos/{id}")
        ep_layout.addWidget(self.new_path_input)
        ep_layout.addWidget(QLabel("Method:"))
        self.new_method_combo = QComboBox()
        self.new_method_combo.addItems(list(self.HTTP_METHODS))
        ep_layout.addWidget(self.new_method_combo)
        add_ep_btn = QPushButton(qta.icon("fa5s.plus", color="orange"), "")
        add_ep_btn.setToolTip("Add Endpoint")
        add_ep_btn.setIconSize(QSize(24, 24))
        add_ep_btn.setFixedWidth(30)
        add_ep_btn.clicked.connect(self._on_add_endpoint)
        ep_layout.addWidget(add_ep_btn)

        complex_ep_btn = QPushButton(qta.icon("fa5s.plus-circle", color="orange"), "Add Full Path")
        complex_ep_btn.setToolTip("Add full-path with details")
        complex_ep_btn.clicked.connect(self._on_add_full_path)
        ep_layout.addWidget(complex_ep_btn)

        layout.addLayout(ep_layout)

        # Árvore de endpoints
        endpoint_label = QLabel("Endpoints:")
        endpoint_label.setToolTip("Lista de endpoints da API selecionada")
        endpoint_label.setMinimumWidth(150)
        endpoint_label.setContentsMargins(0, 10, 0, 0)
        layout.addWidget(endpoint_label)
        self.tree = QTreeWidget()
        self.tree.setToolTip("Lista de endpoints da API selecionada")
        self.tree.setColumnCount(1)
        self.tree.setHeaderLabels(["Path"])
        self.tree.setStyleSheet(background_color)
        self.tree.setHeaderHidden(True)
        self.tree.setMinimumHeight(250)
        self.tree.itemClicked.connect(self._on_tree_item_clicked)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_tree_context_menu)
        layout.addWidget(self.tree)

        # --- Integração: URI editável ---
        integration_layout = QHBoxLayout()
        integration_label = QLabel("Integration URI:")
        integration_label.setToolTip("Informe a URI de integração ou escolha uma Lambda")
        integration_label.setFixedWidth(200)
        integration_layout.addWidget(integration_label)
        self.integration_input = QLineEdit()
        integration_layout.addWidget(self.integration_input)
        update_int_btn = QPushButton(qta.icon("fa5s.pen", color="orange"), "")
        update_int_btn.setToolTip("Update Integration")
        update_int_btn.setIconSize(QSize(24, 24))
        update_int_btn.setFixedWidth(30)
        update_int_btn.clicked.connect(self._on_update_integration)
        integration_layout.addWidget(update_int_btn)
        layout.addLayout(integration_layout)

        lambda_layout = QHBoxLayout()
        lambda_label = QLabel("Lambdas:")
        lambda_label.setToolTip("Informe a URI de integração ou escolha uma Lambda")
        lambda_label.setFixedWidth(150)
        lambda_layout.addWidget(lambda_label)
        self.lambda_combo = QComboBox()
        lambda_layout.addWidget(self.lambda_combo)
        lambda_refresh_btn = QPushButton(qta.icon("fa5s.sync", color="orange"), "")
        lambda_refresh_btn.setToolTip("Refresh Lambdas")
        lambda_refresh_btn.setIconSize(QSize(24, 24))
        lambda_refresh_btn.setFixedWidth(30)
        lambda_refresh_btn.clicked.connect(self._refresh_lambdas)
        lambda_layout.addWidget(lambda_refresh_btn)
        layout.addLayout(lambda_layout)

        path_layout = QHBoxLayout()
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.setSpacing(5)
        path_label = QLabel("Path Template:")
        path_label.setToolTip("Template do path para a requisição")
        path_label.setMinimumWidth(150)
        path_layout.addWidget(path_label)
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("/contratos/{id}")
        self.path_input.setToolTip("Template do path para a requisição")
        self.path_input.setMinimumHeight(50)
        self.path_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.path_input.setStyleSheet(background_color)
        self.path_input.setReadOnly(True)
        path_layout.addWidget(self.path_input)
        layout.addLayout(path_layout)

        endpoint_detail_label = QLabel("Endpoint Details:")
        endpoint_detail_label.setToolTip("Detalhes do endpoint selecionado")
        layout.addWidget(endpoint_detail_label)
        self.endpoint_detail_view = QTextEdit()
        self.endpoint_detail_view.setToolTip("Detalhes do endpoint selecionado")
        self.endpoint_detail_view.setAcceptRichText(False)
        self.endpoint_detail_view.setStyleSheet(background_color)
        self.endpoint_detail_view.setFontFamily("Courier New")
        self.endpoint_detail_view.setFontPointSize(10)
        self.endpoint_detail_view.setLineWrapMode(QTextEdit.NoWrap)
        self.endpoint_detail_view.setTabChangesFocus(True)
        self.endpoint_detail_view.setReadOnly(True)
        self.endpoint_detail_view.setPlaceholderText("Endpoint details (JSON)")
        self.endpoint_detail_view.setMinimumHeight(150)
        layout.addWidget(self.endpoint_detail_view)

        header_label = QLabel("Header Parameters:")
        header_label.setToolTip("Informe os parâmetros de cabeçalho para a requisição")
        header_label.setMinimumWidth(250)
        layout.addWidget(header_label)
        self.header_params_widget = QWidget()
        self.header_params_widget.setMinimumHeight(100)
        self.header_params_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.header_params_widget.setStyleSheet(background_color)
        self.header_params_widget.setToolTip("Informe os parâmetros de cabeçalho para a requisição")
        self.header_params_widget.setContentsMargins(10, 10, 10, 10)
        self.header_params_form = QFormLayout(self.header_params_widget)
        layout.addWidget(self.header_params_widget)

        path_parameters_label = QLabel("Path Parameters:")
        path_parameters_label.setToolTip("Informe os parâmetros de path para a requisição")
        path_parameters_label.setMinimumWidth(150)
        layout.addWidget(path_parameters_label)
        self.path_params_widget = QWidget()
        self.path_params_widget.setMinimumHeight(100)
        self.path_params_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.path_params_widget.setStyleSheet(background_color)
        self.path_params_widget.setToolTip("Informe os parâmetros de path para a requisição")
        self.path_params_widget.setContentsMargins(10, 10, 10, 10)
        self.path_params_form = QFormLayout(self.path_params_widget)
        layout.addWidget(self.path_params_widget)

        query_label = QLabel("Query Parameters:")
        query_label.setToolTip("Informe os parâmetros de consulta para a requisição")
        query_label.setMinimumWidth(100)
        query_label.setContentsMargins(0, 10, 0, 0)
        layout.addWidget(query_label)
        self.query_params_widget = QWidget()
        self.query_params_widget.setMinimumHeight(200)
        self.query_params_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.query_params_widget.setStyleSheet(background_color)
        self.query_params_widget.setToolTip("Informe os parâmetros de consulta para a requisição")
        self.query_params_widget.setContentsMargins(10, 10, 10, 10)
        self.query_params_form = QFormLayout(self.query_params_widget)
        layout.addWidget(self.query_params_widget)

        body_label = QLabel("Request Body:")
        body_label.setToolTip("Informe o corpo da requisição em JSON")
        body_label.setMinimumWidth(150)
        body_label.setContentsMargins(0, 10, 0, 0)
        layout.addWidget(body_label)
        self.body_input = JSONTextEdit()
        self.body_input.setToolTip("Informe o corpo da requisição em JSON")
        self.body_input.setStyleSheet(background_color)
        self.body_input.setMinimumHeight(200)
        layout.addWidget(self.body_input)

        # invoke
        invoke_label = QLabel("Invoke Endpoint:")
        invoke_label.setToolTip("Clique para invocar o endpoint selecionado")
        invoke_label.setMinimumWidth(150)
        invoke_label.setContentsMargins(0, 10, 0, 0)
        layout.addWidget(invoke_label)
        invoke_layout = QHBoxLayout()
        invoke_layout.setContentsMargins(0, 0, 0, 0)
        invoke_layout.setSpacing(5)
        invoke_layout.setAlignment(Qt.AlignCenter)
        layout.addLayout(invoke_layout)
        invoke_btn = QPushButton()
        invoke_btn.setIcon(qta.icon("fa5s.play", color="green"))
        invoke_btn.setToolTip("Invoke selected endpoint")
        invoke_btn.setIconSize(QSize(24, 24))
        invoke_btn.setFixedWidth(100)
        invoke_btn.clicked.connect(self._on_call_endpoint)
        invoke_layout.addWidget(invoke_btn)

        # resposta
        response_label = QLabel("Response:")
        response_label.setToolTip("Resposta da invocação do endpoint")
        response_label.setMinimumWidth(150)
        response_label.setContentsMargins(0, 10, 0, 0)
        layout.addWidget(response_label)
        self.response_output = QTextEdit()
        self.response_output.setToolTip("Resposta da invocação do endpoint")
        self.response_output.setAcceptRichText(False)
        self.response_output.setStyleSheet(background_color)
        self.response_output.setFontFamily("Courier New")
        self.response_output.setFontPointSize(10)
        self.response_output.setLineWrapMode(QTextEdit.NoWrap)
        self.response_output.setTabChangesFocus(True)
        self.response_output.setPlaceholderText("Response will be shown here...")
        self.response_output.setReadOnly(True)
        self.response_output.setMinimumHeight(300)
        layout.addWidget(self.response_output)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _on_add_full_path(self):
        dlg = NewPathDialog(self.HTTP_METHODS, self.lambda_controller, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            path, path_item = dlg.get_result()
            api_id = self.current_api_id
            if not api_id:
                QMessageBox.warning(self, "API Gateway", "Selecione uma API para adicionar o path.")
                return
            if not path or not path_item:
                QMessageBox.warning(self, "API Gateway", "Informe um path e detalhes válidos.")
                return
            try:
                self.controller.create_path(api_id, path, path_item)
                self.controller.create_deployment(api_id, "dev")
                QMessageBox.information(self, "API Gateway", f"Path criado: {path.upper()}")
                self._load_endpoints(api_id)
            except Exception as e:
                QMessageBox.critical(self, "API Gateway", f"Erro ao criar path completo: {e}")


    def _refresh_lambdas(self):
        """
        Recarrega o combo com as funções Lambda locais disponíveis.
        """
        try:
            funcs = self.lambda_controller.list_functions()
            self.lambda_combo.clear()
            self.lambda_combo.addItem("(none)")
            self.lambda_combo.addItems(funcs or [])
        except Exception as e:
            QMessageBox.critical(self, "Lambda", str(e))

    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select OpenAPI File", "", "YAML/JSON Files (*.yaml *.yml *.json)"
        )
        if path:
            self.selected_file = path
            self.file_label.setText(os.path.basename(path))

    def _refresh_apis(self):
        """
        Recarrega o combo de APIs e armazena name→id em self.api_map.
        """
        self.api_combo.clear()
        self.api_map.clear()
        try:
            apis = self.controller.list_apis()
            for api in apis:
                name = api.get("name")
                api_id = api.get("id")
                self.api_map[name] = api_id
                self.api_combo.addItem(name)
            if not apis:
                self.api_combo.addItem("(no APIs)")
        except Exception as e:
            QMessageBox.critical(self, "API Gateway", str(e))

    def _on_delete_api(self):
        name = self.api_combo.currentText()
        api_id = self.api_map.get(name)
        if not api_id:
            QMessageBox.warning(self, "API Gateway", "Selecione uma API para excluir.")
            return
        confirm = QMessageBox.question(
            self, "Delete API",
            f"Deseja excluir a API '{api_id}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return
        try:
            self.controller.delete_api(api_id)
            QMessageBox.information(self, "API Gateway", f"API '{api_id}' excluída.")
            self._refresh_apis()
        except Exception as e:
            QMessageBox.critical(self, "API Gateway", str(e))

    def _on_api_change(self, _):
        name = self.api_combo.currentText()
        api_id = self.api_map.get(name)
        self.current_api_id = api_id
        self.session.update("apigateway", {"selected_api": api_id})
        if api_id:
            try:
                raw = self.controller.get_api_definition(api_id, "dev", "oas30")
                pretty = json.dumps(json.loads(raw), indent=2)
            except Exception as e:
                pretty = f"Não foi possível obter definição: {e}"
        else:
            pretty = "{}"

        if name and api_id:
            self.api_definition_label .setText(f"API Definition (JSON) - {name} ({api_id})")
        else:
            self.api_definition_label.setText("API Definition (JSON)")

        self.detail_view.setPlainText(pretty)

        self.tree.clear()
        if api_id:
            self._load_endpoints(api_id)

    def _load_endpoints(self, api_id: str):
        self.tree.clear()
        self.endpoints = []
        root = QTreeWidgetItem(["/"])
        self.tree.addTopLevelItem(root)
        for ep in self.controller.list_endpoints(api_id):
            self.endpoints.append(ep)
            parts = ep["path"].strip("/").split("/")
            node = root
            for seg in parts:
                if not seg:
                    continue
                found = next((node.child(i) for i in range(node.childCount()) if node.child(i).text(0) == seg), None)
                if not found:
                    found = QTreeWidgetItem([seg])
                    node.addChild(found)
                node = found
            # method item carries (resourceId, method, path_template)
            method_item = QTreeWidgetItem([ep["method"]])
            method_item.setData(0, Qt.UserRole, (ep["resourceId"], ep["method"], ep["path"]))
            node.addChild(method_item)
        root.setExpanded(True)

    def _on_tree_item_clicked(self, item, _):
        text = item.text(0)
        data = item.data(0, Qt.UserRole)
        if not data or text not in self.HTTP_METHODS:
            return
        resource_id, method, path_template = data

        self.path_input.setText(path_template)
        for i in reversed(range(self.path_params_form.count())):
            self.path_params_form.removeRow(i)
        self.path_param_inputs.clear()
        for i in reversed(range(self.query_params_form.count())):
            self.query_params_form.removeRow(i)
        self.query_param_inputs.clear()

        cfg = self.controller.get_method(self.current_api_id, resource_id, method)
        integration = self.controller.get_integration(self.current_api_id, resource_id, method)
        details = {
            "methodConfig": cfg,
            "integrationConfig": integration or {}
        }
        self.endpoint_detail_view.setPlainText(json.dumps(details, indent=2))

        if cfg:
            uri = cfg.get("uri") or cfg.get("integrationUri") or ""
            self.current_uri = uri
            self.integration_input.setText(uri)
            self._current_integration_type = cfg.get("type", "HTTP_PROXY")
            self._current_resource_id = resource_id
            self._current_http_method = method

            for i in reversed(range(self.header_params_form.count())):
                self.header_params_form.removeRow(i)
            self.header_param_inputs = {}

            params = cfg.get("requestParameters") or {}
            for full_name, required in params.items():
                if full_name.startswith("method.request.path."):
                    name = full_name.split('.')[-1]
                    le = QLineEdit()
                    if required:
                        le.setPlaceholderText("required")
                    self.path_param_inputs[name] = le
                    self.path_params_form.addRow(f"{name}:", le)
                elif full_name.startswith("method.request.querystring."):
                    name = full_name.split('.')[-1]
                    le = QLineEdit()
                    if required:
                        le.setPlaceholderText("required")
                    self.query_param_inputs[name] = le
                    self.query_params_form.addRow(f"{name}:", le)
                elif full_name.startswith("method.request.header."):
                    name = full_name.split('.')[-1]
                    le = QLineEdit()
                    le.setPlaceholderText(f"{name} (optional)")
                    le.setToolTip(f"Header parameter: {name}")
                    le.setMinimumWidth(200)
                    le.setMinimumHeight(50)
                    le.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                    if required:
                        le.setPlaceholderText("required")
                    self.header_param_inputs[name] = le
                    self.header_params_form.addRow(f"{name}:", le)

            self._current_parameters = {"path": [], "query": [], "header": []}
            for full, req in cfg.get("requestParameters", {}).items():
                if full.startswith("method.request.path."):
                    n = full.rsplit(".", 1)[-1]
                    self._current_parameters["path"].append({
                        "name": n, "required": True, "schema": {"type": "string"}
                    })
                elif full.startswith("method.request.querystring."):
                    n = full.rsplit(".", 1)[-1]
                    self._current_parameters["query"].append({
                        "name": n, "required": req, "schema": {"type": "string"}
                    })
                elif full.startswith("method.request.header."):
                    n = full.rsplit(".", 1)[-1]
                    self._current_parameters["header"].append({
                        "name": n, "required": req, "schema": {"type": "string"}
                    })
        self.body_input.setPlainText("{}")

        self.load_session(method, path_template)


    def _on_call_endpoint(self):
        api_id = self.current_api_id
        path_template = self.path_input.text().strip()
        method = self.tree.currentItem().text(0) if self.tree.currentItem() else None
        if not api_id or not path_template or method not in self.HTTP_METHODS:
            QMessageBox.warning(self, "API Gateway", "Selecione um método válido.")
            return

        path = path_template
        for name, le in self.path_param_inputs.items():
            val = le.text().strip()
            if not val:
                QMessageBox.warning(self, "API Gateway", f"O path parameter '{name}' é obrigatório.")
                return
            path = path.replace(f"{{{name}}}", val)

        qp = {}
        for name, le in self.query_param_inputs.items():
            val = le.text().strip()
            if le.placeholderText() == "required" and not val:
                QMessageBox.warning(self, "API Gateway", f"O query parameter '{name}' é obrigatório.")
                return
            if val:
                qp[name] = val

        headers = {}
        for name, le in self.header_param_inputs.items():
            val = le.text().strip()
            if le.placeholderText() == "required" and not val:
                QMessageBox.warning(self, "API Gateway", f"O header '{name}' é obrigatório.")
                return
            if val:
                headers[name] = val

        body_text = self.body_input.toPlainText().strip() or "{}"
        try:
            body = json.loads(body_text)
        except Exception as e:
            QMessageBox.warning(self, "API Gateway", f"Body inválido: {e}")
            return

        port = self.get_port()
        path_clean = path.lstrip("/")
        url = f"http://localhost:{port}/restapis/{api_id}/dev/_user_request_/{path_clean}"
        headers = {name: le.text().strip() for name, le in self.header_param_inputs.items() if le.text().strip()}
        try:
            resp = requests.request(method, url, params=qp, json=body, headers=headers)
            try:
                parsed = resp.json()
                pretty = json.dumps(parsed, indent=2)
            except Exception:
                pretty = resp.text
            self.response_output.setPlainText(f"{resp.status_code}:\n{pretty}")
        except Exception as e:
            QMessageBox.critical(self, "API Gateway", f"Erro ao chamar endpoint: {e}")
        finally:
            self.save_session()

    def _on_create_api(self):
        name = self.name_input.text().strip()
        desc = self.desc_input.text().strip()
        if not name:
            QMessageBox.warning(self, "API Gateway", "Informe o nome da API.")
            return
        try:
            api = self.controller.create_api(name, desc)

            self.controller.ensure_integrations(api["id"])

            self.controller.create_deployment(api["id"], "dev")

            QMessageBox.information(
                self, "API Gateway",
                f"API created: {api['id']}\nDeployed to stage 'dev'"
            )
            self.name_input.clear()
            self.desc_input.clear()
            self._refresh_apis()
        except Exception as e:
            QMessageBox.critical(self, "API Gateway", str(e))

    def _on_add_endpoint(self):
        path = self.new_path_input.text().strip()
        method = self.new_method_combo.currentText()
        api_id = self.current_api_id
        if not api_id or not path or method not in self.HTTP_METHODS:
            QMessageBox.warning(self, "API Gateway", "Informe um path e método válidos.")
            return
        try:
            self.controller.create_endpoint(api_id, path, method)
            self.controller.ensure_integrations(api_id)
            self.controller.create_deployment(api_id, "dev")
            QMessageBox.information(self, "API Gateway", f"Endpoint {method} {path} criado.")
            self._load_endpoints(api_id)
        except Exception as e:
            QMessageBox.critical(self, "API Gateway", str(e))

    def _on_update_integration(self):
        api_id = self.current_api_id
        rid = getattr(self, "_current_resource_id", None)
        method = getattr(self, "_current_http_method", None)

        sel_fn = self.lambda_combo.currentText()
        if sel_fn and sel_fn != "(none)":
            fn_arn = f"arn:aws:lambda:us-east-1:000000000000:function:{sel_fn}"
            uri = f"arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/{fn_arn}/invocations"
            itype = "AWS_PROXY"
        else:
            base_uri = self.integration_input.text().strip().rstrip('/')
            if not base_uri.startswith(("http://", "https://")):
                base_uri = f"http://{base_uri}"
            path_tpl = self.path_input.text()
            uri = f"{base_uri}{path_tpl}"
            itype = getattr(self, "_current_integration_type", "HTTP_PROXY")
            confirm = QMessageBox.question(
                self, "Confirm Integration Update",
                f"Você tem certeza que deseja atualizar a integração para:\n{uri}",
                QMessageBox.Ok | QMessageBox.Cancel
            )

            if confirm != QMessageBox.Ok:
                return

        if not api_id or not rid or not method or not uri:
            QMessageBox.warning(self, "API Gateway", "Selecione um método e informe a URI ou Lambda.")
            return
        try:
            self.controller.update_integration(api_id, rid, method, itype, uri)
            self.controller.create_deployment(api_id, "dev")
            self._on_tree_item_clicked(self.tree.currentItem(), None)
            QMessageBox.information(self, "API Gateway", f"Integration updated to:\n{uri}")

            self.current_uri = uri
            self.save_session()
        except Exception as e:
            QMessageBox.critical(self, "API Gateway", str(e))

    def load_session(self, method, path_template):
        endpoint_key = f"{method} {path_template}"
        api_sess = self.session.get_api_session(self.current_api_id)
        saved = api_sess.get("endpoints", {}).get(endpoint_key)
        if saved:
            integ = saved.get("integration", {})
            itype = integ.get("type")
            if itype:
                self._current_integration_type = itype

            for name, le in self.path_param_inputs.items():
                le.setText(saved["path"].get(name, ""))

            for name, le in self.query_param_inputs.items():
                le.setText(saved["query"].get(name, ""))

            for name, le in self.header_param_inputs.items():
                le.setText(saved["header"].get(name, ""))

            try:
                body_json = saved.get("body", {})
                self.body_input.setPlainText(json.dumps(body_json, indent=2))
            except Exception:
                self.body_input.setPlainText(str(saved.get("body", "")))

    def save_session(self):
        try:
            resource_id, http_method, path_tpl = self.tree.currentItem().data(0, Qt.UserRole)
            endpoint_key = f"{http_method.upper()} {path_tpl}"
            api_sess = self.session.get_api_session(self.current_api_id)
            endpoints = api_sess.get("endpoints", {})

            endpoints[endpoint_key] = {
                "path": {n: le.text() for n, le in self.path_param_inputs.items()},
                "query": {n: le.text() for n, le in self.query_param_inputs.items()},
                "header": {n: le.text() for n, le in self.header_param_inputs.items()},
                "body": json.loads(self.body_input.toPlainText() or "{}"),
                "integration": {
                    "type": getattr(self, "_current_integration_type", None),
                    "uri": self.current_uri
                }
            }

            self.session.update_api_session(
                self.current_api_id,
                {"endpoints": endpoints}
            )
        except Exception as e:
            QMessageBox.critical(self, "API Gateway", f"Erro ao salvar sessão: {e}")


    def _on_import_api(self):
        if not self.selected_file:
            QMessageBox.warning(self, "API Gateway", "Selecione um arquivo OpenAPI.")
            return
        try:
            with open(self.selected_file, "r", encoding="utf-8") as f:
                content = f.read()
            api = self.controller.import_api(content)
            if not api:
                QMessageBox.warning(self, "API Gateway", "Não foi possível importar a API.")
                return

            self.current_api_id = api["id"]
            self.controller.ensure_integrations(api["id"])

            self.controller.create_deployment(api["id"], "dev")

            self.session.update_api_session(
                self.current_api_id,
                {"last_import_file": self.selected_file}
            )

            QMessageBox.information(
                self, "API Gateway",
                f"API imported: {api['id']}\nDeployed to stage 'dev'"
            )
            self._refresh_apis()
        except Exception as e:
            QMessageBox.critical(self, "API Gateway", str(e))

    def _on_import_complex_api(self):
       path = self.selected_file
       try:
           if not path:
               QMessageBox.warning(self, "API Gateway", "Selecione um arquivo OpenAPI com referências.")
               return
           api = self.controller.import_complex_api(path)
           # aplica integrações e deploy
           self.controller.ensure_integrations(api["id"])
           self.controller.create_deployment(api["id"], "dev")
           QMessageBox.information(self, "API Gateway", f"API complex imported: {api['id']}")
           self._refresh_apis()
       except Exception as e:
           QMessageBox.critical(self, "API Gateway", str(e))

    def _on_tree_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        data = item.data(0, Qt.UserRole) if item else None
        if not data:
            return

        resource_id, http_method, path_tpl = data

        menu = QMenu(self)
        manage = menu.addMenu("Manage Endpoint")
        edit = manage.addAction("Edit Parameters")
        delete = manage.addAction("Delete Endpoint")

        action = menu.exec_(self.tree.viewport().mapToGlobal(pos))
        if action == edit:
            self._open_params_dialog(item)
        elif action == delete:
            resp = QMessageBox.question(
                self,
                "Confirmar Exclusão",
                f"Deseja realmente excluir o endpoint {http_method} {path_tpl}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if resp == QMessageBox.Yes:
                try:
                    api_id = self.current_api_id

                    self.controller.delete_endpoint(api_id, resource_id, http_method)

                    api_sess  = self.session.get_api_session(api_id)
                    endpoints = api_sess.get("endpoints", {})
                    endpoint_key = f"{http_method} {path_tpl}"
                    endpoints.pop(endpoint_key, None)
                    self.session.update_api_session(api_id, {"endpoints": endpoints})

                    # recarrega UI
                    self._load_endpoints(api_id)
                    QMessageBox.information(self, "API Gateway", "Endpoint excluído com sucesso.")
                except Exception as e:
                    QMessageBox.critical(self, "API Gateway", f"Erro ao excluir endpoint: {e}")

    def _open_params_dialog(self, item):
        dlg = ParamsDialog(
            path_params=self._current_parameters.get("path", []),
            query_params=self._current_parameters.get("query", []),
            header_params=self._current_parameters.get("header", []),
            parent=self
        )

        if dlg.exec_() == QDialog.Accepted:
            vals = dlg.get_values()
            params = vals["path"] + vals["query"] + vals["header"]
            try:
                self.controller.update_parameters(
                    self.current_api_id,
                    self._current_resource_id,
                    self._current_http_method,
                    params
                )
                self.controller.create_deployment(self.current_api_id, "dev")
                self._on_tree_item_clicked(item, None)
                QMessageBox.information(self, "API Gateway", "Parameters atualizados com sucesso.")
            except Exception as e:
                QMessageBox.critical(self, "API Gateway", f"Erro ao atualizar parâmetros: {e}")
