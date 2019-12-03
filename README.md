# symgr

*A symlink manager for maintaining files in source control*

## Introduction

We nerds who want to manage our system config (dotfiles) in source control need
some way to do it. The common approach (which this tool takes) is creating
symlinks to the repository from a directory of your choosing (e.g. `$HOME`).

## Dependencies

Depends on Python, and my [`bak` utility](https://github.com/kbd/bak) being
installed in the path.

## Usage

```bash
$ symgr {from} {to}

# e.g.
$ symgr ~ ~/setup/HOME  # create symlinks in $HOME pointing to ~/setup/HOME
```

I obviously agonized over the argument order and I hope it makes sense to you.
Note that this is reversed from the order of the lower-level `ln -s path
symlink`, which would be `symgr {to} {from}`.

Also includes ability to take a file in your `$HOME` (or anywhere) and swap it
with a symlink pointing to where you want it in your repository. This allows you
to build your setup in source control in the first place.

### Example:

```bash
$ symgr ~/.zshrc ~/setup/HOME
```

## Philosophy

This is one approach to source controlling your home dir. Keep a repository
somewhere, and symlink files under `$HOME` pointing to your repository,
mirroring its structure.

Another approach, well-explained in [this post from
Atalssian](https://www.atlassian.com/git/tutorials/dotfiles), is to make your
home directory itself a git repo, but use a non-standard `.git` dir so that your
`$HOME` doesn't look like a giant repository to git and other tools.

I prefer the separation I get with creating symlinks into a repository using a
small tool vs making my `$HOME` itself a git repo. A tool also allows more
control over git alone. For example, when first linking a directory, `symgr`
renames any existing files (using `bak`) before creating symlinks, whereas using
git directly requires a manual intervention upon first setup (on each computer)
to deal with existing files. This also lets you have your home directory symlink
creation as one part of a larger system setup. See https://github.com/kbd/setup
for how I use this in my own system setup.

## FAQ

Q. I created symlinks using symgr but I changed locations of files. How can I
clean up broken symlinks?

A. This feature is built into (GNU) `find`, with the `-xtype l` argument, so I
didn't add it to 'symgr'. e.g.:

```bash
find . -maxdepth 2 -xtype l
```

to find all broken links under the current directory, max of two directories
deep. You can pipe that to `xargs rm` (after inspection) to delete.
