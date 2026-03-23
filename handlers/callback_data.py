from aiogram.filters.callback_data import CallbackData


class MainMenu(CallbackData, prefix="mm"):
    act: str


class WizardCancel(CallbackData, prefix="wc"):
    pass


class ExpSplitAll(CallbackData, prefix="esa"):
    pass


class ExpToggle(CallbackData, prefix="eto"):
    user_id: int


class ExpConfirm(CallbackData, prefix="eco"):
    pass


class ExpCancel(CallbackData, prefix="ecx"):
    pass
