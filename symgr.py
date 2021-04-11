#!/usr/bin/env python3
import argparse
import logging
import os
import sys
from pathlib import Path
from shutil import copy2
from subprocess import run

log = logging.getLogger(__name__)

SYSTEM_FILES = ('.git', '.gitignore')


class SymPath(type(Path())):  # type: ignore # https://stackoverflow.com/a/34116756
    def get_link_path(self):
        return self.__class__(os.readlink(self))

    def is_ignored(self):
        """Check if the specified path is in the ignore list"""
        return run(['git', 'check-ignore', '-q', self]).returncode == 0

    def backup(self):
        run(['bak', self], check=True)

    def backup_if_file_exists(self):
        if self.exists() and not self.is_dir():
            self.backup()

    def points_to(self, path):
        return self.get_link_path() == path

    def walk(self):
        """Return all files under this directory"""
        for file in sorted(self.iterdir()):
            if file.is_dir():
                yield from file.walk()
            else:
                yield file

    def ensure_parent_exists(self):
        return self.parent.mkdir(parents=True, exist_ok=True)

    def safe_symlink_to(self, other):
        """Ensure destination path exists, back up any existing file"""
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

    def link_at(self, target, relative_to=None):
        assert self.exists(), "source must exist to be linked to"

        if not relative_to:
            relative_to = self.parent if self.is_file() else self

        assert relative_to <= self, "relative to must be a parent of source"  # relative to must be a parent dir
        assert self.resolve() != target.resolve(), "source path must not equal target path"

        if self.is_ignored():
            log.debug(f"{self} is ignored")
            return

        if self.name in SYSTEM_FILES:
            log.debug(f"Ignoring system file {self}")
            return

        if self.is_dir():
            for path in self.walk():
                dest = target / path.relative_to(relative_to)
                path.link_at(dest, relative_to)
        else:
            source_path = self.resolve()
            final_path = target / self.name if target.is_dir() else target
            if final_path.handle_existing_symlink(source_path):
                final_path.safe_symlink_to(source_path)

    def bless(self, to_dir):
        """To bless means to copy a file to a path, then symlink it back to the
        original location, backing up if necessary"""
        assert self.exists(), "source must exist to bless it"
        to_path = to_dir / self.name
        to_path.ensure_parent_exists()
        to_path.backup_if_file_exists()
        copy2(self, to_path)
        to_path.link_at(self)


def main(args):
    frm = SymPath(args.frm)
    to = SymPath(args.to)

    if frm.is_file() and to.is_dir():
        frm.bless(to)
    else:
        frm.link_at(to)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Symlink manager")
    parser.add_argument('frm', metavar='from', help="The directory in which to create links, or the file to bless")
    parser.add_argument('to', help='The directory the links point to, or the dest dir for the blessed file')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    sys.exit(main(args))
