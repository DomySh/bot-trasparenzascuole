from utils import glob, db
import threading, traceback, time
import utils.config as conf
from utils.funcs import send_doc
from concurrent.futures import ThreadPoolExecutor

def init():
    threading.Thread(target=update_docs).start()
    
def get_cached_events_len():
    res = conf.settings("events_len")
    if res is None:
        conf.settings("events_len",0)
        res = 0
    return res 

"""
Update callback

{ "type":"list_scroll", "list":[{"header":""/0,"doc":{...}},{"header":""/0,"doc":"match"},...], "header":""/0}

if there is ""/0 it means that there will be or a string or a number for identify a static string encoded in the code
"""
def send_message_bcast(user, docs_feed):
    def send_func(*argv,**kargs):  
        msg = glob.sendmsg(user.id(),*argv,**kargs)
        if len(docs_feed["list"]) == 1:
            db.FeedMsg.add_msg_feed(docs_feed["list"][0]["doc"],{"chat_id":msg.chat.id, "message_id":msg.message_id})
    send_doc(send_func,docs_feed)

def delete_feeds(match_ids):
    from telegram import Message, Chat
    for match_id in match_ids:
        with conf.BCAST_LOCK:
            with ThreadPoolExecutor(conf.BROADCAST_THREADING_LIMIT) as exec:
                exec.map(lambda msg: glob.updater.bot.delete_message(chat_id=msg["chat_id"], message_id=msg["message_id"]),
                db.FeedMsg.get_msg_feed(match_id))
            
def edit_deleted_feeds(match_ids):
    for match_id in match_ids:
        with conf.BCAST_LOCK:
            with ThreadPoolExecutor(conf.BROADCAST_THREADING_LIMIT) as exec:
                exec.map(lambda msg: glob.updater.bot.editMessageText("Questo documento è stato eliminato! 🚫",chat_id=msg["chat_id"], message_id=msg["message_id"]),
                db.FeedMsg.get_msg_feed(match_id))
            

def check_updates():
    updates = db.Events.update(get_cached_events_len())
    if len(updates) == 0: return 
    conf.settings("events_len",db.Events.length())
    docs_update = []
    deleted_match = []
    for update in updates:
        if update["type"] == "ADD":
            docs_update+=[{"header":None,"doc":ele} for ele in update["target"] if ele not in deleted_match]
        elif update["type"] == "UPDATE":
            docs_update+=[{"header":3,"doc":ele} for ele in update["target"] if ele not in deleted_match]
            delete_feeds(update["target"])
        elif update["type"] == "DELETE":
            deleted_match+=update["target"]
            edit_deleted_feeds(update["target"])
    del deleted_match

    if len(docs_update) > 0:
        update_callback = {"type":"list_scroll", "list":docs_update, "header":2 if len(docs_update) == 1 else 1}
        update_callback["list"][0]["doc"] = db.Docs.match(update_callback["list"][0]["doc"])
        with conf.BCAST_LOCK:
            with ThreadPoolExecutor(conf.BROADCAST_THREADING_LIMIT) as exec:
                exec.map(lambda x: send_message_bcast(x,update_callback),db.TelegramUser.get_all_users())

def update_docs():
    while True:
        try:
            check_updates()
        except Exception as e:
            glob.adminmsg(f"Si è verificato un errore nel controllo degli aggiornamenti delle circolari!\nError: {str(e)}")
            traceback.print_exc()