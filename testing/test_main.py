import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

import cli_crud_app_rich_full_bundle as app


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

@pytest.fixture
def mock_cursor():
    cur = MagicMock()
    cur.description = [
        ("bundle_name",),
        ("type",),
        ("created",),
        ("active",),
        ("deactivated",)
    ]
    return cur


# ---------------------------------------------------------
# select_row_by_key
# ---------------------------------------------------------

def test_select_row_by_key_single_result(mock_cursor, mocker):
    mock_cursor.fetchall.return_value = [
        ("alpha", "type1", datetime(2024, 1, 1), True, None)
    ]

    mocker.patch("cli_crud_app_rich_full_bundle.Prompt.ask", return_value="1")
    mocker.patch("cli_crud_app_rich_full_bundle.console.print")
    mocker.patch("cli_crud_app_rich_full_bundle.display_row")

    result = app.select_row_by_key(mock_cursor, "bundle", "bundle_name", "alpha")

    assert result[0] == "alpha"
    mock_cursor.execute.assert_called_once()
    mock_cursor.fetchall.assert_called_once()


def test_select_row_by_key_no_results(mock_cursor, mocker):
    mock_cursor.fetchall.return_value = []

    mocker.patch("cli_crud_app_rich_full_bundle.console.print")

    result = app.select_row_by_key(mock_cursor, "bundle", "bundle_name", "none")
    assert result is None


# ---------------------------------------------------------
# add_bundle
# ---------------------------------------------------------

def test_add_bundle(mock_cursor, mocker):
    mocker.patch("cli_crud_app_rich_full_bundle.Prompt.ask", side_effect=["BundleX", "type1"])
    mock_cursor.fetchone.return_value = ("BundleX", "type1", datetime.now(), True)

    mocker.patch("cli_crud_app_rich_full_bundle.display_row")
    mocker.patch("cli_crud_app_rich_full_bundle.console.print")

    app.add_bundle(mock_cursor)

    assert mock_cursor.execute.call_count == 1
    assert mock_cursor.fetchone.call_count == 1


# ---------------------------------------------------------
# add_thing
# ---------------------------------------------------------

def test_add_thing(mock_cursor, mocker):
    mocker.patch("cli_crud_app_rich_full_bundle.Prompt.ask", return_value="http://x.com")
    mock_cursor.fetchone.return_value = ("http://x.com", datetime.now())

    mocker.patch("cli_crud_app_rich_full_bundle.display_row")
    mocker.patch("cli_crud_app_rich_full_bundle.console.print")

    app.add_thing(mock_cursor)

    assert mock_cursor.execute.call_count == 1
    assert mock_cursor.fetchone.call_count == 1


# ---------------------------------------------------------
# update_bundle
# ---------------------------------------------------------

def test_update_bundle_with_changes(mock_cursor, mocker):
    # Mock search result
    result_row = ("alpha", "type1", datetime.now(), True, None)
    mock_cursor.description = [(c,) for c in ["bundle_name", "type", "created", "active", "deactivated"]]
    mocker.patch("cli_crud_app_rich_full_bundle.select_row_by_key", return_value=result_row)

    # User chooses to update active + remove deactivated
    mocker.patch("cli_crud_app_rich_full_bundle.Confirm.ask", side_effect=[True, True, True])
    mocker.patch("cli_crud_app_rich_full_bundle.Prompt.ask", return_value="alpha")

    mock_cursor.fetchone.return_value = result_row

    mocker.patch("cli_crud_app_rich_full_bundle.display_row")
    mocker.patch("cli_crud_app_rich_full_bundle.console.print")

    app.update_bundle(mock_cursor)

    # Should run UPDATE
    assert mock_cursor.execute.call_count == 1


def test_update_bundle_no_match(mock_cursor, mocker):
    mocker.patch("cli_crud_app_rich_full_bundle.select_row_by_key", return_value=None)
    mocker.patch("cli_crud_app_rich_full_bundle.Prompt.ask", return_value="x")

    app.update_bundle(mock_cursor)

    mock_cursor.execute.assert_not_called()


# ---------------------------------------------------------
# update_thing
# ---------------------------------------------------------

def test_update_thing(mock_cursor, mocker):
    row = ("http://old.com", datetime.now())
    mock_cursor.description = [(c,) for c in ["thing_url", "update_time"]]
    mocker.patch("cli_crud_app_rich_full_bundle.select_row_by_key", return_value=row)

    mocker.patch("cli_crud_app_rich_full_bundle.Confirm.ask", return_value=True)
    mocker.patch("cli_crud_app_rich_full_bundle.Prompt.ask", side_effect=["old", "http://new.com"])

    mock_cursor.fetchone.return_value = row

    mocker.patch("cli_crud_app_rich_full_bundle.display_row")
    mocker.patch("cli_crud_app_rich_full_bundle.console.print")

    app.update_thing(mock_cursor)

    assert mock_cursor.execute.call_count == 1


# ---------------------------------------------------------
# delete_bundle
# ---------------------------------------------------------

def test_delete_bundle(mock_cursor, mocker):
    row = ("alpha", "t", datetime.now(), True, None)
    mock_cursor.description = [(c,) for c in ["bundle_name", "type", "created", "active", "deactivated"]]

    mocker.patch("cli_crud_app_rich_full_bundle.select_row_by_key", return_value=row)
    mocker.patch("cli_crud_app_rich_full_bundle.Confirm.ask", return_value=True)
    mocker.patch("cli_crud_app_rich_full_bundle.Prompt.ask", return_value="alpha")

    mocker.patch("cli_crud_app_rich_full_bundle.display_row")
    mocker.patch("cli_crud_app_rich_full_bundle.console.print")

    app.delete_bundle(mock_cursor)

    mock_cursor.execute.assert_called_with("DELETE FROM bundle WHERE bundle_name = %s", ("alpha",))


# ---------------------------------------------------------
# delete_thing
# ---------------------------------------------------------

def test_delete_thing(mock_cursor, mocker):
    row = ("http://x.com", datetime.now())
    mock_cursor.description = [(c,) for c in ["thing_url", "update_time"]]

    mocker.patch("cli_crud_app_rich_full_bundle.select_row_by_key", return_value=row)
    mocker.patch("cli_crud_app_rich_full_bundle.Confirm.ask", return_value=True)
    mocker.patch("cli_crud_app_rich_full_bundle.Prompt.ask", return_value="x")

    mocker.patch("cli_crud_app_rich_full_bundle.display_row")
    mocker.patch("cli_crud_app_rich_full_bundle.console.print")

    app.delete_thing(mock_cursor)

    mock_cursor.execute.assert_called_with(
        "DELETE FROM things WHERE thing_url = %s", ("http://x.com",)
    )
