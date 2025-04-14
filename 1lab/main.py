

import socket
import struct
import json
import os
import logging
from threading import Thread


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def server_program():
    HOST = '127.0.0.1'  
    PORT = 65432         

    programs = {}


    if os.path.exists('programs.json'):
        with open('programs.json', 'r') as file:
            programs = json.load(file)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    logging.info(f"Server started and listening on {HOST}:{PORT}")

    def handle_client(client_socket):
        while True:
            try:
    
                data = client_socket.recv(1024)
                if not data:
                    break

                command = data.decode('utf-8')
                logging.info(f"Received command: {command}")

                if command.startswith('ADD'):
                    _, program_name = command.split(' ', 1)
                    if program_name not in programs:
                        programs[program_name] = {'status': 'added'}
                        os.makedirs(program_name, exist_ok=True)
                        logging.info(f"Program {program_name} added.")
                        client_socket.send(f"Program {program_name} added successfully.".encode('utf-8'))
                    else:
                        client_socket.send(f"Program {program_name} already exists.".encode('utf-8'))

                elif command.startswith('GET_OUTPUT'):
                    combined_output = {prog: info for prog, info in programs.items()}
                    client_socket.send(json.dumps(combined_output).encode('utf-8'))

            except Exception as e:
                logging.error(f"Error handling client: {e}")
                break

        client_socket.close()

    while True:
        client_socket, addr = server_socket.accept()
        logging.info(f"Connection established with {addr}")
        client_handler = Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

    with open('programs.json', 'w') as file:
        json.dump(programs, file)

server_program()
Asset 1 of 2
    pass



