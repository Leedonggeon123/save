"""프로젝트 루트에서 클라이언트를 실행하는 호환 진입점입니다."""
import runpy

if __name__ == "__main__":
    runpy.run_module("client.app", run_name="__main__")
