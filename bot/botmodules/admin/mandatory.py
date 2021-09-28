from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, CallbackQueryHandler
from utils.glob import *
import string
from utils import db

RECV_MANDATORY_CODE = 0

@msg(adm = "adminAssign")
def add_admin_mandatory(update,user):
    update.message.reply_text(f"È stato creato un mandato per diventare admin 😎\nCodice Accettazione Mandato: {db.create_mandatory(user)} ⚠️\nIl mandato scadrà tra {db.MANDATORY_TIME_LIMIT} minuto/i ⏱️")

@msg(bypass_maintenance=True)
def mandatory_accept(update,user):
    text = update.message.text
    for ele in text.split():
        if len(ele) == db.MANDATORY_DIGITS and all([l in string.digits for l in ele]):
            status = db.accept_mandatory(ele)
            if status == False:
                update.message.reply_text(f"Codice errato o scaduto! 🚫")
            else:
                sendmsg(status,f"Il mandato è stato accettato da @{user.username()} ID: {user.id()} ✅")
                update.message.reply_text(f"Il mandato è stato accettato e confermato! ✅")
                user.set_admin()
            return ConversationHandler.END
            
    update.message.reply_text("Invia il codice di autorizzazione per il mandato ⚠️")
    return RECV_MANDATORY_CODE


@msg(bypass_maintenance = True)
def mandatory_accept_code(update,user):
    text = update.message.text.split()[0]
    if len(text) == db.MANDATORY_DIGITS and all([l in string.digits for l in text]):
        status = db.accept_mandatory(text)
        if status == False:
            update.message.reply_text(f"Codice errato o scaduto! 🚫")
        else:
            sendmsg(status,f"Il mandato è stato accettato da @{user.username()} ID: {user.id()} ✅")
            update.message.reply_text(f"Il mandato è stato accettato e confermato! ✅")
            user.set_admin()
    else:
        update.message.reply_text(f"Codice invalido! 🚫")
    return ConversationHandler.END

handlers = [
    CommandHandler('addadmin',add_admin_mandatory),
    ConversationHandler(
        entry_points = [CommandHandler('join',mandatory_accept)],
        states = {
            RECV_MANDATORY_CODE: [MessageHandler(EXCLUDE_CANCEL,mandatory_accept_code)]
        },
        fallbacks=[CommandHandler('cancel', cancel_op),CallbackQueryHandler(cancel_op_callback,pattern=callb('cancel'))]
    )
]
