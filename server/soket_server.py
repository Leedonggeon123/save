# import socket

# HOST = "0.0.0.0"
# PORT = 9000

# server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# server.bind((HOST, PORT))
# server.listen()

# print("Socket Server 시작")

# while True:
#     client_socket, address = server.accept()

#     print("클라이언트 연결:", address)

#     data = client_socket.recv(1024)

#     user_id = data.decode()

#     print("연결된 user_id:", user_id)