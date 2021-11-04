from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, ConversationHandler, CallbackQueryHandler
from utils.glob import *
from utils import db, config as conf


ADMIN_LIST_SCROLL = JCallB("admin_scroll")
SHOW_ADMIN_ACTION = JCallB("show_admin_action")
CONFIRM_ADMIN_ACTION = JCallB("admin_action_allow")
EXECUTE_ADMIN_ACTION = JCallB("exec_admin_action")

ALLOW_PERM, DENY_PERM, DELETE_ADMIN = 0,1,2

MAX_LIST_SIZE = 6

#Count page from 1
def get_user_list_in_pages(page):
    full_list = list(db.TelegramUser.get_all_admins())
    max_pages = len(full_list)//MAX_LIST_SIZE
    if len(full_list)%MAX_LIST_SIZE != 0: max_pages+=1
    if page > 0 and page <= max_pages:
        start_count = (page-1)*MAX_LIST_SIZE
        end_count = page*MAX_LIST_SIZE
        if end_count>len(full_list): end_count = len(full_list)
        return full_list[start_count:end_count], max_pages
    return [], max_pages

def build_list_page_message(infos,page,max_pages):
    if len(infos) == 0 or page > max_pages or page < 1:
        if page == 1:
            return "Non ci sono admin registrati! ❌",None
        else:
            return "La pagina da visualizzare non è più valida!",None
    text = f"Elenco degli admin ⚙️, Pagina {page}"
    keyb = []

    for usr in infos:
        keyb.append([
            InlineKeyboardButton(f"{usr.name()} {usr.surename()} ID: {usr.id()}",
                                callback_data=SHOW_ADMIN_ACTION.create({"id":usr.id()}))
        ])

    ctrl_arrow = []
    if (page != 1):
        ctrl_arrow.append(InlineKeyboardButton("❮❮ Indietro",callback_data=ADMIN_LIST_SCROLL.create({"goto":page-1})))
    if page != max_pages:
        ctrl_arrow.append(InlineKeyboardButton("Avanti ❯❯",callback_data=ADMIN_LIST_SCROLL.create({"goto":page+1})))
    if len(ctrl_arrow) != 0:
        keyb.append(ctrl_arrow)
    keyb.append([InlineKeyboardButton("🚫 Annulla",callback_data="cancel")])

    return text, InlineKeyboardMarkup(keyb)

@msg(adm = "adminAssign",jcallb=True)
def execute_admin_action(update,user,data):
    try:
        usr = db.TelegramUser(data["id"])
        if data["operation"] == DELETE_ADMIN:
            usr.remove_admin()
            return get_admin_list(update.message.edit_message_text)
        elif data["operation"] == ALLOW_PERM:
            usr.add_permission(data["target"])
            return show_admin_infos(update,user,{"id":data["id"]}) 
        elif data["operation"] == DENY_PERM:
            usr.remove_permission(data["target"])
            return show_admin_infos(update,user,{"id":data["id"]}) 
        else:
            update.message.edit_message_text("Errore nella callback, si prega di riprovare! 🚫")
            return ConversationHandler.END
    except (KeyError, TypeError):
        update.message.edit_message_text("Errore nella callback, si prega di riprovare! 🚫")
        traceback.print_exc()
    return ConversationHandler.END

@msg(adm = "adminAssign",jcallb=True)
def confirm_admin_action(update,user,data):
    try:
        usr = db.TelegramUser(data["id"])

        keyb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Conferma ✅", 
                    callback_data=EXECUTE_ADMIN_ACTION.create(data)),
                InlineKeyboardButton("Annulla ❌", callback_data="cancel")
            ]
        ])

        if data["operation"] == DELETE_ADMIN:
            update.message.edit_message_text(f"⚠️ Sei sicuro di voler rimuovere {usr.name()} {usr.username()} come admin? ⚠️",reply_markup=keyb)
        elif data["operation"] == ALLOW_PERM:
            text = f"Il permesso \"{data['target']}\" verrà concesso all'utente {usr.name()} {usr.surename()}"
            update.message.edit_message_text(text,reply_markup=keyb)
        elif data["operation"] == DENY_PERM:
            text = f"Il permesso \"{data['target']}\" verrà rimosso all'utente {usr.name()} {usr.surename()}"
            update.message.edit_message_text(text,reply_markup=keyb)
        else:
            update.message.edit_message_text("Errore nella callback, si prega di riprovare! 🚫")
            return ConversationHandler.END
        
    except (KeyError, TypeError):
        update.message.edit_message_text("Errore nella callback, si prega di riprovare! 🚫")
        traceback.print_exc()
    return ConversationHandler.END

@msg(adm = "adminAssign",jcallb=True)
def show_admin_action(update,user,data):
    show_admin_infos(update,user,data)

def show_admin_infos(update,user,data):
    try:
        usr = db.TelegramUser(data["id"])
        text =  f"⚠️ Impostazioni admin ⚠️\n\n"
        text += f"⚙️ Id: {usr.id()}\n"
        text += f"😄 Nome: {usr.name()}\n"
        text += f"😃 Cognome: {usr.surename()}\n"
        text += f"🤖 Username: @{usr.username()}\n"

        keyb = []
        for perm in conf.perms:
            allowed = perm.id in usr.permissions()
            postfix = " ✅" if allowed else " ❌"
            keyb.append([
                InlineKeyboardButton(
                    perm.name + postfix,
                    callback_data=CONFIRM_ADMIN_ACTION.create({"id":usr.id(),"operation": DENY_PERM if allowed else ALLOW_PERM ,"target":perm.id}
                )
            )])
        keyb.append([
            InlineKeyboardButton(
                "⚠️ Rimuovi Admin ⚠️",
                callback_data=CONFIRM_ADMIN_ACTION.create({"id":usr.id(),"operation":DELETE_ADMIN}
            )
        )])
        keyb.append([InlineKeyboardButton("❮❮ Indietro",callback_data=ADMIN_LIST_SCROLL.create({"goto":1}))])
        keyb = InlineKeyboardMarkup(keyb)
        update.message.edit_message_text(text,reply_markup=keyb)
    except (KeyError, TypeError):
        update.message.edit_message_text("Errore nella callback, si prega di riprovare! 🚫")
        traceback.print_exc()
    return ConversationHandler.END

@msg(adm = "adminAssign")
def request_admin_list(update,user):
    return get_admin_list(update.message.reply_text)

def get_admin_list(sendmsg,page=1):
    infos,max_pages = get_user_list_in_pages(page)
    text,mk = build_list_page_message(infos,page,max_pages)
    sendmsg(text,reply_markup=mk)
    return ConversationHandler.END

@msg(adm = "adminAssign", jcallb=True)
def callback_admin_list(update,user,data):
    try:
        return get_admin_list(update.message.edit_message_text, page=data["goto"])
    except (KeyError, TypeError):
        update.message.edit_message_text("Errore nella callback, si prega di riprovare! 🚫")
        traceback.print_exc()
    return ConversationHandler.END

handlers = [
    CommandHandler('adminlist',request_admin_list),
    CallbackQueryHandler(callback_admin_list,pattern=ADMIN_LIST_SCROLL.regex_filter()),
    CallbackQueryHandler(show_admin_action,pattern=SHOW_ADMIN_ACTION.regex_filter()),
    CallbackQueryHandler(confirm_admin_action,pattern=CONFIRM_ADMIN_ACTION.regex_filter()),
    CallbackQueryHandler(execute_admin_action,pattern=EXECUTE_ADMIN_ACTION.regex_filter())
]
