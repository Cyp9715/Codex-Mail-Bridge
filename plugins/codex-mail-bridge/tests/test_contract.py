"""Local CLI contract checks use synthetic data and never access real mail."""
import inspect
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "server"))
import attachments
import bridge


class ContractTests(unittest.TestCase):
    def test_each_operation_schema_matches_its_implementation(self):
        self.assertEqual(len(bridge.OPERATIONS), len(bridge.FUNCTIONS))
        for operation in bridge.OPERATIONS:
            schema = operation["inputSchema"]
            parameters = inspect.signature(bridge.FUNCTIONS[operation["name"]]).parameters
            self.assertFalse(schema["additionalProperties"])
            self.assertLessEqual(set(schema["properties"]), set(parameters))
            self.assertLessEqual({key for key, p in parameters.items() if p.default is inspect.Parameter.empty}, set(schema["required"]))
            for key, spec in schema["properties"].items():
                if key not in schema["required"] and parameters[key].default not in (inspect.Parameter.empty, None):
                    self.assertEqual(spec["default"], parameters[key].default)
            if operation["name"].endswith(("_search", "_search_attachments")):
                self.assertTrue({"after", "before"} <= set(schema["properties"]))
                self.assertFalse({"period", "time_zone"} & set(schema["properties"]))

    def test_json_result_contains_metadata_once_without_binary_content(self):
        value = {"configured": True, "source": "synthetic"}
        with patch.dict(bridge.FUNCTIONS, {"thunderbird_status": lambda: value}):
            self.assertEqual(bridge.call_operation("thunderbird_status", {}), {"ok": True, "result": value})
        transfer = attachments.Transfer({"delivery": "local_original_file", "document_parsed": False})
        with patch.dict(bridge.FUNCTIONS, {"thunderbird_status": lambda: transfer}):
            result = bridge.call_operation("thunderbird_status", {})
        self.assertEqual(result["result"], transfer.metadata)
        self.assertNotIn("blob", json.dumps(result))

    def test_actionable_argument_errors_and_sanitized_unexpected_failures(self):
        result = bridge.call_operation("thunderbird_search", {"period": "this_week"})
        self.assertEqual(result["error"]["code"], "invalid_arguments")
        self.assertEqual(result["error"]["next_action"], "correct_operation_arguments")
        with patch.dict(bridge.FUNCTIONS, {"thunderbird_status": lambda: 1 / 0}):
            result = bridge.call_operation("thunderbird_status", {})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "internal_error")
        self.assertNotIn("division", json.dumps(result))

    def test_invalid_json_shapes_duplicates_and_constants_are_rejected(self):
        for text in ('{"limit":NaN}', '{"limit":1,"limit":2}', 'x', 'x' * 65537):
            with self.assertRaises(ValueError):
                bridge.load_arguments(StringIO(text))
        for arguments in ([], None, True, {"limit": True}):
            self.assertFalse(bridge.call_operation("thunderbird_search", arguments)["ok"])

    def run_cli(self, *args, input=None):
        process = subprocess.run([sys.executable, '-B', str(PLUGIN / 'server/bridge.py'), *args],
                                 input=input, capture_output=True, text=True, encoding='utf-8', timeout=10)
        self.assertEqual(process.stderr, '')
        return process, json.loads(process.stdout)

    def test_description_is_lazy_and_catalog_does_not_read_mail(self):
        with patch.dict(bridge.FUNCTIONS, {name: lambda **kwargs: self.fail('Description read mail') for name in bridge.FUNCTIONS}):
            with patch('sys.stdout', new_callable=StringIO) as output:
                self.assertEqual(bridge.main(['--describe', 'outlook_search']), 0)
            schema = json.loads(output.getvalue())['result']['inputSchema']
            self.assertIn('after', schema['properties'])
            self.assertIn('body_search_limit', schema['properties'])
        process, value = self.run_cli('--list')
        self.assertEqual(process.returncode, 0)
        self.assertEqual(len(value['result']['operations']), 19)

    def test_stdin_file_input_and_unknown_operations_fail_without_execution(self):
        for text in ('[]', '{"limit":true}', '{"jsonrpc":"2.0","method":"initialize"}'):
            process, value = self.run_cli('--call', 'thunderbird_search', '--arguments-stdin', input=text)
            self.assertEqual(process.returncode, 1)
            self.assertEqual(value['error']['code'], 'invalid_arguments')
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'arguments with spaces.json'
            path.write_text('{"query":"회의","unknown":true}', encoding='utf-8-sig')
            process, value = self.run_cli('--call', 'thunderbird_search', '--arguments-file', str(path))
            self.assertEqual(process.returncode, 1)
            self.assertEqual(value['error']['code'], 'invalid_arguments')
        process, value = self.run_cli('--call', 'send_mail')
        self.assertEqual(process.returncode, 1)
        self.assertEqual(value['error']['code'], 'unknown_operation')

    def test_version_and_package_have_no_mcp_server(self):
        process, value = self.run_cli('--version')
        self.assertEqual(process.returncode, 0)
        self.assertEqual(value['result']['version'], json.loads((PLUGIN / 'plugin.json').read_text(encoding='utf-8'))['version'])
        self.assertIs(value['result']['mcp_server'], False)
        for name in ('mcp.json', '.mcp.json', '.app.json', 'hooks/hooks.json'):
            self.assertFalse((PLUGIN / name).exists())
        overlay = json.loads((PLUGIN / '.codex-plugin/plugin.json').read_text(encoding='utf-8'))
        self.assertNotIn('mcpServers', overlay)
        self.assertIs(overlay['requires_local_executor'], True)

    def test_non_json_provider_result_is_sanitized(self):
        with patch.dict(bridge.FUNCTIONS, {'thunderbird_status': lambda: {'value': float('nan')}}):
            with patch('sys.stdout', new_callable=StringIO) as output:
                self.assertEqual(bridge.main(['--call', 'thunderbird_status']), 1)
        result = json.loads(output.getvalue())
        self.assertEqual(result['error']['code'], 'internal_error')
        self.assertNotIn('NaN', output.getvalue())


if __name__ == '__main__':
    unittest.main()
