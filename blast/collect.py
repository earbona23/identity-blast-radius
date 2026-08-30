"""Captura, para UNA identidad, todo lo que un atacante alcanzaría si la compromete.
SOLO LECTURA vía Microsoft Graph.

No es un mapa de todo el tenant (para eso está BloodHound): es el radio de impacto de
UNA cuenta, en una sola pasada, para responder "si phishean a esta persona, ¿qué se
expone?". Se apoya en `transitiveMemberOf` (grupos y roles heredados, incluso a través
de grupos anidados) y en `ownedObjects` (lo que la cuenta puede MODIFICAR, que suele ser
el camino de escalada que nadie ve).
"""
from __future__ import annotations

from blast.graph import GraphClient, GraphError

_TIPO_ROL = "#microsoft.graph.directoryRole"
_TIPO_GRUPO = "#microsoft.graph.group"
_TIPO_APP = "#microsoft.graph.application"
_TIPO_SP = "#microsoft.graph.servicePrincipal"


def _permisos_app(g: GraphClient, app: dict) -> list[str]:
    """Permisos de aplicación (Graph) que otorga poseer esta app."""
    GRAPH_APP_ID = "00000003-0000-0000-c000-000000000000"
    nombres: list[str] = []
    # Mapa GUID->nombre desde el SP de Graph (una vez sería ideal; acá por app basta).
    try:
        sps = list(g.get_all("/servicePrincipals",
                             {"$filter": f"appId eq '{GRAPH_APP_ID}'", "$select": "appRoles"}))
    except GraphError:
        sps = []
    mapa = {}
    for sp in sps:
        for rol in sp.get("appRoles", []):
            mapa[rol["id"]] = rol.get("value", rol["id"])
    for req in app.get("requiredResourceAccess", []):
        if req.get("resourceAppId") != GRAPH_APP_ID:
            continue
        for acc in req.get("resourceAccess", []):
            if acc.get("type") == "Role":
                nombres.append(mapa.get(acc.get("id"), acc.get("id", "?")))
    return nombres


def recolectar(g: GraphClient, upn: str) -> dict:
    usuario = g.get(f"/users/{upn}", {"$select": "id,userPrincipalName,displayName,jobTitle"})
    uid = usuario["id"]

    roles_activos: list[str] = []
    grupos: list[dict] = []
    for obj in g.get_all(f"/users/{uid}/transitiveMemberOf"):
        tipo = obj.get("@odata.type", "")
        if tipo == _TIPO_ROL:
            roles_activos.append(obj.get("displayName", "?"))
        elif tipo == _TIPO_GRUPO:
            grupos.append({
                "nombre": obj.get("displayName", "?"),
                "role_assignable": bool(obj.get("isAssignableToRole")),
            })

    apps_propias: list[dict] = []
    grupos_propios: list[str] = []
    for obj in g.get_all(f"/users/{uid}/ownedObjects"):
        tipo = obj.get("@odata.type", "")
        if tipo == _TIPO_APP:
            apps_propias.append({
                "nombre": obj.get("displayName", "?"),
                "permisos": _permisos_app(g, obj),
            })
        elif tipo in (_TIPO_GRUPO,):
            grupos_propios.append(obj.get("displayName", "?"))

    roles_elegibles: list[str] = []
    try:
        for e in g.get_all("/roleManagement/directory/roleEligibilityScheduleInstances",
                          {"$filter": f"principalId eq '{uid}'", "$expand": "roleDefinition"}):
            roles_elegibles.append((e.get("roleDefinition") or {}).get("displayName", "?"))
    except GraphError:
        pass  # sin PIM o sin permiso: no afirmamos elegibilidad que no pudimos leer

    return {
        "usuario": usuario.get("userPrincipalName", upn),
        "nombre": usuario.get("displayName", ""),
        "titulo": usuario.get("jobTitle", ""),
        "roles_activos": sorted(set(roles_activos)),
        "roles_elegibles": sorted(set(roles_elegibles)),
        "grupos": grupos,
        "grupos_propios": sorted(set(grupos_propios)),
        "apps_propias": apps_propias,
    }
