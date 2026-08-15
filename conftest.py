import pytest
from django.core.management import call_command


@pytest.fixture(scope="session", autouse=True)
def _cache_table(django_db_setup, django_db_blocker):
    """Create the shared DatabaseCache table in the test database.

    CACHES uses the DB backend, so the ``django_cache`` table must exist for
    any code path that touches the cache (allauth rate limits, email
    confirmation cooldown, etc.). It is created once per test session, right
    after the test database is set up.
    """
    with django_db_blocker.unblock():
        call_command("createcachetable", "django_cache", verbosity=0)
