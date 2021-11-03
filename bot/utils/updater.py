from utils import glob, db, funcs
import threading, traceback, time
import utils.config as conf

def init():
    threading.Thread(target=update_docs).start()
    
def get_cached_events_len():
    res = conf.settings("events_len")
    if res is None:
        conf.settings("events_len",db.Events.length())
        res = 0
    return res 

"""
Update callback

{ "type":"list_scroll", "list":[{"header":""/0,"doc":{...}},{"header":""/0,"doc":"_id"},...], "header":""/0}

if there is ""/0 it means that there will be or a string or a number for identify a static string encoded in the code
"""
def send_message_bcast(user, docs_feed):
    def send_func(*argv,**kargs):  
        msg = glob.sendmsg(user.id(),*argv,**kargs)
        metadata = {"chat_id":msg.chat.id, "message_id":msg.message_id,"callback_data":glob.JCallB().create(docs_feed)} if len(docs_feed["list"]) > 1 else {"chat_id":msg.chat.id, "message_id":msg.message_id}
        for doc in docs_feed["list"]:
            if isinstance(doc,dict):
                db.FeedMsg.add_msg_feed(doc["doc"],metadata)
            else:
                db.FeedMsg.add_msg_feed(doc,metadata)
    funcs.send_doc(send_func,docs_feed)

def reload_callback(msg):
    if "callback_data" in msg.keys():
        def send_func(*argv,**args):
            args["chat_id"]=msg["chat_id"]
            args["message_id"]=msg["message_id"]
            glob.updater.bot.edit_message_text(*argv,**args)
        funcs.send_doc(send_func,glob.JCallB().parse(msg["callback_data"]))
        return True
    else:
        return False

def delete_feed(msg):
    if not "callback_data" in msg.keys():
        glob.updater.bot.delete_message(chat_id=msg["chat_id"], message_id=msg["message_id"])

def edit_deleted_feed(msg):
    if not reload_callback(msg):
        glob.updater.bot.edit_message_text("Questo documento è stato eliminato! 🚫",chat_id=msg["chat_id"], message_id=msg["message_id"])

def delete_feeds(match_ids):
    for match_id in match_ids:
        glob.use_threads_bcast(
            delete_feed,db.FeedMsg.get_msg_feed(match_id)
        )

def edit_deleted_feeds(match_ids):
    for match_id in match_ids:
        glob.use_threads_bcast(
            edit_deleted_feed, db.FeedMsg.get_msg_feed(match_id)
        )

def check_updates():
    updates = db.Events.update(get_cached_events_len())
    if len(updates) == 0:
        return
    conf.settings("events_len",conf.settings("events_len")+len(updates))
    docs_update = []
    deleted_match = set([])
    for update in updates:
        if db.get_pid_name(update["pid"]) is None:
            continue
        if update["type"] == "ADD":
            docs_update+=[ele for ele in update["target"] if ele not in deleted_match]
        elif update["type"] == "UPDATE":
            docs_update+=[{"header":3,"doc":ele} for ele in update["target"] if ele not in deleted_match]
            delete_feeds(update["target"])
        elif update["type"] == "DELETE":
            for ele in update["target"]:
                deleted_match.add(ele)
            edit_deleted_feeds(update["target"])
    del deleted_match
    if len(docs_update) > 0:
        update_callback = {"type":"list_scroll", "list":docs_update, "header":2 if len(docs_update) == 1 else 1}
        if isinstance(update_callback["list"][0],dict):
            update_callback["list"][0]["doc"] = db.Docs.match(update_callback["list"][0]["doc"])
        else:
            update_callback["list"][0] = db.Docs.match(update_callback["list"][0])
        glob.use_threads_bcast(lambda x: send_message_bcast(x,update_callback),db.TelegramUser.get_all_users())

def update_docs():
    while True:
        try:
            check_updates()
            time.sleep(1)
        except Exception as e:
            glob.adminmsg(f"Si è verificato un errore nel controllo degli aggiornamenti delle circolari!\nError: {str(e)}")
            traceback.print_exc()
