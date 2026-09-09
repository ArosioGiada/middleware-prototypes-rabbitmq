# Chat Application using RabbitMQ

## Overview
This project implements a simple real-time chat application using RabbitMQ as middleware.  
The system allows multiple users to join chat rooms and exchange messages in real time.

The application was developed incrementally, starting from basic message testing to a complete web-based chat interface.

---

## Final Version - Web Application

### Project structure
- `app.py`  
  Main Flask application handling routes, sessions, and user interaction.

- `rabbitmq_utils.py`  
  Handles all RabbitMQ logic including sending and receiving messages.

- `templates/`
  - `join.html` → user login page (username + room)
  - `chat.html` → chat interface
  - `change_room.html` → allows switching chat rooms



### Technologies used
- Python 3
- RabbitMQ (via Docker)
- Flask (for web interface)
- Pika (RabbitMQ Python client)
- HTML (for UI templates)



### How to Run the Application

1. Start RabbitMQ
Make sure Docker Desktop is running, then start RabbitMQ.

2. Install dependencies

    Windows:
        pip install -r requirements.txt

    Mac:
        pip3 install -r requirements.txt

Alternatively, install manually:

    Windows:
        pip install pika flask

    Mac:
        pip3 install pika flask

3. Run the application:
Windows:
    python app.py

Mac:
    python3 app.py

4. Open the following URL in your browser (displayed in the terminal):
http://localhost:5000



### Features 

- Multiple users
- Multiple chat rooms
- Real-time messaging (polling)
- Change room without logging out
- Logout functionality


### How it works

The system uses a **topic exchange** (`chat_exchange`) in RabbitMQ.

- Each chat room is represented by a routing key (e.g., `room1`)
- Messages are published to the exchange
- Users subscribe to a specific room
- Only users in the same room receive the messages

Message format is JSON:

```json
{
  "sender": "Giada",
  "room": "room1",
  "message": "Hello"
}
```

### Notes

- This is a prototype for learning purposes
- RabbitMQ acts as middleware to decouple communication between clients
- Temporary queues (amq.gen-*) are created dynamically for each user session


## Previous versions - Development process
(included for development reference)

- `test_connection.py`  
  Initial test to verify connection to RabbitMQ.

- `publisher.py` / `subscriber.py`  
  Basic message sending and receiving using RabbitMQ.

- `chat_queue_version.py`  
  Alternative version using simple queues instead of topic exchange.

- `chat.py`  
  Command-line chat application using topic exchange and JSON messages.

- `chat_gui_tkinter.py`  
  First attempt at a GUI using Tkinter (desktop-based interface).

- `chat_web.py`
  Initial web-based implementation (monolithic structure).