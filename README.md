# symgr

*A symlink manager for maintaining files in source control*

All of us nerds who want to manage our system config (dotfiles) in source
control need to figure out how to actually do that. The common approach that
this tool takes is creating symlinks to the repository from a directory of your
choosing, usually `$HOME`.

## Usage

```shell
$ symgr {from} {to}

# e.g.
$ symgr ~ ~/setup/HOME  # create symlinks in $HOME pointing to ~/setup/HOME
```

I obviously agonized over the argument order and I hope it makes sense to you.
Note that this is reversed from the order of the lower-level `ln -s path
symlink`, which would be `symgr {to} {from}`.

Also includes the `-b`/`--bless` argument for taking a file in your `$HOME` (or
anywhere) and swapping it with a symlink pointing to where you want it in your
repository. This allows you to build your setup in source control in the first
place.

### Example:

```shell
$ symgr -b ~/.zshrc ~/setup/HOME
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
renames any existing files (using my [`bak`
utility](https://github.com/kbd/bak)) before creating symlinks, whereas using
git directly requires a manual intervention upon first setup (on each computer)
to deal with existing files. This also lets you have your home directory as one
part of a larger system setup. See https://github.com/kbd/setup for how I use
this in my own system setup.
