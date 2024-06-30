from flask import Flask, render_template, request, send_from_directory, redirect, url_for
import threading
import socket
import json
from datetime import datetime
import os

app = Flask(__name__, static_folder='static', template_folder='templates')


# Маршрут для головної сторінки
@app.route('/')
def index():
    return render_template('index.html')


# Маршрут для сторінки з формою
@app.route('/message.html')
def message():
    return render_template('message.html')


# Обробка форми
@app.route('/message', methods=['POST'])
def handle_message():
    username = request.form['username']
    message = request.form['message']

    # Надсилання даних на socket-сервер
    send_to_socket_server(username, message)

    return redirect(url_for('index'))


# Обробка статичних файлів (CSS, зображення)
@app.route('/style.css')
def css():
    return send_from_directory('static', 'style.css')


@app.route('/logo.png')
def logo():
    return send_from_directory('static', 'logo.png')


# Обробка помилки 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html'), 404


# Функція для надсилання даних на socket-сервер
def send_to_socket_server(username, message):
    data = {
        'username': username,
        'message': message
    }
    udp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_client_socket.sendto(json.dumps(data).encode(), ('127.0.0.1', 5002))


# Socket-сервер для збереження даних у JSON файл
def socket_server():
    udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        udp_server_socket.bind(('127.0.0.1', 5002))
    except OSError as e:
        print(f"Error binding socket: {e}")
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
            print(f"Error receiving message: {e}")
        finally:
            udp_server_socket.close()


if __name__ == '__main__':
    # Запуск socket-сервера у окремому потоці
    threading.Thread(target=socket_server, daemon=True).start()

    # Запуск Flask-сервера у головному потоці
    app.run(port=3000, debug=True)
