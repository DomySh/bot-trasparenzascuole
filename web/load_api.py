from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import DESCENDING, ASCENDING
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
import os, re, uvicorn, asyncio, aiofiles, httpx
from pathlib import Path
from base64 import urlsafe_b64decode
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse, RedirectResponse
from fastapi.background import BackgroundTasks

PUBLIC_LINK = os.environ["API_AXIOS_DATA_LINK"].strip()
if PUBLIC_LINK.endswith("/"): PUBLIC_LINK = PUBLIC_LINK[:-1]

DB_CONN = None
DBNAME = "main"
if os.getenv("EXTERNAL_MONGO","False").lower() in ("true","t","y","yes","1"):
    IP_MONGO_AUTH = os.environ["IP_MONGO_AUTH"]
    PORT_MONGO_AUTH = int(os.environ["PORT_MONGO_AUTH"])
    DBNAME = os.environ["DBNAME_MONGO_AUTH"]
    if os.getenv("EXTERNAL_MONGO_AUTH","False").lower() in ("true","t","y","yes","1"):   
        DB_CONN = AsyncIOMotorClient(
            host=IP_MONGO_AUTH,
            port=PORT_MONGO_AUTH,
            username=os.environ["USER_MONGO_AUTH"],
            password=os.environ["PSW_MONGO_AUTH"],
        )
    else:
        DB_CONN = AsyncIOMotorClient(
            host=IP_MONGO_AUTH,
            port=PORT_MONGO_AUTH
        )
else: 
    DB_CONN = AsyncIOMotorClient("mongodb://mongo/")
DB = DB_CONN[DBNAME]

API_CACHE_ATTACHMENTS = os.getenv("API_CACHE_ATTACHMENTS","False").lower() in ("true","t","y","yes","1")
CORS_DISABLED = os.getenv("CORS_DISABLED","False").lower() in ("true","t","y","yes","1")
DEBUG = os.getenv("DEBUG","False").lower() in ("true","t","y","yes","1")
THREADS = int(os.getenv("THREADS",3))

app = FastAPI(debug=DEBUG)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates_obj = Jinja2Templates(directory="templates")
render = templates_obj.TemplateResponse
httpc = httpx.AsyncClient()

def search_transform(s):
    return {"$text":{"$search":" ".join(['"'+ele.strip()+'"' for ele in s.strip().replace('"','').split() if ele.strip() not in ("",None)])}}


def index_range(index_from,index_to):
    if index_to < index_from:
        index_from, index_to = index_to, index_from
    return index_from, index_to

async def mongolist(cursor):
    return await cursor.to_list(length=None)

@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    response = await call_next(request)
    if CORS_DISABLED:
        response.headers['Access-Control-Allow-Origin'] = "*"
    return response

@app.get("/docs/pid/{pid}")
async def search_pid_info(pid: str):
    """Give informations about the pid sended"""
    return await DB["pids"].find_one({"_id":pid})

@app.get("/docs/pid/{pid}/all")
async def get_all_docs_in_pid(pid: str):
    """Give a list of documents in the pid selected sorted by date"""
    return await mongolist(DB["docs"].find({"pid":pid}).sort("date",ASCENDING))

@app.get("/docs/pid/{pid}/len")
async def count_docs_in_pid(pid: str):
    """Give the number of documents existing in the pid"""
    return {"data": await DB["docs"].count_documents({"pid":pid})}

@app.get("/docs/pid/{pid}/index/{index}")
async def get_doc_in_pid_by_index(pid: str,index: int):
    """Select a document in a pid by its position in time with an index"""
    try: return (await mongolist(DB["docs"].find({"pid":pid}).sort("date",ASCENDING).skip(index).limit(1)))[0]
    except IndexError: raise HTTPException(status_code=404, detail="Invalid index!")

@app.get("/docs/pid/{pid}/range/{index_from}/{index_to}")
async def get_range_of_docs_in_pid(pid: str,index_from: int,index_to: int):
    """Give a range of documents in a pid starting from index_from giving at maximum index_to elements"""
    index_from, index_to = index_range(index_from, index_to)
    return await mongolist(DB["docs"].find({"pid":pid}).sort("date",ASCENDING).skip(index_from).limit(index_to))

@app.get("/docs/pid/{pid}/search/{search_text}")
async def search_document_in_pid_by_text(pid: str, search_text: str):
    """Search docs in a pid sending a text query encoded in urlsafe_b64decode sorted by date"""
    try:
        search_text = search_transform(urlsafe_b64decode(search_text).decode())
        search_text["pid"] = pid
    except Exception:
        raise HTTPException(status_code=404, detail="Invalid search text encoding, please encode with urlsafe/b64decode!")
    return await mongolist(DB["docs"].find(search_text).sort("date",DESCENDING))

@app.get("/docs/all")
async def get_all_docs():
    """Receve all existing docs in the DB sorted by date"""
    return await mongolist(DB["docs"].find({}).sort("date",ASCENDING))

@app.get("/docs/match/{match_id}")
async def get_by_match(match_id: str):
    """Get the document using the match id"""
    return await DB["docs"].find_one({"_id":match_id})

@app.get("/docs/len")
async def count_docs():
    """Receve the number of docs existing in the DB"""
    return {"data": await DB["docs"].count_documents({})}

@app.get("/docs/index/{index}")
async def get_doc_by_index(index: int):
    """Select a document by its position in time with an index"""
    try: return (await mongolist(DB["docs"].find({}).sort("date",ASCENDING).skip(index).limit(1)))[0]
    except IndexError: raise HTTPException(status_code=404, detail="Invalid index!") 

@app.get("/docs/range/{index_from}/{index_to}")
async def get_range_of_docs(index_from: int,index_to: int):
    """Give a range of documents starting from index_from giving at maximum index_to elements"""
    index_from, index_to = index_range(index_from, index_to)
    return await mongolist(DB["docs"].find({}).sort("date",ASCENDING).skip(index_from).limit(index_to))

@app.get("/docs/pids")
async def pids_info():
    """List of all pids"""
    return await mongolist(DB["pids"].find({}))

@app.get("/docs/search/{search_text}")
async def search_document_by_text(search_text: str):
    """Search docs sending a text query encoded in urlsafe_b64decode sorted by date"""
    try:
        search_text = search_transform(urlsafe_b64decode(search_text).decode())
    except Exception:
        raise HTTPException(status_code=404, detail="Invalid search text encoding, please encode with urlsafe/b64decode!")
    return await mongolist(DB["docs"].find(search_text).sort("date",DESCENDING))

@app.get("/events/len")
async def count_events():
    """Number of events saved in the database"""
    return {"data": await DB["docs_events"].count_documents({})}

@app.get("/events/all")
async def get_all_events():
    """Get the complete list of events"""
    return await mongolist(DB["docs_events"].find({},{"_id":False}).sort("date",ASCENDING))

@app.get("/events/index/{index}")
async def get_event_by_index(index: int):
    """Get event by an index ordered by date"""
    try: return (await mongolist(DB["docs_events"].find({},{"_id":False}).sort("date",ASCENDING).skip(index).limit(1)))[0]
    except IndexError: raise HTTPException(status_code=404, detail="Invalid index!")

@app.get("/events/range/{index_from}/{index_to}")
async def events_range(index_from: int, index_to: int):
    index_from, index_to = index_range(index_from, index_to)
    return await mongolist(DB["docs_events"].find({},{"_id":False}).sort("date",ASCENDING).skip(index_from).limit(index_to))

@app.get("/events/update/{last_index}")
async def events_update(last_index: int):
    return await mongolist(DB["docs_events"].find({},{"_id":False}).sort("date",ASCENDING).skip(last_index))

@app.get("/events/pid/{pid}/len")
async def pid_events_len(pid:str):
    return {"data":await DB["docs_events"].count_documents({"pid":pid})}

@app.get("/events/pid/{pid}/all")
async def get_all_events_in_pid(pid: str):
    """get all events saved in a pid"""
    return await mongolist(DB["docs_events"].find({"pid":pid}).sort("date",ASCENDING))

@app.get("/events/pid/{pid}/index/{index}")
async def get_event_by_index_in_pid(pid: str, index: int):
    """Get events in a range in pid"""
    try: return (await mongolist(DB["docs_events"].find({"pid":pid}).sort("date",ASCENDING).skip(index).limit(1)))[0]
    except IndexError: raise HTTPException(status_code=404, detail="Invalid index!")

@app.get("/events/pid/{pid}/range/{index_from}/{index_to}")
async def get_events_range_in_pid(pid: str, index_from: int, index_to: int):
    """Get events in a range in pid"""
    index_from, index_to = index_range(index_from, index_to)
    return await mongolist(DB["docs_events"].find({"pid":pid}).sort("date",ASCENDING).skip(index_from).limit(index_to))

@app.get("/events/pid/{pid}/update/{last_index}")
async def events_updates_in_pid(pid: str, last_index: int):
    """Recieve last updates with the last length saved in pid"""
    return await mongolist(DB["docs_events"].find({"pid":pid}).sort("date",ASCENDING).skip(last_index))

@app.get("/view/{match_id}", response_class=HTMLResponse)
async def pdf_viewer(request: Request, match_id: str):
    """PDF viewer of attachment selected by match id"""
    doc = await DB["docs"].find_one({"_id":match_id})
    if doc is None or doc["attachment"] is None or doc["attachment"]["download"] is None:
        return render("invalid_doc.html",{"request": request, "public_url": PUBLIC_LINK})
    if doc["attachment"]["name"] is None or os.path.splitext(doc["attachment"]["name"])[1].lower() != ".pdf":
        return RedirectResponse(url='/download/'+doc["_id"])
    return render("pdf_reader.html", {"request": request, "doc": doc, "public_url": PUBLIC_LINK})

lock_download_file = asyncio.Lock()
lock_match = {}

async def download_doc(url,path_file):
    req = httpc.build_request("GET",url)
    resp = await httpc.send(req, stream=True)
    async with aiofiles.open(path_file,"wb") as f:
        async for chunk in resp.aiter_bytes():
            await f.write(chunk)

async def add_download_lock(match_id):
    selected_lock = None
    
    async with lock_download_file:
        if match_id in lock_match.keys():
            lock_match[match_id]["count"]+=1
            selected_lock = lock_match[match_id]["lock"]
        else:
            lock_match[match_id] = {"lock":asyncio.Lock(),"count":1}
            await lock_match[match_id]["lock"].acquire()
    
    if selected_lock is None:
        return True
    else:
        await selected_lock.acquire()
        return False

async def remove_download_lock(match_id):
    async with lock_download_file:
        if match_id in lock_match.keys():
            lock_match[match_id]["lock"].release()
            lock_match[match_id]["count"]-=1
            if lock_match[match_id]["count"] <= 0:
                del lock_match[match_id]

async def aioproxy_stream(url):
    req = httpc.build_request("GET",url)
    resp = await httpc.send(req, stream=True)

    return StreamingResponse(resp.aiter_bytes(),headers={"Content-Disposition":resp.headers['Content-Disposition']}, media_type=resp.headers['content-type'], status_code=resp.status_code)

@app.get('/download/{match_id}')
async def download_attachments(match_id: str):
    """Download document attachment (using proxy or cached file)"""
    doc = await DB["docs"].find_one({"_id":match_id})
    if doc is None:
        raise HTTPException(status_code=404, detail="Invalid match id!")
    if doc["attachment"] is None or doc["attachment"]["download"] is None:
        raise HTTPException(status_code=404, detail="No Download link found!")
    if API_CACHE_ATTACHMENTS:
        if re.match(r"^[a-zA-Z0-9-_]*$",match_id):
            path_file = str(Path(__file__).parent.absolute() / "data" / match_id)
            if not os.path.exists(path_file):
                if await add_download_lock(match_id):
                    await download_doc(doc["attachment"]["download"],path_file)
                await remove_download_lock(match_id)
            filename = doc["attachment"]["name"]
            if filename is None:
                filename = match_id
            return FileResponse(path_file,filename=filename)
        else:
            raise HTTPException(status_code=404, detail="Invalid match id!")
    else:
        return await aioproxy_stream(doc["attachment"]["download"])

@app.get("/")
async def web_view(request: Request):
    """Main page of the web platform"""
    customer = await DB["static"].find_one({"_id":"updater"})
    customer = customer["customer_name"] if "customer_name" in customer else None
    return render("index.html", {"request": request, "customer_name": customer, "pids": await mongolist(DB["pids"].find({})) ,"public_url": PUBLIC_LINK})

if __name__ == "__main__": 
    uvicorn.run(
        "load_api:app",
        host="0.0.0.0",
        port=9999,
        reload=DEBUG,
        access_log=DEBUG,
        workers=THREADS
    )
