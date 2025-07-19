import json
from decimal import Decimal

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QLineEdit, QPushButton, QMessageBox, QLabel, QFileDialog
)
import qtawesome as qta

from controller.localstack.dynamodb_controller import DynamoDBController


class DynamoDBComponent(QWidget):
    """
    Componente de UI para operações de DynamoDB:
    tabelas, itens, exclusão em lote e upload de JSON.
    """
    def __init__(self, controller: DynamoDBController, port_input):
        super().__init__()
        self.controller = controller
        self._items = []  # armazena dicts dos itens atuais
        self._build_ui()
        self._refresh_tables()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Tabelas
        layout.addWidget(QLabel("Tabelas:"))
        self.table_list = QListWidget()
        self.table_list.currentItemChanged.connect(lambda *_: self._refresh_items())
        layout.addWidget(self.table_list)

        # Criar / Excluir tabela
        tbl_btn_layout = QHBoxLayout()
        self.table_name_input = QLineEdit()
        self.table_name_input.setPlaceholderText("Nome da tabela")
        tbl_btn_layout.addWidget(self.table_name_input)
        create_tbl_btn = QPushButton(qta.icon("fa5s.plus", color="orange"), "")
        create_tbl_btn.setToolTip("Criar tabela")
        create_tbl_btn.clicked.connect(self._on_create_table)
        tbl_btn_layout.addWidget(create_tbl_btn)
        delete_tbl_btn = QPushButton(qta.icon("fa5s.trash", color="red"), "")
        delete_tbl_btn.setToolTip("Excluir tabela")
        delete_tbl_btn.clicked.connect(self._on_delete_table)
        tbl_btn_layout.addWidget(delete_tbl_btn)
        layout.addLayout(tbl_btn_layout)

        # Itens
        layout.addWidget(QLabel("Itens (campos dinâmicos):"))
        self.item_list = QListWidget()
        layout.addWidget(self.item_list)

        # Inserir item
        item_btn_layout = QHBoxLayout()
        self.item_id_input = QLineEdit()
        self.item_id_input.setPlaceholderText("ID do item")
        item_btn_layout.addWidget(self.item_id_input)
        self.item_data_input = QLineEdit()
        self.item_data_input.setPlaceholderText("Valor (string)")
        item_btn_layout.addWidget(self.item_data_input)
        put_btn = QPushButton(qta.icon("fa5s.upload", color="orange"), "")
        put_btn.setToolTip("Inserir item")
        put_btn.clicked.connect(self._on_put_item)
        item_btn_layout.addWidget(put_btn)
        layout.addLayout(item_btn_layout)

        # Ações de itens
        action_layout = QHBoxLayout()
        refresh_items_btn = QPushButton("Ver itens")
        refresh_items_btn.clicked.connect(self._refresh_items)
        action_layout.addWidget(refresh_items_btn)

        delete_item_btn = QPushButton(qta.icon("fa5s.trash", color="red"), "Excluir item")
        delete_item_btn.clicked.connect(self._on_delete_item)
        action_layout.addWidget(delete_item_btn)

        delete_all_btn = QPushButton(qta.icon("fa5s.trash-alt", color="red"), "Excluir todos")
        delete_all_btn.setToolTip("Excluir todos os itens da tabela")
        delete_all_btn.clicked.connect(self._on_delete_all_items)
        action_layout.addWidget(delete_all_btn)

        upload_json_btn = QPushButton(qta.icon("fa5s.upload", color="orange"), "Upload JSON")
        upload_json_btn.clicked.connect(self._on_upload_json)
        action_layout.addWidget(upload_json_btn)

        layout.addLayout(action_layout)

    def _refresh_tables(self):
        try:
            tables = self.controller.list_tables()
            self.table_list.clear()
            self.table_list.addItems(tables or ["(nenhuma tabela)"])
            self._refresh_items()
        except Exception as e:
            QMessageBox.critical(self, "DynamoDB", str(e))

    def _refresh_items(self):
        table = self.table_list.currentItem().text() if self.table_list.currentItem() else None
        self.item_list.clear()
        self._items = []
        if not table or table.startswith("("):
            return
        try:
            items = self.controller.list_items(table)
            self._items = items
            if items:
                for it in items:
                    item_str = ", ".join(f"{k}: {v}" for k, v in it.items())
                    self.item_list.addItem(item_str)
            else:
                self.item_list.addItem("(nenhum item)")
        except Exception as e:
            QMessageBox.critical(self, "DynamoDB", str(e))

    def _on_create_table(self):
        name = self.table_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "DynamoDB", "Informe o nome da tabela.")
            return
        try:
            self.controller.create_table(name)
            QMessageBox.information(self, "DynamoDB", "Tabela criada com sucesso.")
            self.table_name_input.clear()
            self._refresh_tables()
        except Exception as e:
            QMessageBox.critical(self, "DynamoDB", str(e))

    def _on_delete_table(self):
        table = self.table_list.currentItem().text() if self.table_list.currentItem() else None
        if not table or table.startswith("("):
            QMessageBox.warning(self, "DynamoDB", "Selecione uma tabela.")
            return
        try:
            self.controller.delete_table(table)
            QMessageBox.information(self, "DynamoDB", "Tabela excluída.")
            self._refresh_tables()
        except Exception as e:
            QMessageBox.critical(self, "DynamoDB", str(e))

    def _on_put_item(self):
        table = self.table_list.currentItem().text() if self.table_list.currentItem() else None
        item_id = self.item_id_input.text().strip()
        data = self.item_data_input.text().strip()
        if not table or table.startswith("(") or not item_id or not data:
            QMessageBox.warning(self, "DynamoDB", "Selecione tabela e informe ID e valor.")
            return
        try:
            self.controller.put_item(table, item_id, data)
            QMessageBox.information(self, "DynamoDB", "Item inserido.")
            self.item_id_input.clear()
            self.item_data_input.clear()
            self._refresh_items()
        except Exception as e:
            QMessageBox.critical(self, "DynamoDB", str(e))

    def _on_delete_item(self):
        idx = self.item_list.currentRow()
        table = self.table_list.currentItem().text() if self.table_list.currentItem() else None
        if not table or idx < 0 or idx >= len(self._items):
            QMessageBox.warning(self, "DynamoDB", "Selecione um item para excluir.")
            return
        item_id = self._items[idx].get('id')
        if item_id is None:
            QMessageBox.warning(self, "DynamoDB", "Item selecionado sem chave 'id'.")
            return
        try:
            self.controller.delete_item(table, item_id)
            QMessageBox.information(self, "DynamoDB", f"Item '{item_id}' excluído com sucesso.")
            self._refresh_items()
        except Exception as e:
            QMessageBox.critical(self, "DynamoDB", str(e))

    def _on_delete_all_items(self):
        table = self.table_list.currentItem().text() if self.table_list.currentItem() else None
        if not table or table.startswith("("):
            QMessageBox.warning(self, "DynamoDB", "Selecione uma tabela.")
            return
        confirm = QMessageBox.question(
            self, "Excluir todos os itens",
            f"Deseja excluir todos os itens da tabela '{table}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return
        try:
            count = 0
            for it in list(self._items):
                item_id = it.get('id')
                if item_id:
                    self.controller.delete_item(table, item_id)
                    count += 1
            QMessageBox.information(self, "DynamoDB", f"{count} itens excluídos.")
            self._refresh_items()
        except Exception as e:
            QMessageBox.critical(self, "DynamoDB", str(e))

    def _on_upload_json(self):
        table = self.table_list.currentItem().text() if self.table_list.currentItem() else None
        if not table or table.startswith("("):
            QMessageBox.warning(self, "DynamoDB", "Selecione uma tabela.")
            return
        path, _ = QFileDialog.getOpenFileName(self, "Selecione arquivo JSON", "", "JSON Files (*.json)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f, parse_float=Decimal)
            if not isinstance(data, list):
                QMessageBox.warning(self, "DynamoDB", "JSON deve ser uma lista de objetos.")
                return
            self.controller.batch_put_items(table, data)
            QMessageBox.information(self, "DynamoDB", f"{len(data)} itens inseridos via JSON.")
            self._refresh_items()
        except Exception as e:
            QMessageBox.critical(self, "DynamoDB", str(e))
