"""Identidad DEMO sintética: una cuenta que parece inofensiva por su título pero cuyo
radio de impacto es enorme. Datos INVENTADOS, deterministas.

El caso es el que hace valer la herramienta: 'Ana Gómez', analista de marketing —un
título de bajo perfil—, resulta que:
  · es ELEGIBLE (PIM) para User Administrator,
  · POSEE una app de reportes con Mail.Read (aplicación) ⇒ puede leer TODO el correo
    agregándole una credencial,
  · es miembro de un grupo ASIGNABLE A ROL que otorga Helpdesk Administrator,
  · posee un grupo cuya membresía puede alterar.
Phishearla a ella da mucho más que su cargo sugiere. Ese es el punto.
"""
from __future__ import annotations


def identidad() -> dict:
    return {
        "usuario": "ana.gomez@contoso.com",
        "nombre": "Ana Gómez",
        "titulo": "Analista de Marketing",
        "roles_activos": ["Directory Readers"],
        "roles_elegibles": ["User Administrator"],
        "grupos": [
            {"nombre": "Todos los empleados", "role_assignable": False},
            {"nombre": "Marketing", "role_assignable": False},
            {"nombre": "Soporte Nivel 1 (rol)", "role_assignable": True},
        ],
        "grupos_propios": ["Campañas 2026"],
        "apps_propias": [
            {"nombre": "Reporting Sync", "permisos": ["Mail.Read", "User.Read.All"]},
        ],
    }
