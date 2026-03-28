from aiogram.fsm.state import State, StatesGroup


class FocusStates(StatesGroup):
    # Onboarding
    setting_goal = State()

    # Morning
    entering_task = State()
    entering_medium_tasks = State()
    entering_small_tasks = State()

    # Focus timer
    custom_timer = State()
    in_focus = State()

    # Evening reflection
    reflection_prevented = State()
    reflection_change = State()

    # Goal editing
    editing_goal = State()

    # Weekly goal
    entering_weekly_goal = State()
    updating_weekly_progress = State()

    # Admin
    admin_set_morning = State()
    admin_set_evening = State()
