import os
from threading import Lock

ADMIN_ID = int(os.environ["TG_ADMIN_ID"])
TOKEN = os.environ["TG_BOT_TOKEN"]

USE_WEBHOOK = os.getenv("TG_BOT_USE_WEBHOOK","False").lower() in ("true","t","1","yes","y")

EXTERNAL_API = os.environ["API_EXTERNAL_URL"]

BROADCAST_THREADING_LIMIT = int(os.getenv("THREAD_FOR_BROADCASTING",1))
THREADS = int(os.getenv("THREADS",4))
DEBUG = os.getenv("DEBUG","False").lower() in ("true","t","1","yes","y")
SEND_EXCEPTION_ADVICE_TO_ADMIN = os.getenv("SEND_EXCEPTION_ADVICE_TO_ADMIN","False").lower() in ("true","t","1","yes","y")

BOT_MODULES = [
    "admin.bcast",
    "admin.mandatory",
    "admin.adminlist",
    "admin.stats",
    "admin.admin",
    "admin.maintenance",
    "docs"
]
HANDLERS_MODULES_NAME = "handlers"
BCAST_LOCK = Lock()

class Permission:
    def __init__(self,id,name,description,commands=[]):
        self.id = id
        self.name = name
        self.description = description
        self.commands = commands

perms = [
    Permission("broadcast",name="Invia Broadcast",commands = ["/bcast"],
                description="Invia messaggi a tutti gli utilizzatori del bot per comunicazioni ufficiali!"),
    Permission("stats",name="Vedi le statistiche",commands = ["/stats"],
                description="Vedi le statistiche sugli utilizzatori del bot e le loro impostazioni"),
    Permission("adminAssign",name="Gestione Admin",commands = ["/addadmin", "/adminlist"],
                description="Gestisci amministratori e i loro permessi con questi comandi di amministrazione"),
    Permission("allowMaintenance",name="Usa il bot in manutenzione",commands = [],
                description="Sei autorizzato ad utilizzare il bot anche se è in modalità di manutenzione!"),
    Permission("switchMaintenance",name="Gestisci la modalità di manutenzione",commands = ["/maintenance"],
            description="Sei autorizzato ad attivare o disattivare la modalità di manutenzione")
]

def perm(id):
    for ele in perms:
        if ele.id == id:
            return ele
    return None

def settings(key,value=None):
    from utils.db import _get_settings, _set_settings
    if value is None:
        settings = _get_settings()
        if key not in settings.keys():
            return None
        else:
            return settings[key]
    else:
        if key in ("_id","id"): return
        res = _get_settings()
        res[key] = value
        _set_settings(res)

STATIC_STRINGS = {
    0:"Clicca \"Avanti\" o \"Indietro\" per scorrere i documenti ➡️",
    1:"Ci sono dei nuovi aggiornamenti! 📨🎺",
    2:"C'è un nuovo aggiornamento! 📨🎺",
    3:"\nAttenzione! L'allegato di questo documento è stato aggiornato! ⚠️"  
}
