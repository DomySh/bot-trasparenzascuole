# Configurazione WebHook telegram

Il bot telegram riceve normalmente le informazioni sui messaggi ricevuti tramite polling (Quindi tramite continue richieste ai server di telegram in attesa di nuovi messaggi ricevuti). Questo metodo può essere deleterio per la stabilità del bot, per questo telegram permette la recezione di nuovi messaggi tramite dei webhook: questo comporta anche però la necessità di avviare un altro webserver! Inolte è conisgliato avere un webserver che abbia un nome o un percorso randomico (Al fine di evitare la recezione di connesione al webhook malevole), ed una connessione https che renderà i dati criptati e non accessibili.

Telegram richiede inoltre che il webhook debba essere avviato solo su determinate porte (443, 80, 88, 8443)
[Documentazione telegram setWebhook](https://core.telegram.org/bots/api#setwebhook)

Il webserver per accettare il webhook di telegram è solo avviato sull'interfaccia 127.0.0.1, pertanto come per la configurazione del webserver di base, sarà necessario un webproxy.
Il webhook sarà inoltre aperto sul percorso base ("/"), si consiglia quindi di impostare un percorso casuale tramite il webproxy

Al termine della configurazione del webproxy sarà necessario avere queste informazioni:
- Porta su cui avviare localmente il webhook 
- Indirizzo pubblico per l'accesso al webhook esternamente


## Esempio di una configurazione su NGNIX

Se si vuole integrare il webhook nella piattaforma web, si può integrare la configurazione ngnix della piattaforma web, integrando un percorso dove viene aperto il webhook. In questo esempio si suppone che la piattaforma web sia avviata sulla porta 3003 e il webhook sulla porta 5000

```ngnix=
server {
        listen 80;
        listen [::]:80;

        # --------------
        # Se vuoi rendere la tua pagina https inserisci questo blocco
        # --------------
        listen 443 ssl; 
        listen [::]:443 ssl; 
        ssl_certificate certificato_chiave_pubblica.pem; 
        ssl_certificate_key certificato_chiave_privata.key; 
        # --------------
        # fine blocco https
        # --------------

        server_name documenti.scuola.edu.it; # Cambia il dominio del sito con un dominio che possiedi. (Opzionale)

        location / {
                include proxy_params;
                proxy_pass http://127.0.0.1:3003/; #Modifica la porta se ne hai scelta una differente (Webserver)
        }

        location /hook/random_path {
                include proxy_params;
                proxy_pass http://127.0.0.1:5000/; #Modifica la porta se ne hai scelta una differente (Webhook)
                #Attenzione in questo caso lo "/" finale in proxy_pass è essenziale per la configurazione!
        }
}
```

## [Torna alla guida principale e continua la configurazione](../README.md)