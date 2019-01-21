from VKObserver import VKObserver
import logging
import traceback


def main():
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s:%(message)s')
    main_logger = logging.getLogger("root")
    log_file = logging.FileHandler(filename="HECKUPS.log")
    main_logger.addHandler(log_file)

    try:
        spy = VKObserver()
        spy.run()
    except: # except LITERALLY hugging EVERYTHING
        main_logger.critical(traceback.format_exc())

if __name__ == "__main__":
    main()
