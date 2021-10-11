const button = document.querySelector('.submit-button');
const input = document.getElementById("search");
const content = document.getElementById("content");
let len_docs = NaN;
let page_len = 8; // will be gived the ability to change
let tot_pages = NaN;
let current_page = NaN;
let prefix_api = "";

let search_activated = null;
let search_content = null;
let pids_infos = null
let update_len = 0;

input.addEventListener("keyup", function(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        button.click();
    }
});

function get_pid_name_by_id(id){
    for (let i = 0;i<pids_infos.length;i+=1){
        if (pids_infos[i].id == id){
            return pids_infos[i].name
        }
    }
    return null

}

function bacheca_filter(){
    let select_tag = document.getElementById("pid_select").selectedOptions[0].value
    if (select_tag == "all"){
        prefix_api = ""
        updateURLParameter("pid", null);
    }else{
        prefix_api = "/pid/"+select_tag
        updateURLParameter("pid", select_tag);
    }
    updateButtonMsg()
}

function change_selection_pid(id){
    let select_tag = document.getElementById("pid_select").options
    for(let i=0;i<select_tag.length;i+=1){
        if (select_tag[i].value == id){
            select_tag[i].selected = true;
        }else{
            select_tag[i].selected = false;
        }
    }
}

function check_pid_filter(){
    let pid_filter = findGetParameter("pid")
    if (pid_filter != null && pid_filter != ""){
        let res = get_pid_name_by_id(pid_filter)
        if (res == null){
            updateURLParameter("pid", null);
            prefix_api = ""
        }else{
            updateURLParameter("pid", pid_filter);
            prefix_api = "/pid/"+pid_filter
            change_selection_pid(pid_filter)
        }
    }
}

function updateURLParameter(param, paramVal) {
    if (paramVal != null) paramVal = escape(paramVal)
    let url = window.location.href;
    var TheAnchor = null;
    var newAdditionalURL = "";
    var tempArray = url.split("?");
    var baseURL = tempArray[0];
    var additionalURL = tempArray[1];
    var temp = "";

    if (additionalURL) {
        var tmpAnchor = additionalURL.split("#");
        var TheParams = tmpAnchor[0];
        TheAnchor = tmpAnchor[1];
        if (TheAnchor)
            additionalURL = TheParams;

        tempArray = additionalURL.split("&");

        for (var i = 0; i < tempArray.length; i++) {
            if (tempArray[i].split('=')[0] != param) {
                newAdditionalURL += temp + tempArray[i];
                temp = "&";
            }
        }
    } else {
        var tmpAnchor = baseURL.split("#");
        var TheParams = tmpAnchor[0];
        TheAnchor = tmpAnchor[1];

        if (TheParams)
            baseURL = TheParams;
    }

    var rows_txt;
    if (paramVal != null) {
        rows_txt = temp + "" + param + "=" + paramVal;
    } else {
        rows_txt = "";
    }

    if (TheAnchor)
        rows_txt += "#" + TheAnchor;

    if(newAdditionalURL + rows_txt)
        window.history.replaceState('', '', baseURL + "?" + newAdditionalURL + rows_txt);
    else
    window.history.replaceState('', '', baseURL);
}

async function api_load(query, base_api="/docs", allow_prefix=true) {
    try {    
        prefix = "/"
        if(query.length > 0 && query[0] == '/'){
                prefix = ""
        }
        url_str = ""
        if (allow_prefix) url_str = base_api + prefix_api + prefix + query
        else url_str = base_api + prefix + query
        var res = await $.ajax({
            url: url_str,
            dataType: 'json',
        });
        return res
    } catch (err) {
        return null;
    }
}

async function updateButtonMsg() {
    button.disabled = true
    search_activated = false;
    updateURLParameter("search", input.value)
    reload();


    button.textContent = "Ricerca..."
    button.disabled = false
    button.textContent = "Invia"

};

function removeAllChildNodes(parent) {
    while (parent.firstChild) {
        parent.removeChild(parent.firstChild);
    }
}

function esc(text){
    return $('<div/>').text(text).html();
}

function quoteattr(s, preserveCR) {
    preserveCR = preserveCR ? '&#13;' : '\n';
    return ('' + s) /* Forces the conversion to string. */
        .replace(/&/g, '&amp;') /* This MUST be the 1st replacement. */
        .replace(/'/g, '&apos;') /* The 4 other predefined entities, required. */
        .replace(/"/g, '&quot;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        /*
        You may add other replacements here for HTML only 
        (but it's not necessary).
        Or for XML, only if the named entities are defined in its DTD.
        */ 
        .replace(/\r\n/g, preserveCR) /* Must be before the next replacement. */
        .replace(/[\r\n]/g, preserveCR);
        ;
}

function build_tag(doc) {
    let date = null;
    if (doc.date != null){
        date = Date.parse(doc.date)
        date-=60*60*2*1000
        date = new Date(date).toLocaleString('it-IT');
    }
    let text = `<div class="doc_div">
        <div class="circ_n_doc">
        <h5 class="pid_doc">${get_pid_name_by_id(doc.pid)}<span class="put_right">📝</span></h5>
        <p class="note"><b>📓 Note:</b> ${doc.note != null ? esc(doc.note): "<u>Nessuna nota disponibie!</u>" }</p>
        <p class="descript"><b>🔥 Descrizione:</b> ${doc.description != null ? esc(doc.description): "<u>Nessuna descrizione disponibie!</u>" }</p>
        <p class="date_doc"><b>🗓️ Pubblicata il:</b> ${date != null ? esc(date) : "<u>Data non disponibile!</u>"}</p>
        <a target="_blank" href="${quoteattr("/view/"+doc.match)}" class="download-btn-show">Lettore PDF</a>
        <span class="put_right">
        <a target="_blank" href="${quoteattr(doc.download)}" class="download-btn" download><i class="fa fa-download" aria-hidden="true"></i></a>
        </span>
        </div>`
    return $(text)[0]
}

function page_selector() {
    let text = `<div class="page-selector">`
    if (current_page != 1) {
        text += `<a class="circle-btn c-arrow" onclick="first_page()"><i class="fas fa-angle-double-left"></i></a>`
        text += `<a class="circle-btn c-arrow" onclick="prev_page()"><i class="fas fa-angle-left"></i></a>`
    }

    if (current_page - 1 > 0) {
        let n = current_page - 1
        text += `<a class="circle-btn circle-space-left" onclick="set_page(${n})">${n}</a>`
    }
    let css_additional = ""
    if (current_page - 1 <= 0) css_additional += " circle-space-left "
    if (current_page + 1 > tot_pages) css_additional += " circle-space-right "
    text += `<a class="circle-btn page_selected ${css_additional}" onclick="set_page(${current_page})">${current_page}</a>`
    if (current_page + 1 <= tot_pages) {
        let n = current_page + 1
        text += `<a class="circle-btn circle-space-right" onclick="set_page(${n})">${n}</a>`
    }

    if (current_page != tot_pages) {
        text += `<a class="circle-btn c-arrow" onclick="next_page()"><i class="fas fa-angle-right"></i></a>`
        text += `<a class="circle-btn c-arrow" onclick="last_page()"><i class="fas fa-angle-double-right"></i></a>`
    }

    text += `</div>`
    return $(text)[0]
}

function findGetParameter(parameterName) {
    var result = null,
        tmp = [];
    location.search
        .substr(1)
        .split("&")
        .forEach(function(item) {
            tmp = item.split("=");
            if (tmp[0] === parameterName) result = decodeURIComponent(tmp[1]);
        });
    return result;
}

function isNormalInteger(str) {
    var n = Math.floor(Number(str));
    return n !== Infinity && String(n) === str && n >= 0;
}

function get_current_page() {
    let page = findGetParameter("page");

    if (page == null) {
        page = 1;
    }
    page = parseInt(page);
    if (page > tot_pages) page = tot_pages
    if (page <= 0) page = 1
    if(page != 1)updateURLParameter("page", page);
    else updateURLParameter("page", null);
    current_page = page;
}

async function search_init() {
    if (search_activated) return;
    let search = findGetParameter("search");
    if (search == "" || search == null) {
        updateURLParameter("search", null);
        search = null;
        search_activated = false
        search_content = null
    } else {
        input.value = search;
        search_activated = true;
        search_content = await api_load("/search/" + btoa(search).replace(/\//g, '_').replace(/\+/g, '-'))
        updateURLParameter("page", null);
        search_content = search_content.reverse()
        return;
    }
}

async function updates_detect(){
    new_update = (await api_load("/len",base_api="/events",allow_prefix=false)).data;
    if (new_update != update_len){
        update_len = new_update
        pids_infos = await api_load("/pids",base_api="/docs",allow_prefix=false)
        reload()
    }
}

async function main(){
    update_len = (await api_load("/len",base_api="/events",allow_prefix=false)).data
    setInterval(updates_detect,5000)
    pids_infos = await api_load("/pids",base_api="/docs",allow_prefix=false)
    reload()
}

async function reload() {
    button.textContent = "CARICAMENTO";
    button.disabled = true;

    window.scrollTo({
        top: 0,
        left: 0,
        behavior: 'smooth'
    });
    check_pid_filter()
    await search_init();
    if (search_activated) len_docs = search_content.length
    else len_docs = (await api_load("/len")).data;
    tot_pages = Math.ceil(len_docs / page_len);
    get_current_page();
    removeAllChildNodes(content);
    let from = len_docs - ((current_page - 1) * page_len)
    let to = (from - page_len < 0) ? 0 : from - page_len
    let results = Array();
    if (search_activated) {
        from = [to, to = from][0]; // swap
        for (let i = from; i < to; i += 1) {
            results.push(search_content[i])
        }
    } else {
        results = await api_load("/range/" + from + "/" + to);
    }

    if(results.length > 0){
        for (let i = results.length - 1; i >= 0; i -= 1) {
            content.appendChild(build_tag(results[i]))
        }
        content.appendChild(page_selector())
    }else{
        content.appendChild($(`<center><h2>Nessun risultato trovato!</h2></center>`)[0])
    }

    button.textContent = "INVIA";
    button.disabled = false;


}
button.addEventListener('click', updateButtonMsg);

function next_page() {
    updateURLParameter("page", current_page + 1);
    reload();
}

function first_page() {
    updateURLParameter("page", null);
    reload();
}


function last_page() {
    updateURLParameter("page", tot_pages);
    reload();
}

function set_page(n) {
    if(n != 1)updateURLParameter("page", n);
    else updateURLParameter("page", null);
    reload();
}


function prev_page() {
    
    if(current_page - 1 != 1)updateURLParameter("page", current_page - 1);
    else updateURLParameter("page", null);
    reload();
}

$(window).on('load', function() { 
    main();
});

