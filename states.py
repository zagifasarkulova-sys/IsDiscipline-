from aiogram.fsm.state import State, StatesGroup


class FocusStates(StatesGroup):
    # Onboarding
    entering_user_name = State()
    setting_goal = State()

    # Task
    entering_task = State()
    editing_task = State()

    # Focus timer
    custom_timer = State()
    custom_break = State()
    in_focus = State()

    # Evening reflection
    reflection_prevented = State()
    reflection_change = State()

    # Goal editing
    editing_goal = State()
    entering_weekly_goal = State()

    # Settings
    changing_user_name = State()
    changing_mentor_name = State()
    admin_set_morning = State()
    admin_set_evening = State()
