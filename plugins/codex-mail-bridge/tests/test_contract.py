"""MCP contract checks do not access real clients or mailboxes."""
import inspect
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
import attachments
import bridge


class ContractTests(unittest.TestCase):
    def test_every_tool_schema_matches_its_implementation(self):
        self.assertEqual(len(bridge.TOOLS), len(bridge.FUNCTIONS))
        for tool in bridge.TOOLS:
            schema = tool["inputSchema"]
            parameters = inspect.signature(bridge.FUNCTIONS[tool["name"]]).parameters
            self.assertFalse(schema["additionalProperties"])
            self.assertLessEqual(set(schema["properties"]), set(parameters))
            self.assertLessEqual({key for key, p in parameters.items() if p.default is inspect.Parameter.empty}, set(schema["required"]))
            for key, spec in schema["properties"].items():
                if key not in schema["required"] and parameters[key].default not in (inspect.Parameter.empty, None):
                    self.assertEqual(spec["default"], parameters[key].default)
            if tool["name"].endswith(("_search", "_search_attachments")):
                self.assertTrue({"after", "before"} <= set(schema["properties"]))
                self.assertFalse({"period", "time_zone"} & set(schema["properties"]))

    def test_structured_result_matches_text_fallback_without_file_bytes(self):
        value = {"configured": True, "source": "synthetic"}
        with patch.object(bridge, "CLIENT_PROTOCOL", "2025-06-18"), patch.dict(bridge.FUNCTIONS, {"thunderbird_status": lambda: value}):
            result = bridge.call_tool("thunderbird_status", {})
        self.assertEqual(result["structuredContent"], json.loads(result["content"][0]["text"]))
        transfer = attachments.Transfer({"delivery": "local_original_file", "document_parsed": False},
                                        [{"type": "resource_link", "uri": "mail-bridge://attachment/" + "a" * 32, "name": "sample.pdf"}])
        with patch.object(bridge, "CLIENT_PROTOCOL", "2025-06-18"), patch.dict(bridge.FUNCTIONS, {"thunderbird_status": lambda: transfer}):
            result = bridge.call_tool("thunderbird_status", {})
        self.assertNotIn("blob", result["structuredContent"])
        self.assertEqual(result["content"][1]["type"], "resource_link")

    def test_legacy_protocol_keeps_compatible_text_result(self):
        with patch.object(bridge, "CLIENT_PROTOCOL", "2024-11-05"), patch.dict(bridge.FUNCTIONS, {"thunderbird_status": lambda: {"configured": False}}):
            result = bridge.call_tool("thunderbird_status", {})
        self.assertNotIn("structuredContent", result)
        self.assertEqual(json.loads(result["content"][0]["text"]), {"configured": False})

    def test_actionable_argument_errors_and_sanitized_unexpected_failures(self):
        with patch.object(bridge, "CLIENT_PROTOCOL", "2025-06-18"):
            result = bridge.call_tool("thunderbird_search", {"period": "this_week"})
            self.assertEqual(result["structuredContent"]["code"], "invalid_arguments")
            self.assertEqual(result["structuredContent"]["next_action"], "correct_tool_arguments")
            with patch.dict(bridge.FUNCTIONS, {"thunderbird_status": lambda: 1 / 0}):
                result = bridge.call_tool("thunderbird_status", {})
        self.assertTrue(result["isError"])
        self.assertEqual(result["structuredContent"]["code"], "internal_error")
        self.assertNotIn("division", result["content"][0]["text"])

    def test_internal_rpc_failure_preserves_request_id(self):
        request = {"jsonrpc": "2.0", "id": 77, "method": "ping"}
        with patch.object(bridge, "dispatch", side_effect=RuntimeError("synthetic private fixture detail")):
            result = bridge.handle_request(request)
        self.assertEqual(result["id"], 77)
        self.assertEqual(result["error"]["code"], -32603)
        self.assertNotIn("fixture", json.dumps(result))

    def test_invalid_params_and_ids_cannot_invoke_tools(self):
        result = bridge.handle_request({"jsonrpc": "2.0", "id": 8, "method": "tools/call", "params": []})
        self.assertEqual(result["error"]["code"], -32602)
        result = bridge.handle_request({"jsonrpc": "2.0", "id": True, "method": "ping"})
        self.assertEqual(result["error"]["code"], -32600)
        with patch.dict(bridge.FUNCTIONS, {"thunderbird_status": lambda: self.fail("Notification executed a tool")}):
            self.assertIsNone(bridge.handle_request({"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "thunderbird_status"}}))


if __name__ == "__main__":
    unittest.main()
