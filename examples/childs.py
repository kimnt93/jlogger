import jlogger as jlog

logger = jlog.getLogger("trade")

if __name__ == "__main__":

    # build scoped logger once
    btc_logger = logger.with_value("symbol", "BTCUSDT")
    eth_logger = logger.with_value("symbol", "ETHUSDT")

    btc_logger.info().with_value("price", 65000).msg("tick")
    eth_logger.info().with_value("price", 3200).msg("tick")