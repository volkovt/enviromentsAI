import logging

from PyQt5.QtGui import QShowEvent, QCursor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QSpinBox, QComboBox, QPushButton,
    QLabel, QMessageBox, QProgressDialog, QSizePolicy, QApplication, QFileDialog
)
from PyQt5.QtCore import QSize, Qt, QThread, pyqtSignal
import qtawesome as qta

from controller.localstack.apigateway_controller import APIGatewayController
from controller.localstack.dynamodb_controller import DynamoDBController
from controller.localstack.lambda_controller import LambdaController
from controller.localstack.localstack_controller import LocalStackController
from controller.localstack.s3_controller import S3Controller
from controller.localstack.secret_manager_controller import SecretManagerController
from controller.localstack.sqs_controller import SQSController
from presentation.components.localstack.apigateway_component import APIGatewayComponent
from presentation.components.localstack.dynamodb_component import DynamoDBComponent
from presentation.components.localstack.lambda_component import LambdaComponent
from presentation.components.localstack.s3_component import S3Component
from presentation.components.localstack.secret_manager_component import SecretManagerComponent
from presentation.components.localstack.sqs_component import SQSComponent
from services.localstack.export_service import ExportService
from services.localstack.localstack_session import LocalStackSession

logger = logging.getLogger("[ApplicationManager]")

class LocalStackWorker(QThread):
    """
    Worker para iniciar ou parar o LocalStack sem bloquear a UI.
    """
    success = pyqtSignal(bool)
    error = pyqtSignal(str)

    def __init__(self, controller, start: bool):
        super().__init__()
        self.controller = controller
        self.start_action = start

    def run(self):
        try:
            if self.start_action:
                self.controller.start()
            else:
                self.controller.stop()
            self.success.emit(self.start_action)
        except Exception as e:
            self.error.emit(str(e))


class LocalStackScreen(QWidget):
    """
    Tela genérica para gerenciar o container LocalStack e injetar
    componentes específicos (SQS, S3, etc.) com execução assíncrona.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LocalStack Manager")
        self.setBaseSize(800, 600)
        self._first_show = True

        self.setWindowIcon(qta.icon("fa5s.cube", color="orange"))
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAttribute(Qt.WA_QuitOnClose, False)
        self.setContentsMargins(10, 10, 10, 10)

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)
        self.status_label = QLabel("Status: Desconhecido")
        self.status_label.setContentsMargins(0, 0, 0, 50)

        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignLeft)
        header_layout.addWidget(self.status_label)
        main_layout.addLayout(header_layout)

        content_layout = QVBoxLayout()
        content_layout.setAlignment(Qt.AlignHCenter)
        content_layout.setContentsMargins(20, 0, 20, 0)
        main_layout.addLayout(content_layout)

        port_layout = QHBoxLayout()
        porta_label = QLabel("Porta:")
        porta_label.setFixedWidth(150)
        port_layout.addWidget(porta_label)
        self.port_input = QSpinBox()
        self.port_input.setMinimumWidth(500)
        self.port_input.setCursor(Qt.PointingHandCursor)
        self.port_input.setStyleSheet("font-weight: bold;")
        self.port_input.setToolTip("Porta do container LocalStack.")
        self.port_input.setSingleStep(1)
        self.port_input.setRange(1024, 65535)
        self.port_input.setValue(4566)
        port_layout.addWidget(self.port_input)
        content_layout.addLayout(port_layout)

        svc_layout = QHBoxLayout()
        svc_layout.setAlignment(Qt.AlignHCenter)
        svc_layout.setSpacing(10)
        svc_layout.setContentsMargins(0, 10, 0, 0)
        svc_label = QLabel("Serviço:")
        svc_label.setFixedWidth(150)
        svc_layout.addWidget(svc_label)
        self.svc_combo = QComboBox()
        self.svc_combo.setMinimumWidth(500)
        self.svc_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.svc_combo.setCursor(Qt.PointingHandCursor)
        self.svc_combo.setStyleSheet("font-weight: bold;")
        self.svc_combo.setToolTip("Selecione o serviço LocalStack a ser gerenciado.")
        self.svc_combo.setEditable(False)
        self.svc_combo.addItems(["Nenhum", "SQS", "S3", "Secrets Manager", "DynamoDB", "Lambda", "API Gateway"])
        self.svc_combo.currentTextChanged.connect(self._on_service_change)
        svc_layout.addWidget(self.svc_combo)
        content_layout.addLayout(svc_layout)

        self.service_container = QWidget()
        self.service_layout = QVBoxLayout(self.service_container)
        content_layout.addWidget(self.service_container)

        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignHCenter)
        btn_layout.setSpacing(20)
        btn_layout.setContentsMargins(0, 20, 0, 0)
        self.start_btn = QPushButton()
        self.start_btn.setIcon(qta.icon("fa5s.play", color="green"))
        self.start_btn.setFixedWidth(100)
        self.start_btn.setToolTip("Inicia o container LocalStack na porta especificada.")
        self.start_btn.setEnabled(True)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.setStyleSheet("font-weight: bold;")
        self.start_btn.setIconSize(QSize(24, 24))
        self.stop_btn = QPushButton()
        self.stop_btn.setIcon(qta.icon("fa5s.stop", color="red"))
        self.stop_btn.setFixedWidth(100)
        self.stop_btn.setToolTip("Para o container LocalStack.")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn = QPushButton(
            qta.icon("fa5s.file-code", color="cyan"),
            "Exportar Scripts"
        )
        self.export_btn.setToolTip("Exporta todos os scripts para recriar recursos")
        self.export_btn.clicked.connect(self._on_export_scripts)
        self.export_btn.setEnabled(False)

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.export_btn)
        content_layout.addLayout(btn_layout)

        self.localstack_ctrl = LocalStackController(self.port_input.value)
        self.sqs_ctrl = SQSController(self.port_input.value)
        self.s3_ctrl = S3Controller(self.port_input.value)
        self.sm_ctrl = SecretManagerController(self.port_input.value)
        self.dynamodb_ctrl = DynamoDBController(self.port_input.value)
        self.lambda_ctrl = LambdaController(self.port_input.value)
        self.apigw_ctrl = APIGatewayController(self.port_input.value)

        self.localstack_session = LocalStackSession()

        self.start_btn.clicked.connect(lambda: self._run_action(True))
        self.stop_btn.clicked.connect(lambda: self._run_action(False))

        self._update_ui(self.localstack_ctrl.is_running())

    def _on_export_scripts(self):
        try:
            script = self.localstack_ctrl.export_scripts()
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Salvar scripts",
                "",
                "Shell Script (*.sh)"
            )
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(script)
                QMessageBox.information(
                    self,
                    "Exportar Scripts",
                    f"Scripts exportados em:\n{path}"
                )
        except Exception as e:
            logger.error(f"Erro ao exportar scripts: {e}")
            QMessageBox.critical(self, "Exportar Scripts", str(e))

    def _run_action(self, start: bool):
        self.progress = QProgressDialog(
            "Aguarde...", None, 0, 0, self,
            flags=Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint
        )
        self.progress.setWindowTitle("LocalStack")
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.setCancelButton(None)
        self.progress.show()

        self.worker = LocalStackWorker(self.localstack_ctrl, start)
        self.worker.success.connect(self._on_worker_done)
        self.worker.error.connect(self._on_worker_error)
        self.worker.finished.connect(self.progress.close)
        self.worker.start()

    def _on_worker_done(self, started: bool):
        self._update_ui(started)
        status = "iniciado" if started else "parado"
        QMessageBox.information(self, "LocalStack", f"Container {status} com sucesso!")

    def _on_worker_error(self, message: str):
        QMessageBox.critical(self, "Erro LocalStack", message)

    def _update_ui(self, running: bool):
        """
        Habilita/desabilita controles principais e exibe
        o container de serviço apenas se LocalStack estiver ativo.
        """
        self.port_input.setEnabled(not running)
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        self.export_btn.setEnabled(running)
        self.svc_combo.setEnabled(running)

        service_selected = running and self.svc_combo.currentText() != "Nenhum"
        self.service_container.setVisible(service_selected)

        status = "Rodando" if running else "Parado"
        self.status_label.setText(f"Status: {status}")

        if not service_selected:
            self._clear_service_container()

    def showEvent(self, event: QShowEvent):
        super().showEvent(event)
        self._update_ui(self.localstack_ctrl.is_running())

    def _on_service_change(self, service: str):
        running = self.localstack_ctrl.is_running()
        self._update_ui(running)

        if not running or service == "Nenhum":
            return

        self._clear_service_container()

        if service == "SQS":
            comp = SQSComponent(self.sqs_ctrl, self.port_input)
        elif service == "S3":
            comp = S3Component(self.s3_ctrl, self.port_input)
        elif service == "Secrets Manager":
            comp = SecretManagerComponent(self.sm_ctrl, self.port_input)
        elif service == "DynamoDB":
            comp = DynamoDBComponent(self.dynamodb_ctrl, self.port_input)
        elif service == "Lambda":
            comp = LambdaComponent(self.lambda_ctrl, self.port_input)
        elif service == "API Gateway":
            comp = APIGatewayComponent(self.apigw_ctrl, self.port_input, self.lambda_ctrl)
        else:
            return

        self.service_layout.addWidget(comp)

    def _clear_service_container(self):
        """
        Remove todos os widgets carregados no container de serviço.
        """
        for i in reversed(range(self.service_layout.count())):
            w = self.service_layout.takeAt(i).widget()
            if w:
                w.setParent(None)


    def showEvent(self, event):
        super().showEvent(event)
        if self._first_show:
            self._first_show = False
            try:
                cursor_pos = QCursor.pos()
                desktop = QApplication.desktop()
                screen_index = desktop.screenNumber(cursor_pos)
                geom = desktop.screenGeometry(screen_index)
                self.setGeometry(geom)
                self.setWindowState(self.windowState() | Qt.WindowMaximized)
            except Exception as e:
                logger.error(f"[TasksScreen] erro ao maximizar janela: {e}")