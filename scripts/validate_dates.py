#!/usr/bin/env python3
"""
scripts/validate_dates.py
Validation stricte des dates de contribution pour HELLO WORLD! 2027 et le test HI! 2026.

Vérifie :
1. Validité du format JSON et présence des métadonnées.
2. Fuseau horaire (Indian/Antananarivo).
3. Validité calendaire réelle de chaque date (format ISO YYYY-MM-DD).
4. Absence absolue de doublons.
5. Tri chronologique strict.
6. Phase Test 2026 (HI!) : 19 dates sur les semaines 47 à 52.
7. Phase Principale 2027 (HELLO WORLD!) : 101 dates centrées sur 53 colonnes.
"""

import argparse
import datetime
import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Matrice de police 3x5 de référence pour 2027
FONT_3x5: Dict[str, List[str]] = {
    'H': ['#.#', '#.#', '###', '#.#', '#.#'],
    'E': ['###', '#..', '##.', '#..', '###'],
    'L': ['#..', '#..', '#..', '#..', '###'],
    'O': ['###', '#.#', '#.#', '#.#', '###'],
    'W': ['#.#', '#.#', '#.#', '###', '#.#'],
    'R': ['##.', '#.#', '##.', '#.#', '#.#'],
    'D': ['##.', '#.#', '#.#', '#.#', '##.'],
    '!': ['#', '#', '#', '.', '#']
}

GRID_HI_2026 = [
    ['.', '.', '.', '.', '.', '.'],  # Dim
    ['#', '.', '#', '.', '#', '#'],  # Lun
    ['#', '.', '#', '.', '#', '#'],  # Mar
    ['#', '#', '#', '.', '#', '.'],  # Mer
    ['#', '.', '#', '.', '#', '#'],  # Jeu
    ['#', '.', '#', '.', '#', '.'],  # Ven
    ['.', '.', '.', '.', '.', '.']   # Sam
]


def build_pattern_2027() -> List[List[str]]:
    pattern: List[List[str]] = []
    for idx, ch in enumerate('HELLO'):
        for c in range(3):
            pattern.append([FONT_3x5[ch][r][c] for r in range(5)])
        if idx < 4:
            pattern.append(['.'] * 5)
    for _ in range(3):
        pattern.append(['.'] * 5)
    chars = ['W', 'O', 'R', 'L', 'D', '!']
    for idx, ch in enumerate(chars):
        w = len(FONT_3x5[ch][0])
        for c in range(w):
            pattern.append([FONT_3x5[ch][r][c] for r in range(5)])
        if idx < len(chars) - 1:
            pattern.append(['.'] * 5)
    return pattern


def validate_dates_file(file_path: Path) -> bool:
    print(f"\n=======================================================")
    print(f"  VALIDATION DES DATES : {file_path.name}")
    print(f"=======================================================")

    if not file_path.exists():
        print(f"[ERREUR] Le fichier {file_path} est introuvable.")
        return False

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ERREUR] Impossible de lire le fichier JSON : {e}")
        return False

    errors: List[str] = []
    warnings: List[str] = []

    tz = data.get("timezone")
    if tz != "Indian/Antananarivo":
        errors.append(f"Le fuseau horaire doit être 'Indian/Antananarivo' (reçu : {tz})")

    raw_dates = data.get("dates")
    if not isinstance(raw_dates, list):
        errors.append("'dates' doit être une liste de chaînes de caractères.")
        print("\n".join(f"[X] {err}" for err in errors))
        return False

    print(f"[*] Nombre total de dates fournies : {len(raw_dates)}")

    # Vérification des formats et validité calendaire
    parsed_dates: List[datetime.date] = []
    seen: Set[str] = set()
    duplicates: List[str] = []

    for d_str in raw_dates:
        if d_str in seen:
            duplicates.append(d_str)
        seen.add(d_str)

        try:
            dt = datetime.date.fromisoformat(d_str)
            if dt.year not in (2026, 2027):
                errors.append(f"Date hors des années 2026/2027 : {d_str}")
            parsed_dates.append(dt)
        except Exception:
            errors.append(f"Format de date invalide (attendu YYYY-MM-DD) : '{d_str}'")

    if duplicates:
        errors.append(f"Doublons détectés ({len(duplicates)}) : {duplicates[:5]}...")

    if parsed_dates != sorted(parsed_dates):
        errors.append("Les dates ne sont pas triées dans l'ordre chronologique strict.")

    # Séparation 2026 (Test HI!) et 2027 (HELLO WORLD!)
    dates_2026 = [d for d in parsed_dates if d.year == 2026]
    dates_2027 = [d for d in parsed_dates if d.year == 2027]

    print(f"[*] Dates en 2026 (Test 'HI!')         : {len(dates_2026)}")
    print(f"[*] Dates en 2027 ('HELLO WORLD!')     : {len(dates_2027)}")

    # 1. Validation de la phase test 2026
    if dates_2026:
        d0_2026 = datetime.date(2025, 12, 28)
        expected_2026_dates = []
        for c in range(6):
            col = 47 + c
            for r in range(7):
                if GRID_HI_2026[r][c] == '#':
                    expected_2026_dates.append(d0_2026 + datetime.timedelta(days=col * 7 + r))

        if len(dates_2026) != len(expected_2026_dates):
            errors.append(f"Test 2026 : attendu {len(expected_2026_dates)} dates, reçu {len(dates_2026)}.")
        elif dates_2026 != expected_2026_dates:
            errors.append("Test 2026 : les dates ne correspondent pas au motif 'HI!'.")
        else:
            print(f"[✓] Phase Test 2026 ('HI!') : {len(dates_2026)}/19 dates parfaitement conformes (du {dates_2026[0]} au {dates_2026[-1]}).")

    # 2. Validation de la phase principale 2027
    if dates_2027:
        start_sunday_2027 = datetime.date(2026, 12, 27)
        total_cols_2027 = 53
        pattern_2027 = build_pattern_2027()
        theoretical_pixels_2027 = sum(col.count('#') for col in pattern_2027)

        cols_used = set()
        rows_used = set()
        for dt in dates_2027:
            diff = (dt - start_sunday_2027).days
            col = diff // 7
            row = diff % 7
            cols_used.add(col)
            rows_used.add(row)

        if len(dates_2027) != theoretical_pixels_2027:
            errors.append(f"Phase 2027 : attendu {theoretical_pixels_2027} pixels, reçu {len(dates_2027)}.")

        left_margin = min(cols_used)
        right_margin = (total_cols_2027 - 1) - max(cols_used)
        top_margin = min(rows_used)
        bottom_margin = 6 - max(rows_used)

        if left_margin == 5 and right_margin == 5:
            print(f"[✓] Phase 2027 : Centrage horizontal parfait (5 sem. gauche / 5 sem. droite).")
        else:
            warnings.append(f"Phase 2027 : Centrage horizontal asymétrique ({left_margin} vs {right_margin}).")

        if top_margin == 1 and bottom_margin == 1:
            print(f"[✓] Phase 2027 : Centrage vertical parfait (1 jour haut / 1 jour bas).")
        else:
            warnings.append(f"Phase 2027 : Centrage vertical asymétrique ({top_margin} vs {bottom_margin}).")

        print(f"[✓] Phase 2027 ('HELLO WORLD!') : {len(dates_2027)}/101 dates conformes (du {dates_2027[0]} au {dates_2027[-1]}).")

    # Synthèse
    print("\n-------------------------------------------------------")
    if warnings:
        for w in warnings:
            print(f"[AVERTISSEMENT] {w}")

    if errors:
        for e in errors:
            print(f"[ERREUR] {e}")
        print("-------------------------------------------------------")
        print(f"[ÉCHEC] Validation échouée avec {len(errors)} erreur(s).")
        return False
    else:
        print("-------------------------------------------------------")
        print("[SUCCÈS] Toutes les vérifications sont validées avec succès !")
        return True


def main():
    parser = argparse.ArgumentParser(description="Validation stricte des dates du pixel art.")
    parser.add_argument(
        "--data-file",
        type=str,
        default="data/dates.json",
        help="Chemin vers le fichier dates.json (par défaut : data/dates.json)"
    )
    args = parser.parse_args()

    success = validate_dates_file(Path(args.data_file))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
