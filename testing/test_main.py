import unittest
from unittest.mock import patch, MagicMock
import main

class TestAdminCLI(unittest.TestCase):

    # -------------------------------
    # Database connection test
    # -------------------------------
    @patch("main.getpass.getpass", return_value="password")
    @patch("main.psycopg2.connect")
    def test_get_connection(self, mock_connect, mock_getpass):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        conn = main.get_connection()
        mock_connect.assert_called_once()
        self.assertEqual(conn, mock_conn)

    # -------------------------------
    # Table selection tests
    # -------------------------------
    @patch("builtins.input", side_effect=["1"])
    def test_select_table_valid(self, mock_input):
        table = main.select_table()
        self.assertEqual(table, "bundle")

    @patch("builtins.input", side_effect=["invalid", "2"])
    def test_select_table_invalid_then_valid(self, mock_input):
        table = main.select_table()
        self.assertEqual(table, "book")

    # -------------------------------
    # Key input tests
    # -------------------------------
    @patch("builtins.input", side_effect=["Acme Corp", "123 Main St"])
    def test_get_key_values_bundle(self, mock_input):
        keys = main.get_key_values("bundle")
        self.assertEqual(keys, {"group_name": "Acme Corp", "group_address": "123 Main St"})

    @patch("builtins.input", side_effect=["Weekly Digest"])
    def test_get_key_values_book(self, mock_input):
        keys = main.get_key_values("book")
        self.assertEqual(keys, {"name": "Weekly Digest"})

    # -------------------------------
    # Confirmation prompt tests
    # -------------------------------
    @patch("builtins.input", side_effect=["y"])
    def test_confirm_action_yes(self, mock_input):
        self.assertTrue(main.confirm_action("Confirm?"))

    @patch("builtins.input", side_effect=["n"])
    def test_confirm_action_no(self, mock_input):
        self.assertFalse(main.confirm_action("Confirm?"))

    # -------------------------------
    # Date parsing tests
    # -------------------------------
    def test_parse_date_input_valid(self):
        date_str = main.parse_date_input("11/16/2025")
        self.assertEqual(date_str, "2025-11-16")

    def test_parse_date_input_invalid_then_valid(self):
        self.assertIsNone(main.parse_date_input("invalid"))
        self.assertEqual(main.parse_date_input("2025-11-16"), "2025-11-16")

    # -------------------------------
    # Delete record test
    # -------------------------------
    @patch("main.get_key_values")
    @patch("main.confirm_action", return_value=True)
    def test_delete_record_calls_cursor_execute(self, mock_confirm, mock_get_keys):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_keys.return_value = {"group_name": "Acme Corp", "group_address": "123 Main St"}

        main.delete_record(mock_conn, "bundle")

        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    # -------------------------------
    # Update record test
    # -------------------------------
    @patch("main.get_key_values")
    @patch("main.confirm_action", return_value=True)
    @patch("builtins.input", side_effect=["false", "", "2025-11-30", ""])
    def test_update_record_calls_cursor_execute(self, mock_input, mock_confirm, mock_get_keys):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_keys.return_value = {"group_name": "Acme Corp", "group_address": "123 Main St"}

        main.update_record(mock_conn, "bundle")

        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

if __name__ == "__main__":
    unittest.main()
