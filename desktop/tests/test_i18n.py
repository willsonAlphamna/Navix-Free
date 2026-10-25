import json

from navix.i18n import LANGUAGES, load_language, save_language, translate


def test_three_offline_languages():
    assert list(LANGUAGES) == ['pt-BR', 'en', 'es']
    assert translate('Início', 'pt-BR') == 'Início'
    assert translate('Início', 'en') == 'Home'
    assert translate('Início', 'es') == 'Inicio'


def test_installer_language_persists_and_user_choice_wins(tmp_path):
    assert load_language(tmp_path, 'spanish') == 'es'
    save_language(tmp_path, 'en')
    assert load_language(tmp_path, 'spanish') == 'en'
    assert json.loads((tmp_path / 'ui-settings.json').read_text())['language'] == 'en'
