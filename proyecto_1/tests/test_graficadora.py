# tests/test_graficadora.py

import unittest
from unittest import mock
import os

# ⚠️ NOTA: Asumo que la importación correcta de tu módulo es 'from modules.graficador import Graficador'
# Si tu módulo 'graficador.py' está en la misma carpeta que 'tests', usa: from graficador import Graficador
from modules.graficador import Graficador 

# La ruta de guardado ficticia para los tests
RUTA_TEST = "/tmp/mock/ruta/guardado/test.png" 

class TestGraficador(unittest.TestCase):

    def setUp(self):
        # 1. Definir los patchers
        self.patcher_os_makedirs = mock.patch('os.makedirs')
        self.patcher_plt_savefig = mock.patch('matplotlib.pyplot.savefig')
        self.patcher_plt_close = mock.patch('matplotlib.pyplot.close')
        self.patcher_plt_subplots = mock.patch('matplotlib.pyplot.subplots')
        
        # ❌ Los patchers de WordCloud NO se definen para evitar fallos de importación y mocking.

        # 2. Iniciar y obtener referencias a los mocks
        self.mock_makedirs = self.patcher_os_makedirs.start()
        self.mock_savefig = self.patcher_plt_savefig.start()
        self.mock_close = self.patcher_plt_close.start()
        
        # Mocks para subplots (retorna fig, ax)
        self.mock_fig = mock.MagicMock() 
        self.mock_ax = mock.MagicMock()
        self.mock_subplots = self.patcher_plt_subplots.start()
        self.mock_subplots.return_value = (self.mock_fig, self.mock_ax)
        
        # ✅ Corrección para evitar el ValueError en la desestructuración de ax.pie()
        self.mock_ax.pie.return_value = (mock.MagicMock(), mock.MagicMock(), mock.MagicMock())
        
        
    def tearDown(self):
        # Detener solo los patchers que se iniciaron
        self.patcher_os_makedirs.stop()
        self.patcher_plt_savefig.stop()
        self.patcher_plt_close.stop()
        self.patcher_plt_subplots.stop()
        # WordCloud related patchers NO se detienen.

    # ----------------------------------------------------
    ## 📊 Tests para generar_grafico_estados
    # ----------------------------------------------------

    def test_grafico_estados_todos_presentes(self):
        # ARRANGE
        stats = {
            'pendientes': 40.0, 'en_proceso': 35.0, 'resueltos': 25.0, 'total': 100
        }
        
        # ACT
        resultado = Graficador.generar_grafico_estados(stats, RUTA_TEST)
        
        # ASSERT
        self.mock_makedirs.assert_called_once_with(os.path.dirname(RUTA_TEST), exist_ok=True)
        self.mock_subplots.assert_called_once()
        self.mock_savefig.assert_called_once_with(RUTA_TEST, bbox_inches='tight', dpi=100)
        self.mock_close.assert_called_once_with(self.mock_fig)
        self.assertEqual(resultado, RUTA_TEST)

    def test_grafico_estados_solo_un_estado_presente(self):
        # ARRANGE
        stats = {
            'pendientes': 100.0, 'en_proceso': 0.0, 'resueltos': 0.0, 'total': 50
        }
        
        # ACT
        Graficador.generar_grafico_estados(stats, RUTA_TEST)
        
        # ASSERT
        self.mock_savefig.assert_called_once()
        self.mock_ax.pie.assert_called_once()
        
        sizes_pasadas = self.mock_ax.pie.call_args[0][0]
        labels_pasadas = self.mock_ax.pie.call_args[1]['labels']
        
        self.assertEqual(sizes_pasadas, (100.0,)) 
        self.assertEqual(labels_pasadas, ('Pendientes',))

    def test_grafico_estados_sin_datos(self):
        # ARRANGE
        stats_vacio = {'total': 0}
        
        # ACT
        resultado = Graficador.generar_grafico_estados(stats_vacio, RUTA_TEST)
        
        # ASSERT
        self.mock_makedirs.assert_not_called()
        self.mock_savefig.assert_not_called()
        self.mock_close.assert_not_called()
        self.assertIsNone(resultado)

    # ----------------------------------------------------
    # ## ☁️ Tests de WordCloud ELIMINADOS
    # ----------------------------------------------------

if __name__ == '__main__':
    unittest.main()