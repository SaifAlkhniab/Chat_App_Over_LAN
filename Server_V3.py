import socket
import threading
import tkinter as tk
from tkinter import font
from tkinter.scrolledtext import ScrolledText
import queue

# Global variables
msg_queue = queue.Queue()
clients = []  # List to store all connected clients
client_count = 0  # Counter to assign client numbers
lock = threading.Lock()  # Lock for thread-safe operations

def handle_client(client_socket, client_id):
    """Receives messages from a client and broadcasts them to all clients."""
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                msg_queue.put(f"Client{client_id} disconnected.")
                broadcast(f"Client{client_id} disconnected.", client_socket)
                break
            message = data.decode('utf-8', errors='replace')
            if message:
                full_message = f"Client{client_id}: {message.strip()}"
                msg_queue.put(full_message)
                broadcast(full_message, client_socket)
            else:
                msg_queue.put(f"Received empty message from Client{client_id}.")
        except Exception as e:
            msg_queue.put(f"Error receiving message from Client{client_id}: {e}")
            broadcast(f"Client{client_id} disconnected due to error: {e}", client_socket)
            break

    # Remove the client from the list
    with lock:
        clients.remove(client_socket)
    client_socket.close()

def broadcast(message, sender_socket):
    """Sends a message to all clients except the sender."""
    with lock:
        for client in clients:
            if client != sender_socket:
                try:
                    client.send((message + '\n').encode('utf-8'))
                except Exception as e:
                    msg_queue.put(f"Error broadcasting to a client: {e}")

def start_server():
    """Starts the server and accepts multiple clients."""
    server_ip = ip_entry.get()
    try:
        server_port = int(port_entry.get())
    except ValueError:
        chat_area.insert(tk.END, "Invalid port number.\n")
        return

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((server_ip, server_port))
    except Exception as e:
        chat_area.insert(tk.END, f"Error binding server: {e}\n")
        return

    server_socket.listen(5)  # Allow up to 5 clients in the queue
    chat_area.insert(tk.END, "Server started. Waiting for connections...\n")

    def accept_connections():
        global client_count  # أضف هذا السطر للإعلان عن client_count كمتغير عالمي
        while True:
            try:
                client_socket, addr = server_socket.accept()
                with lock:
                    client_count += 1  # الآن يمكن تعديل client_count بأمان
                    clients.append(client_socket)
                chat_area.insert(tk.END, f"Client{client_count} connected from {addr}\n")
                broadcast(f"Client{client_count} connected.", client_socket)
                # Start a thread to handle the client
                threading.Thread(
                    target=handle_client,
                    args=(client_socket, client_count),
                    daemon=True
                ).start()
            except Exception as e:
                chat_area.insert(tk.END, f"Error accepting connection: {e}\n")
                break
        server_socket.close()

    threading.Thread(target=accept_connections, daemon=True).start()

def update_chat():
    """Updates the chat area periodically with new messages."""
    try:
        while not msg_queue.empty():
            message = msg_queue.get_nowait()
            chat_area.insert(tk.END, message + "\n")
            chat_area.see(tk.END)
    except queue.Empty:
        pass
    root.after(100, update_chat)

def send_message(event=None):
    """Sends a message from the server to all clients."""
    message = message_entry.get().strip()
    if message:
        try:
            full_message = f"Server: {message}"
            chat_area.insert(tk.END, full_message + "\n")
            chat_area.see(tk.END)
            message_entry.delete(0, tk.END)
            # Broadcast the message to all clients
            with lock:
                for client in clients:
                    try:
                        client.send((full_message + '\n').encode('utf-8'))
                    except Exception as e:
                        msg_queue.put(f"Error sending message to a client: {e}")
        except Exception as e:
            chat_area.insert(tk.END, f"Error sending message: {e}\n")

def clear_chat():
    """Clears the chat display area."""
    chat_area.delete(1.0, tk.END)

# Create the main window
root = tk.Tk()
root.title("Chat Server")
root.geometry("800x600")
root.configure(bg="#2C3E50")

# Define custom fonts
title_font = font.Font(family="Arial", size=16, weight="bold")
default_font = font.Font(family="Arial", size=12)
button_font = font.Font(family="Arial", size=10, weight="bold")

# Header Frame (for title)
header_frame = tk.Frame(root, bg="#34495E", pady=10)
header_frame.pack(fill=tk.X)

header_label = tk.Label(
    header_frame,
    text="Chat Server",
    font=title_font,
    fg="#ECF0F1",
    bg="#34495E",
    pady=10
)
header_label.pack()

# Top frame for IP, Port, and control buttons
top_frame = tk.Frame(root, bg="#2C3E50", pady=10)
top_frame.pack(fill=tk.X, padx=20)

# IP Entry
ip_frame = tk.Frame(top_frame, bg="#2C3E50")
ip_frame.pack(side=tk.LEFT, padx=10)

tk.Label(ip_frame, text="IP:", bg="#2C3E50", fg="#ECF0F1", font=default_font).pack(side=tk.LEFT, padx=5)
ip_entry = tk.Entry(ip_frame, width=15, font=default_font, bg="#ECF0F1", fg="#2C3E50", relief=tk.FLAT, borderwidth=2)
ip_entry.pack(side=tk.LEFT, padx=5)
ip_entry.insert(0, "192.168.x.x")

# Port Entry
port_frame = tk.Frame(top_frame, bg="#2C3E50")
port_frame.pack(side=tk.LEFT, padx=10)

tk.Label(port_frame, text="Port:", bg="#2C3E50", fg="#ECF0F1", font=default_font).pack(side=tk.LEFT, padx=5)
port_entry = tk.Entry(port_frame, width=6, font=default_font, bg="#ECF0F1", fg="#2C3E50", relief=tk.FLAT, borderwidth=2)
port_entry.pack(side=tk.LEFT, padx=5)
port_entry.insert(0, "12345")

# Buttons Frame
buttons_frame = tk.Frame(top_frame, bg="#2C3E50")
buttons_frame.pack(side=tk.RIGHT, padx=10)

start_button = tk.Button(
    buttons_frame,
    text="Start Server",
    command=start_server,
    font=button_font,
    bg="#1ABC9C",
    fg="white",
    relief=tk.FLAT,
    padx=15,
    pady=5,
    borderwidth=0,
    activebackground="#16A085",
    cursor="hand2"
)
start_button.pack(side=tk.LEFT, padx=5)

clear_button = tk.Button(
    buttons_frame,
    text="Clear Chat",
    command=clear_chat,
    font=button_font,
    bg="#E74C3C",
    fg="white",
    relief=tk.FLAT,
    padx=15,
    pady=5,
    borderwidth=0,
    activebackground="#C0392B",
    cursor="hand2"
)
clear_button.pack(side=tk.LEFT, padx=5)

# Chat display area
chat_frame = tk.Frame(root, bg="#2C3E50", pady=10)
chat_frame.pack(fill=tk.BOTH, expand=True, padx=20)

chat_area = ScrolledText(
    chat_frame,
    width=80,
    height=20,
    font=default_font,
    bg="#34495E",
    fg="#ECF0F1",
    relief=tk.FLAT,
    borderwidth=2,
    insertbackground="white",
    selectbackground="#1ABC9C",
    wrap=tk.WORD
)
chat_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Message entry frame
message_frame = tk.Frame(root, bg="#2C3E50", pady=10)
message_frame.pack(fill=tk.X, padx=20)

message_entry = tk.Entry(
    message_frame,
    width=60,
    font=default_font,
    bg="#ECF0F1",
    fg="#2C3E50",
    relief=tk.FLAT,
    borderwidth=2,
    insertbackground="#2C3E50"
)
message_entry.pack(side=tk.LEFT, padx=10, pady=5, fill=tk.X, expand=True)
message_entry.bind("<Return>", send_message)

send_button = tk.Button(
    message_frame,
    text="Send",
    command=send_message,
    font=button_font,
    bg="#3498DB",
    fg="white",
    relief=tk.FLAT,
    padx=15,
    pady=5,
    borderwidth=0,
    activebackground="#2980B9",
    cursor="hand2"
)
send_button.pack(side=tk.RIGHT, padx=10)

# Start periodic updates to the chat area
update_chat()

root.mainloop()