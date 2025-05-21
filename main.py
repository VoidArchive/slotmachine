import pygame
from game import Game

if __name__ == "__main__":
    game_instance = Game()
    game_instance.run()
    pygame.quit() # Ensure pygame quits properly after game loop ends
