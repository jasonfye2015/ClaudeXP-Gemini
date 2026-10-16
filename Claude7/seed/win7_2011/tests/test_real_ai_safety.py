"""Offline guardrail coverage; never needs a model server or model files."""
import os
import unittest
from unittest.mock import Mock, patch

from win7_2011.tests.real_ai_support import LlamaRouter, RealHTTP, owned_model
from win7_2011.tests import test_ai_real_servers
from win7_2011.tests import test_ai_real_auth


class RealAISafetyTests(unittest.TestCase):
    def test_disabled_authenticated_check_does_not_read_keys_or_touch_network(self):
        with patch.dict(os.environ, {"WIN7_REAL_AUTH": ""}), \
                patch.object(test_ai_real_auth, "WindowsCredentialStore") as store, \
                patch.object(test_ai_real_auth, "AIService") as service, \
                patch.object(test_ai_real_auth, "configuration") as configuration:
            with self.assertRaises(unittest.SkipTest):
                test_ai_real_auth.RealAuthenticationTests().test_saved_key_change_and_explicit_reconnect()
            store.assert_not_called()
            service.assert_not_called()
            configuration.assert_not_called()

    def test_enabled_auth_check_fails_off_windows_before_reading_keys(self):
        with patch.dict(os.environ, {"WIN7_REAL_AUTH": "1"}), \
                patch.object(test_ai_real_auth.sys, "platform", "linux"), \
                patch.object(test_ai_real_auth, "WindowsCredentialStore") as store:
            with self.assertRaisesRegex(AssertionError, "requires Windows"):
                test_ai_real_auth.RealAuthenticationTests().test_saved_key_change_and_explicit_reconnect()
            store.assert_not_called()

    def test_auth_configuration_requires_ownership_and_distinct_safe_endpoints(self):
        base = {
            "WIN7_REAL_AUTH_TEST_OWNED": "YES", "WIN7_REAL_AUTH_BACKEND": "llama_cpp",
            "WIN7_REAL_AUTH_URL": "http://127.0.0.1:9931",
            "WIN7_REAL_AUTH_HEALTHY_URL": "http://127.0.0.1:9932",
            "WIN7_REAL_AUTH_MODEL": "chat", "WIN7_REAL_AUTH_HEALTHY_MODEL": "chat",
        }
        for override in (
            {"WIN7_REAL_AUTH_TEST_OWNED": "NO"},
            {"WIN7_REAL_AUTH_BACKEND": "unsupported"},
            {"WIN7_REAL_AUTH_HEALTHY_URL": "http://127.0.0.1:9931/v1/"},
            {"WIN7_REAL_AUTH_URL": "http://secret@127.0.0.1:9931"},
            {"WIN7_REAL_AUTH_URL": "http://127.0.0.1:9931?key=secret"},
            {"WIN7_REAL_AUTH_URL": "https://example.com"},
        ):
            with patch.dict(os.environ, {**base, **override}), self.assertRaises(ValueError):
                test_ai_real_auth.configuration()
        with patch.dict(os.environ, base):
            settings = test_ai_real_auth.configuration()
        self.assertEqual(settings.endpoint_for("background"), "http://127.0.0.1:9932")

    def test_disabled_integration_checks_do_not_touch_servers(self):
        with patch.dict(os.environ, {"WIN7_REAL_LLAMA": "",
                                    "WIN7_REAL_LIMIT_LLAMA": ""}), \
                patch.object(RealHTTP, "request", side_effect=AssertionError("Unexpected network")):
            # Invoke only test methods: no QApplication or HTTP fixture needed.
            case = test_ai_real_servers.RealServerTests()
            for name in ("test_llama_router_unload_and_reconnect",):
                with self.subTest(name=name), self.assertRaises(unittest.SkipTest):
                    getattr(case, name)()
            limits = test_ai_real_servers.RealModelLimitTests()
            for name in ("test_llama_model_limits_windows",):
                with self.subTest(name=name), self.assertRaises(unittest.SkipTest):
                    getattr(limits, name)()

    def test_enabled_limits_fail_off_windows_before_network_or_storage(self):
        with patch.dict(os.environ, {"WIN7_REAL_LIMIT_LLAMA": "1"}), \
                patch.object(test_ai_real_servers.sys, "platform", "linux"), \
                patch.object(RealHTTP, "request") as request, \
                patch.object(test_ai_real_servers, "save_ai_settings") as save:
            case = test_ai_real_servers.RealModelLimitTests()
            for name in ("test_llama_model_limits_windows",):
                with self.subTest(name=name), self.assertRaisesRegex(AssertionError, "requires Windows"):
                    getattr(case, name)()
            request.assert_not_called()
            save.assert_not_called()

    def test_windows_limits_require_ownership_and_native_qt_before_network(self):
        base = {"WIN7_REAL_LIMIT_LLAMA": "1", "WIN7_REAL_LIMIT_TEST_OWNED": "YES",
                "QT_QPA_PLATFORM": "windows"}
        for override, message in (
            ({"WIN7_REAL_LIMIT_TEST_OWNED": "NO"}, "Reserve unauthenticated"),
            ({"QT_QPA_PLATFORM": "offscreen"}, "native Windows controls"),
        ):
            with patch.dict(os.environ, {**base, **override}), \
                    patch.object(test_ai_real_servers.sys, "platform", "win32"), \
                    patch.object(RealHTTP, "request") as request:
                with self.assertRaisesRegex(AssertionError, message):
                    test_ai_real_servers.RealModelLimitTests().test_llama_model_limits_windows()
                request.assert_not_called()

    def test_management_rejects_user_model_names(self):
        for name in ("qwen:latest", "", "win7-recovery-test-../user",
                     "win7-recovery-test-user/path", "win7-recovery-test-"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                owned_model(name)

    def test_llama_refuses_autoload_and_non_router_endpoints(self):
        for props in ({"role": "router", "models_autoload": True}, {"role": "model"}):
            with self.subTest(props=props):
                http = Mock()
                http.request.return_value = props
                router = LlamaRouter(http, "win7-recovery-test-primary")
                with self.assertRaises(ValueError):
                    router.prepare()
                self.assertEqual(router.initial, {})
                self.assertEqual(http.request.call_count, 1)

    def test_llama_refuses_management_outside_snapshot(self):
        http = Mock()
        router = LlamaRouter(http, "win7-recovery-test-primary")
        for name in ("user-model", router.primary, "win7-recovery-test-other"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                router.unload(name)
        http.request.assert_not_called()

    def test_llama_restores_only_original_test_preset_states(self):
        http = Mock()
        router = LlamaRouter(http, "win7-recovery-test-primary", "win7-recovery-test-healthy")
        router.initial = {router.primary: "loaded", router.healthy: "unloaded"}
        with patch.object(router, "load") as load, patch.object(router, "unload") as unload:
            router.restore()
        load.assert_called_once_with(router.primary)
        unload.assert_called_once_with(router.healthy)

    def test_llama_cleanup_waits_for_partial_load_before_unloading(self):
        http = Mock()
        router = LlamaRouter(http, "win7-recovery-test-primary")
        router.initial = {router.primary: "unloaded"}
        with patch.object(router, "models", return_value={router.primary: "loading"}), \
                patch.object(router, "wait_state") as wait:
            router.restore()
        http.request.assert_called_once_with("POST", "/models/unload", {"model": router.primary})
        self.assertEqual([call.args for call in wait.call_args_list],
                         [(router.primary, "loaded"), (router.primary, "unloaded")])

    def test_llama_restoring_partial_load_does_not_start_it_again(self):
        http = Mock()
        router = LlamaRouter(http, "win7-recovery-test-primary")
        router.initial = {router.primary: "loaded"}
        with patch.object(router, "models", return_value={router.primary: "loading"}), \
                patch.object(router, "wait_state") as wait:
            router.restore()
        http.request.assert_not_called()
        wait.assert_called_once_with(router.primary, "loaded")

    def test_http_management_rejects_public_and_credential_urls(self):
        for url in ("https://example.com", "http://user:password@127.0.0.1"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                RealHTTP("llama_cpp", url)
