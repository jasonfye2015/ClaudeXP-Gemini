import json
import os
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, QEventLoop, QTimer, Signal
from PySide6.QtWidgets import QApplication

from win7_2011.tests.test_messaging import LlamaServerHandler
from win7_2011.tests.test_ui import sample_account
from win7_2011.win7sim import config
from win7_2011.win7sim.ai_service import AIChannel, AIService
from win7_2011.win7sim.ai_settings import AISettings, ROLE_LABELS, load_ai_settings, save_ai_settings
from win7_2011.win7sim.apps import MessengerApp
from win7_2011.win7sim.desktop import DesktopPage


class ControlledBackend(QObject):
    modelsListed = Signal(bool, object, str)
    connectionFinished = Signal(bool, str)
    responseFinished = Signal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_busy = False
        self.is_connected = False
        self.model_name = ""
        self.calls = []

    def list_models(self, _url):
        self.modelsListed.emit(True, ["chat", "world", "memory"], "Available.")

    def connect_to_server(self, _url, model):
        self.model_name = model
        self.is_connected = True
        self.connectionFinished.emit(True, "Connected.")

    def send_chat(self, messages):
        self.is_busy = True
        self.calls.append((self.model_name, messages))

    def finish(self, success=True, text="Generated reply"):
        self.is_busy = False
        self.responseFinished.emit(success, text)

    def cancel(self):
        self.finish(False, "Cancelled.")


class AISettingsTests(unittest.TestCase):
    def test_single_local_gguf_is_selected_for_first_run(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            system = root / "System"
            models = root / "Models"
            models.mkdir()
            model = models / "NemoMix-Unleashed-12B-Q4_K_M.gguf"
            model.write_bytes(b"fixture")
            executable = root / "Runtime" / "llama-server.exe"
            with (
                patch.object(config, "SYSTEM_ROOT", system),
                patch.object(config, "MODELS_ROOT", models),
                patch.object(config, "LLAMA_SERVER_EXECUTABLE", executable),
            ):
                settings = load_ai_settings()
                self.assertEqual(settings.llama_model_path, str(model))
                self.assertEqual(
                    settings.llama_server_executable, str(executable)
                )
                self.assertEqual(
                    settings.models["direct"], "NemoMix-Unleashed-12B-Q4_K_M"
                )
                # The discovered paths become stable local settings for later launches.
                saved = load_ai_settings()
                self.assertEqual(saved.llama_model_path, str(model))
                self.assertEqual(saved.models["direct"], settings.models["direct"])

    def test_multiple_local_ggufs_are_not_guessed(self):
        with tempfile.TemporaryDirectory() as directory:
            models = Path(directory) / "Models"
            models.mkdir()
            (models / "first.gguf").write_bytes(b"fixture")
            (models / "second.GGUF").write_bytes(b"fixture")
            with (
                patch.object(config, "SYSTEM_ROOT", Path(directory) / "System"),
                patch.object(config, "MODELS_ROOT", models),
            ):
                settings = load_ai_settings()
                self.assertEqual(settings.llama_model_path, "")
                self.assertEqual(settings.models["direct"], "")

    def test_llama_server_launch_options_round_trip_in_central_settings(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
            config, "SYSTEM_ROOT", Path(directory)
        ):
            settings = AISettings(
                backend="llama_cpp",
                url="http://127.0.0.1:9931",
                models=dict.fromkeys(ROLE_LABELS, "nemomix-12b"),
                llama_server_executable=r"C:\Win7\Storage\Runtime\llama.cpp\llama-server.exe",
                llama_model_path=r"C:\Win7\Storage\Models\NemoMix.gguf",
                llama_gpu_layers=73,
            )
            save_ai_settings(settings)
            loaded = load_ai_settings()
            self.assertEqual(loaded.backend, "llama_cpp")
            self.assertEqual(
                loaded.llama_server_executable,
                settings.llama_server_executable,
            )
            self.assertEqual(loaded.llama_model_path, settings.llama_model_path)
            self.assertEqual(loaded.llama_gpu_layers, 73)

    def test_legacy_settings_are_imported_for_all_roles_and_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "ollama.json"
            legacy.write_text(json.dumps({"url": "http://localhost:11434", "model": "old-model"}))
            history_root = root / "Messenger"
            history = [
                {"role": "user", "content": "Existing transcript"},
                {"role": "assistant", "content": "Keep this reply"},
            ]
            with patch.object(config, "SYSTEM_ROOT", root), patch.object(
                config, "MESSENGER_HISTORY", history_root
            ), patch.object(config, "MODELS_ROOT", root / "Models"), patch.dict(
                os.environ, {}, clear=True
            ):
                config.save_messenger_history("test-contact", history, "rook")
                transcript = history_root / "Profiles" / "rook" / "test-contact.json"
                transcript_before = transcript.read_bytes()
                settings = load_ai_settings()
                self.assertEqual(set(settings.models.values()), {"old-model"})
                self.assertEqual(settings.backend, "llama_cpp")
                self.assertEqual(settings.url, "http://127.0.0.1:9931")
                self.assertEqual(config.load_messenger_history("test-contact", "rook"), history)
                self.assertEqual(transcript.read_bytes(), transcript_before)
                before = legacy.read_text()
                settings.models["background"] = "small-model"
                save_ai_settings(settings)
                self.assertEqual(load_ai_settings().models["background"], "small-model")
                self.assertEqual(legacy.read_text(), before)
                self.assertEqual(json.loads((root / "ai.json").read_text())["version"], 5)

    def test_invalid_central_settings_do_not_silently_revert_to_legacy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ai.json").write_text("broken")
            with patch.object(config, "SYSTEM_ROOT", root), self.assertRaises(ValueError):
                load_ai_settings()


class AIServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.ai = AIService(
            backend_factory=ControlledBackend,
            settings=AISettings(models={"direct": "chat", "background": "world", "summary": "memory"}),
        )
        self.ai.test_connection()

    def tearDown(self):
        self.ai.stop()
        self.ai.deleteLater()
        self.app.processEvents()

    def test_jobs_are_serial_prioritized_and_routed_to_role_models(self):
        results = []
        self.ai.jobFinished.connect(lambda *args: results.append(args))
        world = self.ai.submit("background", [{"role": "user", "content": "Update"}])
        direct = self.ai.submit("direct", [{"role": "user", "content": "Hello"}])
        summary = self.ai.submit("summary", [{"role": "user", "content": "Summarize"}])
        self.app.processEvents()
        self.assertEqual([call[0] for call in self.ai.backend.calls], ["chat"])
        self.assertEqual(self.ai.queue_count, 2)
        self.ai.backend.finish()
        self.app.processEvents()
        self.assertEqual([call[0] for call in self.ai.backend.calls], ["chat", "memory"])
        self.ai.backend.finish()
        self.app.processEvents()
        self.ai.backend.finish()
        self.assertEqual([item[0] for item in results], [direct, summary, world])

    def test_defender_scan_temporarily_prioritizes_queued_background_work(self):
        self.ai.set_maintenance_priority_mode(True)
        self.ai.submit("background", [{"role": "user", "content": "World update"}])
        self.ai.submit("direct", [{"role": "user", "content": "New chat"}])
        self.app.processEvents()
        self.assertEqual(self.ai.backend.calls[-1][0], "world")

        self.ai.backend.finish(text="Background update")
        self.app.processEvents()
        self.assertEqual(self.ai.backend.calls[-1][0], "chat")
        self.ai.backend.finish(text="Direct reply")
        self.app.processEvents()

        self.ai.set_maintenance_priority_mode(False)
        self.assertFalse(self.ai.maintenance_priority_mode)

    def test_background_generation_can_use_a_bounded_output_limit(self):
        self.ai.submit(
            "background", [{"role": "user", "content": "Write a short opener"}],
            output_limit=128,
        )
        self.app.processEvents()
        self.assertEqual(self.ai.backend.reply_limit, 128)
        self.ai.backend.finish(text="A short line.")
        self.app.processEvents()
        with self.assertRaises(ValueError):
            self.ai.submit("background", [], output_limit=0)

    def test_llm_diagnostic_signals_capture_sent_prompts_outputs_and_phases(self):
        requests, responses, phases = [], [], []
        self.ai.llmRequestSent.connect(lambda *args: requests.append(args))
        self.ai.llmResponseCaptured.connect(lambda *args: responses.append(args))
        self.ai.llmPhaseChanged.connect(lambda *args: phases.append(args))
        background_messages = [{"role": "user", "content": "Private full background prompt"}]
        direct_messages = [
            {"role": "system", "content": "Full contact instruction"},
            {"role": "user", "content": "Exact user message"},
        ]
        self.ai.submit("background", background_messages)
        direct_id = self.ai.submit("direct", direct_messages)
        self.app.processEvents()
        self.assertEqual(len(requests), 1)
        self.assertEqual(
            requests[0],
            (direct_id, "direct", "chat", direct_messages),
        )
        self.assertEqual(
            [(request_id, phase) for request_id, _role, phase in phases],
            [(direct_id, "sending"), (direct_id, "generating")],
        )
        self.ai.backend.finish(text="Unfiltered raw model output")
        self.app.processEvents()
        self.assertEqual(responses[0], (direct_id, "direct", True, "Unfiltered raw model output"))
        self.assertEqual(
            [(request_id, phase) for request_id, _role, phase in phases[:4]],
            [(direct_id, "sending"), (direct_id, "generating"),
             (direct_id, "output"), (direct_id, "idle")],
        )
        self.assertEqual(len(requests), 2)
        world_id, role, model, sent_messages = requests[1]
        self.assertEqual((role, model, sent_messages), (
            "background", "world", background_messages,
        ))
        self.ai.backend.finish(False, "model request failed")
        self.assertEqual(
            responses[-1], (world_id, "background", False, "model request failed")
        )

    def test_cancelling_one_channel_does_not_cancel_another(self):
        first = AIChannel(self.ai)
        second = AIChannel(self.ai)
        first_results, second_results = [], []
        first.responseFinished.connect(lambda *args: first_results.append(args))
        second.responseFinished.connect(lambda *args: second_results.append(args))
        first.send_chat([{"role": "user", "content": "First"}])
        second.send_chat([{"role": "user", "content": "Second"}])
        self.app.processEvents()
        first.cancel()
        self.app.processEvents()
        self.assertEqual(first_results, [(False, "Request cancelled.")])
        self.assertTrue(second.is_busy)
        self.ai.backend.finish(text="Second response")
        self.assertEqual(second_results, [(True, "Second response")])

    def test_simulated_outage_cancels_direct_work_but_keeps_engine_status_separate(self):
        results = []
        self.ai.jobFinished.connect(lambda *args: results.append(args))
        self.ai.submit("direct", [{"role": "user", "content": "Hello"}])
        self.app.processEvents()
        self.ai.set_simulated_availability(False, True)
        self.assertFalse(results[0][1])
        self.assertTrue(self.ai.connected)
        with self.assertRaises(RuntimeError):
            self.ai.submit("direct", [])
        self.ai.submit("background", [])
        self.app.processEvents()
        self.assertEqual(self.ai.queue_count, 1)
        self.ai.set_simulated_availability(True, False)
        self.app.processEvents()
        self.assertEqual(self.ai.backend.calls[-1][0], "world")

    def test_settings_cannot_change_during_active_generation(self):
        self.ai.submit("direct", [])
        self.app.processEvents()
        with self.assertRaises(RuntimeError):
            self.ai.apply(AISettings())
        self.assertEqual(self.ai.settings.models["direct"], "chat")

    def test_reconnect_rejects_active_queued_and_stopped_work(self):
        with patch.object(self.ai.backend, "list_models", wraps=self.ai.backend.list_models) as probe:
            self.ai.submit("direct", [])
            with self.assertRaises(RuntimeError):
                self.ai.reconnect()
            self.app.processEvents()
            with self.assertRaises(RuntimeError):
                self.ai.reconnect()
            self.assertFalse(self.ai.can_reconnect)
            self.assertEqual(probe.call_count, 0)
            self.ai.cancel_all()
            self.assertTrue(self.ai.can_reconnect)
            self.ai.set_simulated_availability(True, True)
            self.ai.submit("background", [])
            self.app.processEvents()
            with self.assertRaises(RuntimeError):
                self.ai.reconnect()
            self.assertEqual(probe.call_count, 0)
            self.ai.cancel_all()
            self.ai.stop()
            with self.assertRaises(RuntimeError):
                self.ai.reconnect()
            self.assertFalse(self.ai.can_reconnect)
            self.assertEqual(probe.call_count, 0)


class CentralOptionsIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), LlamaServerHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def wait_idle(self, ai):
        loop = QEventLoop()
        timer = QTimer()
        timer.setInterval(5)
        timer.timeout.connect(lambda: loop.quit() if not ai.is_busy else None)
        timer.start()
        QTimer.singleShot(3000, loop.quit)
        loop.exec()
        timer.stop()
        self.assertFalse(ai.is_busy, "Local request did not finish before timeout")

    def test_options_connects_shared_messenger_and_returns_real_server_text(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
            config, "SYSTEM_ROOT", Path(directory)
        ):
            desktop = DesktopPage(sample_account())
            desktop.open_messenger()
            messenger = desktop._windows["messenger"].widget()
            self.assertIsInstance(messenger, MessengerApp)
            self.assertIs(messenger.ai, desktop.ai_service)
            self.assertFalse(hasattr(messenger, "url_edit"))
            messenger.ai_settings_button.click()
            options = desktop.options_window
            self.assertTrue(options.isVisible())
            self.assertEqual(options.tabs.currentIndex(), options.ai_tab_index)
            options.url_edit.setText(f"http://127.0.0.1:{self.server.server_port}")
            for combo in options.model_combos.values():
                combo.setEditText("test-model:3b")
            options.apply_button.click()
            self.wait_idle(desktop.ai_service)
            self.assertTrue(messenger.send_button.isEnabled())
            self.assertIn("other-model", desktop.ai_service.available_models)
            self.assertEqual(set(load_ai_settings().models), set(ROLE_LABELS))
            LlamaServerHandler.reply_text = "Central service response."
            messenger.message_edit.setText("A test conversation")
            messenger.send_button.click()
            self.wait_idle(desktop.ai_service)
            self.assertIn("Central service response.", messenger.transcript.toPlainText())
            self.assertEqual(LlamaServerHandler.requests[-1]["model"], "test-model:3b")
            history = messenger.contact_histories[messenger.selected_contact.contact_id]
            before = list(history)
            options.model_combos["direct"].setEditText("other-model")
            options.apply_button.click()
            self.wait_idle(desktop.ai_service)
            self.assertEqual(history, before, "Changing models must not clear conversations")
            self.assertEqual(messenger.client.model_name, "other-model")
            messenger.message_edit.setText("Use the new model")
            messenger.send_button.click()
            self.wait_idle(desktop.ai_service)
            self.assertEqual(LlamaServerHandler.requests[-1]["model"], "other-model")
            desktop.stop_session()
            desktop.close()
            desktop.deleteLater()
            self.app.processEvents()
