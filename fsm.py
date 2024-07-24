from enum import Enum, auto
import logging

# логирование чтобы в консоли я мог отслеживать как меняются те или иные статусы пользователей
def log_state_change(user_id, from_state, to_state):
    logging.info(f"User {user_id}  state changed from {from_state.name} to {to_state.name}")


class States(Enum):
    START = auto()
    AWAITING_BALANCE = auto()
    REGISTRATION_COMPLETE = auto()
    NONE = auto()

    #добавление доходов
    WAITING_FOR_INCOME_AMOUNT = auto()
    WAITING_FOR_INCOME_CATEGORY = auto()
    INCOME_ADDITION_COMPLETE = auto()

    # добавление расходов
    WAITING_FOR_EXPENSE_AMOUNT = auto()
    WAITING_FOR_EXPENSE_CATEGORY = auto()
    EXPENSE_ADDITION_COMPLETE = auto()

    # своя категория
    AWAITING_CUSTOM_INCOME_CATEGORY_NAME = auto()
    AWAITING_CUSTOM_EXPENSE_CATEGORY_NAME = auto()
    AWAITING_CUSTOM_INCOME_AMOUNT = auto()
    AWAITING_CUSTOM_EXPENSE_AMOUNT = auto()

    # показ его транзакций
    VIEWING_TRANSACTIONS = auto()

    # статистика расходов
    AWAITING_STATS_START_DATE = auto()
    AWAITING_STATS_END_DATE = auto()
    DISPLAYING_STATS = auto()

    # календарь статистики расходов
    AWAITING_STATS_MONTH_SELECTION = auto()
    AWAITING_STATS_DAY_SELECTION = auto()

    # напоминания
    AWAITING_REMINDER_DATE = auto()
    AWAITING_REMINDER_TIME = auto()
    AWAITING_REMINDER_MESSAGE = auto()
    AWAITING_EVERYDAY_RESPONSE = auto()
    REMINDER_ADDITION_COMPLETE = auto()




class FSM:
    def __init__(self):
        self.user_states = {}

    def set_state(self, user_id, state):
        from_state = self.get_state(user_id)
        self.user_states[user_id] = state
        print(f"Изменен статус user {user_id} на {state.name}")
        log_state_change(user_id, from_state, state)

    def get_state(self, user_id):
        return self.user_states.get(user_id, States.NONE)

    def reset_state(self, user_id):
        from_state = self.get_state(user_id)
        self.user_states[user_id] = States.NONE
        print(f"Изменен статус user {user_id} сброс до NONE ")
        log_state_change(user_id, from_state, States.NONE)
