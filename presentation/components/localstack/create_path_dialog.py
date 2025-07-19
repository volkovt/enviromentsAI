from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QCheckBox, QLineEdit, QComboBox


class NewPathDialog(QDialog):
    def __init__(self, methods: set, lambda_controller, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(500)
        self.setWindowTitle("Adicionar Path Completo")
        self.methods = methods
        self.lambda_controller = lambda_controller
        self._build_ui()

    def _build_ui(self):
        layout = QFormLayout(self)
        self.path_input = QLineEdit()
        self.path_input.setToolTip("Caminho do endpoint (ex: /users/{userId})")
        self.path_input.setPlaceholderText("Ex: /users/{userId} ou /products/{productId}/reviews")
        self.path_input.textChanged.connect(self.on_path_changed)
        self.method_combo = QComboBox()
        self.method_combo.addItems(self.methods)
        self.method_combo.setToolTip("Selecione o método HTTP para o endpoint")
        self.method_combo.setCurrentIndex(
            self.method_combo.findText("GET") if "GET" in self.methods else 0
        )
        self.method_combo.currentTextChanged.connect(self.on_method_changed)
        layout.addRow("Path:", self.path_input)
        layout.addRow("Method:", self.method_combo)

        self.summary_input = QLineEdit()
        self.summary_input.setToolTip("Breve descrição do endpoint")
        self.summary_input.setPlaceholderText("Ex: Obter detalhes do usuário")
        self.operation_id_input = QLineEdit()
        self.operation_id_input.setToolTip("ID único da operação (ex: getUserDetails)")
        self.operation_id_input.setPlaceholderText("Ex: getUserDetails ou listProducts")
        layout.addRow("Summary:", self.summary_input)
        layout.addRow("OperationId:", self.operation_id_input)

        self.integration_type = QComboBox()
        self.integration_type.setToolTip("Tipo de integração com o endpoint")
        self.integration_type.addItems(["HTTP_PROXY", "AWS_PROXY", "MOCK"])
        self.integration_type.currentTextChanged.connect(self.on_integration_type_changed)
        self.integration_http_method = QComboBox()
        self.integration_http_method.setToolTip("Método HTTP para a integração")
        self.integration_http_method.addItems(["GET","POST","PUT","DELETE","ANY"])
        self.integration_http_method.setCurrentIndex(0)
        self.integration_uri = QLineEdit()
        self.integration_uri.setToolTip("URI do endpoint de integração (ex: Lambda ARN ou URL)")
        self.payload_version = QLineEdit("2.0")
        self.payload_version.setToolTip("Versão do formato de payload (ex: 1.0, 2.0)")
        layout.addRow("Integration Type:", self.integration_type)
        layout.addRow("Integration HTTP Method:", self.integration_http_method)
        layout.addRow("Integration URI:", self.integration_uri)
        layout.addRow("Payload Format Ver.:", self.payload_version)

        btns = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel, self)
        btns.setToolTip("Clique em OK para criar o path ou Cancelar para fechar")
        btns.setCenterButtons(True)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

        self.integration_type.setCurrentIndex(0)
        self.on_integration_type_changed(self.integration_type.currentText())

    def on_method_changed(self, method):
        if not self.path_input.text().strip():
            return
        operation_id = self.build_operation_id(method, self.path_input.text())
        self.operation_id_input.setText(operation_id)

    def on_path_changed(self, text):
        if not text.strip():
            self.operation_id_input.clear()
            return
        method = self.method_combo.currentText()
        operation_id = self.build_operation_id(method, text)
        self.operation_id_input.setText(operation_id)

        if not text.startswith("/"):
            self.path_input.setText("/" + text.strip())

    def get_result(self):
        path = self.path_input.text().strip()
        method = self.method_combo.currentText().lower()
        if not path.startswith("/"):
            path = "/" + path.strip()

        if not self.operation_id_input.text().strip():
            operation_id = self.build_operation_id(method, path)
            self.operation_id_input.setText(operation_id)
        else:
            operation_id = self.operation_id_input.text().strip()
        if not self.integration_uri.text().strip():
            raise ValueError("A URI de integração não pode estar vazia.")
        if not self.integration_http_method.currentText():
            raise ValueError("O método HTTP de integração não pode estar vazio.")
        if not self.integration_type.currentText():
            raise ValueError("O tipo de integração não pode estar vazio.")
        if not self.payload_version.text().strip():
            raise ValueError("A versão do formato de payload não pode estar vazia.")

        if self.integration_uri.text().strip().endswith(":"):
            integration_uri = self.integration_uri.text().strip().removesuffix(":")
            self.integration_uri.setText(integration_uri)

        if not self.integration_uri.text().strip().endswith(path):
            uri = self.integration_uri.text().strip()
            if uri.endswith("/"):
                uri = uri[:-1]
            uri += path
            if uri.endswith("/"):
                uri = uri[:-1]

            self.integration_uri.setText(uri)

        path_item = {
            method: {
                "summary": self.summary_input.text().strip(),
                "operationId": operation_id,
                "parameters": [],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    }
                },
                "x-amazon-apigateway-integration": {
                    "uri": self.integration_uri.text().strip(),
                    "httpMethod": self.integration_http_method.currentText(),
                    "type": self.integration_type.currentText(),
                    "payloadFormatVersion": self.payload_version.text().strip()
                }
            }
        }
        return path, path_item

    def build_operation_id(self, method, path):
        parts = [p.title() for p in path.replace("{", "").replace("}", "").split("/") if p]
        return method.lower() + "".join(parts)

    def on_integration_type_changed(self, itype):
        """
        Preenche automaticamente a URI conforme o tipo escolhido:
          - HTTP_PROXY → http://localhost:
          - AWS_PROXY   → ARN da primeira Lambda disponível + /invocations
          - MOCK        → desabilita o campo e mostra placeholder criativo
        """
        # sempre habilita por padrão
        self.integration_uri.setDisabled(False)

        if itype == "HTTP_PROXY":
            self.integration_uri.setPlaceholderText("http://localhost:PORT")
            self.integration_uri.setText("http://localhost:")
        elif itype == "AWS_PROXY":
            try:
                funcs = self.lambda_controller.list_functions()
                arn = funcs[0]["FunctionArn"]
                region = arn.split(":")[3]
                uri = (
                    f"arn:aws:apigateway:{region}:lambda:path/2015-03-31/"
                    f"functions/{arn}/invocations"
                )
                self.integration_uri.setText(uri)
                self.integration_uri.setPlaceholderText("")
            except Exception:
                self.integration_uri.setText("")
                self.integration_uri.setPlaceholderText("<selecione ou configure uma Lambda>")
        else:  # MOCK
            self.integration_uri.clear()
            self.integration_uri.setDisabled(True)
            self.integration_uri.setPlaceholderText("Isso é um mock, não precisa de URI")
