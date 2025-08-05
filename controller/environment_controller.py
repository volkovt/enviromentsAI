import logging
import requests
from PyQt5.QtCore import QObject, pyqtSlot

from interface.environment_variables import EnvironmentVariable
from services.notification_manager import NotificationManager
from services.variable_service import VariableService
from services.preferences_service import PreferencesService
from services.workers.path_worker import PathWorker

logger = logging.getLogger("EnvironmentController")

class EnvironmentController(QObject):
    def __init__(self, view):
        super().__init__()
        self.view      = view
        self.var_svc   = VariableService()
        self.pref_svc  = PreferencesService()
        self.notifier  = NotificationManager()
        self._vars     = []
        self._workers = []

        view.variableSelected.connect(self.on_variable_selected)
        view.variableChanged.connect(self.on_variable_changed)
        view.variableAdded.connect(self.on_variable_added)
        view.variableRemoved.connect(self.on_variable_removed)
        view.variableTested.connect(self.on_variable_tested)
        view.splitterMoved.connect(self.on_splitter_moved)
        view.splitDirectionToggled.connect(self.on_split_direction_toggled)

        self.load()

    def load(self):
        try:
            self._vars = self.var_svc.load_all()
            self.view.set_variables(self._vars)
            if self._vars:
                self.view.select_row(0)
                self.view.show_variable(self._vars[0])
            #logger.info("Variáveis carregadas com sucesso")
        except Exception as e:
            logger.error(f"Falha ao carregar variáveis: {e}")

        try:
            ori   = self.pref_svc.get("splitter_orientation", "vertical")
            sizes = self.pref_svc.get(f"splitter_sizes_{ori}", None)
            self.view.restore_splitter(ori, sizes)
        except Exception as e:
            logger.error(f"Falha ao restaurar splitter: {e}")

    def fetch_path(self,
                   path: str,
                   on_success: callable,
                   on_error: callable,
                   on_finished: callable):
        """
        Dispara um PathWorker em thread separada.
        on_success(value) é chamado com o resultado final.
        on_error(err_msg) é chamado se houver exceção.
        on_finished() é chamado sempre ao final.
        """
        worker = PathWorker(path, list(self._vars))
        worker.success.connect(on_success)
        worker.error.connect(on_error)
        worker.finished.connect(on_finished)
        self._workers.append(worker)
        worker.start()

    @pyqtSlot(int)
    def on_variable_selected(self, index):
        if index < 0 or index >= len(self._vars):
            logger.warning(f"Seleção de variável inválida: {index}")
            return
        try:
            self.view.show_variable(self._vars[index])
        except Exception as e:
            logger.error(f"Erro ao exibir variável no índice {index}: {e}")

    @pyqtSlot(int, object)
    def on_variable_changed(self, index, updated):
        if index < 0 or index >= len(self._vars):
            logger.warning(f"Índice de edição inválido: {index}")
            return

        var = self._vars[index]
        try:
            if isinstance(updated, dict) and set(updated.keys()) >= {"name", "enabled", "type"}:
                var.name    = updated["name"]
                var.enabled = updated["enabled"]
                var.type    = updated["type"]

            elif isinstance(updated, str):
                var.value = updated

            elif isinstance(updated, dict):
                var.type = "http"
                var.content_type = updated.get("content_type", "application/json")
                var.method = updated.get("method")
                var.url = updated.get("url")
                var.params = updated.get("params", {})
                var.headers = updated.get("headers", {})
                if var.content_type == "application/x-www-form-urlencoded":
                    var.body_params = updated.get("body_params", {})
                    var.body = updated.get("body", "")
                else:
                    var.body = updated.get("body", "")
                    var.body_params = {}
                var.extract_path = updated.get("extract_path", "")

            self.var_svc.save_all(self._vars)
        except Exception as e:
            logger.error(f"Falha ao salvar variável no índice {index}: {e}")

    @pyqtSlot(object)
    def on_variable_added(self, var: EnvironmentVariable):
        try:
            self._vars.append(var)
            self.var_svc.save_all(self._vars)
            idx = len(self._vars) - 1
            self.view.select_row(idx)
            self.view.show_variable(var)
            logger.info(f"Nova variável '{var.name}' adicionada e exibida")
        except Exception as e:
            logger.error(f"Erro ao adicionar variável: {e}")

    @pyqtSlot(int)
    def on_variable_removed(self, index: int):
        if index < 0 or index >= len(self._vars):
            logger.warning(f"Índice de remoção inválido: {index}")
            return
        try:
            removed = self._vars.pop(index)
            self.var_svc.save_all(self._vars)
            logger.info(f"Variável '{removed.name}' removida com sucesso")
            if self._vars:
                next_idx = min(index, len(self._vars) - 1)
                self.view.select_row(next_idx)
                self.view.show_variable(self._vars[next_idx])
            else:
                self.view.static_editor.hide()
                self.view.http_editor.hide()
            self.notifier.notify("Variável removida", removed.name, 1200)
        except Exception as e:
            logger.error(f"Erro ao remover variável: {e}")

    @pyqtSlot(int)
    def on_variable_tested(self, index: int):
        if index < 0 or index >= len(self._vars):
            logger.warning(f"Índice de teste inválido: {index}")
            return
        var = self._vars[index]
        try:
            if var.content_type == "application/x-www-form-urlencoded":
                data = var.body_params
            else:
                data = var.body.encode("utf-8") if var.body else None

            response = requests.request(
                method=var.method or "GET",
                url=var.url,
                params=var.params,
                headers=var.headers,
                data=data,
                timeout=10
            )
            var.response = response.text
            self.var_svc.save_all(self._vars)
            self.view.http_editor.response_te.setPlainText(var.response)
            self.notifier.notify("Teste concluído", f"{var.name}: {response.status_code}", 1500)
            logger.info(f"Teste HTTP da variável '{var.name}' concluído com status {response.status_code}")
        except Exception as e:
            logger.error(f"Erro ao testar variável '{var.name}': {e}")
            self.notifier.notify("Teste falhou", str(e), 2000)

    @pyqtSlot(str, list)
    def on_splitter_moved(self, orientation, sizes):
        try:
            self.pref_svc.set("splitter_orientation", orientation)
            self.pref_svc.set(f"splitter_sizes_{orientation}", sizes)
            logger.info(f"Configuração do splitter salva: {orientation} {sizes}")
        except Exception as e:
            logger.error(f"Erro ao salvar configuração do splitter: {e}")

    @pyqtSlot(str)
    def on_split_direction_toggled(self, orientation):
        try:
            self.pref_svc.set("splitter_orientation", orientation)
            logger.info(f"Orientação do splitter salva: {orientation}")
        except Exception as e:
            logger.error(f"Erro ao alternar orientação do splitter: {e}")
