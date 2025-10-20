import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import chess
import random

# --- Configuration ---
SQUARE_SIZE = 64
AI_LEVEL = 2  # Default difficulty: 1=Easy, 2=Medium, 3=Hard
LEVEL_DEPTH = {1: 1, 2: 2, 3: 4}  # Depth for each difficulty level

# Unicode chess symbols
PIECES_UNICODE = {
    'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
    'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚'
}

class ChessGUI:
    def __init__(self, master):
        self.master = master
        master.title("Python Chess ♟️")

        self.board = chess.Board()
        self.selected_square = None
        self.valid_moves = []

        self.captured_white = []
        self.captured_black = []

        self.canvas = tk.Canvas(master, width=8 * SQUARE_SIZE, height=8 * SQUARE_SIZE)
        self.canvas.pack(side=tk.LEFT)
        self.canvas.bind("<Button-1>", self.on_click)

        # Side panel
        sidebar = tk.Frame(master, padx=10, pady=10)
        sidebar.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(sidebar, text="Difficulty:", font=("Arial", 12, "bold")).pack(pady=5)
        self.level_select = ttk.Combobox(sidebar, values=["Easy", "Medium", "Hard"], state="readonly")
        self.level_select.current(AI_LEVEL - 1)
        self.level_select.pack(pady=5)
        self.level_select.bind("<<ComboboxSelected>>", self.change_difficulty)

        self.status = tk.Label(sidebar, text="Your move (White)", font=("Arial", 12))
        self.status.pack(pady=20)

        self.captured_label_white = tk.Label(sidebar, text="White captured:", font=("Arial", 10))
        self.captured_label_white.pack(anchor="w")
        self.captured_label_black = tk.Label(sidebar, text="Black captured:", font=("Arial", 10))
        self.captured_label_black.pack(anchor="w")

        self.draw_board()
        self.draw_pieces()

    def change_difficulty(self, event):
        global AI_LEVEL
        level = self.level_select.get()
        AI_LEVEL = {"Easy": 1, "Medium": 2, "Hard": 3}[level]
        self.status.config(text=f"Difficulty set to {level}")

    def draw_board(self):
        self.canvas.delete("square")
        colors = ["#EEEED2", "#769656"]
        for row in range(8):
            for col in range(8):
                color = colors[(row + col) % 2]
                x1 = col * SQUARE_SIZE
                y1 = (7 - row) * SQUARE_SIZE
                x2 = x1 + SQUARE_SIZE
                y2 = y1 + SQUARE_SIZE
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, tags="square")

        # Draw move hints
        if self.selected_square:
            for move in self.valid_moves:
                to_sq = move.to_square
                col = chess.square_file(to_sq)
                row = 7 - chess.square_rank(to_sq)
                x = col * SQUARE_SIZE + SQUARE_SIZE / 2
                y = row * SQUARE_SIZE + SQUARE_SIZE / 2
                self.canvas.create_oval(
                    x - 8, y - 8, x + 8, y + 8,
                    fill="gray", outline="", tags="square"
                )

    def draw_pieces(self):
        self.canvas.delete("piece")
        for square, piece in self.board.piece_map().items():
            row = 7 - chess.square_rank(square)
            col = chess.square_file(square)
            x = col * SQUARE_SIZE + SQUARE_SIZE / 2
            y = row * SQUARE_SIZE + SQUARE_SIZE / 2
            self.canvas.create_text(x, y, text=PIECES_UNICODE[piece.symbol()],
                                    font=("Arial", 40), tags="piece")

    def on_click(self, event):
        col = event.x // SQUARE_SIZE
        row = 7 - (event.y // SQUARE_SIZE)
        square = chess.square(col, row)

        if self.selected_square is None:
            piece = self.board.piece_at(square)
            if piece and piece.color == chess.WHITE:
                self.selected_square = square
                self.valid_moves = [m for m in self.board.legal_moves if m.from_square == square]
                self.draw_board()
                self.draw_pieces()
        else:
            move = chess.Move(self.selected_square, square)
            piece = self.board.piece_at(self.selected_square)

            # Handle pawn promotion
            if piece and piece.piece_type == chess.PAWN and chess.square_rank(square) == 7:
                promo_piece = simpledialog.askstring("Promotion", "Promote to (q, r, b, n):")
                if promo_piece not in ["q", "r", "b", "n"]:
                    promo_piece = "q"
                move = chess.Move(self.selected_square, square, promotion={
                    "q": chess.QUEEN, "r": chess.ROOK, "b": chess.BISHOP, "n": chess.KNIGHT
                }[promo_piece])

            if move in self.board.legal_moves:
                captured = self.board.piece_at(move.to_square)
                if captured:
                    self.captured_black.append(PIECES_UNICODE[captured.symbol()])
                self.board.push(move)
                self.update_captured_labels()
                self.selected_square = None
                self.valid_moves = []
                self.draw_board()
                self.draw_pieces()

                if self.board.is_game_over():
                    result = self.board.result()
                    self.status.config(text=f"Game Over! Result: {result}")
                    return

                self.status.config(text="Computer thinking...")
                self.master.after(200, lambda: self.computer_move())
            else:
                self.selected_square = None
                self.valid_moves = []
                self.draw_board()
                self.draw_pieces()

    def update_captured_labels(self):
        self.captured_label_white.config(text=f"White captured: {' '.join(self.captured_white)}")
        self.captured_label_black.config(text=f"Black captured: {' '.join(self.captured_black)}")

    def evaluate_board(self):
        values = {
            chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
            chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 20000
        }
        score = 0
        for square, piece in self.board.piece_map().items():
            value = values[piece.piece_type]
            rank = chess.square_rank(square)
            file = chess.square_file(square)
            center_bonus = 10 - (abs(3.5 - rank) + abs(3.5 - file)) * 2
            if piece.color == chess.WHITE:
                score += value + center_bonus
            else:
                score -= value + center_bonus
        return score

    def get_best_move(self, depth):
        best_move = None
        best_value = -999999
        moves = list(self.board.legal_moves)

        if AI_LEVEL == 1:
            random.shuffle(moves)
        elif AI_LEVEL == 2:
            moves = sorted(moves, key=lambda m: random.random())

        for move in moves:
            self.board.push(move)
            value = -self.minimax(depth - 1, -1000000, 1000000, False)
            self.board.pop()

            if AI_LEVEL < 3:
                value += random.randint(-30, 30)

            if value > best_value:
                best_value = value
                best_move = move
        return best_move

    def minimax(self, depth, alpha, beta, maximizing_player):
        if depth == 0 or self.board.is_game_over():
            return self.evaluate_board()

        if maximizing_player:
            max_eval = -999999
            for move in self.board.legal_moves:
                self.board.push(move)
                eval = self.minimax(depth - 1, alpha, beta, False)
                self.board.pop()
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = 999999
            for move in self.board.legal_moves:
                self.board.push(move)
                eval = self.minimax(depth - 1, alpha, beta, True)
                self.board.pop()
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def computer_move(self):
        if self.board.is_game_over():
            return

        depth = LEVEL_DEPTH.get(AI_LEVEL, 2)
        best_move = self.get_best_move(depth)
        if best_move:
            piece = self.board.piece_at(best_move.from_square)
            if piece and piece.piece_type == chess.PAWN and chess.square_rank(best_move.to_square) == 0:
                best_move.promotion = chess.QUEEN

            captured = self.board.piece_at(best_move.to_square)
            if captured:
                self.captured_white.append(PIECES_UNICODE[captured.symbol()])

            self.board.push(best_move)
            self.update_captured_labels()
            self.draw_board()
            self.draw_pieces()

            if self.board.is_game_over():
                result = self.board.result()
                self.status.config(text=f"Game Over! Result: {result}")
            else:
                self.status.config(text="Your move (White)")

# --- Run the game ---
root = tk.Tk()
app = ChessGUI(root)
root.mainloop()
