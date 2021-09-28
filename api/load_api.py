import os, base64, werkzeug, flask, requests, re
from flask import Flask, render_template, Blueprint, jsonify, send_file
from pymongo import ASCENDING, DESCENDING, MongoClient
from pathlib import Path
from base64 import urlsafe_b64decode

def ctrl_env(env_id,msg):
    if env_id not in os.environ or os.environ[env_id].strip() == "":
        raise Exception(msg)

ctrl_env("API_AXIOS_DATA_LINK","Insert the public address of this site at API_AXIOS_DATA_LINK")

PUBLIC_LINK = os.environ["API_AXIOS_DATA_LINK"].strip()
if PUBLIC_LINK.endswith("/"): PUBLIC_LINK = PUBLIC_LINK[:-1]
MONGO_URL = "mongodb://mongo/"
DB_CONN = MongoClient(MONGO_URL)
DB = DB_CONN["main"]
API_CACHE_ATTACHMENTS = os.getenv("API_CACHE_ATTACHMENTS","False").lower() in ("true","t","y","yes","1")
CORS_DISABLED = os.getenv("CORS_DISABLED","False").lower() in ("true","t","y","yes","1")
DEBUG = os.getenv("DEBUG","False").lower() in ("true","t","y","yes","1")

def give_a_random(leng = 256):
    return base64.b64encode(os.urandom(leng)).decode()

app = Flask(__name__)
app.config["SECRET_KEY"] = give_a_random()
app.config["PUBLIC"] = PUBLIC_LINK
app.url_map.strict_slashes = False
app.debug = DEBUG

def index_range(index_from,index_to):
    index_from = int(index_from)
    index_to = int(index_to)
    if index_to < index_from:
        index_from, index_to = index_to, index_from
    return index_from, index_to

@app.after_request
def after(response):
    if CORS_DISABLED:
        response.headers['Access-Control-Allow-Origin'] = '*'
    return response

def json_api(function):
    def wrapper(*args, **kargs):
        try:
            func = function(*args, **kargs)
        except IndexError:
            return {"msg":"Invalid paramethers sent!"},404
        except IndexError:
            return {"msg":"Invalid index!"},404
        if func is None:
            return {"msg":"Not Found!"}, 404
        if type(func) == list:
            return jsonify(func)
        if type(func) not in (dict,tuple):
            return {"data":func}
        return func
    wrapper.__name__ = function.__name__
    return wrapper

@app.errorhandler(werkzeug.exceptions.HTTPException)
def return_error(e):
    return {"msg":str(e)}, e.code

# ----------
#  Docs API
# ----------

docs = Blueprint("docs",__name__)

docs_pid = Blueprint("docs_pid",__name__)

@docs_pid.route("/<pid>/")
@json_api
def pidserach_pid_info(pid):
    return DB["pids"].find_one({"id":pid},{"_id":False})

@docs_pid.route("/<pid>/all")
@json_api
def pidserach_get_all_docs(pid):
    return list(DB["docs"].find({"pid":pid},{"_id":False}).sort("date",ASCENDING))

@docs_pid.route("/<pid>/len")
@json_api
def pidserach_get_len_docs(pid):
    return int(DB["docs"].count_documents({"pid":pid}))

@docs_pid.route("/<pid>/index/<index>")
@json_api
def pidserach_get_index_docs(pid,index):
    return DB["docs"].find({"pid":pid},{"_id":False}).sort("date",ASCENDING)[int(index)]


@docs_pid.route("/<pid>/range/<index_from>/<index_to>")
@json_api
def pidserach_get_range_docs(pid,index_from,index_to):
    index_from, index_to = index_range(index_from, index_to)
    return list(DB["docs"].find({"pid":pid},{"_id":False}).sort("date",ASCENDING)[int(index_from):int(index_to)])

@docs_pid.route("/<pid>/search/<search_text>")
@json_api
def pidserach_search_doc(pid, search_text):
    try:
        search_text = urlsafe_b64decode(search_text).decode()
    except UnicodeError:
        return {"msg":"Text sended is not valid"},404
    return list(DB["docs"].find({"pid":pid,"$text":{"$search":search_text}},{"_id":False}).sort("date",DESCENDING))

docs.register_blueprint(docs_pid,url_prefix="/pid")

@docs.route("/all")
@json_api
def get_all():
    return list(DB["docs"].find({},{"_id":False}).sort("date",ASCENDING))

@docs.route("/match/<match_id>")
@json_api
def get_from_post_code(match_id):
    return DB["docs"].find_one({"match":match_id},{"_id":False})

@docs.route("/len")
@json_api
def get_post_len():
    return int(DB["docs"].count_documents({}))

@docs.route("/index/<index>")
@json_api
def get_index_docs(index):
    return DB["docs"].find({},{"_id":False}).sort("date",ASCENDING)[int(index)]

@docs.route("/range/<index_from>/<index_to>")
@json_api
def get_range_docs(index_from,index_to):
    index_from, index_to = index_range(index_from, index_to)
    return list(DB["docs"].find({},{"_id":False}).sort("date",ASCENDING)[int(index_from):int(index_to)])


@docs.route("/pids")
@json_api
def pids_info():
    return list(DB["pids"].find({},{"_id":False}))

@docs.route("/search/<search_text>")
@json_api
def search_doc(search_text):
    try:
        search_text = urlsafe_b64decode(search_text).decode()
    except UnicodeError:
        return {"msg":"Text sended is not valid"},404
    return list(DB["docs"].find({"$text":{"$search":search_text}},{"score":{"$meta":"textScore"},"_id":False}).sort("date",DESCENDING))

app.register_blueprint(docs,url_prefix="/docs")

events = Blueprint("events",__name__)

@events.route("/len")
@json_api
def events_len():
    return int(DB["docs_events"].count_documents({}))

@events.route("/all")
@json_api
def events_all():
    return list(DB["docs_events"].find({},{"_id":False}).sort("date",ASCENDING))

@events.route("/index/<index>")
@json_api
def events_index(index):
    return DB["docs_events"].find({},{"_id":False}).sort("date",ASCENDING)[int(index)]

@events.route("/range/<index_from>/<index_to>")
@json_api
def events_range(index_from, index_to):
    index_from, index_to = index_range(index_from, index_to)
    return list(DB["docs_events"].find({},{"_id":False}).sort("date",ASCENDING)[index_from:index_to])

@events.route("/update/<last_index>")
@json_api
def events_update(last_index):
    return {"len":int(DB["docs_events"].count_documents({})), "updates":list(DB["docs_events"].find({},{"_id":False}).sort("date",ASCENDING)[int(last_index):])}

@events.route("/update/<last_index>/full")
@json_api
def events_update_full(last_index):
    updates = list(DB["docs_events"].find({},{"_id":False}).sort("date",ASCENDING)[int(last_index):])
    for i in range(len(updates)):
        updates[i]["target"] = list(DB["docs"].find({"match":{"$in":updates[i]["target"]}}).sort("date",ASCENDING))
    return {"len":int(DB["docs_events"].count_documents({})), "updates":updates}

events_pid = Blueprint("events_pid",__name__)

@events_pid.route("/<pid>/len")
@json_api
def pid_events_len(pid):
    return int(DB["docs_events"].count_documents({"pid":pid}))

@events_pid.route("/<pid>/all")
@json_api
def pid_events_all(pid):
    return list(DB["docs_events"].find({"pid":pid},{"_id":False}).sort("date",ASCENDING))

@events_pid.route("/<pid>/index/<index>")
@json_api
def pid_events_index(pid, index):
    return DB["docs_events"].find({"pid":pid},{"_id":False}).sort("date",ASCENDING)[int(index)]

@events_pid.route("/<pid>/range/<index_from>/<index_to>")
@json_api
def pid_events_range(pid, index_from, index_to):
    index_from, index_to = index_range(index_from, index_to)
    return list(DB["docs_events"].find({"pid":pid},{"_id":False}).sort("date",ASCENDING)[index_from:index_to])

@events_pid.route("/<pid>/update/<last_index>")
@json_api
def pid_events_update(pid, last_index):
    return {"len":int(DB["docs_events"].count_documents({"pid":pid})), "updates":list(DB["docs_events"].find({"pid":pid},{"_id":False}).sort("date",ASCENDING)[int(last_index):])}

@events_pid.route("/<pid>/update/<last_index>/full")
@json_api
def pid_events_update_full(pid, last_index):
    updates = list(DB["docs_events"].find({"pid":pid},{"_id":False}).sort("date",ASCENDING)[int(last_index):])
    for i in range(len(updates)):
        if updates[i]["type"] != "DELETE":
            updates[i]["target"] = list(DB["docs"].find({"match":{"$in":updates[i]["target"]}}).sort("date",ASCENDING))
    return {"len":int(DB["docs_events"].count_documents({"pid":pid})), "updates":updates}

events.register_blueprint(events_pid, url_prefix="/pid")

app.register_blueprint(events, url_prefix="/events")

@app.route("/view/")
def pdf_view_err():
    return render_template("pdf_view_err.html")

@app.route("/view/<match_id>")
def pdf_view(match_id):
    doc = DB["docs"].find_one({"match":match_id})
    if doc is None:
        return render_template("pdf_view_err.html")
    return render_template("viewer.html",doc=doc)

@app.route('/download/<match_id>')
def proxy(match_id):
    doc = DB["docs"].find_one({"match":match_id})
    if doc is None:
        return {"msg":"Invalid match id!"},404
    if doc["attachment"]["download"] is None:
        return {"msg":"No Download link found!"}
    if API_CACHE_ATTACHMENTS:
        if re.match(r"^[a-zA-Z0-9-_]*$",match_id):
            path_file = str(Path(__file__).parent.absolute() / "data" / (match_id+".pdf"))
            if not os.path.exists(path_file):
                if not os.path.exists(str(Path(__file__).parent.absolute() / "data")):
                    os.mkdir(str(Path(__file__).parent.absolute() / "data"))
                try:
                    with open(path_file,"wb") as f:
                        f.write(requests.get(doc["attachment"]["download"]).content)
                except Exception as e:
                    return {"msg":"Error while downloading the attachment "+str(e)},404
            filename = doc["attachment"]["name"]
            if filename is None:
                filename = match_id+".pdf"
            return send_file(path_file,download_name=filename)
        else:
            return {"msg":"Invalid match id!"},404
    else:
        try:
            request = requests.get(doc["attachment"]["download"], stream=True, params=flask.request.args)
            response = flask.Response(flask.stream_with_context(request.iter_content(chunk_size=1024*1024*3)),
                                content_type=request.headers['content-type'],
                                status=request.status_code)
            response.headers['Access-Control-Allow-Origin'] = None
            return response
        except Exception as e:
            return {"msg":"Error while downloading the attachment "+str(e)},404 

@app.route("/customer/name")
def get_customer_name():
    return {"data":DB["static"].find_one({"id":"updater"})["customer_name"]}

@app.route("/")
def web_view():
    customer = DB["static"].find_one({"id":"updater"})["customer_name"]
    return render_template("webview.html",
                            customer_name=customer,
                            pids= list(DB["pids"].find({})))

if __name__ == "__main__":
    if DEBUG:
        app.run(host="0.0.0.0",port=9999,debug=True)
    else:
        os.system("gunicorn -w 3 -b 0.0.0.0:9999 load_api:app")
