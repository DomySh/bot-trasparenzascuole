from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, CallbackQueryHandler
from utils.glob import *
from utils.funcs import send_doc
from utils import db

WAIT_FOR_SEARCH_STRING = 0
SEARCH_STRING_LIMIT = 300 
LIST_SCROLL = JCallB("list_scroll")

@msg()
def get_last(update,user):
    send_doc(update.message.reply_text,{"type":"index_scroll", "reversed":True})

@msg(jcallb=True)
def show_doc_scroll_callback(update,user,data):
    send_doc(update.message.edit_message_text,data)

@msg()
def search_doc_command_init(update,user):
    update.message.reply_text(
            "Cerca il documento scrivendo le parole che potrebbero essere contenute nelle note o nella descrizione della  📰\n"
            "Puoi annullare l'operazione con il comando /cancel 🚫")
    return WAIT_FOR_SEARCH_STRING

@msg()
def search_doc_command(update,user):
    msg = update.message.text

    if len(msg) > SEARCH_STRING_LIMIT:
        update.message.reply_text(f"Puoi inserire massimo {SEARCH_STRING_LIMIT} caratteri per la ricerca! 🔍\nOperazione Annullata 🚫")
        return ConversationHandler.END   
    data = list(db.Docs.search(msg))
    if len(data) == 0:
        update.message.reply_text("Non ho trovato la circolare che cerchi 😨\n\n"
                                "Per migiorare i risultati prova ad inserire poche parole scegliendo le più generiche 💡\n\n"
                                "La ricerca non fa differenze tra lettere minuscole e maiuscole e non ricerca nel contenuto dell'allegato 🔍")
        return ConversationHandler.END
    send_doc(update.message.reply_text,{"type":"list_scroll", "header":f"Ecco i migliori risultati trovati per '"+str(msg)+"' 🔍","list":data})
    return ConversationHandler.END

handlers = [
    CommandHandler('last',get_last),
    CallbackQueryHandler(show_doc_scroll_callback,pattern=LIST_SCROLL.regex_filter()),
    ConversationHandler(
        entry_points = [CommandHandler('search', search_doc_command_init)],
        states = {
            WAIT_FOR_SEARCH_STRING: [MessageHandler(EXCLUDE_CANCEL,search_doc_command)]
        },
        fallbacks=[CommandHandler('cancel', cancel_op),CallbackQueryHandler(cancel_op_callback,pattern=callb('cancel'))]
    )
]
