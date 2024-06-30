from flask import Flask, render_template, request, send_from_directory, redirect, url_for
import threading
import socket
import json
from datetime import datetime
import os
import logging

app = Flask(__name__, static_folder='static', template_folder='templates')

# Logging configuration
logging.basicConfig(filename='app.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s')


# Route for the index page
@app.route('/')
def index():
    return render_template('index.html')


# Route for the message page
@app.route('/message.html')
def message():
    return render_template('message.html')


# Form handling
@app.route('/message', methods=['POST'])
def handle_message():
    try:
        username = request.form['username']
        message = request.form['message']

        # Validate input data
        if not username or not message:
            raise ValueError("Username or message cannot be empty.")

        # Logging
        logging.info(f"Received message from {username}: {message}")

        # Send data to socket server
        send_to_socket_server(username, message)

        return redirect(url_for('index'))

    except ValueError as ve:
        logging.error(f"Validation error: {str(ve)}")
        return render_template('error.html', message=str(ve)), 400

    except Exception as e:
        logging.error(f"Error handling message: {str(e)}")
        return render_template('error.html'), 500


# Handling static files (CSS, images)
@app.route('/style.css')
def css():
    return send_from_directory('static', 'style.css')


@app.route('/logo.png')
def logo():
    return send_from_directory('static', 'logo.png')


# Handling 404 errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html'), 404


# Function to send data to socket server
def send_to_socket_server(username, message):
    data = {
        'username': username,
        'message': message
    }
    udp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_client_socket.sendto(json.dumps(data).encode(), ('127.0.0.1', 5003))


# Socket server for storing data in JSON file
def socket_server():
    udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        udp_server_socket.bind(('127.0.0.1', 5003))
    except OSError as e:
        logging.error(f"Error binding socket: {e}")
        return

    storage_path = os.path.join('storage', 'data.json')
    if not os.path.exists('storage'):
        os.makedirs('storage')

    while True:
        try:
            message, addr = udp_server_socket.recvfrom(1024)
            data = json.loads(message.decode())

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            record = {timestamp: data}

            if os.path.exists(storage_path):
                with open(storage_path, 'r') as f:
                    content = json.load(f)
                content.update(record)
            else:
                content = record

            with open(storage_path, 'w') as f:
                json.dump(content, f, indent=4)

        except Exception as e:
            logging.error(f"Error receiving message: {e}")

        finally:
            udp_server_socket.close()


if __name__ == '__main__':
    # Start socket server in a separate thread
    threading.Thread(target=socket_server, daemon=True).start()

    # Start Flask server in the main thread
    app.run(port=6000, debug=True)


