import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 
warnings.filterwarnings("ignore", category=ResourceWarning) 
warnings.filterwarnings("ignore", category=UserWarning)
import unittest
from modules.repositorio_abstracto import IRepositorio
from abc import ABC, abstractmethod # Reimportamos ABC solo para claridad

# La clase debe implementar explícitamente todos los métodos para ser instanciable.
# En este caso, simplemente delegamos la llamada a un objeto self.impl para aislar el test.
class RepoMalo(IRepositorio):
    """
    Clase concreta que implementa el RepositorioAbstracto para el test.
    Cada método simplemente llama a su versión en la clase padre para forzar la 
    excepción esperada (NotImplementedError).
    """
    def guardar(self, entidad):
        # Llama a la versión abstracta que lanza NotImplementedError
        return super().guardar(entidad) 

    def obtener_por_id(self, id: int):
        return super().obtener_por_id(id)

    def obtener_todos(self) -> list:
        return super().obtener_todos()

    def actualizar(self, entidad):
        return super().actualizar(entidad)

    def eliminar(self, id: int):
        return super().eliminar(id)

    def obtener_por_filtro(self, **kwargs):
        return super().obtener_por_filtro(**kwargs)

    def obtener_todos_por_filtro(self, **kwargs) -> list:
        return super().obtener_todos_por_filtro(**kwargs)


class TestIRepositorio(unittest.TestCase):
    
    def setUp(self):
        # La instanciación de RepoMalo ahora es permitida por la implementación explícita.
        self.repo = RepoMalo()

    def test_guardar_no_implementado(self):
        """Verifica que IRepositorio.guardar lance NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            self.repo.guardar(None)

    def test_obtener_por_id_no_implementado(self):
        """Verifica que IRepositorio.obtener_por_id lance NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            self.repo.obtener_por_id(1)

    def test_obtener_todos_no_implementado(self):
        """Verifica que IRepositorio.obtener_todos lance NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            self.repo.obtener_todos()

    def test_actualizar_no_implementado(self):
        """Verifica que IRepositorio.actualizar lance NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            self.repo.actualizar(None)

    def test_eliminar_no_implementado(self):
        """Verifica que IRepositorio.eliminar lance NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            self.repo.eliminar(1)
            
    def test_obtener_por_filtro_no_implementado(self):
        """Verifica que IRepositorio.obtener_por_filtro lance NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            self.repo.obtener_por_filtro(nombre="test")
            
    def test_obtener_todos_por_filtro_no_implementado(self):
        """Verifica que IRepositorio.obtener_todos_por_filtro lance NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            self.repo.obtener_todos_por_filtro(nombre="test")

if __name__ == '__main__':
    unittest.main()



#Estas pruebas determinan si se levanta el error correcto al crear una clase concreta
#que no posee los métodos que se piden.