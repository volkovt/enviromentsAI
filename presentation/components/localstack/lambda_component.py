from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QLabel, QLineEdit, QPushButton, QTextEdit,
    QFileDialog, QMessageBox, QListWidgetItem
)
import qtawesome as qta
import json
import os

class LambdaComponent(QWidget):
    """
    Componente de UI para listagem, deploy e invocação de funções Lambda no LocalStack.
    """
    def __init__(self, controller, port_input):
        super().__init__()
        self.controller = controller
        self.get_port = port_input.value
        self.selected_dir = None
        self._build_ui()
        self._refresh_functions()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Layout de deploy
        fn_layout = QHBoxLayout()
        fn_layout.addWidget(QLabel("Function Name:"))
        self.fn_input = QLineEdit()
        fn_layout.addWidget(self.fn_input)
        layout.addLayout(fn_layout)

        select_btn = QPushButton(qta.icon("fa5s.folder-open", color="orange"), "Select Folder")
        select_btn.clicked.connect(self._select_folder)
        fn_layout.addWidget(select_btn)
        self.dir_label = QLabel("No folder selected")
        fn_layout.addWidget(self.dir_label)
        layout.addLayout(fn_layout)

        # Listagem de funções
        layout.addWidget(QLabel("Existing Functions:"))
        self.func_list = QListWidget()
        layout.addWidget(self.func_list)
        list_btn = QPushButton("Refresh Functions")
        list_btn.clicked.connect(self._refresh_functions)
        layout.addWidget(list_btn)

        # Deploy / Invoke separado
        btn_layout = QHBoxLayout()
        self.deploy_btn = QPushButton(qta.icon("fa5s.upload", color="orange"), "Deploy")
        self.deploy_btn.clicked.connect(self._on_deploy)
        btn_layout.addWidget(self.deploy_btn)
        self.invoke_btn = QPushButton(qta.icon("fa5s.play", color="orange"), "Invoke")
        self.invoke_btn.clicked.connect(self._on_invoke)
        btn_layout.addWidget(self.invoke_btn)
        delete_btn = QPushButton(qta.icon("fa5s.trash", color="red"), "Delete")
        delete_btn.clicked.connect(self._on_delete)
        btn_layout.addWidget(delete_btn)
        layout.addLayout(btn_layout)

        layout.addLayout(btn_layout)

        # Payload
        layout.addWidget(QLabel("Payload (JSON):"))
        self.payload_input = QTextEdit()
        self.payload_input.setPlaceholderText("{}")
        layout.addWidget(self.payload_input)

        # Resultado
        layout.addWidget(QLabel("Result:"))
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

    def _select_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select Lambda Folder")
        if path:
            self.selected_dir = path
            self.dir_label.setText(os.path.basename(path))

    def _refresh_functions(self):
        """
        Recarrega a lista de funções exibindo nome e estado.
        Armazena o nome real no Qt.UserRole para usar nos handlers.
        """
        try:
            funcs = self.controller.list_functions()
            self.func_list.clear()
            for fn in funcs:
                cfg = self.controller.get_configuration(fn)
                state = cfg.get("State", "?")
                status = cfg.get("LastUpdateStatus", "?")
                display = f"{fn} [{state}/{status}]"
                item = QListWidgetItem(display)
                item.setData(Qt.UserRole, fn)
                self.func_list.addItem(item)
            if not funcs:
                self.func_list.addItem("(no functions)")
        except Exception as e:
            QMessageBox.critical(self, "Lambda", str(e))

    def _on_deploy(self):
        fn_name = self.fn_input.text().strip()
        if not fn_name:
            QMessageBox.warning(self, "Lambda", "Informe o nome da função.")
            return
        if not self.selected_dir:
            QMessageBox.warning(self, "Lambda", "Selecione a pasta do código.")
            return
        try:
            self.controller.deploy(fn_name, self.selected_dir)
            QMessageBox.information(self, "Lambda", "Função implantada com sucesso!")
            self._refresh_functions()
        except Exception as e:
            QMessageBox.critical(self, "Lambda", str(e))

    def _on_invoke(self):
        item = self.func_list.currentItem()
        fn_name = item.data(Qt.UserRole) if item else None
        if not fn_name:
            QMessageBox.warning(self, "Lambda", "Selecione uma função.")
            return
        payload_str = self.payload_input.toPlainText().strip() or "{}"
        try:
            payload = json.loads(payload_str)
        except Exception as e:
            QMessageBox.warning(self, "Lambda", f"Payload inválido: {e}")
            return
        try:
            result = self.controller.invoke(fn_name, payload)
            try:
                parsed = json.loads(result)
                pretty = json.dumps(parsed, indent=2)
            except Exception:
                pretty = result
            self.output.setPlainText(pretty)
        except Exception as e:
            QMessageBox.critical(self, "Lambda", str(e))

    def _on_delete(self):
        item = self.func_list.currentItem()
        fn_name = item.data(Qt.UserRole) if item else None
        if not fn_name:
            QMessageBox.warning(self, "Lambda", "Selecione uma função para excluir.")
            return
        confirm = QMessageBox.question(
            self, "Delete Lambda",
            f"Deseja excluir a função '{fn_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return
        try:
            self.controller.delete(fn_name)
            QMessageBox.information(self, "Lambda", f"Função '{fn_name}' excluída.")
            self._refresh_functions()
        except Exception as e:
            QMessageBox.critical(self, "Lambda", str(e))
