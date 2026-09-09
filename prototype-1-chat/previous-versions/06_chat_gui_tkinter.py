import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import pika
import json
import sys

EXCHANGE_NAME = "chat_exchange"

if len(sys.argv) < 4:
    print("Usage Windows: python chat_gui_tkinter.py <username> <room> <port>")
    print("Usage Mac: python3 chat_gui_tkinter.py <username> <room> <port>")
    sys.exit(1)

USERNAME = sys.argv[1]
ROOM = sys.argv[2]
PORT = int(sys.argv[3])


class ChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Chat App - {USERNAME} ({ROOM})")
        self.root.geometry("520x450")
        self.root.configure(bg="white")

        self.username = USERNAME
        self.room = ROOM
        self.port = PORT

        # Chat frame
        self.chat_frame = tk.Frame(root, bg="white")
        self.chat_frame.pack(fill="both", expand=True)

        self.chat_area = scrolledtext.ScrolledText(
            self.chat_frame,
            wrap=tk.WORD,
            width=55,
            height=18,
            state='disabled',
            font=("Arial", 11),
            bg="white",
            fg="black",
            insertbackground="black"
        )
        self.chat_area.pack(padx=10, pady=10, fill="both", expand=True)

        self.bottom_frame = tk.Frame(self.chat_frame, bg="white")
        self.bottom_frame.pack(pady=5)

        self.msg_entry = tk.Entry(
            self.bottom_frame,
            width=35,
            font=("Arial", 12),
            bg="white",
            fg="black",
            insertbackground="black",
            relief="solid",
            bd=1
        )
        self.msg_entry.pack(side=tk.LEFT, padx=5)
        self.msg_entry.bind("<Return>", self.send_message_event)

        self.send_button = tk.Button(
            self.bottom_frame,
            text="Send",
            font=("Arial", 12),
            bg="#e6e6e6",
            fg="black",
            command=self.send_message
        )
        self.send_button.pack(side=tk.LEFT)

        self.connect_chat()

    def connect_chat(self):
        try:
            self.send_connection = pika.BlockingConnection(
                pika.ConnectionParameters(host='localhost', port=self.port, heartbeat=600)
            )
            self.send_channel = self.send_connection.channel()
            self.send_channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic')

            self.display_message(f"[Connected to room '{self.room}' as {self.username}]")

            receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            receive_thread.start()

        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
            self.root.destroy()

    def receive_messages(self):
        try:
            self.receive_connection = pika.BlockingConnection(
                pika.ConnectionParameters(host='localhost', port=self.port, heartbeat=600)
            )
            self.receive_channel = self.receive_connection.channel()
            self.receive_channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic')

            result = self.receive_channel.queue_declare(queue='', exclusive=True)
            self.queue_name = result.method.queue

            self.receive_channel.queue_bind(
                exchange=EXCHANGE_NAME,
                queue=self.queue_name,
                routing_key=self.room
            )

            def callback(ch, method, properties, body):
                data = json.loads(body.decode())
                sender = data["sender"]
                message = data["message"]

                if sender != self.username:
                    self.root.after(0, lambda: self.display_message(f"{sender}: {message}"))

            self.receive_channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=callback,
                auto_ack=True
            )

            self.receive_channel.start_consuming()

        except Exception as e:
            self.root.after(0, lambda: self.display_message(f"[Receive error] {e}"))

    def send_message_event(self, event):
        self.send_message()

    def send_message(self):
        message_text = self.msg_entry.get().strip()

        if not message_text:
            return

        message = {
            "sender": self.username,
            "room": self.room,
            "message": message_text
        }

        try:
            self.send_channel.basic_publish(
                exchange=EXCHANGE_NAME,
                routing_key=self.room,
                body=json.dumps(message)
            )

            self.display_message(f"You: {message_text}")
            self.msg_entry.delete(0, tk.END)

        except Exception as e:
            messagebox.showerror("Send Error", str(e))

    def display_message(self, message):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, message + "\n")
        self.chat_area.config(state='disabled')
        self.chat_area.yview(tk.END)


root = tk.Tk()
app = ChatGUI(root)
root.mainloop()
