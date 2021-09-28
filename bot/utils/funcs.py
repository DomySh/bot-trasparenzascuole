from utils.glob import JCallB
import os, requests, html
from utils import config as conf, db
from dateutil import parser

class ApiError(Exception):pass

def api(s:str):
    try:
        s = s.strip()
        if s[0] == "/": s = s[1:]
        url = os.path.join(conf.INTERNAL_API,s)
        res = requests.get(url)
        if res.status_code == 404:
            raise ApiError(res.json()["msg"])
        elif res.status_code != 200:
            raise ApiError(f"Api Status code: {res.status_code}")
        return res.json()
    except ValueError:
        raise ApiError("RequestParse: Invalid JSON data sended!")

def viewer_link(doc:dict):
    return os.path.join(os.path.join(conf.EXTERNAL_API,"view"),doc["match"])

def get_text_circolare(data):
    note = "Nessuna nota disponibile!" if data['note'] is None else data['note']
    descr = "Nessuna descrizione disponibile!" if data['description'] is None else data['description']
    try:
        data_time = parser.parse(data['date']).strftime("%d/%m/%Y %H:%M")
    except Exception:
        data_time = "Data non trovata!"
    return f"""
🔥 <b><u>Descrizione</u>:</b> {html.escape(descr)}

📓 <b><u>Note</u>:</b> {html.escape(note)}

🗓️ Pubblicata il {html.escape(data_time)}
📌 Bacheca: {html.escape(db.get_pid_name(data['pid']))}
"""

def search_doc(s:str):
    from base64 import urlsafe_b64encode
    if type(s) == str: s = s.encode()
    return api("/docs/search/"+urlsafe_b64encode(s).decode())

def invalid_content(callback:callable):
    return callback("I dati ricevuti non sono validi, richiesta rifiutata 🚫")

def platform_error(callback:callable):
    return callback("Ci è stato un problema nella comunicazione con la piattaforma!🚫\nRiprova ad eseguire l'operazione, del il problema persiste, contatta l'amministratore con /contact")   

def get_prefix(str_list):
    conf.STATIC_STRINGS
    res = ""
    for ele in str_list:
        if ele is None: continue
        elif type(ele) == str:
            res += ele
        elif type(ele) == int:
            if ele in conf.STATIC_STRINGS.keys():
                res += conf.STATIC_STRINGS[ele]
        elif type(ele) == list:
            res+=get_prefix(ele)
        res+="\n"
    if len(res) > 0: res = res[:-1]
    return res

"""
Types of feed data
list_scroll:
{ "type":"list_scroll", "list":[{"header":""/0,"doc":{...}},{"header":""/0,"doc":"match"},...], "header":""/0}
index_scroll:
{ "type":"index_scroll", "index":0, "low_limit":0, "high_limit":10, "reversed":False, "header":""}
"""
def send_doc(callback,feed):
    from telegram import (InlineKeyboardMarkup, InlineKeyboardButton, ParseMode)
    BTN_CALL = JCallB("list_scroll")
    if feed is None:
        return callback("Operazione scaduta ⏱️!\nGenera un nuovo messaggio per eseguire l'operazione!")
    if feed["type"] == "list_scroll":
        doc_data = None
        header_doc = None
        try:    
            if not "page" in feed.keys(): feed["page"] = 0
            if type(feed['list'][feed['page']]) == str:
                doc_data = api(f"/docs/match/{feed['list'][feed['page']]}")
            elif "doc" not in feed['list'][feed['page']].keys():
                doc_data = feed['list'][feed['page']]
            elif type(feed['list'][feed['page']]['doc']) == str:
                doc_data = api(f"/docs/match/{feed['list'][feed['page']]['doc']}")
                header_doc = feed['list'][feed['page']]['header'] if "header" in feed['list'][feed['page']].keys() else None
            else:
                doc_data = feed['list'][feed['page']]['doc']
                header_doc = feed['list'][feed['page']]['header'] if "header" in feed['list'][feed['page']].keys() else None
        except ApiError:
            return callback("La circolare cercata non esiste o è stata eliminata 🚫")

        keyb = [[InlineKeyboardButton("Mostra Allegato",url=viewer_link(doc_data))]]
        directional_buttons = []
        if feed["page"] > 0:
            cb_data = dict(feed)
            cb_data["page"]-=1
            directional_buttons.append(InlineKeyboardButton("❮❮ Indietro",callback_data=BTN_CALL.create(cb_data)))
        if feed["page"] < ( len(feed["list"])-1 ):
            cb_data = dict(feed)
            cb_data["page"]+=1
            directional_buttons.append(InlineKeyboardButton("Avanti ❯❯",callback_data=BTN_CALL.create(cb_data)))
        if len(directional_buttons) != 0:
            keyb.append(directional_buttons)
        keyb = InlineKeyboardMarkup(keyb)

        if "header" not in feed.keys(): feed["header"] = None
        text = get_prefix([feed['header'],0 if len(directional_buttons) != 0 else None,header_doc]) + "\n" + get_text_circolare(doc_data)
        return callback(text,parse_mode=ParseMode.HTML, reply_markup=keyb, disable_web_page_preview=True)

    elif feed["type"] == "index_scroll":
        low_limit = feed["low_limit"] if "low_limit" in feed.keys() else 0
        high_limit = feed["high_limit"] if "high_limit" in feed.keys() else api("/docs/len")["data"]-1
        revered_scroll = feed["reversed"] if "reversed" in feed.keys() else False
        header_doc = feed["header"] if "header" in feed.keys() else None
        if "index" not in feed.keys():
            feed["index"] = high_limit if revered_scroll else low_limit
        doc_data = None
        try:
            doc_data = api(f"/docs/index/{feed['index']}")
        except ApiError:
            return callback("La circolare cercata non esiste o è stata eliminata 🚫")
        
        keyb = [[InlineKeyboardButton("Mostra Allegato",url=viewer_link(doc_data))]]
        directional_buttons = []
        if (feed["index"] > low_limit and not revered_scroll) or (feed["index"] < high_limit and revered_scroll):
            cb_data = dict(feed)
            cb_data["index"]+= 1 if revered_scroll else -1
            directional_buttons.append(InlineKeyboardButton("❮❮ Indietro",callback_data=BTN_CALL.create(cb_data)))
        if (feed["index"] < high_limit and not revered_scroll) or (feed["index"] > low_limit and revered_scroll):
            cb_data = dict(feed)
            cb_data["index"]+= -1 if revered_scroll else 1
            directional_buttons.append(InlineKeyboardButton("Avanti ❯❯",callback_data=BTN_CALL.create(cb_data)))
        if len(directional_buttons) != 0:
            keyb.append(directional_buttons)
        
        keyb = InlineKeyboardMarkup(keyb)
        text = get_prefix([header_doc, 0 if len(directional_buttons) != 0 else None]) + "\n" + get_text_circolare(doc_data)
        return callback(text,parse_mode=ParseMode.HTML, reply_markup=keyb, disable_web_page_preview=True)

    return callback("I dati ricevuti non sono validi, richiesta rifiutata 🚫")