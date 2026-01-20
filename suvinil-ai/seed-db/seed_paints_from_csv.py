"""
Seed do catálogo de tintas a partir de um CSV.

Uso:
  python suvinil-ai/seed-db/seed_paints_from_csv.py
  python suvinil-ai/seed-db/seed_paints_from_csv.py --csv "suvinil-ai/docs/Base_de_Dados_de_Tintas_Suvinil .csv"
  python suvinil-ai/seed-db/seed_paints_from_csv.py --dry-run

O script:
- Localiza o CSV em `suvinil-ai/docs/` (por padrão)
- Converte campos para os enums do modelo `Paint`
- Insere no banco de forma idempotente (não duplica por nome+cor+linha)
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

# Adicionar root do backend ao path (suvinil-ai/)
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy.orm import Session

from app.core.database import Base, SessionLocal, engine
from app.models.paint import Acabamento, Ambiente, Linha, Paint
from app.models.user import User


EXPECTED_HEADERS_PT = ["nome", "cor", "tipo_parede", "ambiente", "acabamento", "features", "linha"]
HEADER_ALIASES: Dict[str, str] = {
    # pt-br
    "nome": "nome",
    "cor": "cor",
    "tipo_parede": "tipo_parede",
    "ambiente": "ambiente",
    "acabamento": "acabamento",
    "features": "features",
    "linha": "linha",
    # en (fallback)
    "name": "nome",
    "color": "cor",
    "surface_type": "tipo_parede",
    "environment": "ambiente",
    "finish_type": "acabamento",
    "line": "linha",
}


def _norm(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    v = str(s).strip()
    return v if v != "" else None


def _norm_key(s: Optional[str]) -> str:
    return (_norm(s) or "").strip().lower()


def _parse_ambiente(value: Optional[str]) -> Ambiente:
    v = _norm(value) or ""
    key = _norm_key(v)
    if "interno/externo" in key or "ambos" in key or (("intern" in key) and ("extern" in key)):
        return Ambiente.INTERNO_EXTERNO
    if "extern" in key:
        return Ambiente.EXTERNO
    return Ambiente.INTERNO


def _parse_acabamento(value: Optional[str]) -> Acabamento:
    key = _norm_key(value)
    if "acet" in key or "semi" in key:
        return Acabamento.ACETINADO
    if "brilh" in key:
        return Acabamento.BRILHANTE
    return Acabamento.FOSCO


def _parse_linha(value: Optional[str]) -> Linha:
    key = _norm_key(value)
    if "prem" in key:
        return Linha.PREMIUM
    return Linha.STANDARD


def _pick_default_csv_path(docs_dir: Path) -> Path:
    candidates = sorted(docs_dir.glob("*.csv"))
    preferred = [p for p in candidates if "Base_de_Dados_de_Tintas_Suvinil" in p.name]
    picked = (preferred[0] if preferred else (candidates[0] if candidates else None))
    if not picked:
        raise FileNotFoundError(f"Nenhum CSV encontrado em {docs_dir}")
    return picked


def _sniff_dialect(sample: str) -> csv.Dialect:
    sniffer = csv.Sniffer()
    try:
        return sniffer.sniff(sample, delimiters=[",", ";", "\t", "|"])
    except Exception:
        return csv.get_dialect("excel")


def _read_rows(csv_path: Path) -> Tuple[List[str], List[Dict[str, Optional[str]]]]:
    raw = csv_path.read_text(encoding="utf-8-sig", errors="replace")
    sample = raw[:4096]
    dialect = _sniff_dialect(sample)
    reader = csv.DictReader(raw.splitlines(), dialect=dialect)

    if reader.fieldnames is None:
        raise ValueError(f"CSV sem cabeçalho: {csv_path}")

    headers = [h.strip() for h in reader.fieldnames if h is not None]
    rows: List[Dict[str, Optional[str]]] = []
    for r in reader:
        normalized: Dict[str, Optional[str]] = {}
        for k, v in r.items():
            if k is None:
                continue
            key = k.strip()
            mapped = HEADER_ALIASES.get(key, HEADER_ALIASES.get(key.lower()))
            if not mapped:
                continue
            normalized[mapped] = _norm(v)
        rows.append(normalized)
    return headers, rows


def load_tintas_from_csv(csv_path: Path) -> List[dict]:
    headers, rows = _read_rows(csv_path)

    # Validação leve de cabeçalho (aceita aliases)
    mapped_headers = {HEADER_ALIASES.get(h, HEADER_ALIASES.get(h.lower(), h.lower())) for h in headers}
    missing = [h for h in EXPECTED_HEADERS_PT if h not in mapped_headers]
    if missing:
        raise ValueError(
            f"CSV não tem as colunas esperadas. Faltando: {missing}. "
            f"Encontrado: {headers}"
        )

    tintas: List[dict] = []
    for idx, row in enumerate(rows, 2):  # linha 1 é cabeçalho
        nome = _norm(row.get("nome"))
        if not nome:
            continue
        tinta = {
            "nome": nome,
            "cor": _norm(row.get("cor")),
            "tipo_parede": _norm(row.get("tipo_parede")),
            "ambiente": _parse_ambiente(row.get("ambiente")),
            "acabamento": _parse_acabamento(row.get("acabamento")),
            "features": _norm(row.get("features")),
            "linha": _parse_linha(row.get("linha")),
        }
        tintas.append(tinta)

    return tintas


@dataclass(frozen=True)
class SeedResult:
    inserted: int
    skipped: int
    updated: int


def seed_paints(
    db: Session,
    tintas: Iterable[dict],
    *,
    created_by_username: str = "admin",
    dry_run: bool = False,
    truncate: bool = False,
    update_existing: bool = False,
) -> SeedResult:
    admin_user = db.query(User).filter(User.username == created_by_username).first()
    admin_id = admin_user.id if admin_user else None

    if truncate and not dry_run:
        db.query(Paint).delete()
        db.commit()

    inserted = 0
    skipped = 0
    updated = 0

    for data in tintas:
        # chave idempotente simples (ajuste se necessário)
        existing = (
            db.query(Paint)
            .filter(
                Paint.nome == data["nome"],
                Paint.cor == data.get("cor"),
                Paint.linha == data["linha"],
            )
            .first()
        )

        if existing:
            if update_existing and not dry_run:
                for k, v in data.items():
                    setattr(existing, k, v)
                existing.is_active = True
                updated += 1
            else:
                skipped += 1
            continue

        if dry_run:
            inserted += 1
            continue

        paint = Paint(
            **data,
            is_active=True,
            created_by=admin_id,
        )
        db.add(paint)
        inserted += 1

    if not dry_run:
        db.commit()

    return SeedResult(inserted=inserted, skipped=skipped, updated=updated)


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed do catálogo de tintas a partir de CSV")
    parser.add_argument(
        "--csv",
        dest="csv_path",
        type=str,
        default=None,
        help="Caminho do CSV (default: primeiro *.csv em suvinil-ai/docs/)",
    )
    parser.add_argument(
        "--created-by-username",
        type=str,
        default="admin",
        help="Usuário que será usado no campo created_by (default: admin)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Não escreve no banco, só calcula inserts")
    parser.add_argument("--truncate", action="store_true", help="Apaga a tabela de tintas antes de inserir")
    parser.add_argument(
        "--update-existing",
        action="store_true",
        help="Atualiza registros existentes (pela chave nome+cor+linha) em vez de pular",
    )

    args = parser.parse_args()

    docs_dir = BACKEND_ROOT / "docs"
    csv_path = Path(args.csv_path) if args.csv_path else _pick_default_csv_path(docs_dir)
    if not csv_path.is_absolute():
        # Resolve relativo à raiz do repositório (padrão mais previsível)
        repo_root = BACKEND_ROOT.parent
        csv_path = (repo_root / csv_path).resolve()

    print("=" * 60)
    print("   SUVINIL AI - Seed do Catálogo (CSV)")
    print("=" * 60)
    print(f"\nCSV: {csv_path}")

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV não encontrado: {csv_path}")

    # Garante tabelas (útil em ambiente novo/dev)
    Base.metadata.create_all(bind=engine)

    tintas = load_tintas_from_csv(csv_path)
    print(f"Linhas válidas carregadas: {len(tintas)}")

    db = SessionLocal()
    try:
        result = seed_paints(
            db,
            tintas,
            created_by_username=args.created_by_username,
            dry_run=args.dry_run,
            truncate=args.truncate,
            update_existing=args.update_existing,
        )
        print("\nResultado:")
        if args.dry_run:
            print(f"- Inseriria: {result.inserted}")
            print(f"- Pularia:  {result.skipped}")
            print(f"- Atualizaria: {result.updated} (somente com --update-existing)")
        else:
            print(f"- Inseridos: {result.inserted}")
            print(f"- Pulados:   {result.skipped}")
            print(f"- Atualizados: {result.updated}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())

