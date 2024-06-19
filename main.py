import pygame
import sys
import requests
import socket
import threading
import time

from win32api import GetSystemMetrics

# Initialisation de Pygame
pygame.init()

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
COLORS = [
    (255, 0, 0),    # Rouge
    (0, 255, 0),    # Vert
    (0, 0, 255),    # Bleu
    (255, 255, 0),  # Jaune
    (0, 255, 255),  # Cyan
    (255, 0, 255)   # Magenta
]

# Taille des rectangles
rect_size = 50

# Positions des rectangles des joueurs
positions = {}
my_id = None

# Vitesse de déplacement
speed = 5

direction = "down"
animation = "idle"
frame = 0
frame_counter = 0
frame_delay = 10  # Délais entre les changements de frames d'animation

# Chargement des images d'animation
animations = {
    'down': [pygame.image.load('./assets/sprites/down/walk1.png'), pygame.image.load('./assets/sprites/down/walk2.png')],
    'up': [pygame.image.load('./assets/sprites/top/walk1.png'), pygame.image.load('./assets/sprites/top/walk2.png')],
    'left': [pygame.image.load('./assets/sprites/left/walk1.png'), pygame.image.load('./assets/sprites/left/walk2.png')],
    'right': [pygame.image.load('./assets/sprites/right/walk1.png'), pygame.image.load('./assets/sprites/right/walk2.png')],
    'idle': [pygame.image.load('./assets/sprites/down/idle.png')]  # Par défaut, l'image d'idle vers le bas
}

def receive_data(sock):
    global positions
    while True:
        data = sock.recv(1024).decode()
        if not data:
            break
        positions.clear()
        for line in data.strip().split('\n'):
            try:
                pid, pos = line.split(':')
                x, y = map(int, pos.split(','))
                positions[int(pid)] = [x, y]
            except ValueError:
                continue

WIDTH, HEIGHT = int(GetSystemMetrics(0) * 0.99), int(GetSystemMetrics(1) * 0.9)

# Création de la fenêtre
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Survival Sharp")

# Police de texte
font = pygame.font.Font("./Silver.ttf", 50)

HOST = '127.0.0.1'  # Adresse IP du serveur (à modifier si nécessaire)
PORT = 12345        # Port à utiliser

def game():
    global my_id, direction, animation, frame, frame_counter

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    # Recevoir l'ID du joueur du serveur
    my_id = int(sock.recv(1024).decode().strip())
    positions[my_id] = [100 + my_id * 50, 100]  # Initialiser la position de mon rectangle

    threading.Thread(target=receive_data, args=(sock,)).start()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sock.close()
                sys.exit()

        # Récupérer les touches pressées
        keys = pygame.key.get_pressed()

        # Déplacer son propre rectangle
        if my_id is not None:
            if keys[pygame.K_LEFT]:
                positions[my_id][0] -= speed
                direction = "left"
                animation = "walk"
            if keys[pygame.K_RIGHT]:
                positions[my_id][0] += speed
                direction = "right"
                animation = "walk"
            if keys[pygame.K_UP]:
                positions[my_id][1] -= speed
                direction = "up"
                animation = "walk"
            if keys[pygame.K_DOWN]:
                positions[my_id][1] += speed
                direction = "down"
                animation = "walk"
            if not (keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or keys[pygame.K_UP] or keys[pygame.K_DOWN]):
                animation = "idle"

            # S'assurer que le rectangle reste dans les limites de la fenêtre
            positions[my_id][0] = max(0, min(positions[my_id][0], WIDTH - rect_size))
            positions[my_id][1] = max(0, min(positions[my_id][1], HEIGHT - rect_size))

            # Envoyer la position mise à jour au serveur
            sock.send(f"{positions[my_id][0]},{positions[my_id][1]}\n".encode())

        # Remplir l'écran en blanc
        screen.fill(WHITE)

        # Gestion de l'animation
        if animation == "walk":
            frame_counter += 1
            if frame_counter >= frame_delay:
                frame_counter = 0
                frame = (frame + 1) % 2
        else:
            frame = 0

        # Dessiner les rectangles des joueurs
        for pid, pos in positions.items():
            sprite = animations[direction][frame] if animation == "walk" else animations[direction][0]
            screen.blit(sprite, (pos[0], pos[1]))

        # Mettre à jour l'affichage
        pygame.display.flip()

        # Limiter la vitesse de la boucle
        pygame.time.Clock().tick(60)  # Ajuste la vitesse de l'animation (60 FPS ici)

def receive_messages(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                print(message)
        except:
            print("Vous avez été déconnecté du serveur.")
            client_socket.close()
            break

def login():
    running = True
    email_txt = ""
    pass_txt = ""
    is_email = False
    is_pass = False
    title = font.render("Survival Sharp", True, WHITE)
    email = font.render("Email", True, WHITE)
    password = font.render("Password", True, WHITE)
    background = pygame.image.load("./assets/background.png")
    button = pygame.image.load("./assets/button.jpg")
    button_solid = pygame.Rect(50, 350, 180, 93)
    button_txt = font.render("LOGIN", True, WHITE)

    email_btn = pygame.Rect(15, 150, 250, 30)
    pass_btn = pygame.Rect(15, 250, 250, 30)

    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if email_btn.collidepoint(pos):
                    is_pass = False
                    is_email = True
                elif pass_btn.collidepoint(pos):
                    is_email = False
                    is_pass = True
                elif button_solid.collidepoint(pos):
                    payload = {"email": email_txt, "password": pass_txt}
                    r = requests.post('http://127.0.0.1/login.php', data=payload)
                    if r.text == "Connecté":
                        # Connexion au serveur de jeu
                        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        try:
                            client_socket.connect(('127.0.0.1', 5555))  # Change l'adresse IP et le port si nécessaire
                            threading.Thread(target=receive_messages, args=(client_socket,)).start()
                            game(client_socket)  # Passer au jeu après la connexion
                        except:
                            print("Impossible de se connecter au serveur de jeu.")
                        running = False
                else:
                    is_email = False
                    is_pass = False

        screen.blit(background, (0, 0))
        s = pygame.Surface((WIDTH * 0.2, HEIGHT))  # la taille du rectangle
        s.set_alpha(128)  # niveau alpha
        s.fill(BLACK)  # ceci remplit toute la surface
        screen.blit(s, (0, 0))  # (0, 0) sont les coordonnées en haut à gauche
        screen.blit(title, (15, 15))

        pygame.draw.rect(screen, WHITE, email_btn)
        pygame.draw.rect(screen, WHITE, pass_btn)
        pygame.draw.rect(screen, WHITE, button_solid)

        screen.blit(font.render(email_txt, True, BLACK), (15, 150))
        screen.blit(email, (15, 100))
        screen.blit(password, (15, 200))
        screen.blit(font.render(pass_txt, True, BLACK), (15, 250))
        screen.blit(button, (50, 350))
        screen.blit(button_txt, (102.5, 375))

        if is_email:
            for event in events:
                if event.type == pygame.KEYDOWN and event.key != pygame.K_BACKSPACE:
                    if event.key == pygame.K_BACKSPACE:
                        email_txt = email_txt[:-1]
                    elif event.key == pygame.K_SPACE:
                        email_txt += " "
                    else:
                        email_txt += event.unicode
        elif is_pass:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        pass_txt = pass_txt[:-1]
                    elif event.key == pygame.K_SPACE:
                        pass_txt += " "
                    else:
                        pass_txt += event.unicode

        pygame.display.update()

if __name__ == "__main__":
    game()
