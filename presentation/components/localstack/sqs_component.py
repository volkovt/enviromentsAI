from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QLineEdit,
    QPushButton, QCheckBox, QMessageBox
)

import qtawesome as qta
from controller.localstack.sqs_controller import SQSController

class SQSComponent(QWidget):
    """
    Componente responsável por toda a interface de SQS:
    listar filas, criar/excluir filas, enviar e visualizar mensagens.
    """
    def __init__(self, controller: SQSController, port_input):
        super().__init__()
        self.controller = controller
        self.get_port = port_input.value
        self._build_ui()
        self.refresh_queues()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # 1) Lista de filas
        self.queue_list = QListWidget()
        layout.addWidget(self.queue_list)

        # 2) Criar / Excluir fila
        btn_layout = QHBoxLayout()
        self.queue_name_input = QLineEdit()
        self.queue_name_input.setPlaceholderText("Nome da fila")
        btn_layout.addWidget(self.queue_name_input)

        self.create_btn = QPushButton(qta.icon("fa5s.plus", color="orange"), "")
        self.create_btn.setToolTip("Criar fila")
        self.create_btn.clicked.connect(self.create_queue)
        btn_layout.addWidget(self.create_btn)

        self.delete_btn = QPushButton(qta.icon("fa5s.trash", color="red"), "")
        self.delete_btn.setToolTip("Excluir fila")
        self.delete_btn.clicked.connect(self.delete_queue)
        btn_layout.addWidget(self.delete_btn)

        layout.addLayout(btn_layout)

        # 3) Enviar mensagem
        send_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Mensagem")
        send_layout.addWidget(self.message_input)

        self.send_btn = QPushButton(qta.icon("fa5s.paper-plane", color="orange"), "")
        self.send_btn.setToolTip("Enviar mensagem")
        self.send_btn.clicked.connect(self.send_message)
        send_layout.addWidget(self.send_btn)

        layout.addLayout(send_layout)

        # 4) Espiar / consumir mensagens
        self.consume_chk = QCheckBox("Consumir ao visualizar")
        self.consume_chk.setChecked(True)
        layout.addWidget(self.consume_chk)

        self.view_btn = QPushButton("Ver mensagens")
        self.view_btn.clicked.connect(self.view_messages)
        layout.addWidget(self.view_btn)

        # 5) Lista de mensagens
        self.message_list = QListWidget()
        layout.addWidget(self.message_list)

    def refresh_queues(self):
        try:
            queues = self.controller.list_queues()
            self.queue_list.clear()
            if queues:
                self.queue_list.addItems(queues)
            else:
                self.queue_list.addItem("(nenhuma fila)")
        except Exception as e:
            QMessageBox.critical(self, "Erro SQS", str(e))

    def create_queue(self):
        name = self.queue_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "SQS", "Informe o nome da fila.")
            return
        try:
            url = self.controller.create_queue(name)
            QMessageBox.information(self, "SQS", f"Fila criada:\n{url}")
            self.refresh_queues()
            self.queue_name_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "Erro SQS", str(e))

    def delete_queue(self):
        item = self.queue_list.currentItem()
        if not item or item.text().startswith("("):
            QMessageBox.warning(self, "SQS", "Selecione uma fila.")
            return
        try:
            self.controller.delete_queue(item.text())
            QMessageBox.information(self, "SQS", "Fila excluída com sucesso.")
            self.refresh_queues()
        except Exception as e:
            QMessageBox.critical(self, "Erro SQS", str(e))

    def send_message(self):
        item = self.queue_list.currentItem()
        body = self.message_input.text().strip()
        if not item or not body:
            QMessageBox.warning(self, "SQS", "Selecione a fila e informe a mensagem.")
            return
        try:
            msg_id = self.controller.send_message(item.text(), body)
            QMessageBox.information(self, "SQS", f"Mensagem enviada. ID: {msg_id}")
            self.message_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "Erro SQS", str(e))

    def view_messages(self):
        item = self.queue_list.currentItem()
        if not item:
            QMessageBox.warning(self, "SQS", "Selecione uma fila.")
            return
        try:
            msgs = self.controller.receive_messages(
                item.text(),
                consume=self.consume_chk.isChecked()
            )
            self.message_list.clear()
            if msgs:
                for m in msgs:
                    self.message_list.addItem(m.get("Body", ""))
            else:
                self.message_list.addItem("(nenhuma mensagem)")
        except Exception as e:
            QMessageBox.critical(self, "Erro SQS", str(e))
