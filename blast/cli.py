"""identity-blast-radius — el radio de impacto de UNA identidad de Entra ID.

  python -m blast.cli --demo                       # identidad de ejemplo
  python -m blast.cli --live ana@contoso.com       # una cuenta real (solo lectura)
  python -m blast.cli --demo --json informe.json

Responde: si phishean a esta persona, ¿qué alcanza el atacante? Código de salida 1
si la severidad del radio es 'alto' o 'critico'.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from blast.analyze import Catalogo, analizar
from blast.config import cargar
from blast.report import console


def _recolectar(cfg, upn: str) -> dict:
    if cfg.es_demo:
        from blast.demo import demo_data
        return demo_data.identidad()
    from blast.collect import recolectar
    from blast.graph import GraphClient
    g = GraphClient(cfg.tenant_id, cfg.client_id, cfg.client_secret)
    return recolectar(g, upn)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Radio de impacto de una identidad (solo lectura)")
    p.add_argument("upn", nargs="?", help="UPN de la cuenta (en --live)")
    p.add_argument("--live", action="store_true", help="Consultar el tenant real")
    p.add_argument("--demo", action="store_true", help="Usar la identidad de ejemplo")
    p.add_argument("--json", type=Path)
    p.add_argument("--sin-color", action="store_true")
    args = p.parse_args(argv)

    cfg = cargar(modo="live" if args.live else "demo")
    if not cfg.es_demo and not args.upn:
        print("En --live hay que indicar el UPN de la cuenta.", file=sys.stderr)
        return 2

    datos = _recolectar(cfg, args.upn or "")
    a = analizar(datos, Catalogo())

    if args.json:
        args.json.write_text(json.dumps(a, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Informe escrito: {args.json}", file=sys.stderr)
    else:
        print(console.render(a, demo=cfg.es_demo, color=not args.sin_color))

    return 1 if a["severidad"] in ("alto", "critico") else 0


if __name__ == "__main__":
    raise SystemExit(main())
