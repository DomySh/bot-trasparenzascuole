import requests, re, json, os
from urllib.parse import parse_qs
from lxml import html
from urllib.parse import urlparse
from base64 import b64decode
from hashlib import md5
from base64 import urlsafe_b64encode
from datetime import datetime


def ctrl_env(env_id,msg):
    if env_id not in os.environ or os.environ[env_id].strip() == "":
        raise Exception(msg)

ctrl_env("AXIOS_CUSTOMER_ID", "AXIOS_CUSTOMER_ID is needed by the updater! Please insert an AXIOS customer id to be syncronised")
selected_school = os.environ["AXIOS_CUSTOMER_ID"]

class AxiosApiError(Exception):pass

class Bacheca:
    def __init__(self, customer_id, pid, name):
        self.customer = customer_id
        self.pid = pid
        self.name = name
        self.id = urlsafe_b64encode(md5(self.pid.encode()).digest()).decode().replace("=","")
    def download_data(self):
        return BachecaDataParser(self).parse()
    def rss_count(self):
        return len(requests.get(self.rss_feed_link()).text.split("\n"))  
    def data_link(self):
        return f"https://www.trasparenzascuole.it/Ajax/APP_Ajax_Get.aspx?action=GET_PAGE_BACHECA&Others={self.customer}|{self.pid}|"
    def rss_feed_link(self):
        return f"https://www.trasparenzascuole.it/Public/BCIRSS.aspx?Customer_ID={self.customer}&PID={self.pid}"


class TrasparenzeScuoleMap:
    def __init__(self, customer_id=selected_school, download_pid_list=False, download_school_name=False):
        self.customer_id = customer_id
        if download_pid_list:
            self.download_pid_list()
        else:
            self._pid_list = None
        
        if download_school_name:
            self.name()
        else:
            self._name = None
        

    def pids(self):
        if self._pid_list is None:
            self.download_pid_list()
        return self._pid_list

    def name(self):
        if self._name is None:
            self._name = self._get_customer_name()
        return self._name

    def load_pid_list(self,pid_list):
        self._pid_list = pid_list

    def download_pid_list(self):
        self._pid_list = [Bacheca(self.customer_id,id_pid,name) for id_pid, name in self._get_pids_ids()]

    def _get_customer_name(self):
        customer_info = requests.get(self._get_customer_data_link()).text
        customer_info = html.fromstring(customer_info)
        return customer_info[0].text

    def _get_pids_ids(self):
        main_page = requests.get(self._main_page_link()).text
        main_page = html.fromstring(main_page)
        pids = main_page.xpath("//div[@class='panel-body bacheche-menu']//a[@runat='server']")
        pids = [(urlparse(ele.attrib["href"]),ele.text) for ele in pids if "href" in ele.attrib]
        pids = [(parse_qs(link.query)["PID"][0], name) for link,name in pids]
        return pids
    
    def download_data(self):
        return [ele.download_data() for ele in self.pids()]

    def _get_customer_data_link(self):
        return f"https://www.trasparenzascuole.it/Ajax/APP_Ajax_Get.aspx?action=INIT_BACHECHE&Others={self.customer_id}"
    def _get_data_api_link(self,pid):
        return f"https://www.trasparenzascuole.it/Ajax/APP_Ajax_Get.aspx?action=GET_PAGE_BACHECA&Others={self.customer_id}|{pid}|"
    def _get_rss_feed_link(self,pid):
        return f"https://www.trasparenzascuole.it/Public/BCIRSS.aspx?Customer_ID={self.customer_id}&PID={pid}"
    def _main_page_link(self):
        return f"https://www.trasparenzascuole.it/Public/Bacheche.aspx?Customer_ID={self.customer_id}"

class DocData:

    def __init__(self,pid:Bacheca,description,note,date,hash,download,filename):
        self.pid = pid
        self.description = description
        self.note = note
        self.date = date
        self.hash = hash
        self.download = download
        self.filename = filename
        self._match = None

    def match_id(self):
        if self._match is None:
            res = str(self.date.timestamp())+self.pid.pid
            if self.description is not None:
                res+=self.description
            if self.note is not None:
                res+=self.note
            self._match = urlsafe_b64encode(md5(res.encode()).digest()).decode().replace("=","")
        return self._match

    def __iter__(self):
        yield from {
            "pid": self.pid.id,
            "match": self.match_id(),
            "description": self.description,
            "note": self.note,
            "date": self.date,
            "attachment":{
                "hash": {
                    "digest":self.hash,
                    "type":"SHA256"
                } if not self.hash is None else None,
                "download": self.download,
                "name": self.filename
            }
        }.items()
    
    def json_dict(self):
        res = dict(self)
        res["date"] = int(res["date"].timestamp()) if not res["date"] is None else None
        return res
    
    def __str__(self):
        return json.dumps(self.json_dict())
    
    def __repr__(self):
        return "<Doc match="+str(self.match_id())+">"
        

    

class BachecaDataParser:
    def __init__(self,pid:Bacheca):
        self.pid = pid
    
    def parse(self):
        html_page = requests.get(self.pid.data_link()).json()
        error_code = int(html_page["errorcode"])
        error_msg = html_page["errormsg"]
        if error_code != 0:
            raise AxiosApiError(error_msg) 
        html_page = json.loads(html_page["json"])['pageDownloadFile']
        html_page = html.fromstring(html_page) 
        posts = html_page.xpath("//li[@class='list-group-item']")
        if len(posts) == 1:
            element = posts[0].xpath("//div[@class='col-md-12 text-center']")[0].text 
            if "Non risultano documenti pubblicati in questa sezione" == element:
                posts = []
        posts = [self._parse_post(posts[i]) for i in range(len(posts))]
        return posts
    
    def _parse_post(self,post_xml):
        return DocData(
                self.pid,
                self._get_description(post_xml),
                self._get_note(post_xml),
                self._get_date(post_xml),
                self._get_hash(post_xml),
                self._get_download_link(post_xml),
                self._get_attachment_name(post_xml),
            )
    def _get_download_link(self,post:str):
        try:
            d_tag = post.xpath("div//button")[0]
            d_tag.attrib['data-storagefilename']
            storage_fn = d_tag.attrib['data-storagefilename']
            source_fn = d_tag.attrib['data-sourcefilename']
            data_folder = d_tag.attrib['data-folder']
            return f"https://www.trasparenzascuole.it/Ajax/SD_UploadDownloadHandler.aspx?cid={self.pid.customer}&folder={data_folder}&storagefilename={storage_fn}&sourcefilename={source_fn}"
        except Exception:
            return None
    
    def _get_attachment_name(self,post):
        try:
            d_tag = post.xpath("div//button")[0]
            filename = d_tag.attrib['data-sourcefilename']
            return b64decode(filename).decode()
        except Exception:
            return None


    def _get_date(self,post):
        try:
            date_str = post.xpath("div//h6")[0].text[len('Documento pubblicato il '):]
            return datetime.strptime(date_str,'%d/%m/%Y %H:%M:%S')
        except Exception:
            return None

    def _get_hash(self,post):
        try:
            return post.xpath("div//i")[1].text  
        except Exception:
            return None

    def _get_description(self,post):
        try:
            return post.xpath("div//i")[2].text[len('Descrizione: '):]
        except Exception:
            return None

    def _get_note(self,post):
        try:
            return post.xpath("div//i")[3].text[len('Note: '):]
        except Exception:
            return None    


if __name__ == "__main__":
    print(TrasparenzeScuoleMap().download_data())