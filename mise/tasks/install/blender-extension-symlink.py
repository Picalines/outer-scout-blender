#!python
# [MISE] description="Create a symlink link in the Blender Extension Repository for script reloading"
import os
import sys
from pathlib import Path


def info(message: str):
    print(f"info: {message}")


def error(message: str):
    print(f"error: {message}")
    sys.exit(1)


def getenv_or_exit(env: str):
    if not (value := os.getenv(env)):
        error(f"{env} environment variable not set or empty. See .env.example")
    return value


src_path = Path(getenv_or_exit("REPO_PATH"), "src")
symlink_path = Path(getenv_or_exit("BLENDER_EXTENSION_REPO"), getenv_or_exit("PROJECT_NAME"))

info(f"going to create the symlink at {symlink_path}")

if symlink_path.exists():
    if not symlink_path.is_symlink():
        error("the path exists and it's not a symlink, aborting")

    info("the path exists and it's a symlink, unlinking")
    symlink_path.unlink()

os.symlink(src_path, symlink_path, target_is_directory=True)

info("symlink created")
