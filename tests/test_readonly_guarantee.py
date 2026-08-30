"""La garantía: mapea una identidad, NUNCA escribe ni activa nada en el tenant."""
import pathlib
import re

APP = pathlib.Path(__file__).resolve().parent.parent / "blast"
PROHIBIDO = re.compile(r"requests\.(post|patch|put|delete)\s*\(", re.IGNORECASE)
PERMITIDO_TOKEN = "_AUTORIDAD.format"


def test_no_hay_escrituras_a_graph():
    ofensas = []
    for archivo in APP.rglob("*.py"):
        lineas = archivo.read_text(encoding="utf-8").splitlines()
        for i, linea in enumerate(lineas):
            if PROHIBIDO.search(linea):
                ctx = "\n".join(lineas[max(0, i - 3):i + 5])
                if PERMITIDO_TOKEN in ctx:
                    continue
                ofensas.append(f"{archivo.relative_to(APP)}:{i+1}: {linea.strip()}")
    assert not ofensas, "Escritura a Graph detectada:\n" + "\n".join(ofensas)


def test_cliente_graph_sin_escritura():
    from blast import graph
    c = graph.GraphClient("t", "c", "s")
    for verbo in ("post", "patch", "put", "delete"):
        assert not hasattr(c, verbo)
