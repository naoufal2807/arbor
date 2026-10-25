

class BackendOutputError(Exception):
    def __init__(self, backend: str, done_reason: str, content: str):
        self.backend = backend
        self.done_reason = done_reason
        self.content = content
        super().__init__(f"{backend}: unusable output (done_reason={done_reason!r})")