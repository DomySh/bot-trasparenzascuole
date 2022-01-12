<h1><img align="left" src="doc/icon.png" width="70">Piattaforma Web e Bot Telegram per trasparenzascuole.it</h1>

---

## Che cos'è questo progetto ❓
Questa piattaforma permette alla tua scuola di gestire i dati in trasparenzascuole.it in maniera più efficiente e facilmente accessibile dalla comunità scolastica! Tutto questo tramite una interfaccia web moderna (ma soprattutto reattiva, veloce e intuitiva), e un bot telegram che permette anche la recezione di notifiche, oltre che a permettere di inviare messaggi personalizzati alla comunità scolastica

Guarda la piattaforma in funzione! I.I.S.S Luigi dell'erba (Castellana Grotte):
- https://iiss.domysh.com/
- https://t.me/circolaridellerbabot

--- 

## Configurazione e Avvio ⚙️

#### 1. Configurazione Bot Telegram

Inizialmente dovrai creare il bot su telegram
- Creazione del Bot tramite [@BotFather](https://t.me/BotFather)
- Acquisizione del Token del BOT
- Acquisizione del Chat ID dell'account amministratore. [@get_my_chat_id_bot](https://t.me/get_my_chat_id_bot)

[Guida completa sulla creazione/configurazione del bot telegram](doc/BOTTELEGRAM.md)

--- 

#### 2. Configurazione Piattaforma Web + Webhook (Opzionale)

Configura il tuo server per gestire la piattaforma web tramite un webproxy (ngnix, apache ecc...).
Per il corretto funzionamento della piattaforma inoltre è necessario che il percorso base del webserver coincida con quello pubblico.

Esempio:
- http://documenti.scuola.edu.it/ ✔️
- http://scuola.edu.it/piattaforma_documenti/ ❌

Il webserver del bot viene avviato solo sull'interfaccia locale 127.0.0.1 (localhost)

Al termine della configurazione del proxy assicurati di avere:
- Numero di porta su cui avviare localmente il webserver (Es. 8080)
- Indirizzo pubblico verso cui verrà indirizzata la richiesta (Es. http://documenti.scuola.edu.it/)

[Esempio di configurazione con webproxy Ngnix](doc/NGNIX_CONFIG.md)

<b>Configurazione Webhook (Opzionale, Consigliato)</b>

Per evitare problemi nella comunicazione con telegram, e rendere reattivo il bot, è necessario configurare anche un proxy per il webhook di telegram

[Guida sulla configurazione del webhook](doc/TG_WEBHOOK.md)

---

#### 3. Generazione della configurazione

Ora per creare la configurazione, avviare lo script [mkconfig.py](./mkconfig.py) che chiederà una serie di informazioni utili a creare la configurazione docker (saranno necessarie tutte le informazioni acquisite in precedenza + il link della tua scuola su trasparenzascuole.it)

---

#### 4. Avvio del progetto

Per avviare il progetto, installa `docker` e `docker-compose` sulla tua macchina ed esegui nella cartella principale del progetto il seguente comando:
```bash
docker-compose up -d --build
```
Verifica se la configurazione è stata scritta correttamente guardando i log
```bash
#Log del bot telegram
docker-compose logs bot
#Log della piattaforma web + sincronizzatore
docker-compose logs api
```

---

## Come funziona? 💡

Il progetto è basato su [docker](https://www.docker.com/) che permette di avere una flessibilita e facilità di installazione alta, oltre che ad assicurare un alto livello di sicurezza elevato! Il cuore che batte all'interno del progetto è il database [Mongo DB](https://www.mongodb.com/) responsabile del salvataggio di tutti i documenti e dei dati degli utenti. Infine il progetto ha i 2 container che sviluppano le 2 principali funzionalità: Il bot telegram sviluppato in python e il Web server ASGI basato su uvicorn:fastapi che a suo interno avvia anche un daemon (scritto in python), responsabile della sincronizzazione dei dati con trasparenzascuole.it

## Credits
- [Mozilla PDF.JS](https://mozilla.github.io/pdf.js/)

## [Donazioni](https://donorbox.org/bot-trasparenzascuole)

### Sviluppato da [DomySh](https://domysh.com) 👨‍💻

---

## Futuri Update:
- Aggiornamento alle versione 14 di [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot/projects/7)
