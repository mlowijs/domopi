import subprocess


def save_image(file_name):
    subprocess.call(["fswebcam",
                     "-q",
                     "-r", "1280x720",
                     file_name])