#!/usr/bin/env python3
import argparse
import logging
import os
import sys
from pathlib import Path
from shutil import copy2
from subprocess import DEVNULL, run

log = logging.getLogger(__name__)

SYSTEM_FILES = ('.git', '.gitignore')


class SymPath(type(Path())):  # type: ignore # https://stackoverflow.com/a/34116756
    def get_link_path(self):
        return self.__class__(os.readlink(self))

    def points_to(self, path):
        return self.get_link_path() == path

    def is_ignored(self):
        """Check if the specified path is in the ignore list"""
        cmd = ['git', 'check-ignore', '-q', self]
        return run(cmd, stderr=DEVNULL).returncode == 0

    def is_system_file(self):
        return self.name in SYSTEM_FILES

    def backup(self):
        run(['bak', self], check=True)

    def backup_if_file_exists(self):
        if self.exists() and not self.is_dir():
            self.backup()

    def ensure_parent_exists(self):
        return self.parent.mkdir(parents=True, exist_ok=True)

    def safe_symlink_to(self, other):
        """Ensure destination path exists, back up any existing file"""
        log.info(f"Pointing {self} -> {other}")
        self.ensure_parent_exists()
        self.backup_if_file_exists()
        self.symlink_to(other)

    def handle_existing_symlink(self, to_path):
        """Delete existing symlink if exists and is wrong.

        Returns True if anything still needs to be done,
        False if existing symlink is already correct.
        """
        if not self.is_symlink():
            return True

        log.debug(f"{self} is an existing symlink")
        if self.points_to(to_path):
            log.debug(f"{self} already points to {to_path}, making no changes")
            return False  # nothing to do

        log.info(f"{self} points to {self.get_link_path()}. Removing.")
        self.unlink()
        return True

    def resolve_target(self, name):
        return self / name if self.is_dir() else self

    def link_at(self, target):
        source = self.resolve()  # make absolute
        if not source.exists():
            log.info(f"{source} doesn't exist, skipping")
            return True

        if target.is_symlink() and target.points_to(source):
            log.debug(f"{target} is already a correct symlink; doing nothing")
            return True

        assert source != target.resolve(), "source path must not equal target path"

        if source.is_ignored():
            log.debug(f"{source} is ignored")
            return

        if source.is_system_file():
            log.debug(f"Ignoring system file {source}")
            return

        if source.is_dir():
            log.info(f"Linking directory {source} to {target}")
            for path in sorted(source.iterdir()):
                final_target = target / path.relative_to(source)
                path.link_at(final_target)
        else:
            final_path = target.resolve_target(source.name)
            if final_path.handle_existing_symlink(source):
                final_path.safe_symlink_to(source)

    def bless(self, target):
        """To bless means to copy a file to a path, then symlink it back to the
        original location, backing up if necessary"""
        assert self.exists(), "source must exist to bless it"
        to_path = target.resolve_target(self.name)
        to_path.ensure_parent_exists()
        to_path.backup_if_file_exists()
        copy2(self, to_path)
        to_path.link_at(self)


def main(args):
    frm = SymPath(args.frm)
    to = SymPath(args.to)
    if args.bless:
        frm.bless(to)
    else:
        frm.link_at(to)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Symlink manager")
    parser.add_argument('frm', metavar='from', help="The directory in which to create links, or the file to bless")
    parser.add_argument('to', help='The directory the links point to, or the dest dir for the blessed file')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('-b', '--bless', action='store_true', help='"Bless" the from location to the destination directory. Copy it and link back to it')
    args = parser.parse_args()

    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s:%(message)s")

    sys.exit(main(args))
