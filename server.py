# -*- coding: utf-8 -*-
import socket
from threading import Thread
import sys
import json
import struct
from CNN import DotsNet
from engine import Game
from MCTS import MCTS


def client_connected():
    return  {
        "action": "connected"
    }

def close_client(addr, args):
    try:
        print(addr, "closing.")
        clients[addr]['exe'].stopThreads = True
        clients[addr]['com'].stopThreads = True
        clients[addr]['mcts'] = None
        clients[addr]['game'] = None
        clients[addr]['sock'].close()
        del clients[addr]
    except:
        # already closed
        pass

def close_server():
    print("Closing server...")
    SERVER.close()

    for addr in clients.keys():
        clients[addr]['sock'].close()

    sys.exit()

def new_game(addr, args):
    if args is None:
        if clients[addr]['game'] is not None:
            # 2 - the game already has started
            return  {
                "action": "error",
                "args": {
                    "error_code": 2
                }
            }


    new_game = Game(15, 15)
    crosses = new_game.reset()
    clients[addr]['game'] = new_game
    clients[addr]['mcts'] = MCTS(10, nnet)

    print("game started", addr)

    for i in crosses.keys():
        out = []
        for x, y in crosses[i]:
            out.append(x)
            out.append(y)
        crosses[i] = out
    
    out_args = {
        "action": "new_game_started",
        "args": {
            "crosses_blue": crosses[-1],
            "crosses_red": crosses[1]
        }
    }
    if 'player_color' in args:
        if args['player_color'] == 1:
            a = get_turn_for_game(addr)
            new_game.auto_turn(a)

            out_args['args']['dot'] = new_game.get_pos_of_ind(a)

    return out_args

def end_game(addr, args):
    clients[addr]['game'] = None
    clients[addr]['mcts'] = None

def get_turn_for_game(addr):
    mcts = clients[addr]['mcts']
    game = clients[addr]['game']

    mcts.play_simulations(game)
    pi = mcts.getVecPi(game)         # all actions' probabilities (not possible actions with 0 probability)
    pi = sorted(enumerate(pi), key=lambda p: p[1])
    a = len(pi) - 1
    # ищем свободное действие 
    while pi[a][0] in game.busy_dots:
        a -= 1
    a = pi[a][0]

    
    return a

def auto_turn_server(addr, args):
    if clients[addr]['turn_ignore']:
        print("turn blocked")
        # error 3 - wait for server answer
        return {
            "action": "error",
            "args": {
                "error_code": 3
            }
        }

    if clients[addr]['game'] is None:
        # error 0 - the game haven't been started
        return {
            "action": "error",
            "args": {
                "error_code": 0
            }
        }

    game = clients[addr]['game']
    try:
        game.auto_turn(
            game.get_ind_of_pos(args['dot'][0], args['dot'][1])
        )
    except:
        # error 1 - turn error
        return {
            "action": "error",
            "args": {
                "error_code": 1
            }
        }

    if game.gameEnded():
        end_game(addr)

        return {
            "action": "end_game"
        }

    a = get_turn_for_game(addr)

    game.auto_turn(a)

    if game.gameEnded():
        end_game(addr)
        action_type = "end_game"
    else:
        action_type = "turn"

    # ignore all turns until client have recived turn and answered server
    clients[addr]['turn_ignore'] = True

    return {
        "action": action_type,
        "args": {
            "dot": game.get_pos_of_ind(a)
        }
    }

def client_got_turn(addr, args):
    clients[addr]['turn_ignore'] = False

class Communicator:
    header_len = 4  # (unsigned int) header length in byte which defines length of next json content
    def __init__(self, sock, addr):
        self.executor = None
        self.sock = sock
        self.addr = addr
        self._recv_buffer = b""
        self._send_buffer = b""
        self.json_content = None
        self.json_len = None
        self.response_queue = []
        self.isWriting = False
        self.stopThreads = False

    def set_executor(self, value):
        self.executor = value
        self.start_reading()

    def start_reading(self):
        # starts once when object is identified
        # endless loop
        read_thread = Thread(target=self.read)
        read_thread.daemon = True
        read_thread.start()

    def start_writing(self):
        # starts by executor object
        # finite loop
        if not self.isWriting:
            self.isWriting = True
            write_thread = Thread(target=self.write)
            write_thread.daemon = True
            write_thread.start()

    def write(self):
        while self.response_queue:
            if self.stopThreads:
                break
            self._send_buffer = self._construct_message(self.response_queue.pop())
            print("Sending message", self._send_buffer)
            while True:
                if not self._send_buffer:
                    break
                self._write()

        self.isWriting = False

    def _write(self):
        try:
            # Should be ready to write
            sent = self.sock.send(self._send_buffer)
        except BlockingIOError:
            # Resource temporarily unavailable (errno EWOULDBLOCK)
            pass
        else:
            self._send_buffer = self._send_buffer[sent:]

    def _construct_message(self, json_dict):
        # append to start of json string it's length
        json_string = self._json_encode(json_dict)
        content_len = struct.pack(">I", len(json_string))
        return content_len + json_string

    def read(self):
        while True:
            if self.stopThreads:
                break

            self._read()    # block until can able to read
            
            if self.json_len is None:
                self.get_json_len()

            if self.json_len is not None:
                if self.json_content is None:
                    self.get_json_content()

            if self.json_content is not None:
                self.send_json_to_executor()


    def _read(self):
        try:
            data = self.sock.recv(1024)
        except:
            # nothing to recieve
            pass
        else:
            if data:
                self._recv_buffer += data
            else:
                # No data. Client socked closed
                close_client(self.addr, None)

    def get_json_len(self):
        if len(self._recv_buffer) >= self.header_len:
            self.json_len = struct.unpack('>I', self._recv_buffer[:self.header_len])[0]
            self._recv_buffer = self._recv_buffer[self.header_len:]

    def get_json_content(self):
        if len(self._recv_buffer) >= self.json_len:
            self.json_content = self._json_decode(self._recv_buffer[:self.json_len])
            self._recv_buffer = self._recv_buffer[self.json_len:]

    def send_json_to_executor(self):
        self.executor.add_task(self.json_content)
        self.json_content = None
        self.json_len = None

    def add_response(self, new_response):
        self.response_queue.append(new_response)
        self.start_writing()

    def _json_decode(self, byte_string):
        return json.loads(byte_string.decode('utf8'))

    def _json_encode(self, json_dict):
        return json.dumps(json_dict, ensure_ascii=False).encode('utf8')

class Executor:
    tasks = {
        'disconnect': close_client,
        'new_game': new_game,
        'turn': auto_turn_server,
        'end_game': end_game,
        'got_turn': client_got_turn,
    }

    def __init__(self, addr):
        self.addr = addr
        self.task_queue = []
        self.isExecuting = False
        self.com = None
        self.stopThreads = False

    def set_communicator(self, value):
        self.com = value

    def add_task(self, task_dict):
        self.task_queue.append(task_dict)
        self.start_execution()

    def _json_to_dict(self, json_string):
        return json.loads(json_string)

    def start_execution(self):
        if not self.isExecuting:
            self.isExecuting = True
            execute_thread = Thread(target=self.execute)
            execute_thread.daemon = True
            execute_thread.start()

    def execute(self):
        while self.task_queue:
            print(self.task_queue)
            if self.stopThreads:
                break
            cur_task = self.task_queue.pop()
            self.start_task(cur_task)

        self.isExecuting = False

    def start_task(self, task):
        if 'action' not in task:
            return
        if 'args' not in task:
            args = None
        else:
            args = task['args']

        action = task['action']        
        print('starting action:', action, 'with args:', args)
        response = self.tasks[action](self.addr, args)

        if response is not None:
            self.com.add_response(response)

def accept_wrapper():
    while True:
        conn, addr = SERVER.accept()  # Should be ready to read
        print("accepted connection from", addr)

        # create executor and communicator to execute task
        # on server part and communicate with socket
        exe = Executor(addr)
        com = Communicator(conn, addr)
        exe.set_communicator(com)
        com.set_executor(exe)

        clients[addr] = {
            'sock': conn,
            'exe': exe,
            'com': com,
            'game': None,
            'mcts': None,
            'turn_ignore': False,
        }

        com.add_response(client_connected())
        print("Clients now:", len(clients))

# load trained net
nnet = DotsNet()
nnet.load(folder="source/models/", name="m")

# set server
clients = {}

HOST = "127.0.0.1"
PORT = 6000
SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SERVER.bind((HOST, PORT))

if __name__ == "__main__":
    try:
        SERVER.listen()
        print("Server has started")
        SERVER_THREAD = Thread(target=accept_wrapper)
        SERVER_THREAD.daemon = True
        SERVER_THREAD.start()
        while SERVER_THREAD.isAlive():
            SERVER_THREAD.join(1)
    except KeyboardInterrupt:
        close_server()