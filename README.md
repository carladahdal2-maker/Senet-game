Senet Game with AI (Expectiminimax) 

This project is a digital implementation of the ancient Egyptian board game Senet. 
It features a robust graphical user interface and a sophisticated Artificial Intelligence opponent that utilizes advanced search algorithms
to simulate strategic play.

- AI & Search Algorithms 

The AI is powered by the Expectiminimax algorithm, specifically designed for games involving elements of chance (like stick throwing).

Chance Nodes: The AI calculates the probability of each possible roll (1, 2, 3, 4, or 5) based on the mechanics of four two-sided sticks.

Transposition Tables: Uses a hashing system to store and reuse previously evaluated board states, significantly improving search efficiency.

Heuristic Evaluation: The board is scored based on piece progression, protection, and the number of pieces successfully "borne off" (exited) the board.

Move Ordering: Prioritizes evaluating moves that result in capturing opponent pieces or exiting the board to optimize the search process.

- Game Features

GUI Interface: A full graphical board built with Pygame, including special markers for the "House of Water", "House of Rebirth" and other traditional squares.

Hint System: Players can request a hint. The AI will analyze the current state and highlight the best move for the human player.

Adjustable Difficulty: Users can dynamically change the AI's search depth (1–6) during gameplay to adjust the challenge level.

Authentic Rules: Implements complex traditional rules, including piece swapping, safe zones, and the requirement to land exactly on certain squares to exit.

- Project Structure

main.py: The entry point for the application.

senet_ai.py: Contains the logic for the Expectiminimax search and evaluation functions.

game_controller.py: Manages the game loop, turn transitions, and AI threading.

game.py: Defines the board logic, valid moves, and movement rules.

ui.py: Handles all rendering, animations, and user input.

dice.py: Simulates the throwing of four Senet sticks.

- Getting Started

Ensure you have pygame installed.
Run the game using:
python main.py

Developed as a demonstration of AI search algorithms in stochastic (chance-based) environments.
