from constants import ScreenState


class Command:
    def execute(self, controller):
        raise NotImplementedError("Command must implement execute")


class ApplyDisplayModeCommand(Command):
    def execute(self, controller):
        controller._apply_display_mode()


class StartStoryCommand(Command):
    def __init__(self, level_index):
        self.level_index = level_index

    def execute(self, controller):
        controller.story_state.setup_story(self.level_index)
        controller.set_state(ScreenState.STORY)


class StartLevelCommand(Command):
    def __init__(self, level_index):
        self.level_index = level_index

    def execute(self, controller):
        controller.level_state.setup_level(self.level_index)
        controller.set_state(ScreenState.LEVEL)


class GoToMainMenuCommand(Command):
    def execute(self, controller):
        controller.assets.play_music("music", "ingame_menu.flac")
        controller.set_state(ScreenState.MAIN_MENU)
