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
        self.select_payload = {"action": "SELECT", "table": "bundle"}
        self.insert_payload = {
            "action": "INSERT",
            "table": "bundle",
            "values": {"group_name": "Test", "group_address": "123 St", "active": True}
        }
        self.update_payload = {
            "action": "UPDATE",
            "table": "bundle",
            "values": {"active": False},
            "filters": {"group_name": "Test"}
        }
        self.delete_payload = {
            "action": "DELETE",
            "table": "bundle",
            "filters": {"group_name": "Test"}
        }
        self.lookup_payload = {
            "action": "LOOKUP",
            "table": "bundle",
            "term": "Ted"
        }

    @patch("main.psycopg2.connect")
    def test_select(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.description = [("group_name",), ("active",)]
        mock_cursor.fetchall.return_value = [("Test Group", True)]

        response = main.lambda_handler(self.select_payload, None)
        body = json.loads(response["body"])

        self.assertEqual(body["action"], "SELECT")
        self.assertEqual(body["result"], [{"group_name": "Test Group", "active": True}])

    @patch("main.psycopg2.connect")
    def test_insert(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1

        response = main.lambda_handler(self.insert_payload, None)
        body = json.loads(response["body"])
        self.assertEqual(body["action"], "INSERT")
        self.assertEqual(body["result"]["rowcount"], 1)

    @patch("main.psycopg2.connect")
    def test_update(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1

        response = main.lambda_handler(self.update_payload, None)
        body = json.loads(response["body"])
        self.assertEqual(body["action"], "UPDATE")
        self.assertEqual(body["result"]["rowcount"], 1)

    @patch("main.psycopg2.connect")
    def test_delete(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1

        response = main.lambda_handler(self.delete_payload, None)
        body = json.loads(response["body"])
        self.assertEqual(body["action"], "DELETE")
        self.assertEqual(body["result"]["rowcount"], 1)

    @patch("main.psycopg2.connect")
    def test_lookup(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.description = [("group_name",), ("active",)]
        mock_cursor.fetchall.return_value = [("Teddy", True)]

        response = main.lambda_handler(self.lookup_payload, None)
        body = json.loads(response["body"])
        self.assertEqual(body["action"], "LOOKUP")
        self.assertEqual(body["result"], [{"group_name": "Teddy", "active": True}])


if __name__ == "__main__":
    unittest.main()
