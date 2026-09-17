"""Jewel Cloud 클라이언트 실행 진입점

실행 명령:
    python -m client.app
"""

import sys  
from PySide6.QtWidgets import QApplication 

from .app_window import JewelClient     # 화면들을 구성하는 최상위 창


def main():
    """Qt 앱을 만들고 JewelClient를 표시한 뒤 이벤트 루프 시작"""
    # 버튼 클릭·키보드 입력을 처리하는 앱 생성
    app = QApplication(sys.argv)  
    # 로그인부터 설정까지 모든 페이지를 포함한 창 생성
    window = JewelClient()        
    window.show()  
    return app.exec() 


if __name__ == "__main__":
    # 이 파일을 모듈이 아닌 직접 실행했을 때만 main()을 호출
    raise SystemExit(main())
