import logging
import time
import argparse

from bot_v2 import DeterministicTradingBotV2


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger('run_bot_v2')


def main(duration: int):
    logger.info('Starting in LIVE mode (requires MetaTrader5)')
    bot = DeterministicTradingBotV2()
    try:
        bot.connect()
    except Exception as e:
        logger.error(f'MT5 connect failed: {e}')
        return

    # run until duration seconds elapse
    start = time.time()
    it = 0
    while time.time() - start < duration:
        it += 1
        logger.info(f'Iteration {it}')
        try:
            bot.run_iteration()
        except Exception:
            logger.exception('Iteration error')
        time.sleep(1)

    # report diagnostics
    try:
        bot.report_stats()
    except Exception:
        logger.exception('report_stats failed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--log-duration', type=int, default=3600, help='Duration in seconds to run and log diagnostics')
    args = parser.parse_args()
    main(args.log_duration)
