from os import stat
from re import RegexFlag
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, CallbackQueryHandler
from utils.glob import *
from utils import config as conf

MAINTENANCE_SWITCH = JCallB("maintenance_switch")


@msg(adm="switchMaintenance")
def switch_maintenance(update,user):
    keyb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(f"Abilita {t_or_f(True)}",callback_data=MAINTENANCE_SWITCH.create({"action":True})),
                InlineKeyboardButton(f"Disabilita {t_or_f(False)}",callback_data=MAINTENANCE_SWITCH.create({"action":False}))
            ],
            [InlineKeyboardButton("🚫 Annulla",callback_data="cancel")]

        ]
    )
    status = "Attivata "+t_or_f(True) if conf.settings("maintenance") else "Disattivata "+t_or_f(False)
    update.message.reply_text(f"Limita l'accesso al bot tramite la manutenzione 🔧\nStato manutenzione: "+status, reply_markup=keyb)

@msg(adm="switchMaintenance", jcallb=True)
def switch_maintenance_btns(update,user,data):
    status = conf.settings("maintenance")
    if status == data["action"]:
        txt = "Attivata" if status else "Disattivata"
        update.message.edit_message_text(f"La manutenzione è già {txt}! 🔧")
    else:
        txt = "Attivata" if not status else "Disattivata"
        conf.settings("maintenance",data["action"])
        update.message.edit_message_text(f"La manutenzione è stata {txt}! 🔧")

handlers = [CommandHandler('maintenance',switch_maintenance),CallbackQueryHandler(switch_maintenance_btns,pattern=MAINTENANCE_SWITCH.regex_filter())]
