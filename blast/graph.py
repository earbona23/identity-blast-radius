"""Cliente mínimo de Microsoft Graph — SOLO LECTURA.

GARANTÍA CENTRAL
Este módulo expone ÚNICAMENTE `get()` y `get_all()`. No hay `post`, `patch`, `put`
ni `delete`. Es imposible que el resto del código escriba en el tenant a través de
acá, y `tests/test_readonly_guarantee.py` verifica que nadie agregue esos verbos.

Autenticación por client credentials (app-only). Maneja la paginación de Graph
(`@odata.nextLink`) y el throttling (HTTP 429) con backoff exponencial.
"""
from __future__ import annotations

import time
from collections.abc import Iterator

import requests

GRAPH = "https://graph.microsoft.com/v1.0"
_AUTORIDAD = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"


class GraphError(RuntimeError):
    pass


class GraphClient:
    """Cliente app-only de solo lectura. Un token, reutilizado hasta que expira."""

    def __init__(self, tenant_id: str, client_id: str, client_secret: str) -> None:
        self._tenant = tenant_id
        self._cid = client_id
        self._secret = client_secret
        self._token = ""
        self._expira = 0.0

    def _asegurar_token(self) -> str:
        if self._token and time.monotonic() < self._expira - 60:
            return self._token
        r = requests.post(
            _AUTORIDAD.format(tenant=self._tenant),
            data={
                "client_id": self._cid,
                "client_secret": self._secret,
                "grant_type": "client_credentials",
                "scope": "https://graph.microsoft.com/.default",
            },
            timeout=30,
        )
        if r.status_code == 401:
            raise GraphError("Credenciales rechazadas: revisá tenant/client/secret.")
        if not r.ok:
            raise GraphError(f"No se pudo obtener el token ({r.status_code}): {r.text[:200]}")
        cuerpo = r.json()
        self._token = cuerpo["access_token"]
        self._expira = time.monotonic() + int(cuerpo.get("expires_in", 3600))
        return self._token

    def get(self, ruta: str, params: dict | None = None) -> dict:
        """Un GET a Graph, con reintento ante throttling. NUNCA escribe."""
        url = ruta if ruta.startswith("http") else f"{GRAPH}{ruta}"
        for intento in range(5):
            r = requests.get(
                url,
                headers={"Authorization": f"Bearer {self._asegurar_token()}"},
                params=params,
                timeout=30,
            )
            if r.status_code == 429:  # throttling: respetar Retry-After
                espera = int(r.headers.get("Retry-After", 2 ** intento))
                time.sleep(min(espera, 30))
                continue
            if r.status_code == 403:
                raise GraphError(
                    f"Permiso denegado en {ruta}. Falta un scope de Graph "
                    "(ver README) o el consentimiento de administrador."
                )
            if not r.ok:
                raise GraphError(f"Graph {r.status_code} en {ruta}: {r.text[:200]}")
            return r.json()
        raise GraphError(f"Throttling persistente en {ruta} tras varios reintentos.")

    def get_all(self, ruta: str, params: dict | None = None) -> Iterator[dict]:
        """Itera TODAS las páginas de una colección (@odata.nextLink)."""
        pagina = self.get(ruta, params)
        while True:
            yield from pagina.get("value", [])
            siguiente = pagina.get("@odata.nextLink")
            if not siguiente:
                return
            pagina = self.get(siguiente)
