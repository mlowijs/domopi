import subprocess


def play_sound(file_path):
    subprocess.Popen(["mpg123",
                      file_path])