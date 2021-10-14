from threading import Lock
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, CallbackQueryHandler
import time
from utils.glob import *
from utils import db, config as conf
from concurrent.futures import ThreadPoolExecutor

GET_BCAST_MSG = 0
BCAST_EXECUTE = JCallB("bcast_exec")
BCAST_EDIT = JCallB("bcast_edit")

@msg(adm = "broadcast", context=True)
def bcast_command(update,context, user):
    keyb = InlineKeyboardMarkup([[InlineKeyboardButton("Cancella ❌",callback_data='cancel')]])
    msg = update.message.reply_text("Inviami il messaggio che desideri inviare 💬", reply_markup=keyb)
    context.chat_data["first_msg_bcast"] = msg
    return GET_BCAST_MSG

def bcast_msg_build(data,user):
    msg = ""
    if data["include_header"]:
        msg+=data["header"]
    msg+=data["text"]
    if data["dynamic_text"]:
        msg = msg.replace("%name%",user.name() if user.name() != None else "Utente")
    return msg

def bcast_keyb(callbdata):
    callback_header_switched = dict(callbdata)
    callback_header_switched["include_header"] ^= True
    callback_dynamic_switched = dict(callbdata)
    callback_dynamic_switched["dynamic_text"] ^= True
    keyb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Invia ✅",callback_data=BCAST_EXECUTE.create(callbdata)),InlineKeyboardButton("Cancella ❌",callback_data='cancel')],
        [InlineKeyboardButton("Includi intestazione "+t_or_f(callbdata["include_header"]),callback_data=BCAST_EDIT.create(callback_header_switched))],
        [InlineKeyboardButton("Testo dinamico (%name%) "+t_or_f(callbdata["dynamic_text"]),callback_data=BCAST_EDIT.create(callback_dynamic_switched))]
    ])
    return keyb

@msg(adm = "broadcast", context=True)
def bcast_recv_message(update,context, user):
    if "first_msg_bcast" in context.chat_data.keys():
        context.chat_data["first_msg_bcast"].edit_reply_markup()
        del context.chat_data["first_msg_bcast"]
    callbdata = {"text":update.message.text, "header":f"Messaggio da: {user.name()} {user.surename()} ✉️\n\n", "dynamic_text":"%name%" in update.message.text, "include_header":True, "id_to_skip": user.id() }
    update.message.reply_text(f"Ecco il messaggio che verrà mandato in broadcast 🌍\n---------------\n"+bcast_msg_build(callbdata,user),reply_markup=bcast_keyb(callbdata))
    return ConversationHandler.END

@msg(adm = "broadcast", jcallb=True)
def bcast_edit(update, user, data):
    update.message.edit_message_text(f"Ecco il messaggio che verrà mandato in broadcast 🌍\n---------------\n"+bcast_msg_build(data,user),reply_markup=bcast_keyb(data))
    return ConversationHandler.END

global MESSAGES_SENDED, TIME_WAIT, MESSAGES_SENDED_CACHED, MSG_LOCK
MESSAGES_SENDED = MESSAGES_SENDED_CACHED = TIME_WAIT = 0
MSG_LOCK = Lock()

def broadcast_message_send(user,update_msg,cbdata):
    global MESSAGES_SENDED, TIME_WAIT, MESSAGES_SENDED_CACHED, MSG_LOCK
    if user.id() == cbdata["id_to_skip"]: return 
    sendmsg(user.id(),bcast_msg_build(cbdata,user))
    with MSG_LOCK:
        MESSAGES_SENDED+=1
        if MESSAGES_SENDED_CACHED != MESSAGES_SENDED and time.time() > TIME_WAIT:
            MESSAGES_SENDED_CACHED = MESSAGES_SENDED
            update_msg(f"Sto inviando il messaggio (Inviato a {MESSAGES_SENDED_CACHED} utenti) 🌍")
            TIME_WAIT = time.time() + 1

@msg(adm = "broadcast", jcallb=True)
def bcast_accepted(update,user,data):
    global MESSAGES_SENDED, TIME_WAIT, MESSAGES_SENDED_CACHED
    if conf.BCAST_LOCK.locked():
        update.message.edit_message_text("Il bot sta già inviando un'altro messaggio, questo messaggio verrà inviato appena possibile! 💬\nNel frattempo non sarà possibile usare il bot 😤")
    with conf.BCAST_LOCK:
        try:
            MESSAGES_SENDED = MESSAGES_SENDED_CACHED = 0
            TIME_WAIT = time.time()
            update.message.edit_message_text("Sto inviando i messaggi... 💬")
            with ThreadPoolExecutor(conf.BROADCAST_THREADING_LIMIT) as exec:
                exec.map(lambda x: broadcast_message_send(x,update.message.edit_message_text,data),db.TelegramUser.get_all_users())
            update.message.edit_message_text("Il messaggio è stato inviato a tutti! 💬")
        except Exception as e:
            adminmsg("Attenzione è stata generata una Exception nel comando di amministrazione broadcast\nError: "+str(e))
            traceback.print_exc()
            update.message.edit_message_text("Si è rilevato un errore nell'operazione di broadcast! 🚫\nInvio annullato!")
    return ConversationHandler.END

handlers = [
    CallbackQueryHandler(bcast_accepted,pattern=BCAST_EXECUTE.regex_filter()),
    CallbackQueryHandler(bcast_edit,pattern=BCAST_EDIT.regex_filter()),
    ConversationHandler(
        entry_points = [CommandHandler('bcast', bcast_command)],
        states = {
            GET_BCAST_MSG: [MessageHandler(Filters.text,bcast_recv_message)]
        },
        fallbacks=[CommandHandler('cancel', cancel_op),CallbackQueryHandler(cancel_op_callback,pattern=callb('cancel'))]
    )
]
