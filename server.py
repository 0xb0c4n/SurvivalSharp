import socket
import threading

# Paramètres du serveur
HOST = '0.0.0.0'  # Écoute sur toutes les interfaces réseau
PORT = 12345      # Port à utiliser

# Dictionnaire pour stocker les positions des joueurs
positions = {}
players = {}
lock = threading.Lock()

def handle_client(conn, addr, player_id):
    global positions
    print(f"Connexion de {addr} assignée au joueur {player_id}")
    conn.send(f"{player_id}\n".encode())
    
    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break

            x, y = map(int, data.split(','))
            with lock:
                positions[player_id] = [x, y]
                # Envoyer les positions mises à jour à tous les clients
                all_positions = "\n".join([f"{pid}:{x},{y}" for pid, (x, y) in positions.items()])
                for pid, player_conn in players.items():
                    player_conn.sendall(all_positions.encode())
    finally:
        with lock:
            del positions[player_id]
            del players[player_id]
        conn.close()

def main():
    global players
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print("Serveur démarré, en attente de connexions...")

    player_id = 0

    while True:
        conn, addr = server.accept()
        with lock:
            players[player_id] = conn
            positions[player_id] = [100 + player_id * 50, 100]  # Position initiale unique pour chaque joueur
        threading.Thread(target=handle_client, args=(conn, addr, player_id)).start()
        player_id += 1

if __name__ == "__main__":
    main()
