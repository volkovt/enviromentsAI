import datetime
import json

from PyQt5.QtCore import pyqtSignal, QThread
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit,
    QComboBox, QMessageBox, QFileDialog
)
import qtawesome as qta

class KafkaWorker(QThread):
    success = pyqtSignal(str, object)
    error   = pyqtSignal(str, str)

    def __init__(self, controller, action: str, *args):
        super().__init__()
        self.controller = controller
        self.action     = action
        self.args       = args

    def run(self):
        try:
            if self.action == "start":
                self.controller.start()
                self.success.emit("start", None)
            elif self.action == "stop":
                self.controller.stop()
                self.success.emit("stop", None)
            elif self.action == "register_schema":
                topic, avsc = self.args
                res = self.controller.register_schema(topic, avsc)
                self.success.emit("register_schema", res)
            elif self.action == "get_schema":
                topic = self.args[0]
                schema = self.controller.get_schema(topic)
                self.success.emit("get_schema", schema)
            elif self.action == "produce_avro":
                topic, record, avsc = self.args
                self.controller.produce_avro(topic, record, avsc)
                self.success.emit("produce", record)
            elif self.action == "consume_avro":
                topic, avsc = self.args
                recs = self.controller.consume_avro(topic, avsc)
                self.success.emit("consume", recs)
            elif self.action == "produce":
                topic, text = self.args
                self.controller.produce(topic, text)
                self.success.emit("produce", text)
            elif self.action == "consume":
                topic = self.args[0]
                output = self.controller.consume(topic)
                self.success.emit("consume", output)
            elif self.action == "list_topics":
                topics = self.controller.list_topics()
                self.success.emit("list_topics", topics)
            elif self.action == "create_topic":
                topic = self.args[0]
                self.controller.create_topic(topic)
                self.success.emit("create_topic", None)
        except Exception as e:
            self.error.emit(self.action, str(e))

class KafkaComponent(QWidget):
    """UI para gerenciar container Kafka: start/stop, tópicos, produzir/consumir mensagens."""
    def __init__(self, controller, port_provider: callable):
        super().__init__()
        self.avsc_str = None
        self.controller = controller
        self.get_port = port_provider
        self._build_ui()

        # checa estado inicial
        try:
            running = self.controller.is_running()
        except Exception:
            running = False
        self._update_status(running)

        # se já está rodando, carrega tópicos
        if running:
            self._on_refresh_topics()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.status_label = QLabel("Status: Parado")
        layout.addWidget(self.status_label)

        h = QHBoxLayout()
        self.start_btn = QPushButton(qta.icon("fa5s.play", color="orange"), "Iniciar Kafka")
        self.start_btn.clicked.connect(self._on_start)
        h.addWidget(self.start_btn)
        self.stop_btn = QPushButton(qta.icon("fa5s.stop", color="orange"), "Parar Kafka")
        self.stop_btn.clicked.connect(self._on_stop)
        h.addWidget(self.stop_btn)
        layout.addLayout(h)

        h = QHBoxLayout()
        h.addWidget(QLabel("Novo tópico:"))
        self.topic_input = QLineEdit()
        h.addWidget(self.topic_input)
        btn = QPushButton(qta.icon("fa5s.plus", color="orange"), "")
        btn.setToolTip("Criar tópico")
        btn.clicked.connect(self._on_create_topic)
        h.addWidget(btn)
        layout.addLayout(h)

        h = QHBoxLayout()
        h.addWidget(QLabel("Tópicos:"))
        self.topic_combo = QComboBox()
        self.topic_combo.currentIndexChanged.connect(self._on_topic_selected)
        h.addWidget(self.topic_combo)
        btn = QPushButton(qta.icon("fa5s.sync", color="orange"), "")
        btn.setToolTip("Atualizar tópicos")
        btn.clicked.connect(self._on_refresh_topics)
        h.addWidget(btn)
        layout.addLayout(h)

        schema_layout = QHBoxLayout()
        schema_layout.addWidget(QLabel("Schema Avro:"))
        self.schema_label = QLabel("nenhum")
        schema_layout.addWidget(self.schema_label, stretch=1)
        btn_schema = QPushButton("Anexar .avsc")
        btn_schema.clicked.connect(self._on_attach_schema)
        schema_layout.addWidget(btn_schema)
        layout.addLayout(schema_layout)

        h = QHBoxLayout()
        h.addWidget(QLabel("Mensagem:"))
        self.msg_input = QLineEdit()
        h.addWidget(self.msg_input)
        btn = QPushButton(qta.icon("fa5s.paper-plane", color="green"), "")
        btn.setToolTip("Produzir mensagem")
        btn.clicked.connect(self._on_produce)
        h.addWidget(btn)
        layout.addLayout(h)

        h = QHBoxLayout()
        h.addWidget(QLabel("Consumir de:"))
        self.consume_combo = QComboBox()
        h.addWidget(self.consume_combo)
        btn = QPushButton(qta.icon("fa5s.download", color="blue"), "")
        btn.setToolTip("Consumir mensagens")
        btn.clicked.connect(self._on_consume)
        h.addWidget(btn)
        layout.addLayout(h)

        layout.addWidget(QLabel("Mensagens recebidas:"))
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

    def _on_attach_schema(self):
        path, _ = QFileDialog.getOpenFileName(self, "Selecione schema .avsc", "", "AVSC Files (*.avsc)")
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            avsc = f.read()
        # registra schema em background
        self.worker = KafkaWorker(self.controller, "register_schema", self.topic_combo.currentText(), avsc)
        self.worker.success.connect(self._on_schema_registered)
        self.worker.error.connect(self._on_worker_error)
        self.worker.start()

    def _on_topic_selected(self, index: int):
        topic = self.topic_combo.itemText(index)
        if not topic:
            return
        self.worker = KafkaWorker(self.controller, "get_schema", topic)
        self.worker.success.connect(self._on_worker_success)
        self.worker.error.connect(self._on_worker_error)
        self.worker.start()

    def _on_schema_registered(self, action: str, result):
        self.avsc_str = self.worker.args[1]
        self.schema_label.setText("carregado")

    def _update_status(self, running: bool):
        self.status_label.setText(f"Status: {'Rodando' if running else 'Parado'}")
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)

    def _on_start(self):
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.worker = KafkaWorker(self.controller, "start")
        self.worker.success.connect(self._on_worker_success)
        self.worker.error.connect(self._on_worker_error)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def _on_stop(self):
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.worker = KafkaWorker(self.controller, "stop")
        self.worker.success.connect(self._on_worker_success)
        self.worker.error.connect(self._on_worker_error)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def _on_create_topic(self):
        nome = self.topic_input.text().strip()
        if not nome:
            QMessageBox.warning(self, "Aviso", "Informe o nome do tópico.")
            return
        self.worker = KafkaWorker(self.controller, "create_topic", nome)
        self.worker.success.connect(self._on_worker_success)
        self.worker.error.connect(self._on_worker_error)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def _on_refresh_topics(self):
        self.worker = KafkaWorker(self.controller, "list_topics")
        self.worker.success.connect(self._on_worker_success)
        self.worker.error.connect(self._on_worker_error)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def _on_produce(self):
        topic = self.topic_combo.currentText()
        text = self.msg_input.text().strip()
        if not topic or not text:
            QMessageBox.warning(self, "Aviso", "Selecione tópico e informe mensagem.")
            return

        if self.avsc_str:
            try:
                record = json.loads(text)
            except json.JSONDecodeError as e:
                QMessageBox.warning(self, "JSON inválido", str(e))
                return
            self.worker = KafkaWorker(self.controller, "produce_avro", topic, record, self.avsc_str)
        else:
            self.worker = KafkaWorker(self.controller, "produce", topic, text)

        self.worker.success.connect(self._on_worker_success)
        self.worker.error.connect(self._on_worker_error)
        self.worker.start()

    def _on_consume(self):
        topic = self.consume_combo.currentText()
        if not topic:
            QMessageBox.warning(self, "Aviso", "Selecione o tópico.")
            return

        if self.avsc_str:
            self.worker = KafkaWorker(self.controller, "consume_avro", topic, self.avsc_str)
        else:
            self.worker = KafkaWorker(self.controller, "consume", topic)

        self.worker.success.connect(self._on_worker_success)
        self.worker.error.connect(self._on_worker_error)
        self.worker.start()

    def _serialize(self, o):
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        raise TypeError(f"Type {type(o)} not serializable")

    def _on_worker_success(self, action: str, result):
        if action == "start":
            self._update_status(True)
            self._on_refresh_topics()
        elif action == "stop":
            self._update_status(False)
            self.topic_combo.clear()
            self.consume_combo.clear()
            self.output.clear()
        elif action == "list_topics":
            self.topic_combo.clear()
            self.consume_combo.clear()
            self.topic_combo.addItems(result)
            self.consume_combo.addItems(result)
        elif action == "create_topic":
            self.topic_input.clear()
            self._on_refresh_topics()
        elif action == "get_schema":
            schema = result
            if schema:
                self.avsc_str = schema
                self.schema_label.setText("schema carregado")
            else:
                self.avsc_str = None
                self.schema_label.setText("nenhum schema")
        elif action == "produce":
            self.msg_input.clear()
            self.output.append(f"[enviado] {result}")
        elif action == "consume":
            if isinstance(result, list):
                if not result:
                    self.output.append("[nenhuma mensagem recebida]")
                else:
                    for rec in result:
                        self.output.append(
                            f"[consumido] {json.dumps(rec, ensure_ascii=False, default=self._serialize)}"
                        )
            else:
                text = str(result)
                if not text.strip():
                    self.output.append("[nenhuma mensagem recebida]")
                else:
                    for linha in text.splitlines():
                        self.output.append(f"[consumido] {linha}")

    def _on_worker_error(self, action: str, msg: str):
        QMessageBox.critical(self, f"Erro em {action}", msg)
        # restaura botões
        running = self.controller.is_running()
        self._update_status(running)