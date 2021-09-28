# Esempio configurazione NGNIX

Supponendo che abbia deciso di avviare il webserver sulla porta 3003 (Ricorda questo numero poichè sarà utile nella configurazione) Questa è una configurazione che potrebbe essere utilizzata con un webserver ngnix per rendere pubblica la piattaforma su https://documenti.scuola.edu.it

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
                proxy_pass http://127.0.0.1:3003/; #Modifica la porta se ne hai scelta una differente
        }
}
```

## [Torna alla guida principale e continua la configurazione](../README.md)