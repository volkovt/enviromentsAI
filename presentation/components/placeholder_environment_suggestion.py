import json
import logging

from PyQt5.QtWidgets import QLineEdit, QPlainTextEdit, QCompleter
from PyQt5.QtCore import Qt, QStringListModel

logger = logging.getLogger("PlaceholderEnvironmentSuggestion")

class CustomCompleter(QCompleter):
    """
    Subclasse QCompleter para desativar inserção automática de texto pelo Qt.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def insertCompletion(self, completion: str):
        return

class PlaceholderSuggestionProvider:
    """
    Fornece sugestões de placeholders do tipo VAR.prop...VAR.prop.subprop.
    Usa VariableService para carregar dados JSON de forma genérico.
    """
    def __init__(self, variable_service):
        self.variable_service = variable_service

    def suggestions(self, text_before_cursor: str) -> list[str]:
        raw = text_before_cursor.split('{{')[-1] if '{{' in text_before_cursor else text_before_cursor
        token = raw.strip()
        if not token:
            return []

        parts = token.split('.')
        var_prefix = parts[0]
        nested = parts[1:]
        results: list[str] = []

        for var in self.variable_service.load_all():
            if var.name.lower().startswith(var_prefix.lower()):
                if not nested:
                    results.append(var.name)
                else:
                    try:
                        data = json.loads(var.response or var.value)
                    except Exception:
                        continue
                    curr = data
                    for key in nested[:-1]:
                        if isinstance(curr, dict) and key in curr:
                            curr = curr[key]
                        else:
                            curr = None
                            break
                    if not isinstance(curr, dict):
                        continue
                    last = nested[-1]
                    for k in curr:
                        if k.lower().startswith(last.lower()):
                            path = ".".join(nested[:-1] + [k])
                            results.append(f"{var.name}.{path}")
        return results

class PlaceholderLineEdit(QLineEdit):
    """
    QLineEdit com autocomplete de placeholders, preservando '{{' e '}}'.
    Usa CustomCompleter para desativar inserção automática do Qt e inserir manualmente.
    """
    def __init__(self, provider: PlaceholderSuggestionProvider, parent=None):
        super().__init__(parent)
        self.provider = provider
        self.model = QStringListModel()
        self.completer = CustomCompleter(self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setModel(self.model)
        self.completer.setWidget(self)
        self.setCompleter(self.completer)

        self.textEdited.connect(self._update_completer)
        self.completer.popup().clicked.connect(self._on_popup_clicked)

    def _update_completer(self, text: str):
        try:
            pos = self.cursorPosition()
            prefix = text[:pos]

            start = prefix.rfind("{{")
            if start == -1 or "}}" in prefix[start+2:]:
                self.completer.popup().hide()
                return

            suggestions = self.provider.suggestions(prefix)
            if not suggestions:
                self.completer.popup().hide()
                return

            self.model.setStringList(suggestions)
            token = prefix[start+2:].strip()
            self.completer.setCompletionPrefix(token)
            try:
                self.completer.popup().setMinimumWidth(self.width())
            except Exception:
                pass
            self.completer.complete()
        except Exception as e:
            logger.error(f"[PlaceholderLineEdit] erro ao atualizar completer: {e}")
            self.completer.popup().hide()

    def keyPressEvent(self, event):
        popup = self.completer.popup()
        if popup.isVisible() and event.key() in (Qt.Key_Down, Qt.Key_Up):
            popup.keyPressEvent(event)
            return
        if popup.isVisible() and event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Tab):
            index = popup.currentIndex()
            completion = index.data() if index.isValid() else self.completer.currentCompletion()
            if completion:
                self._insert_completion(completion)
            popup.hide()
            return

        popup.hide()
        super().keyPressEvent(event)
        self._update_completer(self.text())

    def _on_popup_clicked(self, index):
        try:
            completion = index.data()
            if completion:
                self._insert_completion(completion)
        except Exception as e:
            logger.error(f"[PlaceholderLineEdit] erro ao tratar clique no popup: {e}")
        finally:
            self.completer.popup().hide()

    def _insert_completion(self, completion: str):
        try:
            text = self.text()
            pos = self.cursorPosition()

            open_idx = text.rfind("{{", 0, pos)
            if open_idx != -1:
                close_idx = text.find("}}", open_idx + 2)
                after = text[close_idx+2:] if close_idx != -1 else ""
                new_text = text[:open_idx] + "{{" + completion + "}}" + after
                self.setText(new_text)
                self.setCursorPosition(open_idx + 2 + len(completion))
                return

            if text[:pos] == completion:
                new_text = "{{" + completion + "}}"
                self.setText(new_text)
                self.setCursorPosition(2 + len(completion))
                return

            new_text = text[:pos] + completion + text[pos:]
            self.setText(new_text)
            self.setCursorPosition(pos + len(completion))

        except Exception as e:
            logger.error(f"[PlaceholderLineEdit] erro ao inserir completion: {e}")