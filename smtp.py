import socket
import ssl
import base64
import configparser

config = configparser.ConfigParser()
config.read('user.ini')

HOST = 'smtp.yandex.ru'
PORT = 465
LOGIN = config['DEFAULT']['LOGIN']
PASSWORD = config['DEFAULT']['PASSWORD']


def send_command(sock: socket.socket, command, buffer=1024):
    sock.send(command + b'\n')
    return sock.recv(buffer).decode()


def create_message(login: str,
                   recipient: str,
                   theme: str,
                   message_text: str):
    return (
        f'From: {login}\n'
        f'To: {recipient}\n'
        f'Subject: {theme}\n\n'
        f'{message_text}\n'
        f'.'
    )
    # create message
    # обрабатывать точки


def send_message(sock: socket.socket,
                 recipient: str,
                 subject: str,
                 text: str):
    print(send_command(sock, b'MAIL FROM:' + LOGIN.encode()))

    print(send_command(sock, b'RCPT TO:' + recipient.encode()))
    print(send_command(sock, b'DATA'))

    message = create_message(
        LOGIN,
        recipient,
        subject,
        text
    )

    print(send_command(sock, message.encode()))


def login_in(sock: socket.socket):
    print(sock.recv(1024).decode())
    send_command(sock, b'EHLO test')
    print(send_command(sock, b'AUTH LOGIN'))
    print(send_command(sock, base64.b64encode(LOGIN.encode())))
    print(send_command(sock, base64.b64encode(PASSWORD.encode())))


if __name__ == '__main__':
    # send_message()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock = ssl.wrap_socket(sock)
        sock.connect((HOST, PORT))

        login_in(sock)
        send_message(sock, LOGIN, 'hello', 'world')
