from __future__ import annotations

import html
import os

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from handlers.callback_data import MainMenu
from services.i18n import Locale, tr


def support_mono_url() -> str:
    return (os.getenv("SUPPORT_MONO_URL") or "").strip()


def support_buymeacoffee_url() -> str:
    return (os.getenv("SUPPORT_BUYMEACOFFEE_URL") or "").strip()


def support_feedback_url() -> str:
    return (os.getenv("SUPPORT_FEEDBACK_URL") or "").strip()


def help_text_html(locale: Locale) -> str:
    core = tr(locale, "help.block")
    mono = support_mono_url()
    bmac = support_buymeacoffee_url()
    if locale == "uk":
        tail = tr(locale, "help.support_mono") if mono else tr(locale, "help.support_generic")
    else:
        if bmac:
            tail = tr(locale, "help.support_bmac")
        elif mono:
            tail = tr(locale, "help.support_mono")
        else:
            tail = tr(locale, "help.support_generic")
    return core + tail


def coffee_footer_html(locale: Locale) -> str:
    block = tr(locale, "coffee.block")
    mono = support_mono_url()
    bmac = support_buymeacoffee_url()
    if locale == "uk" and mono:
        return "\n".join(
            [
                block,
                "",
                f'• <a href="{html.escape(mono, quote=True)}">{tr(locale, "coffee.link_mono")}</a>',
            ]
        )
    if locale == "en":
        if bmac:
            return "\n".join(
                [
                    block,
                    "",
                    f'• <a href="{html.escape(bmac, quote=True)}">{tr(locale, "coffee.link_bmac")}</a>',
                ]
            )
        if mono:
            return "\n".join(
                [
                    block,
                    "",
                    f'• <a href="{html.escape(mono, quote=True)}">{tr(locale, "coffee.link_mono")}</a>',
                ]
            )
    return block


def help_reply_markup(locale: Locale) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if locale == "uk":
        if u := support_mono_url():
            rows.append([InlineKeyboardButton(text=tr(locale, "btn.support_mono"), url=u)])
    else:
        if u := support_buymeacoffee_url():
            rows.append([InlineKeyboardButton(text=tr(locale, "btn.support_bmac"), url=u)])
        elif u := support_mono_url():
            rows.append([InlineKeyboardButton(text=tr(locale, "btn.support_mono"), url=u)])
    if u := support_feedback_url():
        rows.append([InlineKeyboardButton(text=tr(locale, "btn.feedback_dev"), url=u)])
    rows.append(
        [InlineKeyboardButton(text=tr(locale, "btn.back_actions"), callback_data=MainMenu(act="mn").pack())]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
