import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html


#Clase elemento individual
class ElementoDash():



    def __init__(self,tipo,element_id, label=None,content=None):
        
        self.tipo=tipo
        self.element_id = element_id
        self.label = label
        self.content = content

        self.objeto = None
        self.elemento_base = None

        if self.tipo=="select":
            self.elemento_base =  dbc.Select(options=self.content,
                id=self.element_id)
            self.objeto = dbc.InputGroup(
            [
                dbc.InputGroupAddon(self.label, addon_type="prepend"),
                self.elemento_base
                
            ]
        )
        elif self.tipo=="table":
            self.elemento_base  = dbc.Table(self.content, bordered=True,id=self.element_id, responsive=True,style={
 'whiteSpace': 'pre-line'
 })
            self.objeto = [ html.H3(self.label),self.elemento_base]
            
        
        elif self.tipo=="graph":
            self.elemento_base = dcc.Graph(config={
        'displayModeBar': False},id=self.element_id )
            self.objeto = [html.H3(self.label),self.elemento_base]
        else:
            raise Exception(f"el tipo de elemento {tipo} no está definido")

    def encerrar_en_tarjeta(self):

        self.objeto = dbc.Card(
        dbc.CardBody(self.objeto),
        className="mt-3")

    def actualizar_contenido (self, nuevo_contenido):
        self.content = nuevo_contenido

#Clase layout de la página

class DashLayout():
    #Atributos inicializados siempre igual
    elementos = {}
    salida = html.Div()

    def __init__(self,extra_elements=[]):
        self.extra_elements = extra_elements
        #Podría pasar elementos creados por fuera de esta estructura como los filtros !!!

    def crear_elemento (self, tipo,element_id,  label=None, content=None,encerrado=True):
        nuevo_elemento = ElementoDash(tipo,element_id, label, content)
        if encerrado:
            nuevo_elemento.encerrar_en_tarjeta()
        self.elementos[element_id] = nuevo_elemento


    def actualizar_elemento(self,element_id,nuevo_contenido,nuevo_label = None):
        elemento_anterior = self.elementos[element_id]
        if nuevo_label!= None:
            elemento_anterior.label=nuevo_label

        elemento_anterior.actualizar_contenido(nuevo_contenido)
        self.elementos[element_id] = elemento_anterior
        
    def ordenar_elementos (self, orden_elementos):
        children= []
        if self.extra_elements:
            children.extend(self.extra_elements)
        #Agrega elementos extra primero
        for elemento in orden_elementos:
            if elemento in self.elementos:
                children.append(self.elementos[elemento].objeto)

        self.salida=html.Div(children)