# Vehicles Tracking

Il progetto può essere eseguito dal file`main.py`.  

All'interno del _main_ possono essere settati i seguenti parametri:
- `video_url`: indica l'Url del video di youtube o il percorso 
  locale del video. Per cambiare il path, aprire il file `url.py` nella directory 
  `Common` e modificare la voce _path_ del dizionario della città desiderata.
  
- `excluded_area`: true se si vuole escludere una porzione di area
  (settata di default per le varie città disponibili) per il tracking;
  
- `show_log`: true se mostrare i log durante l'esecuzione del 
  progetto.
  
Le città disponibili sono:

- Cambridge, Market Central, MA
- Derry, .....

Al seguente link è possibile scaricare i video delle città disponbili:
[link](https://www.github.com "Github home")

**NB**: si consiglia di utilizzare un video locale, poichè se si imposta un Url di youtube, il tracking potrebbe presentarsi a scatti 
a causa del buffering nello scaricare i pacchetti del video della libreria `pafy`.

<!--Per informazioni legate all'implementazione del progetto consulare la documentazione nella directory `doc`. -->


