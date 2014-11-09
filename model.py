import sqlite3
from ast import literal_eval as parse

db = sqlite3.connect('chess.db')

class InvalidMove(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class ChessGame:
    turn = 'white'
    board = [
        ['BR', 'BN', 'BB', 'BK', 'BQ', 'BB', 'BN', 'BR'],
        ['BP', 'BP', 'BP', 'BP', 'BP', 'BP', 'BP', 'BP'],
        ['', '', '', '', '', '', '', ''],
        ['', '', '', '', '', '', '', ''],
        ['', '', '', '', '', '', '', ''],
        ['', '', '', '', '', '', '', ''],
        ['WP', 'WP', 'WP', 'WP', 'WP', 'WP', 'WP', 'WP'],
        ['WR', 'WN', 'WB', 'WK', 'WQ', 'WB', 'WN', 'WR'],
    ]

    last_move = [(-1, -1), (-1, -1)]
    room_id = -1

    def __init__(self, room_id):
        game = db.execute('SELECT turn, board, last_move FROM games WHERE room = ?', (room_id, )).fetchone()

        self.room_id = room_id

        if game is not None:
            (turn, board, last_move) = game
            self.turn = turn
            self.board = parse(board)
            self.last_move = parse(last_move)
        else:
            db.execute(
                'INSERT INTO games VALUES (?, ?, ?, ?)',
                (str(self.room_id), str(self.board), str(self.turn), str(self.last_move))
            )

            db.commit()


    def move(self, command):
        coords = command.split(' to ')
        move_from = coords[0]
        move_to = coords[1]

        (from_x, from_y) = algebra_to_coord(move_from)
        (to_x, to_y) = algebra_to_coord(move_to)

        moving_piece = self.board[from_y][from_x]

        # Check validity
        if moving_piece == '':
            raise InvalidMove('There is no piece at ' + move_to)
        if moving_piece[0].lower() != self.turn[0].lower():
            raise InvalidMove('It is ' + self.turn + '\'s turn to move.')

        # Move
        self.board[from_y][from_x] = ''
        self.board[to_y][to_x] = moving_piece

        # Promotions
        if moving_piece == 'BP' and to_y == 7:
            self.board[to_y][to_x] = 'BQ'
        elif moving_piece == 'WP' and to_y == 0:
            self.board[to_y][to_x] = 'WQ'

        # Swap turns
        if self.turn == 'white':
            self.turn = 'black'
        else:
            self.turn = 'white'

        self.last_move = [
            (from_x, from_y),
            (to_x, to_y)
        ]

        self.save()

    def restart(self):
        db.execute(
            'DELETE FROM games WHERE room=?',
            (self.room_id,)
        )

        db.commit()

    def save(self):
        db.execute(
            'UPDATE games SET turn=?,board=?,last_move=? WHERE room=?',
            (self.turn, str(self.board), str(self.last_move), self.room_id)
        )

        db.commit()

def algebra_to_coord(algebra):
    x = ord(algebra[0]) - 96 - 1
    y = 8 - int(algebra[1])

    return x, y