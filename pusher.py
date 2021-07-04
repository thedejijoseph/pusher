#!/usr/bin/env python

import argh

from controller import watch, exclude, remove, \
        watchlist, status, \
        push, collect, \
        add_auth, reset_auth, \
        start, stop


parser = argh.ArghParser()

basic = [watch, exclude, remove]
info = [watchlist, status]
sync = [push, collect]
auth = [add_auth, reset_auth]
control = [start, stop]

parser.add_commands(basic)
parser.add_commands(info)
parser.add_commands(sync)
parser.add_commands(auth)
parser.add_commands(control)


if __name__ == '__main__':
    parser.dispatch()
