# presentation/components/environment_screen.py

import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter,
    QSizePolicy, QScrollArea, QLabel, QTableWidgetItem, QCheckBox, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal
import qtawesome as qta

from interface.environment_variables import EnvironmentVariable
from presentation.components.HttpEditor import HttpEditor
from presentation.components.parameter_table import ParameterTableWidget
from presentation.components.static_editor import StaticEditor

logger = logging.getLogger("EnvironmentWidget")

class EnvironmentWidget(QWidget):
    variableSelected       = pyqtSignal(int)
    variableChanged        = pyqtSignal(int, object)
    variableAdded          = pyqtSignal(object)
    variableRemoved        = pyqtSignal(int)
    variableTested         = pyqtSignal(int)
    splitterMoved          = pyqtSignal(str, list)
    splitDirectionToggled  = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._create_ui()
        self._connect_signals()

    def _create_ui(self):
        self.main_layout = QVBoxLayout(self)
        bar = QHBoxLayout()
        bar.addWidget(QLabel("Variáveis de Ambiente"))
        self.btn_toggle = QPushButton(icon=qta.icon('fa5s.arrows-alt-v', color='orange'))
        bar.addStretch(); bar.addWidget(self.btn_toggle)
        self.main_layout.addLayout(bar)

        w_vars = QWidget()
        v_vars_layout = QVBoxLayout(w_vars)
        v_vars_layout.setContentsMargins(0,0,0,0)

        # botões de adicionar/remoção
        self.btn_add = QPushButton("")
        self.btn_add.setIcon(qta.icon('fa5s.plus', color='green'))
        self.btn_add.setToolTip("Adicionar nova variável")

        self.btn_remove = QPushButton("")
        self.btn_remove.setIcon(qta.icon('fa5s.trash', color='red'))
        self.btn_remove.setToolTip("Remover variável selecionada")

        h_btn = QHBoxLayout()
        h_btn.setContentsMargins(0,0,0,0)
        h_btn.setSpacing(5)
        h_btn.addStretch()
        h_btn.addWidget(self.btn_add)
        h_btn.addWidget(self.btn_remove)
        v_vars_layout.addLayout(h_btn)

        # tabela de variáveis
        self.table = ParameterTableWidget()
        self.table.setHorizontalHeaderLabels(["Ativo","Nome","Tipo"])
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        v_vars_layout.addWidget(self.table)

        # splitter e área de edição
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.addWidget(w_vars)

        self.editor_area = QWidget()
        self.editor_layout = QVBoxLayout(self.editor_area)
        self.static_editor = StaticEditor()
        self.http_editor   = HttpEditor()
        self.editor_layout.addWidget(self.static_editor)
        self.editor_layout.addWidget(self.http_editor)
        self.static_editor.hide()
        self.http_editor.hide()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.editor_area)
        self.splitter.addWidget(self.scroll_area)

        self.main_layout.addWidget(self.splitter)

    def set_variables(self, vars_list: list[EnvironmentVariable]):
        try:
            self.table.blockSignals(True)
            self.table.setRowCount(0)
            for var in vars_list:
                self._append_variable_row(var)
            logger.info(f"{len(vars_list)} variáveis carregadas na interface")
        except Exception as e:
            logger.error(f"Falha ao definir variáveis: {e}")
        finally:
            self.table.blockSignals(False)

    def select_row(self, index: int):
        try:
            self.table.selectRow(index)
        except Exception as e:
            logger.error(f"Falha ao selecionar linha {index}: {e}")

    def _append_variable_row(self, var: EnvironmentVariable):
        try:
            row = self.table.rowCount()
            self.table.insertRow(row)
            # Ativo
            cb = QCheckBox()
            cb.setChecked(var.enabled)
            self.table.setCellWidget(row, 0, cb)
            # Nome
            name_item = QTableWidgetItem(var.name)
            self.table.setItem(row, 1, name_item)
            # Tipo
            combo = QComboBox()
            combo.addItems(["static","http"])
            combo.setCurrentText(var.type)
            combo.currentTextChanged.connect(lambda text, r=row: self._on_type_changed(text, r))
            self.table.setCellWidget(row, 2, combo)
        except Exception as e:
            logger.error(f"Falha ao inserir linha de variável: {e}")

    def _on_type_changed(self, new_type: str, row: int):
        """
        Quando o usuário muda o tipo da variável no combo,
        primeiro atualiza o model (via variableChanged) e
        depois força a reexibição (via variableSelected).
        """
        try:
            # lê nome e estado atuais da linha
            enabled = bool(self.table.cellWidget(row, 0).isChecked())
            name = self.table.item(row, 1).text()
            # sinaliza alteração completa (name, enabled e type)
            self.variableChanged.emit(row, {
                "name": name,
                "enabled": enabled,
                "type": new_type
            })
            # força recarregar o editor correto
            self.variableSelected.emit(row)
        except Exception as e:
            logger.error(f"Erro ao mudar tipo da variável na linha {row}: {e}")

    def _connect_signals(self):
        self.btn_add.clicked.connect(self._on_add)
        self.btn_remove.clicked.connect(self._on_remove)
        self.table.itemSelectionChanged.connect(
            lambda: self.variableSelected.emit(self.table.currentRow())
        )
        self.table.cellChanged.connect(self._on_table_cell_changed)
        self.static_editor.valueChanged.connect(lambda v: self._emit_change(v))
        self.http_editor.configChanged.connect(lambda cfg: self._emit_change(cfg))
        self.http_editor.test_btn.clicked.connect(
            lambda: self.variableTested.emit(self.table.currentRow())
        )
        self.splitter.splitterMoved.connect(
            lambda pos, idx: self.splitterMoved.emit(
                "horizontal" if self.splitter.orientation()==Qt.Horizontal else "vertical",
                self.splitter.sizes()
            )
        )
        self.btn_toggle.clicked.connect(self._toggle_direction)

    def _on_add(self):
        try:
            var = EnvironmentVariable(enabled=True, name="", type="static", value="")
            self._append_variable_row(var)
            logger.info("Variável adicionada na interface")
            self.variableAdded.emit(var)
        except Exception as e:
            logger.error(f"Erro ao adicionar variável: {e}")

    def _on_remove(self):
        try:
            idx = self.table.currentRow()
            if idx < 0:
                logger.warning("Nenhuma variável selecionada para remoção")
                return
            self.table.removeRow(idx)
            logger.info(f"Variável removida linha {idx}")
            self.variableRemoved.emit(idx)
        except Exception as e:
            logger.error(f"Erro ao remover variável: {e}")

    def _on_table_cell_changed(self, row: int, col: int):
        try:
            enabled = bool(self.table.cellWidget(row, 0).isChecked())
            name    = self.table.item(row, 1).text()
            type_   = self.table.cellWidget(row, 2).currentText()
            self.variableChanged.emit(row, {"enabled": enabled, "name": name, "type": type_})
            logger.info(f"Variável linha {row} alterada: name='{name}', enabled={enabled}, type='{type_}'")
        except Exception as e:
            logger.error(f"Erro ao processar edição de célula: {e}")

    def show_variable(self, var: EnvironmentVariable):
        try:
            if var.type == "static":
                self.http_editor.hide()
                self.static_editor.show(var.value)
            else:
                self.static_editor.hide()
                self.http_editor.show(
                    method=var.method,
                    url=var.url,
                    params=var.params,
                    headers=var.headers,
                    body=var.body,
                    body_params=var.body_params,
                    response=var.response,
                    extract_path=var.extract_path,
                    content_type=var.content_type
                )
        except Exception as e:
            logger.error(f"Erro ao exibir variável '{var.name}': {e}")

    def _emit_change(self, updated):
        idx = self.table.currentRow()
        self.variableChanged.emit(idx, updated)

    def _toggle_direction(self):
        try:
            ori = Qt.Horizontal if self.splitter.orientation() == Qt.Vertical else Qt.Vertical
            self.splitter.setOrientation(ori)
            icon = 'fa5s.arrows-alt-h' if ori == Qt.Horizontal else 'fa5s.arrows-alt-v'
            self.btn_toggle.setIcon(qta.icon(icon, color='orange'))
            direction = "horizontal" if ori == Qt.Horizontal else "vertical"
            self.splitDirectionToggled.emit(direction)
            logger.info(f"Splitter alternado para {direction}")
        except Exception as e:
            logger.error(f"Falha ao alternar direção do splitter: {e}")

    def restore_splitter(self, orientation, sizes):
        try:
            ori = Qt.Horizontal if orientation == "horizontal" else Qt.Vertical
            self.splitter.setOrientation(ori)
            if sizes and len(sizes) == 2:
                self.splitter.setSizes(sizes)
        except Exception as e:
            logger.error(f"Falha ao restaurar splitter: {e}")
