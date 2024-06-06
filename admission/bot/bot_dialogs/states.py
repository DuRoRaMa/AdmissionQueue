from aiogram.fsm.state import State, StatesGroup


class TalonMenu(StatesGroup):
    GREETINGS = State()
    SUBSCRIBING = State()
    SUBSCRIBED = State()
    TALON_NOT_FOUND = State()
    TALON_IS_BUSY = State()


class Talon(StatesGroup):
    LIST = State()
    INFO = State()
    COMMENT = State()
    COMMENTED = State()


class Helper(StatesGroup):
    MAIN = State()
    LIST = State()
