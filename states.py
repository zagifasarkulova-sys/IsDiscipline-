from aiogram.fsm.state import State, StatesGroup


class AddTask(StatesGroup):
    waiting_title = State()
    waiting_remind_choice = State()
    waiting_remind_date = State()
    waiting_remind_time = State()


class EditTask(StatesGroup):
    waiting_new_title = State()
    waiting_remind_choice = State()
    waiting_remind_date = State()
    waiting_remind_time = State()


class FocusSession(StatesGroup):
    choosing_task = State()
    in_progress = State()
