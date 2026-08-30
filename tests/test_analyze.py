from blast.analyze import Catalogo, analizar
from blast.demo import demo_data

CAT = Catalogo()


def test_severidad_es_el_peor_camino_alcanzable():
    a = analizar(demo_data.identidad(), CAT)
    # User Administrator (alto) elegible + Helpdesk via grupo-rol (alto) + Mail.Read (alto)
    assert a["severidad"] == "alto"


def test_app_propia_con_mail_read_es_un_camino():
    a = analizar(demo_data.identidad(), CAT)
    vias = [c["via"] for c in a["caminos"]]
    assert "posee la app" in vias
    app_camino = next(c for c in a["caminos"] if c["via"] == "posee la app")
    assert "Mail.Read" in app_camino["detalle"]


def test_grupo_asignable_a_rol_es_un_camino():
    a = analizar(demo_data.identidad(), CAT)
    assert any("grupo asignable a rol" in c["via"] for c in a["caminos"])


def test_pim_elegible_aparece_como_a_un_paso():
    a = analizar(demo_data.identidad(), CAT)
    assert any(c["via"] == "puede ACTIVAR (PIM)" for c in a["caminos"])


def test_cuenta_realmente_inofensiva_da_severidad_normal():
    datos = {"usuario": "u@x.com", "nombre": "U", "titulo": "",
             "roles_activos": [], "roles_elegibles": [],
             "grupos": [{"nombre": "Todos", "role_assignable": False}],
             "grupos_propios": [], "apps_propias": []}
    a = analizar(datos, CAT)
    assert a["severidad"] == "normal"
    assert a["resumen"]["caminos_de_riesgo"] == 0


def test_rol_no_catalogado_no_eleva_pero_se_lista():
    datos = {"usuario": "u@x.com", "nombre": "U", "titulo": "",
             "roles_activos": ["Rol Inventado"], "roles_elegibles": [],
             "grupos": [], "grupos_propios": [], "apps_propias": []}
    a = analizar(datos, CAT)
    assert a["severidad"] == "normal"
    assert a["ahora_mismo"][0]["rol"] == "Rol Inventado"
