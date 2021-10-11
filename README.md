# Vehicles Tracking

Il progetto può essere eseguito dal file`main.py`, in cui verranno mostrate 
le view di interesse (video per il tracking, maschere e tabella). Per iniziare 
il tracciamento è necessario cliccare il pulsante _space_ (barra spaziatrice) della tastiera.

All'interno del _main_ possono essere settati i seguenti parametri:
- `video_url`: è una stringa ed indica l’URL del video di youtube o il suo percorso locale della 
               città specificata. Per cambiare il _path_, aprire il file `url.py` nella directory
               `Common` e modificare la voce _path_ della città desiderata;
  
  
- `excluded_area`: è un booleano. Se si vuole considerare solo la porzione di area di interesse 
                  per il tracciamento (creata di default per le varie città disponibili) settarlo 
                  a _true_ altrimenti impostarlo a _false_;
  

- `show_log`: è un booleano. Impostarlo a _true_ se si vuole mostrare i log a video, durante 
              l’esecuzione del progetto altrimenti impostarlo a _false_.
  
Le città disponibili sono:

- Cambridge, Market Central, MA;

Al seguente link è possibile scaricare i video delle città disponbili:
[link_video](https://drive.google.com/drive/folders/1ISbDFiZLpddMju-U-YJhSiqN1Q7djeAu?usp=sharing)

**NB**: si consiglia di utilizzare un video locale, poichè se si imposta un Url di youtube, il tracking potrebbe presentarsi a scatti 
a causa del buffering nello scaricare i pacchetti del video della libreria `pafy`.

Per informazioni legate all'implementazione del progetto consulare la documentazione nella directory `doc`.


