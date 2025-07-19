from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QLineEdit, QPushButton, QMessageBox, QFileDialog, QLabel
)
import qtawesome as qta

from controller.localstack.s3_controller import S3Controller

class S3Component(QWidget):
    """
    Componente de UI para operações S3: buckets e objetos,
    incluindo visualizar e excluir objetos.
    """
    def __init__(self, controller: S3Controller, port_input):
        super().__init__()
        self.controller = controller
        self.get_port = port_input.value
        self._build_ui()
        self._refresh_buckets()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Buckets
        layout.addWidget(QLabel("Buckets:"))
        self.bucket_list = QListWidget()
        layout.addWidget(self.bucket_list)

        # Criar bucket
        create_layout = QHBoxLayout()
        self.bucket_name_input = QLineEdit()
        self.bucket_name_input.setPlaceholderText("Nome do bucket")
        create_btn = QPushButton(qta.icon("fa5s.plus", color="orange"), "")
        create_btn.setToolTip("Criar bucket")
        create_btn.clicked.connect(self._on_create_bucket)
        create_layout.addWidget(self.bucket_name_input)
        create_layout.addWidget(create_btn)
        layout.addLayout(create_layout)

        # Excluir bucket
        del_bucket_btn = QPushButton(qta.icon("fa5s.trash", color="red"), "Excluir bucket")
        del_bucket_btn.clicked.connect(self._on_delete_bucket)
        layout.addWidget(del_bucket_btn)

        # Objetos
        layout.addWidget(QLabel("Objetos:"))
        self.obj_list = QListWidget()
        layout.addWidget(self.obj_list)

        # Botões de objetos
        obj_btn_layout = QHBoxLayout()
        view_btn = QPushButton("Ver objetos")
        view_btn.clicked.connect(self._refresh_objects)
        obj_btn_layout.addWidget(view_btn)
        del_obj_btn = QPushButton(qta.icon("fa5s.trash", color="red"), "Excluir objeto")
        del_obj_btn.clicked.connect(self._on_delete_object)
        obj_btn_layout.addWidget(del_obj_btn)
        layout.addLayout(obj_btn_layout)

        # Upload / Download
        send_layout = QHBoxLayout()
        up_btn = QPushButton(qta.icon("fa5s.upload", color="orange"), "Upload")
        up_btn.clicked.connect(self._on_upload_object)
        send_layout.addWidget(up_btn)

        down_btn = QPushButton(qta.icon("fa5s.download", color="orange"), "Download")
        down_btn.clicked.connect(self._on_download_object)
        send_layout.addWidget(down_btn)
        layout.addLayout(send_layout)

    def _refresh_buckets(self):
        try:
            buckets = self.controller.list_buckets()
            self.bucket_list.clear()
            self.bucket_list.addItems(buckets or ["(nenhum bucket)"])
            self._refresh_objects()
        except Exception as e:
            QMessageBox.critical(self, "S3", str(e))

    def _refresh_objects(self):
        bucket = self.bucket_list.currentItem().text() if self.bucket_list.currentItem() else None
        self.obj_list.clear()
        if not bucket:
            return
        try:
            objs = self.controller.list_objects(bucket)
            self.obj_list.addItems(objs or ["(nenhum objeto)"])
        except Exception as e:
            QMessageBox.critical(self, "S3", str(e))

    def _on_create_bucket(self):
        name = self.bucket_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "S3", "Informe o nome do bucket.")
            return
        try:
            self.controller.create_bucket(name)
            QMessageBox.information(self, "S3", "Bucket criado com sucesso.")
            self.bucket_name_input.clear()
            self._refresh_buckets()
        except Exception as e:
            QMessageBox.critical(self, "S3", str(e))

    def _on_delete_bucket(self):
        item = self.bucket_list.currentItem()
        if not item:
            QMessageBox.warning(self, "S3", "Selecione um bucket.")
            return
        try:
            self.controller.delete_bucket(item.text())
            QMessageBox.information(self, "S3", "Bucket excluído.")
            self._refresh_buckets()
        except Exception as e:
            QMessageBox.critical(self, "S3", str(e))

    def _on_upload_object(self):
        bucket = self.bucket_list.currentItem().text() if self.bucket_list.currentItem() else None
        if not bucket:
            QMessageBox.warning(self, "S3", "Selecione um bucket.")
            return
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecione arquivo")
        if not file_path:
            return
        key, ok = QFileDialog.getSaveFileName(self, "Nome do objeto em S3", "")
        if not ok:
            return
        try:
            self.controller.upload_object(bucket, file_path, key)
            QMessageBox.information(self, "S3", "Upload concluído.")
            self._refresh_objects()
        except Exception as e:
            QMessageBox.critical(self, "S3", str(e))

    def _on_download_object(self):
        bucket = self.bucket_list.currentItem().text() if self.bucket_list.currentItem() else None
        obj = self.obj_list.currentItem().text() if self.obj_list.currentItem() else None
        if not bucket or not obj:
            QMessageBox.warning(self, "S3", "Selecione bucket e objeto.")
            return
        dest_dir = QFileDialog.getExistingDirectory(self, "Pasta de destino")
        if not dest_dir:
            return
        dest_path = f"{dest_dir}/{obj}"
        try:
            self.controller.download_object(bucket, obj, dest_path)
            QMessageBox.information(self, "S3", f"Download salvo em:\n{dest_path}")
        except Exception as e:
            QMessageBox.critical(self, "S3", str(e))

    def _on_delete_object(self):
        bucket = self.bucket_list.currentItem().text() if self.bucket_list.currentItem() else None
        obj = self.obj_list.currentItem().text() if self.obj_list.currentItem() else None
        if not bucket or not obj:
            QMessageBox.warning(self, "S3", "Selecione bucket e objeto para excluir.")
            return
        try:
            self.controller.delete_object(bucket, obj)
            QMessageBox.information(self, "S3", "Objeto excluído com sucesso.")
            self._refresh_objects()
        except Exception as e:
            QMessageBox.critical(self, "S3", str(e))
