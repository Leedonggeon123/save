"""클라우드 클라이언트와 메일 클라이언트를 함께 실행하는 테스트용 진입점.

루트의 client/server/source 파일은 수정하지 않고, 실행 시점에만 메일 기능을
대시보드의 메일 버튼에 연결한다. 메일 TCP 서버도 이 테스트 프로세스의 자식
프로세스로만 실행되며, 프로그램 종료 시 함께 종료된다.
"""

from __future__ import annotations

import os
import runpy
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAIL_ROOT = Path(__file__).resolve().parent
MAIL_CLIENT_ROOT = MAIL_ROOT / "mail_client"


def start_mail_server() -> subprocess.Popen:
    """현재 테스트 프로젝트의 메일 TCP 서버만 로컬에서 시작한다."""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, (str(MAIL_CLIENT_ROOT), environment.get("PYTHONPATH", "")))
    )
    environment["CLOUD_SERVER_HOST"] = "127.0.0.1"
    environment["CLOUD_SERVER_PORT"] = "9000"
    return subprocess.Popen(
        [sys.executable, "-m", "server.mail_tcp_server"],
        cwd=MAIL_CLIENT_ROOT,
        env=environment,
    )


def install_mail_button_bridge() -> None:
    """대시보드 메일 버튼을 실행 시점에 메일 화면으로 연결한다."""
    sys.path.insert(0, str(PROJECT_ROOT))
    sys.path.insert(0, str(MAIL_ROOT))

    from client.main_window import DashboardPage
    from mail_client.client.mail_management_window import MailManagementController

    controller_holder: dict[str, MailManagementController | None] = {"controller": None}

    def open_mail(_dashboard: DashboardPage) -> None:
        controller = controller_holder["controller"]
        if controller is None:
            controller = MailManagementController()
            controller_holder["controller"] = controller
        controller.show()

    DashboardPage.open_mail = open_mail


def main() -> int:
    mail_server = start_mail_server()
    try:
        install_mail_button_bridge()
        runpy.run_path(str(PROJECT_ROOT / "main_gui.py"), run_name="__main__")
    finally:
        if mail_server.poll() is None:
            mail_server.terminate()
            try:
                mail_server.wait(timeout=2)
            except subprocess.TimeoutExpired:
                mail_server.kill()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
