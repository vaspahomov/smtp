import json
import socket
import ssl
import base64
import configparser
import os

config = configparser.ConfigParser()
config.read('user.ini')
config.read('attachments/message.ini')

HOST = config['DEFAULT']['HOST_NAME']
PORT = int(config['DEFAULT']['HOST_PORT'])
LOGIN = config['DEFAULT']['LOGIN']
PASSWORD = config['DEFAULT']['PASSWORD']


def send_command(sock: socket.socket, command, buffer=1024):
    print(command)
    sock.send(command + b'\r\n')
    return sock.recv(buffer).decode()


def create_message(login: str, recipient: str, theme: str, message_text: str) -> str:
    if len(message_text.split('\n')) > 1:
        message_text.replace('\n.', '\n..')
    else:
        message_text.replace('.', '..')
    return (
        f'From: {login}\r\n'
        f'To: {recipient}\r\n'
        f'Subject: {theme}\r\n\r\n'
        f'{message_text}\r\n'
        f'.\r\n'
    )


def encode_subj(subj: str) -> str:
    b64_message = base64.b64encode(subj.encode('cp1251')).decode('cp1251')
    multiline_message = ''
    l = int(len(b64_message) / 32)
    for e in range(l + 1):
        if l > e:
            multiline_message += f'=?cp-1251?B?{b64_message[e * 32: (e + 1) * 32]}?=\r\n  '
        else:
            multiline_message += f'=?cp-1251?B?{b64_message[e * 32:]}?='

    return multiline_message


def create_message_with_attachment(login: str, recipient: str, theme: str, message_text: str, files: list) -> str:
    separator = '@vaspahomov'
    if message_text[0] == '.':
        message_text = '.' + message_text
    message_text = message_text.replace('\n.', '\n..')
    mess = (
        f'To: {recipient}\r\n'
        f'From: {login}\r\n'
        f'MIME-Version: 1.0\r\n'
        f'Subject: {encode_subj(theme)}\r\n'
        f'Content-Type: multipart/mixed; boundary="{separator}"; charset=UTF-8\r\n\r\n'
        f'--{separator}\r\n\r\n'
        f'{message_text}\r\n'
        f'--{separator}\r\n'
    )
    for e in files:
        content_type = e[2]
        content_filename = e[0]
        content_file = e[1]
        mess += (
            f'Content--Type: {content_type}; name="{content_filename}"\r\n'
            f'Content-Disposition: attachment; filename="{content_filename}"\r\n'
            f'Content-Transfer-Encoding: base64\r\n\r\n'
            f'{content_file}\r\n'
            f'--{separator}\r\n')
    mess += f'--{separator}--\r\n'
    mess += f'.\r\n'
    return mess


def send_message(sock: socket.socket, recipient: str, message: str):
    print(send_command(sock, f'MAIL FROM: <{LOGIN}>'.encode('cp1251')))
    print(send_command(sock, f'RCPT TO: <{recipient}>'.encode('cp1251')))
    print(send_command(sock, b'DATA'))
    print(send_command(sock, message.encode('cp1251')))


def login_in(sock: socket.socket):
    print(sock.recv(1024).decode())
    print(send_command(sock, f'EHLO test'.encode()))
    print(send_command(sock, b'AUTH LOGIN'))
    print(send_command(sock, base64.b64encode(LOGIN.encode())))
    print(send_command(sock, base64.b64encode(PASSWORD.encode())))


def close_connection(sock: socket.socket):
    print(send_command(sock, b'QUIT'))


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
        close_connection(sock)
