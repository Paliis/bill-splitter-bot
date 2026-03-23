from aiogram.fsm.state import State, StatesGroup


class TripSG(StatesGroup):
    waiting_name = State()


class ExpenseSG(StatesGroup):
    waiting_amount = State()
    waiting_description = State()
    choosing_participants = State()
