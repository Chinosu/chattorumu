from pathlib import Path

project_root = Path(__file__).parent.parent
LOG_PATH = str(project_root / "server.log")
SOCKET_PATH = str(project_root / "chattorumu.sock")
MESSAGE_SIZE = 280
