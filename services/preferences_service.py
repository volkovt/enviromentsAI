import json, os

class PreferencesService:
    def __init__(self, prefs_path="environment_variables.json.prefs.json"):
        self.prefs_path = prefs_path
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.prefs_path):
            with open(self.prefs_path, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def get(self, key, default=None):
        with open(self.prefs_path, "r", encoding="utf-8") as f:
            prefs = json.load(f)
        return prefs.get(key, default)

    def set(self, key, value):
        with open(self.prefs_path, "r+", encoding="utf-8") as f:
            prefs = json.load(f)
            prefs[key] = value
            f.seek(0)
            json.dump(prefs, f, indent=2)
            f.truncate()
