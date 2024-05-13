from pathlib import Path

project_root = Path(__file__).parent
LOG_PATH = str(project_root.parent / "server.log")
SOCKET_PATH = str(project_root.parent / "chattorumu.sock")
MESSAGE_SIZE = 280
