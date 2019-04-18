import json
import socket
import ssl
import base64
import configparser
import os

config = configparser.ConfigParser()
config.read('user.ini')
config.read('attachments/message.ini')

HOST = 'smtp.yandex.ru'
PORT = 465
LOGIN = config['DEFAULT']['LOGIN']
PASSWORD = config['DEFAULT']['PASSWORD']


def send_command(sock: socket.socket, command, buffer=1024):
    sock.send(command + b'\n')
    return sock.recv(buffer).decode()


def create_message(
        login: str,
        recipient: str,
        theme: str,
        message_text: str) -> str:
    return (
        f'From: {login}\n'
        f'To: {recipient}\n'
        f'Subject: {theme}\n\n'
        f'{message_text}\n'
        f'.'
    )


def create_message_with_attachment(
        login: str,
        recipient: str,
        theme: str,
        message_text: str,
        files: list) -> str:
    separator = 'sep'
    message_text = message_text.replace('.', '..')
    mess = (
        f'To: {recipient}\n'
        f'From: {login}\n'
        f'MIME-Version: 1.0\n'
        f'Subject: {theme}\n'
        f'Content-Type: multipart/mixed; boundary={separator}; charset=UTF-8\n\n'
        f'--sep\n\n'
        f'{message_text}\n'
        f'--sep\n'
    )
    for e in files:
        content_type = e[2]
        content_filename = e[0]
        content_file = e[1]
        mess += (
            f'Content--Type: {content_type}; name="{content_filename}"\n'
            f'Content-Disposition: attachment; filename="{content_filename}"\n'
            f'Content-Transfer-Encoding: base64\n\n'
            f'{content_file}\n'
            f'--sep\n')
    mess += f'--sep--\n'
    mess += f'.'
    print(mess)
    return mess


def send_message(sock: socket.socket, recipient: str, message: str):
    print(send_command(sock, b'MAIL FROM:' + LOGIN.encode('cp1251')))

    print(send_command(sock, b'RCPT TO:' + recipient.encode('cp1251')))
    print(send_command(sock, b'DATA'))
    print(send_command(sock, message.encode('cp1251')))


def login_in(sock: socket.socket):
    print(sock.recv(1024).decode())
    send_command(sock, b'EHLO test')
    print(send_command(sock, b'AUTH LOGIN'))
    print(send_command(sock, base64.b64encode(LOGIN.encode())))
    print(send_command(sock, base64.b64encode(PASSWORD.encode())))


def get_attachments():
    files = []
    with open('content_types.json') as f:
        content_types = json.loads(f.read())
    for e in config['MESSAGE']['ATTACHMENTS'].split(';'):
        if not os.path.isfile(e):
            print(f'no such file: {e}')
            continue
        with open(e, 'rb') as f:
            file_content = f.read()
            content_type = content_types[e.split('.')[-1]]
            content = base64.b64encode(file_content).decode()
            files.append((e, content, content_type))

    return files


if __name__ == '__main__':
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock = ssl.wrap_socket(sock)
        sock.connect((HOST, PORT))

        login_in(sock)

        with open('attachments/message.txt') as f:
            message_text = f.read()

        files = get_attachments()

        if len(files) == 0:
            mess = create_message(LOGIN,
                                  config['MESSAGE']['RECIPIENT'],
                                  config['MESSAGE']['SUBJECT'],
                                  message_text)
        else:
            mess = create_message_with_attachment(LOGIN,
                                                  config['MESSAGE']['RECIPIENT'],
                                                  config['MESSAGE']['SUBJECT'],
                                                  message_text,
                                                  files)

        send_message(sock, config['MESSAGE']['RECIPIENT'], mess)
