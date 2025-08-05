import json
import urllib

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit,
    QPushButton, QCheckBox, QTableWidgetItem
)
from PyQt5.QtCore import pyqtSignal
from presentation.components.parameter_table import ParameterTableWidget
from presentation.components.json_text_edit import JSONTextEdit

class HttpEditor(QWidget):
    """
    Editor para variáveis HTTP, com métodos, URL, params, headers, body,
    visualização de response e campo de extração.
    Emite `configChanged` sempre que qualquer campo é modificado.
    """
    configChanged = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Método:"))
        self.method_cb = QComboBox()
        self.method_cb.addItems(["GET", "POST", "PUT", "DELETE"])
        layout.addWidget(self.method_cb)

        layout.addWidget(QLabel("URL:"))
        self.url_le = QLineEdit()
        layout.addWidget(self.url_le)

        layout.addWidget(QLabel("Query Params:"))
        self.params_table = ParameterTableWidget(minimumHeight=100)
        layout.addWidget(self.params_table)
        btn_add_param = QPushButton("Adicionar Param")
        btn_add_param.clicked.connect(lambda: self._add_row(self.params_table))
        layout.addWidget(btn_add_param)

        layout.addWidget(QLabel("Headers:"))
        self.headers_table = ParameterTableWidget(minimumHeight=100)
        layout.addWidget(self.headers_table)
        btn_add_header = QPushButton("Adicionar Header")
        btn_add_header.clicked.connect(lambda: self._add_row(self.headers_table))
        layout.addWidget(btn_add_header)

        layout.addWidget(QLabel("Content-Type:"))
        self.content_type_cb = QComboBox()
        self.content_type_cb.addItems([
            "application/json",
            "application/x-www-form-urlencoded"
        ])
        layout.addWidget(self.content_type_cb)

        layout.addWidget(QLabel("Body (JSON):"))
        self.body_te = JSONTextEdit()
        layout.addWidget(self.body_te)

        layout.addWidget(QLabel("Body (Form URL Encoded):"))
        self.body_form_table = ParameterTableWidget(minimumHeight=100)
        self.body_form_table.hide()
        layout.addWidget(self.body_form_table)
        btn_add_body = QPushButton("Adicionar Campo de Form")
        btn_add_body.clicked.connect(lambda: self._add_row(self.body_form_table))
        layout.addWidget(btn_add_body)

        layout.addWidget(QLabel("Response Body:"))
        self.response_te = JSONTextEdit()
        self.response_te.setReadOnly(True)
        layout.addWidget(self.response_te)

        layout.addWidget(QLabel("Campo de extração:"))
        self.extract_le = QLineEdit()
        layout.addWidget(self.extract_le)

        self.test_btn = QPushButton("Testar Variável")
        layout.addWidget(self.test_btn)

    def _add_row(self, table: ParameterTableWidget):
        row = table.rowCount()
        table.insertRow(row)
        cb = QCheckBox()
        cb.setChecked(True)
        table.setCellWidget(row, 0, cb)
        table.setItem(row, 1, QTableWidgetItem(""))
        table.setItem(row, 2, QTableWidgetItem(""))

    def _connect_signals(self):
        self.method_cb.currentTextChanged.connect(self._emit_config_changed)
        self.url_le.textChanged.connect(self._emit_config_changed)
        self.extract_le.textChanged.connect(self._emit_config_changed)
        self.params_table.cellChanged.connect(lambda r, c: self._emit_config_changed())
        self.headers_table.cellChanged.connect(lambda r, c: self._emit_config_changed())
        self.content_type_cb.currentTextChanged.connect(self._update_body_editor_visibility)
        self.body_te.textChanged.connect(self._emit_config_changed)
        self.response_te.textChanged.connect(self._emit_config_changed)
        self.test_btn.clicked.connect(lambda: self._emit_config_changed())

    def _update_body_editor_visibility(self):
        is_json = self.content_type_cb.currentText() == "application/json"
        self.body_te.setVisible(is_json)
        self.body_form_table.setVisible(not is_json)
        self._emit_config_changed()

    def show(self, *, method, url, params, headers, body, body_params, response, extract_path, content_type):
        """
        Popula cada widget com os valores recebidos.
        """
        self.content_type_cb.setCurrentText(content_type or "application/json")
        self._update_body_editor_visibility()

        self.method_cb.setCurrentText(method or "GET")
        self.url_le.setText(url or "")

        self.params_table.setRowCount(0)
        for key, val in (params or {}).items():
            self._add_row(self.params_table)
            r = self.params_table.rowCount() - 1
            self.params_table.cellWidget(r, 0).setChecked(True)
            self.params_table.setItem(r, 1, QTableWidgetItem(key))
            self.params_table.setItem(r, 2, QTableWidgetItem(val))

        self.headers_table.setRowCount(0)
        for key, val in (headers or {}).items():
            self._add_row(self.headers_table)
            r = self.headers_table.rowCount() - 1
            self.headers_table.cellWidget(r, 0).setChecked(True)
            self.headers_table.setItem(r, 1, QTableWidgetItem(key))
            self.headers_table.setItem(r, 2, QTableWidgetItem(val))

        self.body_form_table.setRowCount(0)
        for k, v in (body_params or {}).items():
            self._add_row(self.body_form_table)
            r = self.body_form_table.rowCount() - 1
            self.body_form_table.cellWidget(r, 0).setChecked(True)
            self.body_form_table.setItem(r, 1, QTableWidgetItem(k))
            self.body_form_table.setItem(r, 2, QTableWidgetItem(v))

        self.body_te.setPlainText(body or "")
        self.response_te.setPlainText(response or "")
        self.extract_le.setText(extract_path or "")
        super().show()

    def _emit_config_changed(self):
        cfg = {
            "type": "http",
            "content_type": self.content_type_cb.currentText(),
            "method": self.method_cb.currentText(),
            "url": self.url_le.text().strip(),
            "params": self._collect_table(self.params_table),
            "headers": self._collect_table(self.headers_table),
            "extract_path": self.extract_le.text().strip()
        }
        if cfg["content_type"] == "application/x-www-form-urlencoded":
            cfg["body_params"] = self._collect_table(self.body_form_table)
            # opcional: construir string já codificada
            cfg["body"] = urllib.parse.urlencode(cfg["body_params"])
        else:
            cfg["body"] = self.body_te.toPlainText().strip()
            cfg["body_params"] = {}
        self.configChanged.emit(cfg)

    def _collect_table(self, table: ParameterTableWidget) -> dict:
        result = {}
        for row in range(table.rowCount()):
            cb = table.cellWidget(row, 0)
            if cb and not cb.isChecked():
                continue
            key_item = table.item(row, 1)
            val_item = table.item(row, 2)
            if key_item and val_item:
                result[key_item.text()] = val_item.text()
        return result
