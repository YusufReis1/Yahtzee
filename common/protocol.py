import json

class MessageType:
    HELLO   = "HELLO"
    MATCHED = "MATCHED"
    ROLL    = "ROLL"
    SELECT  = "SELECT"
    UPDATE  = "UPDATE"
    END     = "END"
    PING    = "PING"

class Message:
    def __init__(self, msg_type: str, payload: dict):
        self.type    = msg_type
        self.payload = payload

    def to_json(self) -> str:
        return json.dumps({"type": self.type, "payload": self.payload})

    @staticmethod
    def from_json(raw: str) -> "Message":
        d = json.loads(raw)
        return Message(d["type"], d.get("payload", {}))
