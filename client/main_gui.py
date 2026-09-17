"""프로젝트 루트에서 main_gui를 실행하기 위한 진입점"""
import runpy

if __name__ == "__main__":
    runpy.run_module("client.app", run_name="__main__")
