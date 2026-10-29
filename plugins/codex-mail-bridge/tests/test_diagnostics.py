"""Thunderbird setup guidance with synthetic configuration and no mailbox access."""
from contextlib import ExitStack
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
import accounts
import bridge
from create_demo import create_demo


class InstallationTests(unittest.TestCase):
    def test_discovers_custom_path_installation(self):
        with patch.object(accounts.sys, "platform", "linux"), patch.object(accounts.shutil, "which", return_value="/opt/synthetic/thunderbird"):
            self.assertIn(Path("/opt/synthetic/thunderbird"), accounts._installation_candidates())

    def test_discovers_windows_app_paths_in_both_registry_views(self):
        from contextlib import nullcontext
        registry = SimpleNamespace(HKEY_CURRENT_USER=1, HKEY_LOCAL_MACHINE=2,
                                   KEY_READ=4, KEY_WOW64_64KEY=8, KEY_WOW64_32KEY=16,
                                   OpenKey=lambda *args: nullcontext("synthetic-key"),
                                   QueryValueEx=lambda *args: ('"C:/Synthetic/Thunderbird/thunderbird.exe"', 1))
        with patch.object(accounts.sys, "platform", "win32"), patch.object(accounts.shutil, "which", return_value=None), patch.dict(sys.modules, {"winreg": registry}):
            candidates = accounts._installation_candidates()
        self.assertEqual(candidates.count(Path("C:/Synthetic/Thunderbird/thunderbird.exe")), 4)

    def test_detects_an_existing_executable_without_starting_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            executable = Path(temporary) / "thunderbird"
            executable.write_text("not executable test data", encoding="utf-8")
            with patch.object(accounts, "_installation_candidates", return_value=[executable]):
                self.assertEqual(accounts.installation_status()["state"], "detected")

    def test_missing_executable_is_not_reported_as_proven_uninstallation(self):
        with patch.object(accounts, "_installation_candidates", return_value=[]):
            result = accounts.installation_status()
        self.assertEqual(result["state"], "not_detected")
        self.assertIn("portable", result["note"].lower())
        self.assertNotIn("path", result)

    def test_unreadable_install_location_is_unconfirmed(self):
        with patch.object(accounts, "_installation_candidates", side_effect=PermissionError("private path")):
            result = accounts.installation_status()
        self.assertEqual(result["state"], "unconfirmed")
        self.assertNotIn("private path", json.dumps(result))


class SetupGuidanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.dict(os.environ, create_demo(self.directory)))
        self.profile = accounts.profiles()[0]
        self.stack.enter_context(patch.object(accounts, "installation_status", return_value={
            "state": "detected", "note": "Synthetic executable registration."}))

    def test_unselected_account_gets_explicit_selection_guidance(self):
        result = bridge.call_operation("thunderbird_diagnostics", {})
        self.assertTrue(result["ok"])
        value = result["result"]
        self.assertEqual(value["code"], "selection_required")
        self.assertEqual(value["next_action"], "discover_and_select_account")
        self.assertEqual(value["account_count"], 3)
        self.assertFalse(value["authentication_verified"])
        self.assertFalse(accounts.selection_path().exists())

    def test_missing_application_and_profiles_get_installation_guidance(self):
        with patch.object(accounts, "profiles", return_value=[]), patch.object(accounts, "installation_status", return_value={"state": "not_detected", "note": "Portable installs may not be detected."}):
            value = accounts.diagnostics()
        self.assertEqual(value["code"], "thunderbird_not_detected")
        self.assertEqual(value["next_action"], "install_thunderbird")
        self.assertIn("https://www.thunderbird.net/", value["guidance"])

    def test_installed_application_without_a_profile_gets_setup_guidance(self):
        with patch.object(accounts, "profiles", return_value=[]):
            value = accounts.diagnostics()
        self.assertEqual(value["code"], "thunderbird_profile_unconfirmed")
        self.assertEqual(value["next_action"], "open_thunderbird_and_register_account")

    def test_empty_profile_gets_account_registration_guidance(self):
        (self.profile["path"] / "prefs.js").write_text("// no configured account\n", encoding="utf-8")
        value = accounts.diagnostics()
        self.assertEqual(value["code"], "account_registration_unconfirmed")
        self.assertEqual(value["next_action"], "register_thunderbird_account")
        self.assertEqual(value["account_count"], 0)

    def test_unreadable_account_configuration_is_not_called_an_empty_account(self):
        with patch.object(accounts, "read_accounts", side_effect=PermissionError("private account/path")):
            value = accounts.diagnostics()
        self.assertEqual(value["code"], "account_registration_unconfirmed")
        self.assertEqual(value["next_action"], "check_thunderbird_profile_access")
        self.assertEqual(value["profiles_unreadable"], 1)
        self.assertNotIn("private account/path", json.dumps(value))

    def test_malformed_registry_guides_access_repair_instead_of_reinstallation(self):
        (Path(os.environ["THUNDERBIRD_HOME"]) / "profiles.ini").write_text("not an INI registry", encoding="utf-8")
        with patch.object(accounts, "installation_status", return_value={"state": "not_detected", "note": "Synthetic portable installation."}):
            value = accounts.diagnostics()
        self.assertEqual(value["code"], "thunderbird_profile_unconfirmed")
        self.assertEqual(value["next_action"], "check_thunderbird_profile_access")
        self.assertGreater(value["profiles_unreadable"], 0)

    def test_unreadable_registry_is_reported_without_exposing_its_path(self):
        registry = Path(os.environ["THUNDERBIRD_HOME"]) / "profiles.ini"
        original = Path.is_file
        def inspect(path):
            if path == registry:
                raise PermissionError("private registry path")
            return original(path)
        with patch.object(Path, "is_file", inspect), patch.object(accounts, "installation_status", return_value={"state": "not_detected", "note": "Synthetic portable installation."}):
            value = accounts.diagnostics()
        self.assertEqual(value["next_action"], "check_thunderbird_profile_access")
        self.assertNotIn("private registry path", json.dumps(value))

    def test_inaccessible_profile_is_not_reported_as_missing_installation(self):
        preferences = self.profile["path"] / "prefs.js"
        original = Path.is_file
        def inspect(path):
            if path == preferences:
                raise PermissionError("private profile path")
            return original(path)
        with patch.object(Path, "is_file", inspect), patch.object(accounts, "installation_status", return_value={"state": "not_detected", "note": "Synthetic portable installation."}):
            value = accounts.diagnostics()
        self.assertEqual(value["next_action"], "check_thunderbird_profile_access")
        self.assertNotIn("private profile path", json.dumps(value))

    def test_registered_account_without_index_gets_indexing_guidance(self):
        (self.profile["path"] / "global-messages-db.sqlite").unlink()
        value = accounts.diagnostics()
        self.assertEqual(value["code"], "thunderbird_index_missing")
        self.assertEqual(value["next_action"], "enable_indexing_and_sync")

    def test_existing_local_data_remains_usable_without_a_detected_executable(self):
        accounts.select_account(self.profile["id"], "account1", confirm=True)
        with patch.object(accounts, "installation_status", return_value={"state": "not_detected", "note": "Portable installs may not be detected."}):
            value = accounts.diagnostics()
            self.assertEqual(value["code"], "selection_saved")
            self.assertEqual(value["next_action"], "check_thunderbird_status")
            self.assertTrue(bridge.status()["configured"])

    def test_diagnostics_does_not_read_mail_or_expose_identity(self):
        with patch.object(sqlite3, "connect", side_effect=AssertionError("Diagnostics must not open mail")):
            value = accounts.diagnostics()
        output = json.dumps(value)
        for private in ("demo@example.test", "imap.example.test", str(self.directory), self.profile["id"], "account1"):
            self.assertNotIn(private, output)
        self.assertFalse(value["mail_read"])
        self.assertFalse(value["client_started"])

    def test_status_without_selection_also_returns_setup_guidance(self):
        (self.profile["path"] / "prefs.js").write_text("", encoding="utf-8")
        value = bridge.status()
        self.assertFalse(value["configured"])
        self.assertEqual(value["setup"]["code"], "account_registration_unconfirmed")

    def test_empty_account_discovery_does_not_ask_to_select_from_an_empty_list(self):
        (self.profile["path"] / "prefs.js").write_text("", encoding="utf-8")
        value = bridge.discover_accounts(self.profile["id"])
        self.assertEqual(value["accounts"], [])
        self.assertEqual(value["setup"]["next_action"], "register_thunderbird_account")

    def test_a_removed_selected_account_returns_registration_recovery(self):
        accounts.select_account(self.profile["id"], "account1", confirm=True)
        (self.profile["path"] / "prefs.js").write_text("", encoding="utf-8")
        result = bridge.call_operation("thunderbird_status", {})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "account_registration_unconfirmed")
        self.assertEqual(result["error"]["next_action"], "run_thunderbird_diagnostics")


if __name__ == "__main__":
    unittest.main()
