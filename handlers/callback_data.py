from aiogram.filters.callback_data import CallbackData


class MainMenu(CallbackData, prefix="mm"):
    act: str


class WizardCancel(CallbackData, prefix="wc"):
    pass


class TripCurrency(CallbackData, prefix="tcr"):
    code: str


class ExpSplitAll(CallbackData, prefix="esa"):
    pass


class ExpRefreshMembers(CallbackData, prefix="erm"):
    pass


class ExpToggle(CallbackData, prefix="eto"):
    user_id: int


class ExpConfirm(CallbackData, prefix="eco"):
    pass


class ExpCancel(CallbackData, prefix="ecx"):
    pass
