import json


class RepoJsonLoader:

    @staticmethod
    def load(path: str):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
