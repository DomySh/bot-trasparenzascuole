
import re, os

yaml_json = {
    "version":"'3.9'",
    "services":{
        
        "bot":{
            "restart":"unless-stopped",
            "build":"./bot",
            "environment":[]
        },
        "web":{
            "restart":"unless-stopped",
            "build":"./web",
            "environment":[]
        }
    }
}

global API_PORT

API_PORT = None

def y_or_n(default=False):
    while True:
        res = input("(Y/n) > " if default else "(y/N) > ")
        res = res.lower().strip()
        if len(res) == 0:
            return default
        if len(res) > 0 and res[0] in "yn":
            return res[0] == "y"
        else:
            print("Inserisci 'y' o 'n'")

def get_mongo_ip():
    while True:
        print("[[ IP_MONGO_AUTH ]]\nInserisci l'ip del database mongodb (Senza numero di porta)")
        res = input("> ")
        if res.strip() != "":
            res = res.strip()
            yaml_json["services"]["bot"]["environment"].append(f"IP_MONGO_AUTH={res}")
            yaml_json["services"]["web"]["environment"].append(f"IP_MONGO_AUTH={res}")
            break 

def get_mongo_port():
    while True:
        print("[[ PORT_MONGO_AUTH ]]\nInserisci la porta su cui è avviato mongodb")
        res = input("(Default=27017)> ")
        if res.strip() == "": res = "27017"
        if res.isdecimal() and int(res)>=0 and int(res)<=65535:
            yaml_json["services"]["bot"]["environment"].append(f"PORT_MONGO_AUTH={int(res)}")
            yaml_json["services"]["web"]["environment"].append(f"PORT_MONGO_AUTH={int(res)}")
            break 

def mongo_auth_user():
    while True:
        print("[[ USER_MONGO_AUTH ]]\nInserisci il nome utente con cui autenticarti")
        res = input("> ")
        if res.strip() != "":
            res = res.strip()
            yaml_json["services"]["bot"]["environment"].append(f"USER_MONGO_AUTH={res}")
            yaml_json["services"]["web"]["environment"].append(f"USER_MONGO_AUTH={res}")
            break  

def mongo_auth_psw():
    while True:
        print("[[ PSW_MONGO_AUTH ]]\nInserisci la password dell'utente")
        res = input("> ")
        if res.strip() != "":
            res = res.strip()
            yaml_json["services"]["bot"]["environment"].append(f"PSW_MONGO_AUTH={res}")
            yaml_json["services"]["web"]["environment"].append(f"PSW_MONGO_AUTH={res}")
            break 
    

def mongo_auth_dbname():
    while True:
        print("[[ DBNAME_MONGO_AUTH ]]\nInserisci il nome del database da utilizzare")
        res = input("> ").strip()
        if res != "":
            yaml_json["services"]["bot"]["environment"].append(f"DBNAME_MONGO_AUTH={res}")
            yaml_json["services"]["web"]["environment"].append(f"DBNAME_MONGO_AUTH={res}") 
            break
    

def mongo_auth():
    print("Vuoi accedere al server mongodb con un username e password?")
    if y_or_n(True):
        yaml_json["services"]["bot"]["environment"].append("EXTERNAL_MONGO_AUTH=1")
        yaml_json["services"]["web"]["environment"].append("EXTERNAL_MONGO_AUTH=1")
        mongo_auth_user()
        mongo_auth_psw()
    else:
        yaml_json["services"]["bot"]["environment"].append("EXTERNAL_MONGO_AUTH=0")
        yaml_json["services"]["web"]["environment"].append("EXTERNAL_MONGO_AUTH=0")


def mongodb_conn():
    print("Vuoi utilizzare un database mongodb generato con un container docker?")
    if y_or_n(True):
        yaml_json["services"]["bot"]["environment"].append("EXTERNAL_MONGO=0")
        yaml_json["services"]["web"]["environment"].append("EXTERNAL_MONGO=0")
        yaml_json["services"]["mongo"] = {
            "image":"mongo:4",
            "restart":"unless-stopped",
            "volumes":["./mongodbdata:/data/db"]
        }
        yaml_json["services"]["web"]["depends_on"]=["mongo"]
        yaml_json["services"]["bot"]["depends_on"]=["mongo"]

    else:
        yaml_json["services"]["bot"]["environment"].append("EXTERNAL_MONGO=1")
        yaml_json["services"]["web"]["environment"].append("EXTERNAL_MONGO=1")
        get_mongo_ip()
        get_mongo_port()
        mongo_auth_dbname()
        mongo_auth()

def get_admin_id():
    while True:
        print("[[ ADMIN_CHAT_ID ]]\nInserisci il Chat id dell'utente superamministratore\nDocumentazione: https://github.com/DomySh/bot-trasparenzascuole/blob/main/doc/BOTTELEGRAM.md")
        res = input("> ")
        if res.isdecimal() and int(res)>=0:
            yaml_json["services"]["bot"]["environment"].append(f"TG_ADMIN_ID={int(res)}")
            break

def get_bot_token():
    while True:
        print("[[ BOT_TOKEN ]]\nInserisci il token del Bot Telegram\nDocumentazione: https://github.com/DomySh/bot-trasparenzascuole/blob/main/doc/BOTTELEGRAM.md")
        res = input("> ")
        if re.match(r"^[0-9]+:[a-zA-Z0-9_-]{35}$",res):
            yaml_json["services"]["bot"]["environment"].append(f"TG_BOT_TOKEN={res}")
            break

def threads_for_broadcast():
    while True:
        print("""[[ BROADCAST_THREAD ]]\nPer l'invio delle notifiche per nuovi documenti o per l'invio di messaggi broadcast personalizzati,
vengono utilizzati i thread, pertanto si può impostare un numero di thread da utilizzare in questi 
casi per l'invio dei messaggi, tramite questo parametro. Imposta il valore in base alle potenzialità
della tuo server.""")
        res = input("(Default=3) > ")
        if res == "": res = "3"
        if res.isdecimal() and int(res)>=1 and int(res)<=100:
            yaml_json["services"]["bot"]["environment"].append(f"THREAD_FOR_BROADCASTING={int(res)}")
            break

def webhook_choose():
    print("[[ USE_TELEGRAM_WEHOOK ]]\nVuoi utilizzare i WebHook per il bot telegram?\nDocumentazione: https://github.com/DomySh/bot-trasparenzascuole/blob/main/doc/TG_WEBHOOK.md")
    if y_or_n(True):
        yaml_json["services"]["bot"]["environment"].append(f"TG_BOT_USE_WEBHOOK=1")
        webhook_port()
        webhook_url()
    else:
        yaml_json["services"]["bot"]["environment"].append(f"TG_BOT_USE_WEBHOOK=0")


def set_debug():
    print("[[ DEBUG ]]\nVuoi creare una configurazione per DEBUG?\nQuesta funzionerà disattiverà il webhook e attiverà in automatico la console di debug di flask, e la modalità di manutenzione.")
    if y_or_n(False):
        yaml_json["services"]["bot"]["environment"].append("DEBUG=1")
        yaml_json["services"]["web"]["environment"].append("DEBUG=1")
        yaml_json["services"]["web"]["volumes"]=["./web/:/execute/"]
        yaml_json["services"]["bot"]["volumes"]=["./bot/:/execute/"]
        if "mongo" in yaml_json["services"].keys():
            yaml_json["services"]["mongo"]["ports"]=["127.0.0.1:27017:27017"]
        yaml_json["services"]["web"]["environment"].append("API_CACHE_ATTACHMENTS=0")
        yaml_json["services"]["bot"]["environment"].append("TG_BOT_USE_WEBHOOK=0")
        global API_PORT
        yaml_json["services"]["bot"]["environment"].append(f"API_EXTERNAL_URL=http://127.0.0.1:{API_PORT}/")
        yaml_json["services"]["web"]["environment"].append(f"API_AXIOS_DATA_LINK=http://127.0.0.1:{API_PORT}/")
        yaml_json["services"]["web"]["environment"].append("THREADS=1")
        yaml_json["services"]["bot"]["environment"].append("THREADS=1")
        yaml_json["services"]["bot"]["environment"].append("THREAD_FOR_BROADCASTING=1")
        yaml_json["services"]["web"]["environment"].append("AXIOS_UPDATER_FREQUENCY=60")
        yaml_json["services"]["bot"]["environment"].append(f"SEND_EXCEPTION_ADVICE_TO_ADMIN=1")
        yaml_json["services"]["web"]["environment"].append(f"CORS_DISABLED=1")
        return True
    else:
        yaml_json["services"]["bot"]["environment"].append("DEBUG=0")
        yaml_json["services"]["web"]["environment"].append("DEBUG=0")
        return False

def api_public_link():
    while True:
        print("[[ API_WEB_PUBLIC ]]\nInserisci l'indirizzo pubblico da cui è sarà possibile accedere alla piattaforma WEB\nDocumentazione: https://github.com/DomySh/bot-trasparenzascuole/blob/main/README.md")
        res = input("> ")
        if re.match(r"^http(s)?:\/\/[(?a-zA-Z0-9@:%._\+~#=]+\.[a-z]{2,}(\/)?$",res):
            yaml_json["services"]["bot"]["environment"].append(f"API_EXTERNAL_URL={res}")
            yaml_json["services"]["web"]["environment"].append(f"API_AXIOS_DATA_LINK={res}")
            break

def cache_attachments():
    print("""[[ CACHE_ATTACHMENTS ]]\nGli allegati vengono scaricati direttamente dalla piattaforma axios nella visualizzazione PDF,
pertanto se la piattaforma smetterà di funzionare, gli allegati non saranno disponibili.
Attivando questa opzione nella cartella che si creerà all'avvio del progetto (./pdffiles)
verranno scaricati i pdf che sono richiesti, solo per la prima volta in cui saranno richiesti,
a seguito i PDF saranno indipendenti dalla piattaform axios.""")
    if y_or_n(True):
        yaml_json["services"]["web"]["environment"].append(f"API_CACHE_ATTACHMENTS=1")
        yaml_json["services"]["web"]["volumes"]=["./pdffiles:/execute/data"]
    else:
        yaml_json["services"]["web"]["environment"].append(f"API_CACHE_ATTACHMENTS=0")

def webhook_url():
    while True:
        print("Inserisci l'indirizzo per l'acceso pubblico al server per la webhook\nDocumentazione: https://github.com/DomySh/bot-trasparenzascuole/blob/main/doc/TG_WEBHOOK.md")
        res = input("> ")
        if re.match(r"^http(s)?:\/\/[(?a-zA-Z0-9@:%._\+~#=]+\.[a-z]{2,}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)$",res):
            yaml_json["services"]["bot"]["environment"].append(f"TG_BOT_WEBHOOK_URL={res}")
            break 

def send_alerts_to_admin():
    print("""[[ SEGNAL_ADMIN_EXCEPTION ]]\nDurante l'esecuzione del bot le eccezioni vengono catturate e segnalate all'utente,
se desideri che le eccezioni vengano segnalate anche al super amministratore abilita questa funzione
(l'utente verrà informato che l'amministrazione è stato segnalato sull'evento)""")
    if y_or_n(False):
        yaml_json["services"]["bot"]["environment"].append(f"SEND_EXCEPTION_ADVICE_TO_ADMIN=1")
    else:
        yaml_json["services"]["bot"]["environment"].append(f"SEND_EXCEPTION_ADVICE_TO_ADMIN=0")

def cors_disabled():
    print("""[[ DISABLE_CORS ]]\nLa piattaforma web contiene delle API per accedere alle informazioni nel database mongodb,
di default queste non sono accessibili da domini differenti da quello in cui è avviata la piattaforma.
Per disattivare i controlli di sicurezza cors al fine di utilizzare le API della piattaforma per applicativi
abilita questa opzione.""")
    if y_or_n(False):
        yaml_json["services"]["web"]["environment"].append(f"CORS_DISABLED=1")
    else:
        yaml_json["services"]["web"]["environment"].append(f"CORS_DISABLED=0")

def web_platform_port():
    global API_PORT
    while True:
        print("[[ WEB_API_PORT ]]\nScegli su quale porta avviare (sull'interfaccia 127.0.0.1) la piattaforma web\nDocumentazione: https://github.com/DomySh/bot-trasparenzascuole/blob/main/README.md")
        res = input("(Default=8080)> ")
        if res == "": res = "8080"
        if res.isdecimal() and int(res)>=0 and int(res)<=65535:
            API_PORT = int(res)
            yaml_json["services"]["web"]["ports"]=[f"127.0.0.1:{int(res)}:9999"]
            break

def webhook_port():
    while True:
        print("[[ WEBHOOK_PORT ]]\nScegli su quale porta avviare (sull'interfaccia 127.0.0.1) la webhook\nDocumentazione: https://github.com/DomySh/bot-trasparenzascuole/blob/main/doc/TG_WEBHOOK.md")
        res = input("> ")
        if res.isdecimal() and int(res)>=0 and int(res)<=65535:
            yaml_json["services"]["bot"]["ports"]=[f"127.0.0.1:{int(res)}:9999"]
            break

def axios_customer_id():
    while True:
        print("[[ AXIOS_CUSTOMER_ID ]]\nInserisci il customer id sulla piattaforma axios, o il link della tua scuola su trasparenzascuole.it\nDocumentazione: https://github.com/DomySh/bot-trasparenzascuole/blob/main/README.md")
        res = input("> ")
        if len(re.findall(r"Customer_ID=([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})",res)) > 0:
            res = re.findall(r"Customer_ID=([a-fA-F0-9]{8}\-[a-fA-F0-9]{4}\-[a-fA-F0-9]{4}\-[a-fA-F0-9]{4}\-[a-fA-F0-9]{12})",res)[0]
        elif re.match(r"^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$",res):
            res = re.findall(r"^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$",res)[0]
        else:
            res = None
        if res:
            yaml_json["services"]["web"]["environment"].append(f"AXIOS_CUSTOMER_ID={res}")
            break

def bot_threads():
    while True:
        print("[[ BOT_THREADS ]]\nScegli quanti thread dedicare all'ascolto dei messaggi sul bot telegram.")
        res = input("(DEFAULT=4)> ")
        if res == "": res = "4"
        if res.isdecimal() and int(res)>0 and int(res)<=100:
            yaml_json["services"]["bot"]["environment"].append(f"THREADS={int(res)}")
            break
        

def api_threads():
    while True:
        print("[[ API_THREADS ]]\nScegli quanti thread dedicare alla piattaforma web")
        res = input("(DEFAULT=1)> ")
        if res == "": res = "1"
        if res.isdecimal() and int(res)>0 and int(res)<=100:
            yaml_json["services"]["web"]["environment"].append(f"THREADS={int(res)}")
            break

def ask_for_threads():
    print("Vuoi personalizzare il numero di thread da utilizzare per la piattaforma? (Consigliato se è presente una grande utenza)")
    if y_or_n(False):
        bot_threads()
        api_threads()
        threads_for_broadcast()
    else:
        yaml_json["services"]["bot"]["environment"].append("THREADS=4")
        yaml_json["services"]["web"]["environment"].append("THREADS=1")
        yaml_json["services"]["bot"]["environment"].append(f"THREAD_FOR_BROADCASTING=3")

def updater_frequency():
    while True:
        print("[[ UPDATE_FREQUENCY ]]\nScegli l'intervallo di tempo da aspettare ripetutapente per il download dei dati dalla piattaforma axios")
        res = input("(DEFAULT=2, Minuti)> ")
        if res == "": res = "2"
        if not res.isdecimal(): continue
        if int(res)>=1 and int(res)<=60*24:
            yaml_json["services"]["web"]["environment"].append(f"AXIOS_UPDATER_FREQUENCY={int(res)*60}")
            break    

def from_json_to_yml(json_data:dict):
    yml = ""
    for key,value in json_data.items():
        if type(value) in (str,int,float):
            yml += f"{key}: {value}\n"
        elif type(value) == dict:
            yml+=f"{key}:\n"
            for line in from_json_to_yml(value).split("\n"):
                yml+=f"    {line}\n"
        elif type(value) == list:
            yml+=f"{key}:\n"
            for ele in value:
                yml+=f"    - {ele}\n"
    return yml

def basic_infos():
    get_bot_token()
    get_admin_id()
    axios_customer_id()
    web_platform_port()
    mongodb_conn()

def handle():
    
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if os.path.exists("./docker-compose.yml"):
        print("Vuoi sovrascrivere la configurazione corrente?")
        if not y_or_n(False):
            exit()

    basic_infos()
    if not set_debug():
        api_public_link()
        webhook_choose()   
        cache_attachments()
        ask_for_threads()
        updater_frequency()
        send_alerts_to_admin()
        cors_disabled()
    with open("./docker-compose.yml","wt") as f:
        f.write(from_json_to_yml(yaml_json))
    print("\nConfigurazione generata!\nAvvia con docker-compose up -d --build")

if __name__ == "__main__":
    handle()
