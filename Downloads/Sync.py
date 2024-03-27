#!/usr/bin/env python3

"""
========================
== Level-2 Downloader ==
========================

Description:
    - Script to facilate the download of a Level-2 production.

Usage:
    - run ./sync.py -h for help.

Notes:
    - Remember to set up the ssh keys for the remote server first! (i.e use kinit to get a token).

"""

import subprocess
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count
import psutil

# setting some constants for default values
DEFAULT_BW_LIMIT = 50000  # e.g. 50 MB/s
DEFAULT_LOG_FILENAME = "L2_production.log"
SEPARATE_LOG_FILENAME = f"{DEFAULT_LOG_FILENAME}-additonal-info.log"


def setup_logging(log_filename, separate_log_filename):
    # setting up the outut logging file
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # separate logger file for more detailed info
    separate_logger = logging.getLogger("separate")
    separate_handler = logging.FileHandler(separate_log_filename)
    separate_formatter = logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    separate_handler.setFormatter(separate_formatter)
    separate_logger.addHandler(separate_handler)
    separate_logger.setLevel(logging.INFO)

    # stream handler for terminal output so we can what is happening :')
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    separate_logger.addHandler(stream_handler)

    return separate_logger


def download_directory(directory, args, separate_logger):
    try:
        source = f"{args.source}/{directory}"
        destination = f"{args.destination}/{directory}"
        # destination = f"{args.destination}/" # for updating individual files

        rsync_path = "rsync"  # or set /usr/bin/rsync if not in PATH
        rsync_args = [rsync_path, "-vzraWPe", "ssh", f"--bwlimit={args.bwlimit}"]
        # todo: add cmd line args in script for rysnc args

        if args.exclude:
            rsync_args.extend(["--exclude", args.exclude])

        rsync_args.extend([source, destination])

        logging.info(f"Running rsync command: {' '.join(rsync_args)}")
        separate_logger.info(f"Running rsync command: {' '.join(rsync_args)}")

        process = subprocess.run(
            rsync_args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        stdout_str = process.stdout.decode("utf-8")
        stderr_str = process.stderr.decode("utf-8")

        logging.info(f"Output for {directory}:\n{stdout_str}\n{stderr_str}")
        separate_logger.info(f"Output for {directory}:\n{stdout_str}\n{stderr_str}")
        return directory, True

    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to download {directory}: {e}")
        separate_logger.error(f"Failed to download {directory}: {e}")
        return directory, False


def main():
    parser = argparse.ArgumentParser(
        description="Run parallel rsync downloads of directories from a remote server"
    )
    parser.add_argument(
        "--source",
        type=str,
        required=True,
        help="Source directory"
    )

    parser.add_argument(
        "--destination",
        type=str,
        required=True,
        help="Destination directory"
    )

    parser.add_argument(
        "--bwlimit",
        type=int,
        default=DEFAULT_BW_LIMIT,
        help="Bandwidth limit for rsync (in KB/s)",
    )

    parser.add_argument(
        "--exclude",
        type=str,
        help="Pattern to exclude from rsync")

    parser.add_argument(
        "--retry",
        action="store_true",
        help="Retry failed downloads")

    parser.add_argument(
        "--filename",
        type=str,
        default=DEFAULT_LOG_FILENAME,
        help="Log filename"
    )

    args = parser.parse_args()

    separate_logger = setup_logging(args.filename, SEPARATE_LOG_FILENAME)

    subdirectories = [
        "1l/5j3b_discriminant_ttH/",
        "1l/5j3b_discriminant_ttlight/",
        "1l/5j3b_discriminant_ttc/",
        "1l/5j3b_discriminant_ttbb/",
        "1l/5j3b_discriminant_ttb/",
        "1l/5j3b_discriminant_ttB/",
        "1l/boosted/",
        "2l/3j3b_discriminant_ttH/",
        "2l/3j3b_discriminant_ttlight/",
        "2l/3j3b_discriminant_ttc/",
        "2l/3j3b_discriminant_ttbb/",
        "2l/3j3b_discriminant_ttb/",
        "2l/3j3b_discriminant_ttB/",
        "2l/boosted_STXS5/",
        "2l/boosted_STXS6/",
    ]
    directories = subdirectories

    # set up the executor to run the downloads in parallel, with a max of 4 threads to prevent overloading the server
    # i.e set num to how many concurrent downloads you want, use with caution...
    with ThreadPoolExecutor(max_workers=min(4, cpu_count())) as executor:
        future_to_dir = {
            executor.submit(
                download_directory, directory, args, separate_logger
            ): directory
            for directory in directories
        }
        retry_dirs = []
        # now, wait for the downloads to finish and retry any failed downloads if this is requested
        for future in as_completed(future_to_dir):
            directory, success = future.result()
            if not success and args.retry:
                retry_dirs.append(directory)

        if retry_dirs:
            logging.info("Retrying failed downloads...")
            separate_logger.info("Retrying failed downloads...")
            for directory in retry_dirs:
                executor.submit(download_directory, directory, args, separate_logger)

    # some log stats of the downloads and CPUs utilised
    separate_logger.info(f"Total downloads: {len(directories)}")
    separate_logger.info(f"Total CPUs: {psutil.cpu_count(logical=False)}")


if __name__ == "__main__":
    main()
