

import argh

from controller import watch, exclude, remove, \
    watchlist, status, push, collect


parser = argh.ArghParser()
parser.add_commands([\
    watch, exclude, remove, \
    watchlist, status, push, collect])


if __name__ == '__main__':
    parser.dispatch()
