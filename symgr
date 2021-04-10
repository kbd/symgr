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
    def current_link_path(self):
        return self.__class__(os.readlink(self))

    def is_ignored(self):
        """Check if the specified path is in the ignore list"""
        return run(['git', 'check-ignore', '-q', str(self)]).returncode == 0

    def backup(self):
        run(['bak', self], check=True)

    def walk(self):
        """Return all files under this directory"""
        for file in self.iterdir():
            if file.is_dir():
                yield from file.walk()
            else:
                yield file


def link_directories(source_dir, dest_dir):
    """Symlink all files within source_dir into dest_dir."""
    source_dir = SymPath(source_dir).expanduser()
    dest_dir = SymPath(dest_dir).expanduser()
    assert source_dir != dest_dir
    _link_directories(source_dir, dest_dir)


def _link_directories(source_dir, dest_dir):
    """Do the linking without validation or type coercion.

    Useful as an entry-point for tests"""
    log.info(f"Creating symlinks: {source_dir} -> {dest_dir}")
    for file in sorted(source_dir.walk()):
        source_path = file
        dest_path = dest_dir / file.relative_to(source_dir)

        # don't link files ignored by git
        if source_path.is_ignored():
            log.debug(f"{source_path} is ignored")
            continue
        elif source_path.name in SYSTEM_FILES:
            log.debug(f"Ignoring system file {source_path}")
            continue

        log.debug(f"Creating link at {dest_path} to {source_path}")
        link_file(source_path, dest_path)


def link_file(link_path: Path, dest_path: Path):
    # coerce to SymPaths in case
    link_path = SymPath(link_path).resolve()  # ensure absolute
    dest_path = SymPath(dest_path)
    if link_path.parent.resolve() == dest_path.parent.resolve():
        msg = (
            f"Parent directories being linked point to the same place: "
            f"{link_path.parent} == {dest_path.parent}"
        )
        log.error(msg)
        raise Exception(msg)

    # create parent directories if necessary
    if not dest_path.parent.exists():
        log.info(f"Creating directory: {dest_path.parent}")
        dest_path.parent.mkdir(parents=True)

    # handle existing symlink
    if dest_path.is_symlink():
        log.debug(f"{dest_path} is an existing symlink")
        curr_link_path = dest_path.current_link_path()
        if curr_link_path == link_path:
            # if the link points where we want, leave it alone
            log.debug(f"{dest_path} already points to {link_path}, making no changes")
            return
        else:
            # otherwise remove the wrong-pointing symlink
            log.info(f"{dest_path} points to {curr_link_path}. Removing.")
            dest_path.unlink()
    # back up existing files
    elif dest_path.is_file():
        log.info(f"Existing file at {dest_path}. Backing up.")
        dest_path.backup()

    log.info(f"Creating symlink at {dest_path} to {link_path}")
    dest_path.symlink_to(link_path)



def bless(from_path, to_dir):
    to_path = to_dir / from_path.name
    copy2(from_path, to_path)
    link_file(to_path, from_path)


def main(args):
    """Link 'frm' to 'to'.

    Has DWIM behavior depending on what 'frm' and 'to' are:

    if 'frm' is a file and 'to' is a dir:
    - eg ~/.zshrc ~/setup/HOME
    - copy ~/.zshrc into ~/setup/HOME and symlink from ~/.zshrc into ...HOME
    - both frm and to must exist

    if 'frm' is a file and 'to' is a file:
    - eg. ~/bin/symgr ~/setup/HOME/bin/3rdparty/symgr/symgr
    - symlink 'frm' to 'to' (back up what's there, etc.)
    - to must exist, frm may not

    if 'frm' and 'to' are both dirs:
    - eg ~ ~/setup/HOME
    - link everything within them
    - strictly, to must exist, frm may not, but for this program both must exist

    if frm is a dir and to is a file:
    - makes no sense
    """
    frm = Path(args.frm)
    to = Path(args.to)

    if frm.is_file() and to.is_dir():
        log.info(f"Blessing file at {frm}. Moving to {to} and linking original path there.")
        return bless(frm, to)

    if frm.is_dir() and to.is_dir():
        log.info(f"Linking the files in {to} into {frm}")
        return link_directories(to, frm)

    if to.is_file():
        # if you got here, frm is either a file or doesn't exist, link frm to
        # 'to' and let the code rename 'to' if it exists
        log.info(f"Linking {frm} to {to}")
        return link_file(to, frm)

    log.error(f"Invalid arguments: from: {frm}, to: {to}. A required path may not exist.")
    return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Symlink manager")
    parser.add_argument('frm', metavar='from', help="The directory in which to create links, or the file to bless")
    parser.add_argument('to', help='The directory the links point to, or the dest dir for the blessed file')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    sys.exit(main(args))
