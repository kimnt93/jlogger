import io
import json
import logging
import unittest
import uuid

import jlogger as jlog
from jlogger import config
from jlogger.formatter import JsonFormatter


class LoggerTests(unittest.TestCase):
    def setUp(self) -> None:
        config._configured = False
        root = logging.getLogger()
        root.handlers.clear()
        root.setLevel(logging.NOTSET)
        jlog.setTimeFormat(jlog.TimeFormat.UNIX)

    def make_logger(self, name: str = "trade"):
        logger = jlog.getLogger(name)
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JsonFormatter())

        root = logging.getLogger()
        root.handlers.clear()
        root.addHandler(handler)
        root.setLevel(logging.DEBUG)
        return logger, stream

    def test_existing_fluent_api_emits_json(self) -> None:
        logger, stream = self.make_logger()

        logger.with_value("symbol", "BTCUSDT").info().with_value("price", 65000).msg("tick")

        payload = json.loads(stream.getvalue())
        self.assertEqual(payload["logger"], "trade")
        self.assertEqual(payload["level"], "info")
        self.assertEqual(payload["message"], "tick")
        self.assertEqual(payload["symbol"], "BTCUSDT")
        self.assertEqual(payload["price"], 65000)

    def test_unsupported_values_fall_back_to_string(self) -> None:
        logger, stream = self.make_logger("api")
        request_id = uuid.uuid4()

        logger.info().with_value("request_id", request_id).msg("request received")

        payload = json.loads(stream.getvalue())
        self.assertEqual(payload["request_id"], str(request_id))

    def test_snake_case_aliases_and_batch_values(self) -> None:
        logger, stream = self.make_logger("worker")

        jlog.set_level("debug")
        jlog.get_logger("worker").debug().with_values(task="sync", attempt=2).msg("started")

        payload = json.loads(stream.getvalue())
        self.assertEqual(payload["level"], "debug")
        self.assertEqual(payload["task"], "sync")
        self.assertEqual(payload["attempt"], 2)

    def test_set_level_before_get_logger_is_preserved(self) -> None:
        jlog.setLevel("error")
        logger = jlog.getLogger("quiet")
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JsonFormatter())

        root = logging.getLogger()
        root.handlers.clear()
        root.addHandler(handler)

        logger.info().msg("hidden")
        logger.error().msg("visible")

        lines = [line for line in stream.getvalue().splitlines() if line]
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["message"], "visible")


if __name__ == "__main__":
    unittest.main()
