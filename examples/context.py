import uuid
import jlogger as jlog

logger = jlog.getLogger("api")

def handle_request(user_id: int):
    # initial context logger
    req_logger = logger.with_value("request_id", uuid.uuid4()) \
                       .with_value("user_id", user_id)

    req_logger.info().msg("request received")

    req_logger.info() \
        .with_value("status", 200) \
        .msg("request completed")


if __name__ == "__main__":
    handle_request(42)