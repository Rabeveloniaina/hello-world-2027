#!/usr/bin/env python3
"""
scripts/preview_pixel_art.py
Visualisation du pixel art HELLO WORLD! pour le calendrier GitHub 2027.

Génère :
1. Une représentation textuelle (ASCII) dans le terminal.
2. Une image PNG fidèle au rendu du GitHub Contribution Graph (thème sombre GitHub).
"""

import argparse
import datetime
import json
from pathlib import Path
from typing import Dict, List, Tuple

# Police compacte 3x5 pour chaque caractère
FONT_3x5: Dict[str, List[str]] = {
    'H': [
        '#.#',
        '#.#',
        '###',
        '#.#',
        '#.#'
    ],
    'E': [
        '###',
        '#..',
        '##.',
        '#..',
        '###'
    ],
    'L': [
        '#..',
        '#..',
        '#..',
        '#..',
        '###'
    ],
    'O': [
        '###',
        '#.#',
        '#.#',
        '#.#',
        '###'
    ],
    'W': [
        '#.#',
        '#.#',
        '#.#',
        '###',
        '#.#'
    ],
    'R': [
        '##.',
        '#.#',
        '##.',
        '#.#',
        '#.#'
    ],
    'D': [
        '##.',
        '#.#',
        '#.#',
        '#.#',
        '##.'
    ],
    '!': [
        '#',
        '#',
        '#',
        '.',
        '#'
    ]
}


def build_pattern() -> List[List[str]]:
    """
    Construit la matrice de colonnes pour 'HELLO WORLD!' (hauteur 5 pixels, largeur 43 colonnes).
    - Espacement inter-lettres : 1 colonne vide.
    - Espacement entre 'HELLO' et 'WORLD!' : 3 colonnes vides.
    """
    pattern: List[List[str]] = []

    # Mot 'HELLO'
    for idx, ch in enumerate('HELLO'):
        for c in range(3):
            pattern.append([FONT_3x5[ch][r][c] for r in range(5)])
        if idx < 4:
            pattern.append(['.'] * 5)

    # Espace entre les deux mots (3 colonnes)
    for _ in range(3):
        pattern.append(['.'] * 5)

    # Mot 'WORLD!'
    chars = ['W', 'O', 'R', 'L', 'D', '!']
    for idx, ch in enumerate(chars):
        w = len(FONT_3x5[ch][0])
        for c in range(w):
            pattern.append([FONT_3x5[ch][r][c] for r in range(5)])
        if idx < len(chars) - 1:
            pattern.append(['.'] * 5)

    return pattern


def build_calendar_grid(
    row_offset: int = 1,
    col_offset: int = 5,
    year: int = 2027
) -> Tuple[List[List[str]], List[datetime.date]]:
    """
    Projette le motif de pixel art sur la grille complète GitHub 53 colonnes x 7 lignes.
    Retourne la grille 7x53 et la liste des dates de contribution actives.
    """
    # 2027 commence le vendredi 01/01/2027
    # La colonne 0 commence le dimanche 27/12/2026
    start_sunday = datetime.date(2026, 12, 27)
    pattern = build_pattern()
    pattern_width = len(pattern)  # 43 colonnes

    # Initialiser une grille de 7 lignes x 53 colonnes
    grid = [['.' for _ in range(53)] for _ in range(7)]
    active_dates: List[datetime.date] = []

    for c_idx in range(pattern_width):
        col = col_offset + c_idx
        for r_idx in range(5):
            if pattern[c_idx][r_idx] == '#':
                row = row_offset + r_idx
                grid[row][col] = '#'
                dt = start_sunday + datetime.timedelta(days=col * 7 + row)
                active_dates.append(dt)

    return grid, sorted(active_dates)


def print_ascii_preview(grid: List[List[str]], row_offset: int, col_offset: int, active_dates: List[datetime.date]) -> None:
    """Affiche la prévisualisation textuelle du calendrier et du motif."""
    day_labels = ['Dim (Sun)', 'Lun (Mon)', 'Mar (Tue)', 'Mer (Wed)', 'Jeu (Thu)', 'Ven (Fri)', 'Sam (Sat)']
    start_sunday = datetime.date(2026, 12, 27)

    # Déterminer les étiquettes de mois sur les 53 colonnes
    month_header = [' '] * 53
    last_month = None
    for c in range(53):
        col_date = start_sunday + datetime.timedelta(days=c * 7)
        if col_date.year == 2027 and col_date.month != last_month:
            m_abbr = col_date.strftime('%b')[:3]
            for i, ch in enumerate(m_abbr):
                if c + i < 53:
                    month_header[c + i] = ch
            last_month = col_date.month

    print("=" * 80)
    print("  HELLO WORLD! 2027 — PRÉVISUALISATION DU GITHUB CONTRIBUTION GRAPH")
    print("=" * 80)
    print(f"Total contributions requises : {len(active_dates)} pixels")
    print(f"Période active : {active_dates[0]} -> {active_dates[-1]}")
    print(f"Centrage horizontal : {col_offset} semaines à gauche, {53 - (col_offset + 43)} à droite (sur 53)")
    print(f"Centrage vertical   : {row_offset} jour(s) en haut, {7 - (row_offset + 5)} jour(s) en bas (sur 7)")
    print()
    print("        " + "".join(month_header))
    print("        " + "-" * 53)

    for r in range(7):
        row_str = "".join('■' if grid[r][c] == '#' else '·' for c in range(53))
        print(f"{day_labels[r]:9s} |{row_str}|")

    print("        " + "-" * 53)
    print("Légende : [■] Jour de contribution actif (vert)   [·] Jour inactif (gris)")
    print("=" * 80)


def generate_png_preview(
    grid: List[List[str]],
    active_dates: List[datetime.date],
    output_path: Path,
    title_suffix: str = "Centré (Lundi-Vendredi)"
) -> None:
    """Génère une image PNG haute définition reproduisant fidèlement le style GitHub."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("[AVERTISSEMENT] Le module Pillow n'est pas installé. Ignore la génération du PNG.")
        print("Pour installer Pillow : pip install Pillow")
        return

    # Dimensions
    cell_size = 14
    cell_gap = 4
    cell_radius = 2

    margin_left = 60
    margin_top = 80
    margin_bottom = 60
    margin_right = 40

    cols = 53
    rows = 7

    grid_width = cols * cell_size + (cols - 1) * cell_gap
    grid_height = rows * cell_size + (rows - 1) * cell_gap

    img_width = margin_left + grid_width + margin_right
    img_height = margin_top + grid_height + margin_bottom

    # Couleurs du thème sombre GitHub
    bg_color = (13, 17, 23)        # #0d1117
    card_bg = (22, 27, 34)         # #161b22
    card_border = (48, 54, 61)     # #30363d
    cell_inactive = (22, 27, 34)   # #161b22
    cell_border_in = (33, 38, 45)  # #21262d
    cell_active = (57, 211, 83)    # #39d353 (GitHub green level 4)
    cell_active_border = (46, 160, 67) # #2ea043
    text_primary = (230, 237, 243) # #e6edf3
    text_secondary = (125, 133, 144) # #7d8590
    cell_out_of_year = (9, 13, 19) # jours hors 2027

    img = Image.new('RGB', (img_width, img_height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Chargement d'une police système ou par défaut
    try:
        font_title = ImageFont.truetype("arial.ttf", 16)
        font_sub = ImageFont.truetype("arial.ttf", 11)
        font_labels = ImageFont.truetype("arial.ttf", 10)
    except IOError:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_labels = ImageFont.load_default()

    # Titre
    title = f"HELLO WORLD! 2027 — GitHub Contribution Graph [{title_suffix}]"
    subtitle = f"101 contributions réelles • 53 semaines • Fuseau : Indian/Antananarivo (UTC+3) • Du {active_dates[0]} au {active_dates[-1]}"
    draw.text((margin_left, 20), title, fill=text_primary, font=font_title)
    draw.text((margin_left, 45), subtitle, fill=text_secondary, font=font_sub)

    # Dates du calendrier 2027
    start_sunday = datetime.date(2026, 12, 27)

    # Dessin des en-têtes de mois au-dessus de la grille
    last_month = None
    for c in range(cols):
        col_date = start_sunday + datetime.timedelta(days=c * 7)
        if col_date.year == 2027 and col_date.month != last_month:
            m_abbr = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"][col_date.month - 1]
            x_pos = margin_left + c * (cell_size + cell_gap)
            draw.text((x_pos, margin_top - 18), m_abbr, fill=text_secondary, font=font_labels)
            last_month = col_date.month

    # Dessin des étiquettes de jours à gauche (GitHub affiche Lun, Mer, Ven)
    day_labels_dict = {1: "Lun", 3: "Mer", 5: "Ven"}
    for r_idx, label in day_labels_dict.items():
        y_pos = margin_top + r_idx * (cell_size + cell_gap) + 1
        draw.text((margin_left - 30, y_pos), label, fill=text_secondary, font=font_labels)

    # Dessin des cellules
    for c in range(cols):
        for r in range(rows):
            dt = start_sunday + datetime.timedelta(days=c * 7 + r)
            x0 = margin_left + c * (cell_size + cell_gap)
            y0 = margin_top + r * (cell_size + cell_gap)
            x1 = x0 + cell_size
            y1 = y0 + cell_size

            is_active = (grid[r][c] == '#')
            is_in_2027 = (dt.year == 2027)

            if not is_in_2027:
                fill_color = cell_out_of_year
                outline_color = cell_out_of_year
            elif is_active:
                fill_color = cell_active
                outline_color = cell_active_border
            else:
                fill_color = cell_inactive
                outline_color = cell_border_in

            draw.rounded_rectangle([x0, y0, x1, y1], radius=cell_radius, fill=fill_color, outline=outline_color)

    # Légende en bas
    leg_y = margin_top + grid_height + 22
    leg_x = margin_left

    # Échantillon inactif
    draw.rounded_rectangle([leg_x, leg_y, leg_x + 12, leg_y + 12], radius=2, fill=cell_inactive, outline=cell_border_in)
    draw.text((leg_x + 18, leg_y), "Jour inactif (0 contribution)", fill=text_secondary, font=font_labels)

    # Échantillon actif
    leg_x2 = leg_x + 200
    draw.rounded_rectangle([leg_x2, leg_y, leg_x2 + 12, leg_y + 12], radius=2, fill=cell_active, outline=cell_active_border)
    draw.text((leg_x2 + 18, leg_y), f"Jour actif pixel art ({len(active_dates)} jours prévus)", fill=text_secondary, font=font_labels)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG")
    print(f"[OK] Image PNG générée avec succès : {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Prévisualisation du pixel art HELLO WORLD! 2027.")
    parser.add_argument(
        "--mode",
        choices=["centered", "proposal"],
        default="centered",
        help="Mode d'alignement vertical : 'centered' (lignes 1 à 5, centrage parfait) ou 'proposal' (lignes 0 à 4, proposition initiale)"
    )
    parser.add_argument(
        "--output-png",
        type=str,
        default="assets/calendar_preview.png",
        help="Chemin de sortie pour l'image PNG (par défaut : assets/calendar_preview.png)"
    )
    args = parser.parse_args()

    row_offset = 1 if args.mode == "centered" else 0
    title_suffix = "Centré (Lundi-Vendredi)" if args.mode == "centered" else "Proposition initiale (Dimanche-Jeudi)"

    grid, active_dates = build_calendar_grid(row_offset=row_offset, col_offset=5)
    print_ascii_preview(grid, row_offset=row_offset, col_offset=5, active_dates=active_dates)

    out_path = Path(args.output_png)
    generate_png_preview(grid, active_dates, out_path, title_suffix=title_suffix)


if __name__ == "__main__":
    main()
