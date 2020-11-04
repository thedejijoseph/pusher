

import argh

from controller import watch, exclude, remove


parser = argh.ArghParser()
parser.add_commands([watch, exclude, remove])


if __name__ == '__main__':
    parser.dispatch()
