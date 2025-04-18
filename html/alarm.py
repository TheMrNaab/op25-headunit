import socket

HOST = '0.0.0.0'
PORT = 9000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"Listening on port {PORT}...")
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        try:
            while True:
                data = conn.recv(4096)
                if not data:
                    print("Connection closed cleanly by peer.")
                    break
                print("Received:", data)
        except ConnectionResetError:
            print("Connection reset by DVR (peer).")