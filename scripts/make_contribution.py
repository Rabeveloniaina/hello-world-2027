#!/usr/bin/env python3
"""
scripts/make_contribution.py
Logique de vérification et de création d'une contribution pixel art pour HELLO WORLD! 2027.

Fonctionnement :
1. Détermine la date cible (soit fournie via --date, soit la date du jour à Madagascar : Indian/Antananarivo).
2. Charge la liste des dates programmées depuis data/dates.json.
3. Vérifie si la date cible est planifiée.
4. Vérifie si une contribution a déjà été enregistrée pour cette date (idempotence).
5. En mode --dry-run : simule l'opération sans créer de fichier.
6. En mode normal : crée le fichier contributions/YYYY-MM-DD.txt et positionne les variables GitHub Actions.
"""

import argparse
import datetime
import json
import os
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

# Fuseau horaire officiel du projet (UTC+3)
PROJECT_TIMEZONE = "Indian/Antananarivo"


def set_github_output(key: str, value: str) -> None:
    """Positionne une variable de sortie pour les étapes ultérieures du workflow GitHub Actions."""
    gh_output_path = os.getenv("GITHUB_OUTPUT")
    if gh_output_path:
        try:
            with open(gh_output_path, "a", encoding="utf-8") as f:
                f.write(f"{key}={value}\n")
        except Exception as e:
            print(f"[ATTENTION] Impossible d'écrire dans GITHUB_OUTPUT: {e}")


def main():
    parser = argparse.ArgumentParser(description="Générateur de contribution HELLO WORLD! 2027.")
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Date cible au format YYYY-MM-DD (par défaut : date actuelle à Madagascar)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mode simulation : teste la logique sans créer de fichier ni modifier le dépôt"
    )
    parser.add_argument(
        "--data-file",
        type=str,
        default="data/dates.json",
        help="Chemin vers le fichier dates.json (par défaut : data/dates.json)"
    )
    parser.add_argument(
        "--contributions-dir",
        type=str,
        default="contributions",
        help="Répertoire des contributions (par défaut : contributions)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force la recréation du fichier de contribution même s'il existe déjà"
    )
    args = parser.parse_args()

    # Initialisation par défaut des sorties GitHub Actions
    set_github_output("committed", "false")
    set_github_output("reason", "unknown")

    # 1. Détermination de l'heure et date actuelles à Madagascar
    tz = ZoneInfo(PROJECT_TIMEZONE)
    now_in_tz = datetime.datetime.now(tz)
    print(f"=======================================================")
    print(f"  HELLO WORLD! 2027 — CRÉATION DE CONTRIBUTION")
    print(f"=======================================================")
    print(f"[*] Horloge locale Madagascar ({PROJECT_TIMEZONE}) : {now_in_tz.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    # 2. Détermination de la date cible
    if args.date:
        try:
            target_date = datetime.date.fromisoformat(args.date)
            is_manual_simulation = True
            print(f"[*] Mode spécifié : Date manuelle passée en argument -> {target_date}")
        except ValueError:
            print(f"[ERREUR] Format de date invalide : '{args.date}'. Format requis : YYYY-MM-DD.")
            set_github_output("reason", "invalid_date_format")
            sys.exit(1)
    else:
        target_date = now_in_tz.date()
        is_manual_simulation = False
        print(f"[*] Mode production : Utilisation de la date réelle du jour -> {target_date}")

    date_str = target_date.isoformat()
    set_github_output("contribution_date", date_str)

    # 3. Chargement des dates programmées
    data_path = Path(args.data_file)
    if not data_path.exists():
        print(f"[ERREUR] Le fichier de configuration '{data_path}' est introuvable.")
        set_github_output("reason", "missing_data_file")
        sys.exit(1)

    try:
        with open(data_path, "r", encoding="utf-8") as f:
            calendar_data = json.load(f)
    except Exception as e:
        print(f"[ERREUR] Impossible de lire '{data_path}' : {e}")
        set_github_output("reason", "json_read_error")
        sys.exit(1)

    scheduled_dates = set(calendar_data.get("dates", []))
    total_scheduled = len(scheduled_dates)
    print(f"[*] Fichier de dates chargé : {data_path} ({total_scheduled} contributions programmées au total)")

    # 4. Vérification si la date cible est programmée
    if date_str not in scheduled_dates:
        print(f"[INFO] La date {date_str} n'est PAS une date de contribution planifiée.")
        print(f"[INFO] Aucune action n'est requise. Arrêt propre du traitement.")
        set_github_output("committed", "false")
        set_github_output("reason", "not_scheduled")
        sys.exit(0)

    # Indice de la contribution parmi la liste ordonnée
    ordered_dates = sorted(list(scheduled_dates))
    contrib_index = ordered_dates.index(date_str) + 1

    print(f"[MATCH] La date {date_str} correspond au pixel actif #{contrib_index}/{total_scheduled} !")

    # 5. Vérification des doublons (existence du fichier)
    contrib_dir = Path(args.contributions_dir)
    contrib_dir.mkdir(parents=True, exist_ok=True)
    target_file = contrib_dir / f"{date_str}.txt"

    if target_file.exists() and not args.force:
        print(f"[INFO] Le fichier '{target_file}' existe déjà.")
        print(f"[INFO] Une contribution a déjà été effectuée pour cette date. Arrêt propre pour éviter les doublons.")
        set_github_output("committed", "false")
        set_github_output("reason", "already_exists")
        sys.exit(0)

    # 6. Mode DRY-RUN (simulation)
    if args.dry_run:
        print(f"[DRY-RUN] Simulation réussie : la contribution #{contrib_index} pour le {date_str} est valide.")
        print(f"[DRY-RUN] En mode réel, le fichier '{target_file}' aurait été créé et commité.")
        set_github_output("committed", "false")
        set_github_output("reason", "dry_run_success")
        sys.exit(0)

    # 7. Création réelle du fichier de contribution
    try:
        timestamp_iso = now_in_tz.isoformat()
        content = (
            f"HELLO WORLD! Pixel Art Contribution\n"
            f"Date: {date_str}\n"
            f"Project: HELLO WORLD! 2027\n"
            f"Timezone: {PROJECT_TIMEZONE}\n"
            f"Timestamp: {timestamp_iso}\n"
            f"Contribution: #{contrib_index}/{total_scheduled}\n"
            f"Mode: {'Manual trigger' if is_manual_simulation else 'Automated daily cron'}\n"
        )
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"[SUCCÈS] Fichier de contribution créé avec succès : {target_file}")
        print(f"[*] Contenu généré :\n---\n{content.strip()}\n---")
        set_github_output("committed", "true")
        set_github_output("reason", "created")
        sys.exit(0)

    except Exception as e:
        print(f"[ERREUR] Échec lors de l'écriture du fichier '{target_file}' : {e}")
        set_github_output("committed", "false")
        set_github_output("reason", "file_write_error")
        sys.exit(1)


if __name__ == "__main__":
    main()
