import unittest
from unittest.mock import patch, MagicMock
import json
import os

# Patch environment variables before importing main
env_vars = {
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "DB_NAME": "testdb",
    "DB_USER": "testuser",
    "DB_PASS": "testpass"
}

with patch.dict(os.environ, env_vars):
    import main  # Now main.py sees the env vars


class TestCrudLambda(unittest.TestCase):

    def setUp(self):
        # Example payloads
        self.select_bundle_payload = {"action": "SELECT", "table": "bundle"}
        self.insert_bundle_payload = {
            "action": "INSERT",
            "table": "bundle",
            "values": {"group_name": "Test", "group_address": "123 St", "active": True}
        }
        self.update_bundle_payload = {
            "action": "UPDATE",
            "table": "bundle",
            "values": {"active": False},
            "filters": {"group_name": "Test", "group_address": "123 St"}
        }
        self.update_bundle_missing_key = {
            "action": "UPDATE",
            "table": "bundle",
            "values": {"active": False},
            "filters": {"group_name": "Test"}  # missing group_address
        }
        self.delete_bundle_payload = {
            "action": "DELETE",
            "table": "bundle",
            "filters": {"group_name": "Test", "group_address": "123 St"}
        }
        self.lookup_bundle_payload = {
            "action": "LOOKUP",
            "table": "bundle",
            "filters": {"group_name": "Test", "group_address": "123 St"}
        }

        self.insert_book_payload = {
            "action": "INSERT",
            "table": "book",
            "values": {"name": "Python 101", "update_frequency": "daily"}
        }
        self.update_book_payload = {
            "action": "UPDATE",
            "table": "book",
            "values": {"update_frequency": "weekly"},
            "filters": {"name": "Python 101"}
        }

    @patch("main.psycopg2.connect")
    def test_select_bundle(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.description = [("group_name",), ("active",)]
        mock_cursor.fetchall.return_value = [("Test Group", True)]

        response = main.lambda_handler(self.select_bundle_payload, None)
        body = json.loads(response["body"])
        self.assertEqual(body["action"], "SELECT")
        self.assertEqual(body["result"], [{"group_name": "Test Group", "active": True}])

    @patch("main.psycopg2.connect")
    def test_insert_bundle(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1

        response = main.lambda_handler(self.insert_bundle_payload, None)
        body = json.loads(response["body"])
        self.assertEqual(body["action"], "INSERT")
        self.assertEqual(body["result"]["rowcount"], 1)

    @patch("main.psycopg2.connect")
    def test_update_bundle(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1

        response = main.lambda_handler(self.update_bundle_payload, None)
        body = json.loads(response["body"])
        self.assertEqual(body["action"], "UPDATE")
        self.assertEqual(body["result"]["rowcount"], 1)

    def test_update_bundle_missing_key(self):
        """Should fail because missing unique key (group_address)"""
        response = main.lambda_handler(self.update_bundle_missing_key, None)
        self.assertEqual(response["statusCode"], 400)
        self.assertIn("Missing required unique key", json.loads(response["body"]))

    @patch("main.psycopg2.connect")
    def test_delete_bundle(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1

        response = main.lambda_handler(self.delete_bundle_payload, None)
        body = json.loads(response["body"])
        self.assertEqual(body["action"], "DELETE")
        self.assertEqual(body["result"]["rowcount"], 1)

    @patch("main.psycopg2.connect")
    def test_lookup_bundle(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.description = [("group_name",), ("active",)]
        mock_cursor.fetchall.return_value = [("Test Group", True)]

        response = main.lambda_handler(self.lookup_bundle_payload, None)
        body = json.loads(response["body"])
        self.assertEqual(body["action"], "LOOKUP")
        self.assertEqual(body["result"], [{"group_name": "Test Group", "active": True}])

    @patch("main.psycopg2.connect")
    def test_insert_book(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1

        response = main.lambda_handler(self.insert_book_payload, None)
        body = json.loads(response["body"])
        self.assertEqual(body["action"], "INSERT")
        self.assertEqual(body["result"]["rowcount"], 1)

    @patch("main.psycopg2.connect")
    def test_update_book(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1

        response = main.lambda_handler(self.update_book_payload, None)
        body = json.loads(response["body"])
        self.assertEqual(body["action"], "UPDATE")
        self.assertEqual(body["result"]["rowcount"], 1)


if __name__ == "__main__":
    unittest.main()
