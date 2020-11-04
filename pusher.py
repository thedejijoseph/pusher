

import argh

from controller import watch, exclude, remove, watchlist


parser = argh.ArghParser()
parser.add_commands([watch, exclude, remove, watchlist])


if __name__ == '__main__':
    parser.dispatch()
