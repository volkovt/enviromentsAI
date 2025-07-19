from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import (
    QFormLayout, QWidget, QLineEdit, QTabWidget, QVBoxLayout,
    QDialog, QDialogButtonBox, QPushButton, QHBoxLayout, QLabel, QCheckBox, QComboBox
)

import qtawesome as qta

class ParamsDialog(QDialog):
    def __init__(self, path_params=None, query_params=None, header_params=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Parameters")
        path_params = path_params or []
        query_params = query_params or []
        header_params = header_params or []

        self.inputs = {"path": [], "query": [], "header": []}

        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        for kind, params in (("path", path_params), ("query", query_params), ("header", header_params)):
            tab = QWidget(); vlay = QVBoxLayout(tab)
            add_btn = QPushButton(f"Add {kind.title()} Param")
            add_btn.clicked.connect(lambda _, k=kind: self._add_row(k))
            vlay.addWidget(add_btn)
            form = QFormLayout(); setattr(self, f"_{kind}_form", form)
            vlay.addLayout(form)
            for p in params:
                self._add_row(kind, p)
            tabs.addTab(tab, kind.title())

        layout.addWidget(tabs)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _add_row(self, kind, param=None):
        name = param.get("name", "") if param else ""
        type_ = param.get("schema", {}).get("type", "string") if param else "string"
        required = param.get("required", False) if param else False

        form: QFormLayout = getattr(self, f"_{kind}_form")

        row = QWidget(); h = QHBoxLayout(row); h.setContentsMargins(0,0,0,0)
        le_name = QLineEdit(name)
        cb_required = QCheckBox("required"); cb_required.setChecked(required)
        combo_type = QComboBox(); combo_type.addItems(["string","integer","number","boolean"]); combo_type.setCurrentText(type_)
        btn_rm = QPushButton()
        btn_rm.setIcon(qta.icon("fa5s.trash-alt", color="red"))
        btn_rm.setToolTip("Remove this parameter")
        btn_rm.setIconSize(QSize(24, 24))
        btn_rm.setFixedWidth(30)
        btn_rm.clicked.connect(lambda _, w=row, k=kind, ln=le_name: self._remove_row(w, k, ln))

        h.addWidget(QLabel("Name:")); h.addWidget(le_name)
        h.addWidget(QLabel("Type:")); h.addWidget(combo_type)
        h.addWidget(cb_required); h.addWidget(btn_rm)
        form.addRow(row)
        self.inputs[kind].append((row, le_name, combo_type, cb_required))

    def _remove_row(self, row, kind, le_name):
        form: QFormLayout = getattr(self, f"_{kind}_form")
        form.removeWidget(row); row.deleteLater()
        self.inputs[kind] = [
            t for t in self.inputs[kind]
            if t[1] is not le_name
        ]

    def get_values(self):
        result = {"path": [], "query": [], "header": []}
        for kind in result:
            for row, le_name, combo_type, cb_required in self.inputs[kind]:
                name = le_name.text().strip()
                if not name: continue
                result[kind].append({
                    "name": name,
                    "in": kind,
                    "required": cb_required.isChecked(),
                    "schema": {"type": combo_type.currentText()}
                })
        return result
