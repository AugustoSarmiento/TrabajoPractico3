from abc import ABC, abstractmethod 

class MonticuloBinario(ABC):
    def __init__(self):
        self.__lista_monticulo = [0] #Para que la raíz sea el índice 1no 
        self.__tamano_actual = 0  #Se podría usar lista_monticulo.ñen() - 1 pero implica hacer un getter

    @abstractmethod
    def _comparar(self, a, b) -> bool:
        pass

    def __infiltrar_arriba(self, i: int):
        padre_idx = i // 2
        while padre_idx > 0:
            # Llama al método de comparación de la subclase
            if self._comparar(self.__lista_monticulo[i], self.__lista_monticulo[padre_idx]):
                self.__lista_monticulo[i], self.__lista_monticulo[padre_idx] = \
                    self.__lista_monticulo[padre_idx], self.__lista_monticulo[i]
            else:
                break
            i = padre_idx
            padre_idx = i // 2

    def __infiltrar_abajo(self, i: int):
        while (i * 2) <= self.__tamano_actual:
            hijo_idx = self.__obtener_hijo_prioritario(i)
            
            # Llama al método de comparación de la subclase
            if self._comparar(self.__lista_monticulo[i], self.__lista_monticulo[hijo_idx]):
                break
            
            self.__lista_monticulo[i], self.__lista_monticulo[hijo_idx] = \
                self.__lista_monticulo[hijo_idx], self.__lista_monticulo[i]
            i = hijo_idx

    def __obtener_hijo_prioritario(self, i: int) -> int:
        hijo_izq_idx = i * 2
        hijo_der_idx = i * 2 + 1

        if hijo_der_idx > self.__tamano_actual:
            return hijo_izq_idx
        else:
            # Llama al método de comparación de la subclase
            if self._comparar(self.__lista_monticulo[hijo_izq_idx], self.__lista_monticulo[hijo_der_idx]):
                return hijo_izq_idx
            else:
                return hijo_der_idx

    def insertar(self, valor):
        self.__lista_monticulo.append(valor)
        self.__tamano_actual += 1
        self.__infiltrar_arriba(self.__tamano_actual)

    def eliminar_raiz(self):
        if self.esta_vacio():
            return None
        
        raiz = self.__lista_monticulo[1]
        self.__lista_monticulo[1] = self.__lista_monticulo[self.__tamano_actual]
        self.__tamano_actual -= 1
        self.__lista_monticulo.pop()
        self.__infiltrar_abajo(1)
        return raiz

    def obtener_raiz(self):
        return self.__lista_monticulo[1] if not self.esta_vacio() else None

    def tamano(self) -> int:
        return self.__tamano_actual

    def esta_vacio(self) -> bool:
        return self.__tamano_actual == 0


class MonticuloMinimos(MonticuloBinario):
    def _comparar(self, a, b) -> bool:
        # La raíz es el MÍNIMO
        return a < b

class MonticuloMaximos(MonticuloBinario):
    def _comparar(self, a, b) -> bool:
        # La raíz es el MÁXIMO
        return a > b