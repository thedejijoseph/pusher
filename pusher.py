

import argh

from controller import watch, exclude, remove, \
    watchlist, status, push, collect, add_creds


parser = argh.ArghParser()
parser.add_commands([\
    watch, exclude, remove, \
    watchlist, status, push, collect, add_creds])


if __name__ == '__main__':
    parser.dispatch()
