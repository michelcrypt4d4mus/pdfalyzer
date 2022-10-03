from datetime import datetime


def timestamp_for_filename() -> str:
    """Returns a string showing current time in a file name friendly format"""
    return datetime.now().strftime("%Y-%m-%dT%H.%M.%S")


def load_word_list(file_path):
    """For very simple files (1 col CSVs, if you wll)"""
    with open(file_path, 'r') as f:
        return [line.rstrip().lstrip() for line in f.readlines()]


def load_binary_data(file_path):
    with open(file_path, 'rb') as f:
        return f.read()
