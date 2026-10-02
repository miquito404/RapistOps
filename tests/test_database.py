import pytest


pytestmark = pytest.mark.database


def test_database_connection(database_connection):
    assert database_connection.execute("SELECT 1").fetchone() == (1,)
    assert database_connection.execute("SELECT current_database()").fetchone() == ("rapistops_test",)
