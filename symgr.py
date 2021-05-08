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

    def safe_symlink_to(self, other, bless=False, dry_run=False):
        """Ensure destination path exists, back up any existing file"""
        me = self.resolve_target(other.name)
        d = f" ({dry_run=})" if dry_run else ''
        log.info(f"{me} -> {other}{d}")

        if dry_run:
            return True

        if me.handle_existing_symlink(other):
            me.ensure_parent_exists()
            me.backup_if_file_exists()
            if bless:
                me = me.resolve()
                copy2(other, me)
                other.backup_if_file_exists()
                other.symlink_to(me)
            else:
                me.symlink_to(other)

        return True

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

    def link_at(self, target, bless=False, dry_run=False):
        source = self.resolve()  # make absolute
        if not source.exists():
            log.info(f"{source} doesn't exist, skipping")
            return True

        if target.is_symlink() and target.points_to(source):
            log.debug(f"{target} is already a correct symlink; doing nothing")
            return True

        if source == target.resolve():
            log.critical("source path must not equal target path")
            return False

        if bless and not source.exists():
            log.critical(f"{source} must exist to bless it")
            return False

        if not args.no_ignore and source.is_ignored():
            log.debug(f"{source} is ignored")
            return False

        if source.is_system_file():
            log.debug(f"Ignoring system file {source}")
            return False

        if source.is_dir():
            log.info(f"Linking directory {source} to {target}")
            for path in sorted(source.iterdir()):
                final_target = target / path.relative_to(source)
                path.link_at(final_target, bless=bless, dry_run=dry_run)
        else:
            target.safe_symlink_to(source, bless=bless, dry_run=dry_run)

        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Symlink manager")
    parser.add_argument('frm', metavar='from', help="The directory in which to create links, or the file to bless")
    parser.add_argument('to', help='The directory the links point to, or the dest dir for the blessed file')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('-b', '--bless', action='store_true', help='"Bless" the from location to the destination directory. Copy it and link back to it')
    parser.add_argument('-I', '--no-ignore', action='store_true', help="Don't respect git ignore")
    parser.add_argument('-D', '--dry-run', action='store_true', help="Don't take any action, show what would be done")
    args = parser.parse_args()

    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s:%(message)s")
    result = SymPath(args.frm).link_at(SymPath(args.to), bless=args.bless, dry_run=args.dry_run)
    sys.exit(not result)
