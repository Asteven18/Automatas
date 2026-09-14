class Estado:
    # constructor
    def __init__(self, id_estado, es_aceptacion=False):
        self.id = id_estado
        self.esAceptacion = es_aceptacion

    # marca * si el estado es aceptado, sino en blanco
    def __repr__(self):
        marca = "(*)" if self.esAceptacion else ""
        return f"q{self.id}{marca}"
    
    #verifica que sean iguales los estados
    def __eq__(self, otro):
        return isinstance(otro, Estado) and self.id == otro.id
    
    # permite que el estado sea usado como clave en diccionarios y conjuntos
    def __hash__(self):
        return hash(self.id)
