"""Qt translation loading for the Argos Translate GUI."""

from pathlib import Path

from PyQt5.QtCore import QLocale, QTranslator


def install_system_translator(app, locale_name=None, translations_dir=None):
    """Install the best available translation for the current system locale."""
    locale_name = locale_name or QLocale.system().name()
    translations_dir = Path(translations_dir or Path(__file__).parent / "translations")
    candidates = [locale_name]
    language = locale_name.split("_", 1)[0]
    if language not in candidates:
        candidates.append(language)

    translator = QTranslator(app)
    for candidate in candidates:
        catalog = translations_dir / f"argos_translate_{candidate}.qm"
        if catalog.is_file() and translator.load(str(catalog)):
            app.installTranslator(translator)
            return translator
    return None
