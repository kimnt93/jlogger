import io
import json
import unittest
import uuid

import jlogger as jlog


class LoggerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.stream = io.StringIO()
        jlog.set_output(self.stream)
        jlog.setLevel("debug")
        jlog.setTimeFormat(jlog.TimeFormat.UNIX)

    def lines(self):
        return [line for line in self.stream.getvalue().splitlines() if line]

    def test_existing_fluent_api_emits_json(self) -> None:
        logger = jlog.getLogger("trade")
        logger.with_value("symbol", "BTCUSDT").info().with_value("price", 65000).msg("tick")

        payload = json.loads(self.lines()[0])
        self.assertEqual(payload["logger"], "trade")
        self.assertEqual(payload["level"], "info")
        self.assertEqual(payload["message"], "tick")
        self.assertEqual(payload["symbol"], "BTCUSDT")
        self.assertEqual(payload["price"], 65000)

    def test_unsupported_values_fall_back_to_string(self) -> None:
        logger = jlog.getLogger("api")
        request_id = uuid.uuid4()

        logger.info().with_value("request_id", request_id).msg("request received")

        payload = json.loads(self.lines()[0])
        self.assertEqual(payload["request_id"], str(request_id))

    def test_snake_case_aliases_and_batch_values(self) -> None:
        jlog.set_level("debug")
        jlog.get_logger("worker").debug().with_values(task="sync", attempt=2).msg("started")

        payload = json.loads(self.lines()[0])
        self.assertEqual(payload["level"], "debug")
        self.assertEqual(payload["task"], "sync")
        self.assertEqual(payload["attempt"], 2)

    def test_scoped_context_is_not_shared(self) -> None:
        base = jlog.getLogger("svc").with_value("service", "api")
        child = base.with_value("request_id", "abc")

        base.info().msg("base")
        child.info().with_value("extra", 1).msg("child")

        base_payload = json.loads(self.lines()[0])
        child_payload = json.loads(self.lines()[1])
        self.assertNotIn("request_id", base_payload)
        self.assertEqual(child_payload["request_id"], "abc")
        self.assertEqual(child_payload["extra"], 1)

    def test_global_level_filters(self) -> None:
        jlog.setLevel("error")
        logger = jlog.getLogger("quiet")

        logger.info().msg("hidden")
        logger.error().msg("visible")

        lines = self.lines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["message"], "visible")

    def test_per_logger_level_override(self) -> None:
        jlog.setLevel("critical")
        chatty = jlog.getLogger("chatty", level="debug")

        chatty.debug().msg("still emitted")

        lines = self.lines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["level"], "debug")


if __name__ == "__main__":
    unittest.main()
