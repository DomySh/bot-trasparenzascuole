from datetime import datetime
from re import match
import circolari, os, socket, traceback, time
from pymongo import MongoClient, IndexModel, ASCENDING, TEXT
from pathlib import Path
from base64 import urlsafe_b64encode
from hashlib import md5

global NEW_UPDATES_CHECKED
MONGO_URL = "mongodb://mongo/"
DB_CONN = MongoClient(MONGO_URL)
DB = DB_CONN["main"]
AXIOS = circolari.TrasparenzeScuoleMap()
NEW_UPDATES_CHECKED = False
AXIOS_PIDS_EXPIRE = int(os.getenv("AXIOS_PIDS_EXPIRE",60*60*12))
UPDATE_FREQUENCY = int(os.getenv("AXIOS_UPDATER_FREQUENCY",60*1))
API_CACHE_ATTACHMENTS = os.getenv("API_CACHE_ATTACHMENTS","False").lower() in ("true","t","y","yes","1")
"""
DB data managment
docs:
    {
        "pid": "pid_id", #Index 
        "match": "match_id", #index Unique
        "description": "description",
        "note": "notes",
        "n_doc": "number of document", #Index
        "date": "date of the pubblication", #Index
        "attachment":{
            "hash": {
                "digest":"hexdigest",
                "type":"type of hash"
            },
            "download": "download link axios",
            "name": "filename attached file"
        }
    }
pids:
    {
        "pid": "bacheca_id" #index Unique,
        "id": "md5_id" #Index Unique
        "name": "name of the bacheca",
        "rss_count": "RSS line feed count" 
    }
docs_events:
    {
        "date": "date of the detection of the event", #Index
        "type": "DELETE"|"UPDATE"|"ADD",
        "target": "match_id"
    }
static:
    {
        "id":"updater",
        ...
    }
"""

def signal_updates():
    global NEW_UPDATES_CHECKED
    if NEW_UPDATES_CHECKED:
        sk = socket.socket()
        sk.connect(("bot",4040))
        sk.close()
        NEW_UPDATES_CHECKED = False

def delete_data_file(match_id):
    if API_CACHE_ATTACHMENTS:
        path_file = Path(__file__).parent.absolute() / "data" / (match_id+".pdf")
        if os.path.exists(path_file):
            os.remove(path_file)

def update_doc(doc):
    DB["docs"].update_one({"match":doc.match_id()},{"$set":dict(doc)})
    delete_data_file(doc.match_id())
    return doc.match_id()


def download_and_update(pid:circolari.Bacheca):
    docs = pid.download_data()
    cached_docs = list(DB["docs"].find({"pid":pid.id}))
    docs_match = [ele.match_id() for ele in docs]
    cached_docs_match = [ele["match"] for ele in cached_docs]
    #Search for deletions
    to_delete = [ele for ele in cached_docs_match if ele not in docs_match]
    if len(to_delete) > 0:
        for ele in to_delete: delete_data_file(ele)
        DB["docs"].delete_many({"match":{"$in":to_delete}})
        DB["docs_events"].insert_one({"date":datetime.now(),"type":"DELETE","target":to_delete,"pid":pid.id})
    #Searching for updates
    update_list = []
    for doc in docs:
        for doc_cached in cached_docs:
            if doc_cached["match"] == doc.match_id():
                if doc_cached["attachment"]["hash"]["digest"].strip().lower() != doc.hash.strip().lower():
                    print(doc.match_id(),doc_cached["attachment"]["hash"]["digest"].strip().lower(),"!=",doc.hash.strip().lower())
                    update_list.append(update_doc(doc))
    if len(update_list) > 0:
        DB["docs_events"].insert_one({"date":datetime.now(),"type":"UPDATE","target":update_list,"pid":pid.id})
    #Searching for additions
    to_add = [ele for ele in docs if ele.match_id() not in cached_docs_match]
    if len(to_add) > 0:
        DB["docs"].insert_many([dict(ele) for ele in to_add])
        DB["docs_events"].insert_one({"date":datetime.now(),"type":"ADD","target":[ele.match_id() for ele in to_add],"pid":pid.id})
def db_init_collections():
    DB["docs"].create_indexes([
        IndexModel([("pid",ASCENDING)]),
        IndexModel([("match",ASCENDING)],unique=True),
        IndexModel([("date",ASCENDING)]),
        IndexModel([("note",TEXT),("description",TEXT),("attachment.name",TEXT)]),
    ])
    DB["pids"].create_indexes([
        IndexModel([("id",ASCENDING)],unique=True),
        IndexModel([("name",TEXT)])
    ])
    DB["docs_events"].create_indexes([
        IndexModel([("date",ASCENDING)])
    ])
    DB["static"].create_indexes([
        IndexModel([("id",ASCENDING)],unique=True),
    ])

def get_settings():
    settings = DB["static"].find_one({"id":"updater"})
    if settings is None:
        DB["static"].insert_one({"id":"updater"})
        settings = {"id":"updater"}
    return settings

def update_settings(settings):
    DB["static"].update_one({"id":"updater"},{"$set":settings})

def update_pids(settings):
    global NEW_UPDATES_CHECKED
    NEW_UPDATES_CHECKED = True
    pids = AXIOS.pids()
    for ele in DB["pids"].find({"id":{"$nin":[ele.id for ele in pids]}}):
        DB["docs"].delete_many({"pid":ele["id"]})
        DB["docs_events"].delete_many({"pid":ele["id"]})
    DB["pids"].delete_many({"id":{"$nin":[ele.id for ele in pids]}})
    synced_pids =  [ele["pid"] for ele in list(DB["pids"].find({}))]
    for pid in pids:
        if pid.pid not in synced_pids:
            DB["pids"].insert_one({"pid":pid.pid,"id":pid.id,"name":pid.name,"rss_count":0})
        else:
            DB["pids"].update_one({"id":pid.id},{"$set":{"name":pid.name}})
    settings["last_pid_updates"] = datetime.now()
    settings["customer_name"] = AXIOS.name()
    
def check_pids_expire():
    settings = get_settings()
    if "last_pid_updates" not in settings:
        update_pids(settings)
    else:
        expired = settings["last_pid_updates"].timestamp()+AXIOS_PIDS_EXPIRE <= datetime.now().timestamp()
        if expired:
            update_pids(settings)
        else:
            pids = list(DB["pids"].find({}))
            AXIOS.load_pid_list([circolari.Bacheca(AXIOS.customer_id,pid["pid"],pid["name"]) for pid in pids])
    update_settings(settings)

def force_pids_update():
    DB["static"].update_one({"id":"updater"},{"$unset":{"last_pid_updates":""}})

def check_and_update_pids():
    global NEW_UPDATES_CHECKED
    for pid in AXIOS.pids():
        cached_rss_count = DB["pids"].find_one({"id":pid.id})["rss_count"]
        online_rss_count = pid.rss_count()
        if cached_rss_count != online_rss_count:
            try:
                NEW_UPDATES_CHECKED = True
                download_and_update(pid)
                DB["pids"].update_one({"id":pid.id},{"$set":{"rss_count":online_rss_count}})
            except Exception:
                force_pids_update()
                traceback.print_exc()

def updater():
    try:
        db_init_collections()
        check_pids_expire()
        check_and_update_pids()
        signal_updates()
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    while True:
        updater()
        time.sleep(UPDATE_FREQUENCY)

