from datetime import datetime
import hashlib, binascii
import circolari, os, traceback, time
from pymongo import MongoClient, IndexModel, ASCENDING, TEXT
from os.path import join as pjoin
from pathlib import Path

AXIOS = circolari.TrasparenzeScuoleMap(os.environ["AXIOS_CUSTOMER_ID"])
AXIOS_PIDS_EXPIRE = int(os.getenv("AXIOS_PIDS_EXPIRE",60*60*1))
UPDATE_FREQUENCY = int(os.getenv("AXIOS_UPDATER_FREQUENCY",60*3))
API_CACHE_ATTACHMENTS = os.getenv("API_CACHE_ATTACHMENTS","False").lower() in ("true","t","y","yes","1")
DATA_DIR = Path(__file__).parent.absolute() / "data"
DB_CONN = None
DEBUG = os.getenv("DEBUG","False").lower() in ("true","t","y","yes","1")
DBNAME = "main"
if os.getenv("EXTERNAL_MONGO","False").lower() in ("true","t","y","yes","1"):
    IP_MONGO_AUTH = os.environ["IP_MONGO_AUTH"]
    PORT_MONGO_AUTH = int(os.environ["PORT_MONGO_AUTH"])
    DBNAME = os.environ["DBNAME_MONGO_AUTH"]
    if os.getenv("EXTERNAL_MONGO_AUTH","False").lower() in ("true","t","y","yes","1"):
        DB_CONN = MongoClient(
            host=IP_MONGO_AUTH,
            port=PORT_MONGO_AUTH,
            username=os.environ["USER_MONGO_AUTH"],
            password=os.environ["PSW_MONGO_AUTH"],
        )
    else:
        DB_CONN = MongoClient(
            host=IP_MONGO_AUTH,
            port=PORT_MONGO_AUTH
        )
else: 
    DB_CONN = MongoClient("mongodb://mongo/")
DB = DB_CONN[DBNAME]
"""
DB data managment
docs:
    {
        "pid": "pid_id", #Index 
        "_id": "match_id", #index Unique
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
        "_id": "md5_id" #Index Unique
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
        "_id":"updater",
        ...
    }
"""

def delete_data_file(match_id):
    if API_CACHE_ATTACHMENTS:
        path_file = pjoin(DATA_DIR,match_id)
        if os.path.exists(path_file):
            os.remove(path_file)

def hash_check(match_id,hash):
    with open(pjoin(DATA_DIR,match_id),"rb") as f:
        content = f.read()
    if hashlib.sha256(content).digest() != hash:
        delete_data_file(match_id)


def check_files():
    files = set(os.listdir(DATA_DIR))
    for doc in DB["docs"].find():
        if doc["_id"] in files:
            files.remove(doc["_id"])
            if "hash" in doc["attachment"] and not doc["attachment"]["hash"] is None:
                hash_check(doc["_id"],binascii.unhexlify(doc["attachment"]["hash"]["digest"]))
    for ele in files:
        delete_data_file(ele)


def update_doc(doc):
    DB["docs"].update_one({"_id":doc.match_id()},{"$set":dict(doc)})
    delete_data_file(doc.match_id())
    return doc.match_id()


def download_and_update(pid:circolari.Bacheca):
    docs = pid.download_data()
    cached_docs = list(DB["docs"].find({"pid":pid.id}))
    docs_match = [ele.match_id() for ele in docs]
    cached_docs_match = [ele["_id"] for ele in cached_docs]
    #Search for deletions
    to_delete = [ele for ele in cached_docs_match if ele not in docs_match]
    if len(to_delete) > 0:
        for ele in to_delete: delete_data_file(ele)
        DB["docs"].delete_many({"_id":{"$in":to_delete}})
        DB["docs_events"].insert_one({"date":datetime.now(),"type":"DELETE","target":to_delete,"pid":pid.id})
    #Searching for updates
    update_list = []
    for doc in docs:
        for doc_cached in cached_docs:
            if doc_cached["_id"] == doc.match_id():
                if doc_cached["attachment"]["hash"]["digest"].strip().lower() != doc.hash.strip().lower():
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
        IndexModel([("date",ASCENDING)]),
        IndexModel([("keywords",TEXT)],default_language="it"),
    ])
    DB["pids"].create_indexes([
        IndexModel([("name",TEXT)])
    ])
    DB["docs_events"].create_indexes([
        IndexModel([("date",ASCENDING)])
    ])

def get_settings():
    settings = DB["static"].find_one({"_id":"updater"})
    if settings is None:
        DB["static"].insert_one({"_id":"updater"})
        settings = {"_id":"updater"}
    return settings

def update_settings(settings):
    DB["static"].update_one({"_id":"updater"},{"$set":settings})

def update_pids(settings):
    pids = AXIOS.pids()
    for ele in DB["pids"].find({"_id":{"$nin":[ele.id for ele in pids]}}):
        if API_CACHE_ATTACHMENTS:
            for doc_to_del in DB["docs"].find({"pid":ele["_id"]}):
                delete_data_file(doc_to_del["_id"])
        DB["docs"].delete_many({"pid":ele["_id"]})
    DB["pids"].delete_many({"_id":{"$nin":[ele.id for ele in pids]}})
    synced_pids =  [ele["pid"] for ele in list(DB["pids"].find({}))]
    for pid in pids:
        if pid.pid not in synced_pids:
            DB["pids"].insert_one({"pid":pid.pid,"_id":pid.id,"name":pid.name,"rss_count":0})
        else:
            DB["pids"].update_one({"_id":pid.id},{"$set":{"name":pid.name}})
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
    DB["static"].update_one({"_id":"updater"},{"$unset":{"last_pid_updates":""}})

def check_and_update_pids():
    for pid in AXIOS.pids():
        cached_rss_count = DB["pids"].find_one({"_id":pid.id})["rss_count"]
        online_rss_count = pid.rss_count()
        if cached_rss_count != online_rss_count:
            try:
                download_and_update(pid)
                DB["pids"].update_one({"_id":pid.id},{"$set":{"rss_count":online_rss_count}})
            except Exception:
                force_pids_update()
                traceback.print_exc()

def updater():
    if API_CACHE_ATTACHMENTS:
        check_files()
    try:
        db_init_collections()
        check_pids_expire()
        check_and_update_pids()
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    while True:
        updater()
        time.sleep(UPDATE_FREQUENCY)
