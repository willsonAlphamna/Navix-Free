import json

import pytest

from navix.owner_auth import OwnerAccount


def test_local_login_is_hashed_and_matches_only_correct_password(tmp_path):
    account = OwnerAccount(tmp_path)
    assert not account.exists
    account.enroll('senha-local-forte-2026')
    assert account.exists
    data = account.path.read_text(encoding='utf-8')
    assert 'senha-local-forte-2026' not in data
    assert json.loads(data)['method'] == 'pbkdf2-sha256'
    assert not account.verify('senha-errada')
    assert account.verify('senha-local-forte-2026')


def test_local_login_never_overwrites_an_existing_password(tmp_path):
    account = OwnerAccount(tmp_path)
    with pytest.raises(ValueError, match='pelo menos 10'):
        account.enroll('123')
    account.enroll('uma-senha-muito-forte')
    with pytest.raises(ValueError, match='existe'):
        account.enroll('outra-senha-diferente')
    assert account.verify('uma-senha-muito-forte')


def test_local_login_rate_limits_failed_attempts(tmp_path):
    current = [50.0]
    account = OwnerAccount(tmp_path, clock=lambda: current[0])
    account.enroll('senha-super-secreta')
    for _ in range(5):
        assert not account.verify('errada')
    assert account.seconds_until_retry() == 30
    assert not account.verify('senha-super-secreta')
    current[0] += 31
    assert account.verify('senha-super-secreta')
