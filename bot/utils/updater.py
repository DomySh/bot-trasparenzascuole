from utils import glob, db
import socket, threading, traceback
import utils.config as conf
from utils.funcs import send_doc
from concurrent.futures import ThreadPoolExecutor

def init():
    update_docs()
    start_update_deamons()

def event_loop(sk):
    while True:
        conn, _ = sk.accept()
        conn.close()
        update_docs() 

def start_update_deamons():
    sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sk.bind(("0.0.0.0",4040))
    sk.listen(1)
    threading.Thread(target=event_loop,args=(sk,)).start()

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
    def send_func(*argv,**kargs): glob.sendmsg(user.id(),*argv,**kargs)
    send_doc(send_func,docs_feed)

def check_updates():
    updates = db.Events.update(get_cached_events_len())
    conf.settings("events_len",db.Events.length())
    conf.settings("pid_infos",db.Docs.pids_info())
    if len(updates) == 0: return 
    docs_update = []
    deleted_match = []
    for update in updates:
        if update["type"] == "ADD":
            docs_update+=[{"header":None,"doc":ele} for ele in update["target"] if ele not in deleted_match]
        elif update["type"] == "UPDATE":
            docs_update+=[{"header":3,"doc":ele} for ele in update["target"] if ele not in deleted_match]
        elif update["type"] == "DELETE":
            deleted_match+=update["target"]
    del deleted_match

    if len(docs_update) > 0:
        docs_update[0]["doc"] = db.Docs.match(docs_update[0]['doc'])
        update_callback = {"type":"list_scroll", "list":docs_update, "header":2 if len(docs_update) == 1 else 1}
        with conf.BCAST_LOCK:
            with ThreadPoolExecutor(conf.BROADCAST_THREADING_LIMIT) as exec:
                exec.map(lambda x: send_message_bcast(x,update_callback),db.TelegramUser.get_all_users())

def update_docs():
    try:
        check_updates()
    except Exception as e:
        glob.adminmsg(f"Si è verificato un errore nel controllo degli aggiornamenti delle circolari!\nError: {str(e)}")
        traceback.print_exc()