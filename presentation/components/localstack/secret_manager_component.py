from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QLineEdit, QPushButton, QMessageBox, QLabel, QInputDialog
)
import qtawesome as qta

class SecretManagerComponent(QWidget):
    """
    Componente de UI para operações de Secrets Manager:
    listar, criar, ver, atualizar e excluir segredos.
    """
    def __init__(self, controller, port_input):
        super().__init__()
        self.controller = controller
        self.get_port = port_input.value
        self._build_ui()
        self._refresh_secrets()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Lista de segredos
        layout.addWidget(QLabel("Segredos:"))
        self.secret_list = QListWidget()
        layout.addWidget(self.secret_list)

        # Criar segredo
        create_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nome do segredo")
        create_btn = QPushButton(qta.icon("fa5s.lock", color="orange"), "")
        create_btn.setToolTip("Criar segredo")
        create_btn.clicked.connect(self._on_create_secret)
        create_layout.addWidget(self.name_input)
        create_layout.addWidget(create_btn)
        layout.addLayout(create_layout)

        # Ações de visualização/atualização/exclusão
        btn_layout = QHBoxLayout()
        view_btn = QPushButton("Ver valor")
        view_btn.clicked.connect(self._on_view_secret)
        btn_layout.addWidget(view_btn)

        update_btn = QPushButton("Atualizar valor")
        update_btn.clicked.connect(self._on_update_secret)
        btn_layout.addWidget(update_btn)

        del_btn = QPushButton(qta.icon("fa5s.trash", color="red"), "Excluir")
        del_btn.clicked.connect(self._on_delete_secret)
        btn_layout.addWidget(del_btn)

        layout.addLayout(btn_layout)

    def _refresh_secrets(self):
        try:
            secrets = self.controller.list_secrets()
            self.secret_list.clear()
            for s in secrets:
                self.secret_list.addItem(s["Name"])
        except Exception as e:
            QMessageBox.critical(self, "Secrets Manager", str(e))

    def _on_create_secret(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Secrets Manager", "Informe o nome do segredo.")
            return
        value, ok = QInputDialog.getText(self, "Valor do segredo", "Informe o valor:")
        if not ok:
            return
        try:
            arn = self.controller.create_secret(name, value)
            QMessageBox.information(self, "Secrets Manager", f"Segredo criado:\n{arn}")
            self.name_input.clear()
            self._refresh_secrets()
        except Exception as e:
            QMessageBox.critical(self, "Secrets Manager", str(e))

    def _on_view_secret(self):
        item = self.secret_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Secrets Manager", "Selecione um segredo.")
            return
        try:
            value = self.controller.get_secret_value(item.text())
            QMessageBox.information(self, "Secrets Manager", f"Valor:\n{value}")
        except Exception as e:
            QMessageBox.critical(self, "Secrets Manager", str(e))

    def _on_update_secret(self):
        item = self.secret_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Secrets Manager", "Selecione um segredo.")
            return
        new_value, ok = QInputDialog.getText(self, "Novo valor", "Informe o novo valor:")
        if not ok:
            return
        try:
            version = self.controller.update_secret(item.text(), new_value)
            QMessageBox.information(self, "Secrets Manager", f"Segredo atualizado. Versão: {version}")
        except Exception as e:
            QMessageBox.critical(self, "Secrets Manager", str(e))

    def _on_delete_secret(self):
        item = self.secret_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Secrets Manager", "Selecione um segredo.")
            return
        confirm = QMessageBox.question(
            self, "Excluir Segredo",
            f"Deseja excluir '{item.text()}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return
        try:
            self.controller.delete_secret(item.text())
            QMessageBox.information(self, "Secrets Manager", "Segredo excluído.")
            self._refresh_secrets()
        except Exception as e:
            QMessageBox.critical(self, "Secrets Manager", str(e))
