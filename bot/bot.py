import importlib
from utils import updater as update_job
import utils.glob as glob
import utils.config as conf
from utils import db
from telegram.ext import (Updater, CommandHandler,
                            MessageHandler, Filters, ConversationHandler,
                            CallbackQueryHandler)

@glob.msg()
def start_msg(update,user):
    update.message.reply_text(
            "Benvenuto! D'ora in poi mi occuperò io di informarti sui nuovi documenti! 👍\n"
            "Se vuoi cercare i documenti, usa il comando /search 🔎\n\n"
            "Funzionalità del bot:\n"
            "🔔 Avvisi: Qui puoi ricevere importanti comunicazioni comunicate da docenti o studenti che hanno necessità di inviare avvisi\n"
            "📨 Documenti: Ogni volta che esce un nuovo documento, il bot ti invia una notifica e ti permette di visualizzarlo in comodità!\n"
            "Per sfogliare i documenti incomodità puoi utilizzare l'interfaccia web "+conf.EXTERNAL_API)

@glob.msg(bypass_maintenance = True)
def contact_msg(update,user):
    update.message.reply_text("Il bot è stato creato da <b>Domingo Dirutigliano</b>\n\n"
                            "🌍 Website: <a href=\"https://domysh.com/it/\">DomySh.com</a>\n"
                            "💸 Donazioni: <a href=\"https://donorbox.org/luigi-dell-erba-bot-circolari\">LINK</a>\n"
                            "📬 E-Mail: <a href=\"mailto://me@domysh.com\">me@domysh.com</a>\n"
                            "💬 Telegram: <a href=\"https://t.me/DomySh\">@DomySh</a>\n"
                            "💻 Codice Sorgente: <a href=\"https://github.com/DomySh/bot-trasparenzascuole\">domysh/bot-trasparenzascuole</a>",parse_mode='HTML')


@glob.msg()
def not_valid(update,user):
    update.message.reply_text("❌ Inserisci un comando valido!")
    return ConversationHandler.END

@glob.msg()
def not_valid_callback(update,user):
    update.message.edit_message_text("❌ Inserisci un comando valido!")
    return ConversationHandler.END


def load_modules():
    conversations = []
    other_handlers = []
    for module in conf.BOT_MODULES:
        module = "botmodules."+module
        mod = importlib.import_module(module)
        if conf.HANDLERS_MODULES_NAME in dir(mod) and type(getattr(mod,conf.HANDLERS_MODULES_NAME)) == list:
            for hendl in getattr(mod,conf.HANDLERS_MODULES_NAME):
                if type(hendl) == ConversationHandler:
                    conversations.append(hendl)
                else:
                    other_handlers.append(hendl)
    for hendl in conversations + other_handlers:
        glob.updater.dispatcher.add_handler(hendl)

def default_handlers():
    import botmodules.docs
    glob.updater.dispatcher.add_handler(CommandHandler('start',start_msg))
    glob.updater.dispatcher.add_handler(CommandHandler('contact',contact_msg))
    glob.updater.dispatcher.add_handler(CommandHandler('cancel', glob.cancel_op))
    glob.updater.dispatcher.add_handler(CallbackQueryHandler(glob.cancel_op_callback,pattern=glob.callb('cancel')))
    glob.updater.dispatcher.add_handler(MessageHandler(Filters.text,botmodules.docs.search_doc_command))
    glob.updater.dispatcher.add_handler(CallbackQueryHandler(not_valid_callback,pattern="^(.|\\n)*$"))

def init_dp():
    load_modules()
    default_handlers()

def init():
    import functools
    import builtins as __builtin__
    __builtin__.print = functools.partial(print, flush=True)
    glob.updater = Updater(conf.TOKEN, use_context=True)
    db.init()
    update_job.init()
    init_dp()

def run_bot_loop():
    if not conf.DEBUG:
        if conf.USE_WEBHOOK:
            glob.updater.start_webhook(
                listen="0.0.0.0",
                port=9999,
                url_path="/",
                webhook_url=conf.WEBHOOK_URL
            )
        else:
            glob.updater.start_polling()
    else:
        glob.updater.start_polling()
        conf.settings("maintenance",True)
    if conf.DEBUG:
        print("------------------- Bot in DEBUGGING Starting! ----------------------")
    else:
        print("------------------- Bot Starting! ----------------------")
    
    glob.updater.idle()

def main():
    init()
    run_bot_loop()

"""
DA IMPLEMENTARE:
- Attivazione / Disattivazione Maintenance mode
"""


if __name__ == '__main__': main()

