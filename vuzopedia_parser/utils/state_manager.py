import json
import os
import logging

class StateManager:
    def __init__(self, path):
        self.path = path
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.state = json.load(f)
            except Exception as e:
                logging.getLogger(__name__).warning(f"Не удалось загрузить состояние: {e}")
                self.state = {}
        else:
            self.state = {}
        self.state.setdefault("visited_universities", [])
        self.state.setdefault("processed_programs", [])

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
            logging.getLogger(__name__).info(f"State saved to {self.path}")
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to save state: {e}")

    def mark_university_done(self, uni_url):
        if uni_url not in self.state["visited_universities"]:
            self.state["visited_universities"].append(uni_url)
            self.save()

    def mark_program_done(self, prog_url):
        if prog_url not in self.state["processed_programs"]:
            self.state["processed_programs"].append(prog_url)
            self.save()

    def is_university_done(self, uni_url):
        return uni_url in self.state["visited_universities"]

    def is_program_done(self, prog_url):
        return prog_url in self.state["processed_programs"]