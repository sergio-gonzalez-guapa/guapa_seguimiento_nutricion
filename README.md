# Aplicativo web Agrícola Guapa

Este aplicativo web construido en Dash permite visualizar información relevante para monitorear el estado del cultivo, especialmente en lo que corresponde a aplicaciones. La estructura principal consta de los siguientes elementos:

-app.py -> Crea el servidor y aloja funciones compartidas de Dash

-index.py -> Define el layout y sus callbacks, así como la ejecución del servidor creado en app.py

-apps -> Aloja los scripts correspondientes a las distintas funcionalidades de la aplicación. En este proyecto se definió que cada script asociado a una funcionalidad incluye tanto la definición de su layout como los callbacks de sus funciones específicas

## Funcionalidades

- /home: En la página principal está previsto tener un listado de novedades del aplicativo para informar sobre las últimas actualizaciones que ha recibido.

- /estado-bloques: En esta funcionalidad se busca dar inicio a la exploración de grupos y bloques a través de su búsqueda preliminar por lote. Si bien hasta la fecha las aplicaciones preforza se realizan en el lote completo, el objetivo de la aplicación es hacer seguimiento a nivel de grupos y llegar hasta el detalle de bloque, ya que el lote solo debe usarse como referencia espacial. 




