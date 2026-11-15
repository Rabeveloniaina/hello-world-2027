#!/usr/bin/env python3
"""
scripts/validate_dates.py
Validation stricte des dates de contribution pour HELLO WORLD! 2027.

Vérifie :
1. Validité du format JSON et présence des métadonnées (year, timezone, dates).
2. Année civile stricte (2027) et fuseau horaire (Indian/Antananarivo).
3. Validité calendaire réelle de chaque date (format ISO YYYY-MM-DD).
4. Absence absolue de doublons.
5. Tri chronologique strict.
6. Correspondance exacte 1:1 avec les pixels actifs de la matrice HELLO WORLD!.
7. Bornes du calendrier GitHub (53 colonnes, 7 lignes).
8. Centrage horizontal et vertical.
"""

import argparse
import datetime
import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Matrice de police 3x5 de référence
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


def build_pattern() -> List[List[str]]:
    pattern: List[List[str]] = []
    # HELLO
    for idx, ch in enumerate('HELLO'):
        for c in range(3):
            pattern.append([FONT_3x5[ch][r][c] for r in range(5)])
        if idx < 4:
            pattern.append(['.'] * 5)
    # Espace mots (3 colonnes)
    for _ in range(3):
        pattern.append(['.'] * 5)
    # WORLD!
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

    # 1. Vérification des métadonnées
    if data.get("year") != 2027:
        errors.append(f"L'année spécifiée doit être 2027 (reçu : {data.get('year')})")

    tz = data.get("timezone")
    if tz != "Indian/Antananarivo":
        errors.append(f"Le fuseau horaire doit être 'Indian/Antananarivo' (reçu : {tz})")

    raw_dates = data.get("dates")
    if not isinstance(raw_dates, list):
        errors.append("'dates' doit être une liste de chaînes de caractères.")
        print("\n".join(f"[X] {err}" for err in errors))
        return False

    print(f"[*] Nombre de dates fournies : {len(raw_dates)}")

    # 2. Vérification des formats et validité calendaire
    parsed_dates: List[datetime.date] = []
    seen: Set[str] = set()
    duplicates: List[str] = []

    for d_str in raw_dates:
        if d_str in seen:
            duplicates.append(d_str)
        seen.add(d_str)

        try:
            dt = datetime.date.fromisoformat(d_str)
            if dt.year != 2027:
                errors.append(f"Date hors de l'année 2027 : {d_str}")
            parsed_dates.append(dt)
        except Exception:
            errors.append(f"Format de date invalide (attendu YYYY-MM-DD) : '{d_str}'")

    if duplicates:
        errors.append(f"Doublons détectés ({len(duplicates)}) : {duplicates[:5]}...")

    # 3. Vérification du tri
    if parsed_dates != sorted(parsed_dates):
        errors.append("Les dates ne sont pas triées dans l'ordre chronologique strict.")

    # 4. Projection sur le calendrier GitHub 2027
    start_sunday = datetime.date(2026, 12, 27)  # Dimanche semaine 0
    end_saturday = datetime.date(2028, 1, 1)    # Samedi semaine 52
    total_cols = (end_saturday - start_sunday).days // 7 + 1  # 53 colonnes

    cols_used: Set[int] = set()
    rows_used: Set[int] = set()
    coords: Set[Tuple[int, int]] = set()

    for dt in parsed_dates:
        days_diff = (dt - start_sunday).days
        col = days_diff // 7
        row = days_diff % 7
        cols_used.add(col)
        rows_used.add(row)
        coords.add((col, row))

        if col < 0 or col >= total_cols:
            errors.append(f"La date {dt} déborde de la grille GitHub (colonne {col} sur {total_cols})")

    # 5. Comparaison avec la matrice théorique
    pattern = build_pattern()
    pattern_width = len(pattern)  # 43
    theoretical_pixels = sum(col.count('#') for col in pattern)

    print(f"[*] Pixels actifs théoriques dans la police 3x5 : {theoretical_pixels}")
    print(f"[*] Pixels actifs dans le fichier JSON         : {len(coords)}")

    if len(coords) != theoretical_pixels:
        errors.append(
            f"Le nombre de dates ({len(coords)}) ne correspond pas au total de pixels du motif ({theoretical_pixels})."
        )

    # 6. Détection du cadrage et centrage
    if cols_used and rows_used:
        min_col, max_col = min(cols_used), max(cols_used)
        min_row, max_row = min(rows_used), max(rows_used)

        left_margin = min_col
        right_margin = (total_cols - 1) - max_col
        width = max_col - min_col + 1

        top_margin = min_row
        bottom_margin = 6 - max_row
        height = max_row - min_row + 1

        print(f"[*] Dimensions du dessin : Largeur = {width} colonnes, Hauteur = {height} lignes")
        print(f"[*] Centrage horizontal  : Marge gauche = {left_margin} sem., Marge droite = {right_margin} sem. (Total = {total_cols})")
        print(f"[*] Centrage vertical    : Marge haut = {top_margin} jour(s), Marge bas = {bottom_margin} jour(s) (Total = 7)")

        if left_margin == right_margin:
            print("[✓] Centrage horizontal parfait (symétrie 5 / 5 colonnes).")
        else:
            warnings.append(f"Centrage horizontal asymétrique ({left_margin} vs {right_margin}).")

        if top_margin == bottom_margin:
            print(f"[✓] Centrage vertical parfait ({top_margin} jour au-dessus, {bottom_margin} jour en-dessous).")
        else:
            warnings.append(
                f"Centrage vertical non symétrique : Marge haut = {top_margin} jour(s), Marge bas = {bottom_margin} jour(s)."
            )

        # Vérification pixel par pixel de la correspondance au motif
        matched_pixels = 0
        for c_idx in range(pattern_width):
            c_abs = min_col + c_idx
            for r_idx in range(5):
                if pattern[c_idx][r_idx] == '#':
                    r_abs = min_row + r_idx
                    if (c_abs, r_abs) in coords:
                        matched_pixels += 1
                    else:
                        errors.append(f"Pixel manquant aux coordonnées col={c_abs}, row={r_abs}")

        print(f"[*] Correspondance pixel art : {matched_pixels}/{theoretical_pixels} pixels conformes.")

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
    parser = argparse.ArgumentParser(description="Validation stricte des dates du pixel art 2027.")
    parser.add_argument(
        "--data-file",
        type=str,
        default="data/dates.json",
        help="Chemin vers le fichier dates.json à valider (par défaut : data/dates.json)"
    )
    args = parser.parse_args()

    success = validate_dates_file(Path(args.data_file))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
