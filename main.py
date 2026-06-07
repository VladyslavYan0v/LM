import sys

from game_controller import GameController

if __name__ == "__main__":
    if not getattr(sys, "frozen", False):
        try:
            import generate_level
            generate_level.create_all_levels()
        except Exception as e:
            print(f"Warning: failed to regenerate levels: {e}")

    game = GameController()
    game.run()
