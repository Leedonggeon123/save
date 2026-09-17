import os
import socket

SERVER_IP = os.getenv("JEWEL_SERVER_HOST", "127.0.0.1")
SOCKET_PORT = 9000


def connect_socket(user_id):                                                    # 로그인 성공시 user_id를 인자에 넣기
    client_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    client_socket.connect((SERVER_IP, SOCKET_PORT))

    client_socket.send(str(user_id).encode())

    print("Socket 서버에 user_id 전송:", user_id)

    client_socket.close()