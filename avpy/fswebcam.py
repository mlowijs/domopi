import subprocess


def save_image(file_name):
    subprocess.call(["fswebcam",
                     "-q",
                     "-r", "1280x720",
                     "--rotate", "90",
                     file_name])