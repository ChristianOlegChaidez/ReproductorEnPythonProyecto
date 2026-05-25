from Cancion import Cancion
from Etiqueta import Etiqueta

class CancionEtiqueta(Cancion, Etiqueta):
    def __init__(self, titulo, artista, duracion, ruta, etiqueta, genero):
        Cancion.__init__(self, titulo, artista, duracion, ruta)
        Etiqueta.__init__(self, etiqueta, genero)