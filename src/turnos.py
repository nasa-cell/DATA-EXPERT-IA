"""Turnos para los procesos largos (entrenar, «Procesar varios»): solo unos pocos a la vez, para
que la computadora no se ponga lenta, y los demás esperan en fila por orden de llegada."""

import collections
import threading


class TurnoJusto:
    """Como un semáforo, pero por orden de llegada y con la cantidad de cupos ajustable mientras
    la aplicación está abierta (3 o 6 a la vez, lo elige la persona)."""

    def __init__(self, cupos: int):
        self._cupos = cupos
        self._ocupados = 0
        self._fila = collections.deque()
        self._condicion = threading.Condition()

    @property
    def cupos(self) -> int:
        return self._cupos

    def cambiar_cupos(self, cupos: int):
        """Si se agrandan, los que esperaban empiezan enseguida; si se achican, los que ya
        corren terminan y los nuevos esperan hasta que haya lugar."""
        with self._condicion:
            self._cupos = cupos
            self._condicion.notify_all()

    def __enter__(self):
        with self._condicion:
            yo = object()
            self._fila.append(yo)
            self._condicion.wait_for(lambda: self._ocupados < self._cupos and self._fila[0] is yo)
            self._fila.popleft()
            self._ocupados += 1
            self._condicion.notify_all()   # si queda otro lugar, el siguiente de la fila también pasa
        return self

    def __exit__(self, *error):
        with self._condicion:
            self._ocupados -= 1
            self._condicion.notify_all()
