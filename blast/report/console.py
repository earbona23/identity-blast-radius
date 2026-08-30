"""Reporte de consola: el radio de impacto de una identidad, en una pantalla."""
from __future__ import annotations

_COL = {"critico": "\033[91m", "alto": "\033[93m", "medio": "\033[96m",
        "bajo": "\033[92m", "normal": "\033[90m"}
_RESET = "\033[0m"
_DIM = "\033[90m"


def render(a: dict, demo: bool, color: bool = True) -> str:
    def c(txt, nivel):
        return f"{_COL.get(nivel, '')}{txt}{_RESET}" if color else txt

    out = []
    if demo:
        out.append("  ●  DATOS DEMO — identidad sintética, ningún tenant real  ●\n")
    titulo = f"{a['nombre']} ({a['titulo']})" if a["titulo"] else a["usuario"]
    out.append("RADIO DE IMPACTO SI SE COMPROMETE ESTA CUENTA")
    out.append("=" * 58)
    out.append(f"Cuenta    : {a['usuario']}")
    out.append(f"Identidad : {titulo}")
    out.append("Severidad : " + c(a["severidad"].upper(), a["severidad"]))
    r = a["resumen"]
    out.append(f"           {r['caminos_de_riesgo']} camino(s) de riesgo · "
               f"{r['roles_activos']} rol(es) activo(s) · {r['roles_elegibles']} elegible(s) · "
               f"{r['apps_propias']} app(s) propia(s)")
    out.append("")

    if a["caminos"]:
        out.append("LO QUE ALCANZA EL ATACANTE:")
        for cm in a["caminos"]:
            marca = c(f"[{cm['nivel']}]", cm["nivel"])
            out.append(f"  {marca:<22} {cm['via']}: {cm['detalle']}")
        out.append("")

    out.append(c("Detalle por nivel de cercanía:", _DIM))
    out.append(f"  1. Ahora mismo (roles activos): {', '.join(x['rol'] for x in a['ahora_mismo']) or '—'}")
    out.append(f"  2. A un paso (PIM/grupos-rol) : {', '.join(x['rol'] for x in a['a_un_paso']) or '—'}")
    apps = [f"{x['app']} ({', '.join(x['permisos'])})" for x in a["hereda_de_apps"]]
    out.append(f"  3. Hereda de apps que posee   : {', '.join(apps) or '—'}")
    out.append(f"  4. Grupos que puede modificar : {', '.join(a['puede_modificar']) or '—'}")
    out.append("")
    out.append("Herramienta de SOLO LECTURA. No modifica ni activa nada. Mapea UNA identidad.")
    return "\n".join(out)
