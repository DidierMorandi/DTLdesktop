#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Traductions FR/EN pour l'interface console de DTLdesktop."""

from __future__ import annotations

import locale
import os
from typing import Any


DEFAULT_LANGUAGE = "fr"
SUPPORTED_LANGUAGES = {"fr", "en"}
_language = DEFAULT_LANGUAGE


TRANSLATIONS: dict[str, dict[str, str]] = {
    "fr": {
        "app.subtitle": "Gestionnaire de configurations du bureau Windows",
        "arg.description": "Gestionnaire de configurations du bureau Windows",
        "arg.auto": "restaure le profil reconnu",
        "arg.save": "enregistre la configuration détectée sans demander de nom",
        "arg.restore": "restaure un profil",
        "arg.apply": "applique orientation, résolution, fonds et icônes d'un profil",
        "arg.test": "simule une restauration",
        "arg.diagnose": "affiche la configuration détectée",
        "arg.lang": "langue de l'interface",
        "arg.version": "affiche le numéro de version et quitte",
        "arg.help": "affiche cette aide et quitte",
        "arg.options": "options",
        "configuration.selected": "Configuration sélectionnée : {profile}",
        "configuration.new": "Nouvelle configuration",
        "configuration.recognized": "Configuration reconnue : {profile}",
        "configuration.saved": "Configuration « {profile} » enregistrée : {icons} icône(s), {monitors} écran(s).",
        "configuration.saved_short": "Configuration « {profile} » enregistrée ({icons} icône(s)).",
        "configuration.none_compatible": "Nouvelle configuration : aucun profil compatible.",
        "language.switch_hint": "For English speaking, type 1.",
        "monitor.title": "Moniteur {index}{primary}",
        "monitor.primary": " (principal)",
        "layout": "Disposition",
        "profile": "Profil : {profile}",
        "profiles.none": "Aucun profil enregistré.",
        "profiles.invalid_choice": "Choix annulé.",
        "profile.configure": "Profil à configurer",
        "profile.compare": "Profil à comparer",
        "profile.icons_restore": "Profil dont les icônes seront restaurées",
        "profile.apply": "Profil à appliquer",
        "screen": "Écran {index}",
        "screen.configure": "Écran à configurer",
        "screen.invalid": "Configuration annulée.",
        "screen.line": "{index}. Écran {index} — {resolution} {orientation}",
        "comparison.screens": "Écrans : {status}",
        "comparison.identical": "identiques",
        "comparison.different": "différents",
        "comparison.moved_icons": "Icônes déplacées : {count}",
        "comparison.missing_icons": "Icônes absentes : {count}",
        "comparison.new_icons": "Nouvelles icônes : {count}",
        "comparison.wallpaper_differences": "Fonds d'écran incohérents : {count}",
        "comparison.restore_possible": "Restauration possible, sans modification effectuée.",
        "comparison.none": "Différence : aucune",
        "wallpaper.diagnostic": "Diagnostic des fonds d'écran",
        "wallpaper.current": "Fond :\n{name}",
        "wallpaper.ok": "✓ conforme",
        "wallpaper.bad": "⚠ fond d'écran incohérent",
        "wallpaper.expected": "Attendu :\n{name}",
        "wallpaper.observed": "Observé :\n{name}",
        "wallpaper.undefined": "(non défini)",
        "wallpaper.choose_each": "Choisissez le fond de chaque écran.",
        "wallpaper.choose_landscape": "Sélectionnez maintenant le fond paysage dans l'Explorateur Windows.",
        "wallpaper.choose_portrait": "Sélectionnez maintenant le fond portrait dans l'Explorateur Windows.",
        "wallpaper.dialog_landscape": "DTLdesktop — Fond paysage de l'écran {screen}",
        "wallpaper.dialog_portrait": "DTLdesktop — Fond portrait de l'écran {screen}",
        "wallpaper.dialog_screen": "DTLdesktop — {configuration} — Fond de l'écran {screen}",
        "wallpaper.landscape": "Fond paysage : {name}",
        "wallpaper.portrait": "Fond portrait : {name}",
        "wallpaper.keep_landscape": "Sélection annulée : le fond paysage actuel est conservé.",
        "wallpaper.keep_portrait": "Sélection annulée : le fond portrait actuel est conservé.",
        "wallpaper.rules_saved": "Règles enregistrées.",
        "wallpaper.landscape_value": "Paysage : {name}",
        "wallpaper.portrait_value": "Portrait : {name}",
        "wallpaper.screen_selected": "Écran {index} : {name}",
        "wallpaper.screen_kept": "Écran {index} : sélection annulée, fond actuel conservé.",
        "wallpaper.none_changed": "Aucun fond n'a été modifié.",
        "wallpaper.applied": "{count} fond(s) appliqué(s).",
        "wallpaper.corrected": "{count} fond(s) d'écran corrigé(s).",
        "wallpaper.save_hint": "Appuyez sur S pour enregistrer « {configuration} ».",
        "wallpaper.fix_question": "Corriger les fonds d'écran ? O/N : ",
        "menu.apply": "[A] Appliquer un profil",
        "menu.save": "[S] Sauvegarder le profil actuel",
        "menu.restore_diagnose": "[R] Restaurer les icônes  [D] Diagnostiquer",
        "menu.compare": "[C] Comparer",
        "menu.wallpapers_quit": "[F] Choisir les fonds     [H] Aide     [Q] Quitter",
        "menu.choice": "Votre choix : ",
        "menu.unknown": "Choix non reconnu.",
        "help.title": "Aide du menu",
        "help.apply": "A : applique un profil complet : orientation, disposition, fonds d'écran et positions d'icônes.",
        "help.save": "S : enregistre l'état actuel du bureau dans le profil sélectionné.",
        "help.restore": "R : restaure seulement les positions d'icônes du profil choisi.",
        "help.diagnose": "D : affiche l'état détecté et vérifie si les fonds d'écran correspondent au profil.",
        "help.compare": "C : compare le profil choisi avec l'état actuel, sans modifier le bureau.",
        "help.wallpapers": "F : choisit les images de fond à utiliser pour la configuration actuelle.",
        "help.quit": "Q : quitte DTLdesktop sans autre action.",
        "prompt.index": "{prompt} [1-{count}] : ",
        "prompt.continue": "Continuer ? O/N : ",
        "prompt.confirm_restore": "Confirmer la restauration ? O/N : ",
        "prompt.create_profile": "Voulez-vous créer un nouveau profil ? Utilisez S.",
        "simulation": "Simulation — aucune modification",
        "restore.confirmed": "{count} icône(s) restaurée(s).",
        "restore.missing": "{count} icône(s) du profil sont absentes.",
        "restore.cancelled": "Restauration annulée.",
        "apply.changes": "Le profil « {profile} » va modifier l'orientation ou la disposition de {count} écran(s).",
        "apply.running": "Application du profil en cours…",
        "apply.done": "Profil « {profile} » appliqué et vérifié.",
        "apply.summary": "{wallpapers} fond(s) et {icons} icône(s) restaurés.",
        "apply.cancelled": "Application annulée.",
        "apply.cli_done": "Profil « {profile} » appliqué : {wallpapers} fond(s), {icons} icône(s).",
        "auto.summary": "Restauration automatique : {icons} icône(s), {wallpapers} fond(s) d'écran.",
        "error": "Erreur : {error}",
        "orientation.landscape": "Paysage",
        "orientation.portrait": "Portrait",
        "orientation.square": "Carré",
        "error.empty_profile_name": "Le nom du profil est vide ou invalide.",
        "error.windows_images": "La sélection des images nécessite Windows.",
        "error.wallpapers_need_windows": "Les fonds par écran nécessitent Windows.",
        "error.wallpaper_init": "Windows n'a pas pu initialiser la gestion des fonds d'écran.",
        "error.wallpaper_unavailable": "La gestion des fonds distincts par écran n'est pas disponible.",
        "error.windows_action": "Windows n'a pas pu {action}.",
        "action.count_monitors": "compter les écrans",
        "action.identify_monitor": "identifier un écran",
        "action.read_monitor_position": "lire la position d'un écran",
        "action.read_wallpaper": "lire un fond d'écran",
        "action.apply_wallpaper": "appliquer un fond d'écran",
        "action.select_wallpaper_framing": "sélectionner le cadrage du fond d'écran",
        "action.check_wallpaper_mode": "vérifier le mode d'affichage du fond",
        "error.wallpaper_framing_kept": "Windows n'a pas conservé le cadrage demandé.",
        "error.icon_list": "Windows n'a pas permis de lire la liste des icônes.",
        "error.icon_prepare": "Impossible de préparer la lecture des icônes.",
        "error.icon_read": "Impossible de lire les informations d'une icône.",
        "error.display_mode_read": "Impossible de lire le mode d'affichage de {device}.",
        "error.display_empty": "Le profil ne contient aucun mode d'affichage.",
        "error.display_missing_id": "Un écran du profil ne possède pas d'identifiant Windows.",
        "error.display_unavailable": "L'écran {device} n'est pas disponible.",
        "error.display_refused": "Windows a refusé le mode d'affichage de {device} (code {status}).",
        "error.display_apply": "Windows n'a pas pu appliquer la configuration (code {status}).",
        "error.no_monitors": "Windows n'a retourné aucun écran.",
        "error.desktop_missing": "Le bureau Windows est introuvable. Redémarrez l'Explorateur Windows puis réessayez.",
        "error.icons_access": "Accès aux icônes refusé. Lancez DTLdesktop avec le même niveau de droits que l'Explorateur Windows.",
        "error.windows_only": "DTLdesktop fonctionne uniquement sous Windows.",
        "error.monitor_count_mismatch": "Le nombre d'écrans connectés ne correspond pas à celui du profil.",
        "error.profile_unreadable": "Le profil « {name} » est incomplet ou illisible.",
        "error.invalid_screen": "Le numéro d'écran est invalide.",
        "error.file_missing": "Le fichier est introuvable : {path}",
        "error.wallpaper_monitor_match": "Impossible d'associer le fond d'écran au moniteur.",
        "error.orientation_not_confirmed": "La nouvelle orientation n'a pas été confirmée par Windows.",
        "error.invalid_display": "orientation ou résolution non conforme",
        "error.invalid_wallpaper": "fond d'écran non conforme",
        "error.invalid_framing": "cadrage du fond d'écran non conforme",
        "error.rollback_ok": "La configuration précédente a été restaurée.",
        "error.rollback_bad": "Le retour automatique n'a pas pu être entièrement validé.",
        "error.apply_validation": "La nouvelle configuration n'a pas pu être validée : {error} {status}",
    },
    "en": {
        "app.subtitle": "Windows desktop configuration manager",
        "arg.description": "Windows desktop configuration manager",
        "arg.auto": "restores the recognized profile",
        "arg.save": "saves the detected configuration without asking for a name",
        "arg.restore": "restores a profile",
        "arg.apply": "applies orientation, resolution, wallpapers and icons from a profile",
        "arg.test": "simulates a restore",
        "arg.diagnose": "shows the detected configuration",
        "arg.lang": "interface language",
        "arg.version": "shows the version number and exits",
        "arg.help": "shows this help message and exits",
        "arg.options": "options",
        "configuration.selected": "Selected configuration: {profile}",
        "configuration.new": "New configuration",
        "configuration.recognized": "Recognized configuration: {profile}",
        "configuration.saved": "Configuration “{profile}” saved: {icons} icon(s), {monitors} monitor(s).",
        "configuration.saved_short": "Configuration “{profile}” saved ({icons} icon(s)).",
        "configuration.none_compatible": "New configuration: no compatible profile.",
        "language.switch_hint": "Pour l'interface en français, tapez 2.",
        "monitor.title": "Monitor {index}{primary}",
        "monitor.primary": " (primary)",
        "layout": "Layout",
        "profile": "Profile: {profile}",
        "profiles.none": "No saved profile.",
        "profiles.invalid_choice": "Choice cancelled.",
        "profile.configure": "Profile to configure",
        "profile.compare": "Profile to compare",
        "profile.icons_restore": "Profile whose icons will be restored",
        "profile.apply": "Profile to apply",
        "screen": "Screen {index}",
        "screen.configure": "Screen to configure",
        "screen.invalid": "Configuration cancelled.",
        "screen.line": "{index}. Screen {index} — {resolution} {orientation}",
        "comparison.screens": "Monitors: {status}",
        "comparison.identical": "identical",
        "comparison.different": "different",
        "comparison.moved_icons": "Moved icons: {count}",
        "comparison.missing_icons": "Missing icons: {count}",
        "comparison.new_icons": "New icons: {count}",
        "comparison.wallpaper_differences": "Inconsistent wallpapers: {count}",
        "comparison.restore_possible": "Restore is possible; no change was made.",
        "comparison.none": "Difference: none",
        "wallpaper.diagnostic": "Wallpaper diagnostic",
        "wallpaper.current": "Wallpaper:\n{name}",
        "wallpaper.ok": "✓ compliant",
        "wallpaper.bad": "⚠ inconsistent wallpaper",
        "wallpaper.expected": "Expected:\n{name}",
        "wallpaper.observed": "Observed:\n{name}",
        "wallpaper.undefined": "(not set)",
        "wallpaper.choose_each": "Choose each screen's wallpaper.",
        "wallpaper.choose_landscape": "Now select the landscape wallpaper in Windows Explorer.",
        "wallpaper.choose_portrait": "Now select the portrait wallpaper in Windows Explorer.",
        "wallpaper.dialog_landscape": "DTLdesktop — landscape wallpaper for screen {screen}",
        "wallpaper.dialog_portrait": "DTLdesktop — portrait wallpaper for screen {screen}",
        "wallpaper.dialog_screen": "DTLdesktop — {configuration} — wallpaper for screen {screen}",
        "wallpaper.landscape": "Landscape wallpaper: {name}",
        "wallpaper.portrait": "Portrait wallpaper: {name}",
        "wallpaper.keep_landscape": "Selection cancelled: current landscape wallpaper kept.",
        "wallpaper.keep_portrait": "Selection cancelled: current portrait wallpaper kept.",
        "wallpaper.rules_saved": "Rules saved.",
        "wallpaper.landscape_value": "Landscape: {name}",
        "wallpaper.portrait_value": "Portrait: {name}",
        "wallpaper.screen_selected": "Screen {index}: {name}",
        "wallpaper.screen_kept": "Screen {index}: selection cancelled, current wallpaper kept.",
        "wallpaper.none_changed": "No wallpaper was changed.",
        "wallpaper.applied": "{count} wallpaper(s) applied.",
        "wallpaper.corrected": "{count} wallpaper(s) corrected.",
        "wallpaper.save_hint": "Press S to save “{configuration}”.",
        "wallpaper.fix_question": "Fix wallpapers? Y/N: ",
        "menu.apply": "[A] Apply a profile",
        "menu.save": "[S] Save current profile",
        "menu.restore_diagnose": "[R] Restore icons  [D] Diagnose",
        "menu.compare": "[C] Compare",
        "menu.wallpapers_quit": "[F] Choose wallpapers  [H] Help  [Q] Quit",
        "menu.choice": "Your choice: ",
        "menu.unknown": "Unrecognized choice.",
        "help.title": "Menu help",
        "help.apply": "A: applies a complete profile: orientation, layout, wallpapers and icon positions.",
        "help.save": "S: saves the current desktop state into the selected profile.",
        "help.restore": "R: restores only the icon positions from the chosen profile.",
        "help.diagnose": "D: shows the detected state and checks whether wallpapers match the profile.",
        "help.compare": "C: compares the chosen profile with the current state without changing the desktop.",
        "help.wallpapers": "F: chooses the wallpaper images to use for the current configuration.",
        "help.quit": "Q: exits DTLdesktop without further action.",
        "prompt.index": "{prompt} [1-{count}]: ",
        "prompt.continue": "Continue? Y/N: ",
        "prompt.confirm_restore": "Confirm restore? Y/N: ",
        "prompt.create_profile": "Do you want to create a new profile? Use S.",
        "simulation": "Simulation — no change",
        "restore.confirmed": "{count} icon(s) restored.",
        "restore.missing": "{count} profile icon(s) are missing.",
        "restore.cancelled": "Restore cancelled.",
        "apply.changes": "Profile “{profile}” will change the orientation or layout of {count} monitor(s).",
        "apply.running": "Applying profile…",
        "apply.done": "Profile “{profile}” applied and verified.",
        "apply.summary": "{wallpapers} wallpaper(s) and {icons} icon(s) restored.",
        "apply.cancelled": "Apply cancelled.",
        "apply.cli_done": "Profile “{profile}” applied: {wallpapers} wallpaper(s), {icons} icon(s).",
        "auto.summary": "Automatic restore: {icons} icon(s), {wallpapers} wallpaper(s).",
        "error": "Error: {error}",
        "orientation.landscape": "Landscape",
        "orientation.portrait": "Portrait",
        "orientation.square": "Square",
    },
}

TRANSLATIONS["en"].update(
    {
        key: value
        for key, value in {
            "error.empty_profile_name": "The profile name is empty or invalid.",
            "error.windows_images": "Image selection requires Windows.",
            "error.wallpapers_need_windows": "Per-monitor wallpapers require Windows.",
            "error.wallpaper_init": "Windows could not initialize wallpaper management.",
            "error.wallpaper_unavailable": "Per-monitor wallpaper management is not available.",
            "error.windows_action": "Windows could not {action}.",
            "action.count_monitors": "count monitors",
            "action.identify_monitor": "identify a monitor",
            "action.read_monitor_position": "read a monitor position",
            "action.read_wallpaper": "read a wallpaper",
            "action.apply_wallpaper": "apply a wallpaper",
            "action.select_wallpaper_framing": "select wallpaper framing",
            "action.check_wallpaper_mode": "check the wallpaper display mode",
            "error.wallpaper_framing_kept": "Windows did not keep the requested wallpaper framing.",
            "error.icon_list": "Windows did not allow reading the icon list.",
            "error.icon_prepare": "Could not prepare icon reading.",
            "error.icon_read": "Could not read icon information.",
            "error.display_mode_read": "Could not read the display mode for {device}.",
            "error.display_empty": "The profile does not contain any display mode.",
            "error.display_missing_id": "A profile monitor has no Windows identifier.",
            "error.display_unavailable": "Monitor {device} is not available.",
            "error.display_refused": "Windows rejected the display mode for {device} (code {status}).",
            "error.display_apply": "Windows could not apply the configuration (code {status}).",
            "error.no_monitors": "Windows did not return any monitor.",
            "error.desktop_missing": "The Windows desktop was not found. Restart Windows Explorer and try again.",
            "error.icons_access": "Icon access denied. Run DTLdesktop with the same privilege level as Windows Explorer.",
            "error.windows_only": "DTLdesktop only works on Windows.",
            "error.monitor_count_mismatch": "The number of connected monitors does not match the profile.",
            "error.profile_unreadable": "Profile “{name}” is incomplete or unreadable.",
            "error.invalid_screen": "The screen number is invalid.",
            "error.file_missing": "File not found: {path}",
            "error.wallpaper_monitor_match": "Could not match the wallpaper to the monitor.",
            "error.orientation_not_confirmed": "The new orientation was not confirmed by Windows.",
            "error.invalid_display": "orientation or resolution not compliant",
            "error.invalid_wallpaper": "wallpaper not compliant",
            "error.invalid_framing": "wallpaper framing not compliant",
            "error.rollback_ok": "The previous configuration was restored.",
            "error.rollback_bad": "Automatic rollback could not be fully validated.",
            "error.apply_validation": "The new configuration could not be validated: {error} {status}",
        }.items()
    }
)


def available_language_codes() -> tuple[str, ...]:
    return ("fr", "en")


def normalize_language(value: str | None) -> str:
    if not value:
        return ""
    code = value.replace("_", "-").split("-", 1)[0].casefold()
    return code if code in SUPPORTED_LANGUAGES else ""


def detect_language() -> str:
    for key in ("DTLDESKTOP_LANG", "LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        detected = normalize_language(os.environ.get(key))
        if detected:
            return detected
    try:
        detected = normalize_language(locale.getlocale()[0])
    except (TypeError, ValueError):
        detected = ""
    return detected or DEFAULT_LANGUAGE


def set_language(value: str | None) -> str:
    global _language
    _language = normalize_language(value) or DEFAULT_LANGUAGE
    return _language


def current_language() -> str:
    return _language


def t(key: str, **values: Any) -> str:
    text = TRANSLATIONS.get(_language, TRANSLATIONS[DEFAULT_LANGUAGE]).get(
        key, TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key)
    )
    return text.format(**values) if values else text


def yes_answers() -> set[str]:
    return {"O", "Y"} if _language == "fr" else {"Y", "O"}


def is_yes(value: str) -> bool:
    return value.strip().upper() in yes_answers()


def orientation_label(value: object) -> str:
    normalized = str(value).casefold()
    if normalized.startswith("portrait"):
        return t("orientation.portrait")
    if normalized.startswith("carr") or normalized.startswith("square"):
        return t("orientation.square")
    return t("orientation.landscape")
