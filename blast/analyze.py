"""Calcula el radio de impacto a partir de lo recolectado para una identidad.

Organiza lo alcanzable en NIVELES, del más directo al más indirecto, porque no todo el
radio pesa igual:
  1. AHORA MISMO      — roles activos que la cuenta ya tiene.
  2. A UN PASO        — roles que puede ACTIVAR (PIM elegible) o alcanzar por ser miembro
                        de un grupo asignable a rol.
  3. HEREDA DE APPS   — permisos de aplicación que la cuenta obtiene por POSEER una app
                        (poseerla = poder agregarle credenciales = actuar como ella).
  4. PUEDE MODIFICAR  — grupos que posee y cuya membresía puede alterar.

La severidad del radio = el nivel más alto alcanzable por cualquiera de esos caminos.
"""
from __future__ import annotations

from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

CATALOGO = Path(__file__).resolve().parent.parent / "rules" / "high_value.yaml"
_ORDEN = ["normal", "bajo", "medio", "alto", "critico"]


class Catalogo:
    def __init__(self, ruta: Path | None = None) -> None:
        if yaml is None:
            raise SystemExit("Se necesita PyYAML: pip install -r requirements.txt")
        d = yaml.safe_load((ruta or CATALOGO).read_text(encoding="utf-8")) or {}
        self.roles: dict = d.get("roles", {})
        self.perms: dict = d.get("app_permissions", {})

    def nivel_rol(self, rol: str) -> str:
        return self.roles.get(rol, "normal")

    def nivel_perm(self, perm: str) -> str:
        return self.perms.get(perm, "normal")


def _peor(niveles: list[str]) -> str:
    peor = "normal"
    for n in niveles:
        if _ORDEN.index(n) > _ORDEN.index(peor):
            peor = n
    return peor


def analizar(datos: dict, cat: Catalogo) -> dict:
    niveles_alcanzados: list[str] = []
    caminos: list[dict] = []

    # 1. AHORA MISMO
    ahora = [{"rol": r, "nivel": cat.nivel_rol(r)} for r in datos["roles_activos"]]
    niveles_alcanzados += [x["nivel"] for x in ahora]
    for x in ahora:
        if x["nivel"] != "normal":
            caminos.append({"via": "rol activo", "detalle": x["rol"], "nivel": x["nivel"]})

    # 2. A UN PASO — PIM elegible + grupos asignables a rol
    elegibles = [{"rol": r, "nivel": cat.nivel_rol(r)} for r in datos["roles_elegibles"]]
    niveles_alcanzados += [x["nivel"] for x in elegibles]
    for x in elegibles:
        if x["nivel"] != "normal":
            caminos.append({"via": "puede ACTIVAR (PIM)", "detalle": x["rol"], "nivel": x["nivel"]})
    grupos_rol = [gr["nombre"] for gr in datos["grupos"] if gr.get("role_assignable")]
    for gnombre in grupos_rol:
        caminos.append({"via": "miembro de grupo asignable a rol", "detalle": gnombre, "nivel": "alto"})
        niveles_alcanzados.append("alto")

    # 3. HEREDA DE APPS
    apps = []
    for app in datos["apps_propias"]:
        peor_perm = _peor([cat.nivel_perm(p) for p in app["permisos"]]) if app["permisos"] else "normal"
        apps.append({"app": app["nombre"], "permisos": app["permisos"], "nivel": peor_perm})
        niveles_alcanzados.append(peor_perm)
        if peor_perm != "normal":
            altos = [p for p in app["permisos"] if cat.nivel_perm(p) in ("alto", "critico")]
            caminos.append({"via": "posee la app", "detalle": f"{app['nombre']} → {', '.join(altos)}",
                            "nivel": peor_perm})

    # 4. PUEDE MODIFICAR
    for gnombre in datos["grupos_propios"]:
        caminos.append({"via": "posee el grupo (puede alterar membresía)", "detalle": gnombre, "nivel": "medio"})
        niveles_alcanzados.append("medio")

    severidad = _peor(niveles_alcanzados) if niveles_alcanzados else "normal"
    orden = {"critico": 0, "alto": 1, "medio": 2, "bajo": 3, "normal": 4}
    caminos.sort(key=lambda c: orden.get(c["nivel"], 9))

    return {
        "usuario": datos["usuario"],
        "nombre": datos["nombre"],
        "titulo": datos["titulo"],
        "severidad": severidad,
        "resumen": {
            "roles_activos": len(datos["roles_activos"]),
            "roles_elegibles": len(datos["roles_elegibles"]),
            "grupos": len(datos["grupos"]),
            "apps_propias": len(datos["apps_propias"]),
            "caminos_de_riesgo": len(caminos),
        },
        "ahora_mismo": ahora,
        "a_un_paso": elegibles + [{"rol": g, "nivel": "alto", "via": "grupo asignable"} for g in grupos_rol],
        "hereda_de_apps": apps,
        "puede_modificar": datos["grupos_propios"],
        "caminos": caminos,
    }
