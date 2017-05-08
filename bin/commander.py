# -*- coding: utf-8; -*-
"""
Converts commander.el declaration into a Python ArgumentParser
object with subparsers.

Basic lisp parser based on http://norvig.com/lispy.html
"""
from __future__ import print_function

# ppylint: disable=superfluous-parens
import re
from itertools import groupby
from argparse import ArgumentParser


class ParseError(Exception):
    """An error indicating a failure to parse the lisp file."""


def tokenizer(program):
    """Generates tokens from program.

    The tokens are opening and closing parens, strings and symbols.
    Comments are skipped.
    """
    # Remove all comments
    program = re.sub(r';.*$', '', program, flags=re.MULTILINE)
    i = 0
    strend_re = re.compile(r'(?<!\\)"')
    ws_re = re.compile(r'\s+')
    symend_re = re.compile(r'\s|\)')
    while i < len(program):
        wsm = ws_re.match(program, i)
        if wsm:
            i = wsm.end()
        elif program[i] in "()`',@":
            yield program[i]
            i += 1
        elif program[i] == '"':
            strend = strend_re.search(program, i + 1)
            try:
                yield program[i:strend.end()]
                i = strend.end()
            except AttributeError:
                raise ParseError("Unterminated string")
        else:
            symend = symend_re.search(program, i+1)
            if symend:
                yield program[i:symend.start()]
                i = symend.start()
            else:
                yield program[i:]
                i = len(program)


def tokenize(program):
    """Return the list of tokens making up program.

    The tokenizer is *very* simple, strip comments and split on
    whitespace.  Parens are handled special by surrounding them with
    whitespace before splitting.
    """
    return list(tokenizer(program))
    # program = re.sub(r';.*$', '', program, flags=re.MULTILINE)
    # return program.replace('(', ' ( ').replace(')', ' ) ').split()


class Symbol(str):
    """Type for symbol atoms."""
    pass


def atom(token):
    """Return the atom of token.

    The atom type is int, str or Symbol.
    """
    # try:
    #     return int(token)
    # except ValueError:
    if token[0] == '"' and token[-1] == '"':
        return token[1:-1]
    return Symbol(token)


def read_from_tokens(tokens):
    """Read an expression from a sequence of tokens."""
    if len(tokens) == 0:
        raise ParseError("unexpected eof")
    token = tokens.pop(0)
    if token[0] == '"':
        return atom(token)
    elif token == '(':
        subl = []
        try:
            while tokens[0] != ')':
                subl.append(read_from_tokens(tokens))
        except IndexError:
            raise ParseError("unexpected eof")
        tokens.pop(0)  # pop off ')'
        return subl
    elif token == ')':
        raise ParseError("unexpected )")
    else:
        return atom(token)


def reader(tokens, token=None):
    """Read an expression from tokens..
    If token is set, use that before reading from tokens."""
    tokens = iter(tokens)
    if token is None:
        try:
            token = next(tokens)
        except StopIteration:
            return None
    try:
        if token[0] == '"':
            return atom(token)
        elif token == '(':
            sublist = []
            token = next(tokens)
            while token != ')':
                sublist.append(reader(tokens, token=token))
                token = next(tokens)
            return sublist
        elif token == ')':
            raise ParseError('unexpected )')
        else:
            return atom(token)
    except StopIteration:
        raise ParseError("Unexpected eof")


def parse(program):
    """Read an elisp program from a string.
    Return the AST."""
    return read_from_tokens(tokenize(program))


def eleval(x, env):
    if isinstance(x, Symbol):  # variable reference
        return env[x]
    elif not isinstance(x, list):  # constant literal
        return x
    elif x[0] == 'defun':
        env[x[1]] = x[2:]
    # elif x[0] == 'commander':
    #     things = {}
    #     for prim, sexp in groupby(sorted(x[1:]), lambda s: s[0]):
    #         things[prim] = list(sexp)
    #     env['commander'] = things
    else:
        return None

def make_subparser_args(command, env):
    words = command[1].split()
    kwargs = {'title': words[0], 'arguments': []}
    if isinstance(command[2], Symbol):
        # See if there is a function of that name
        fn = env.get(command[2],
                     # default is a 2-element list of empty lists
                     [[], []])
        if isinstance(fn[1], unicode) or isinstance(fn[1], str):
            kwargs['help'] = fn[1]
    else:
        kwargs['help'] = command[2]
    if 'help' not in kwargs:
        kwargs['help'] = "Default help"
    if len(words) == 2:
        argdict = {}
        if '<' in words[1]:
            argdict['nargs'] = '?'
        elif '[' in words[1]:
            argdict['nargs'] = 1
        argdict['name'] = words[1][1:-1]
        kwargs['arguments'].append(argdict)
    elif len(words) >= 3:
        raise ParseError('Cannot handle (%s)' % ' '.join(command))
    # TODO: handle default values
    return kwargs


class OptionError(Exception):
    """Error while parsing an `option'."""


class Commander(ArgumentParser):
    """The Commander."""
    def __init__(self, form, env=None, cmdfuncs=None, **kwargs):
        commander = {}
        for prim, sexp in groupby(sorted(form[1:]), lambda s: s[0]):
            commander[prim] = list(sexp)
        if 'add_help' not in kwargs:
            kwargs['add_help'] = False
        if 'description' not in kwargs and 'description' in commander:
            kwargs['description'] = commander['description'][0][1]
        super(Commander, self).__init__(**kwargs)
        self.form = form
        self.commander = commander
        self.env = env or {}
        self.cmdfuncs = cmdfuncs or {}
        self.default_command = self.commander.get('default',
                                                  [['default', None]])[-1][1:]
        self.subparsers = self.add_subparsers(title='COMMANDS',
                                              parser_class=ArgumentParser,
                                              dest='caskcmd',
                                              help='',
                                              metavar='')
        for opt in iter(self.commander.get('option', [])):
            self.add_option(opt)
        self.commands = set()
        for cmd in iter(self.commander.get('command', [])):
            self.add_command(cmd)

    def get_func_doc(self, funcname):
        """Return the docstring of funcname, or None if funcname is not in
        self.env or if it has no documentation.
        >>> c = Commander([], {'foo': [[], "help"], 'bar': [[],2]})
        >>> c.get_func_doc('foo')
        'help'
        >>> c.get_func_doc('bar')
        >>> c.get_func_doc('baz')
        """
        func = self.env.get(funcname)
        if func is not None and isinstance(func[1], str):
            return func[1]
        return None

    def get_nargs(self, argstring):
        """Return a suitable nargs value for argstring.
        argstring should be the second half of an option name string.

        >>> Commander([]).get_nargs('[foo]')
        '?'
        >>> Commander([]).get_nargs('[*]')
        '*'
        >>> Commander([]).get_nargs('<foo>')
        1
        >>> Commander([]).get_nargs('<*>')
        '+'
        >>> Commander([]).get_nargs('')
        """
        if not argstring:
            return None
        inner = {'[': {'*': '*', 'default': '?'},
                 '<': {'*': '+', 'default': 1}}[argstring[0]]
        return inner.get(argstring[1:-1], inner['default'])

    def add_option(self, option):
        """Add option.
        option is a list ['option', flags, help, function, ...]
        where help may be missing.
        """
        if isinstance(option[2], Symbol):
            option.insert(2, None)
        flags, doc, func = option[1:4]
        flagnames = [f.split()[0] for f in flags.split(',')]
        kwargs = {'help':  doc or self.get_func_doc(func)}
        try:
            argstring = flags.split(',')[0].split()[1]
            kwargs['metavar'] = argstring[1:-1].upper()
        except IndexError:
            argstring = ''
        kwargs['nargs'] = self.get_nargs(argstring)
        kwargs['action'] = 'store_true' if kwargs['nargs'] is None else None
        self.add_argument(*flagnames,
                          **{k: v for k, v in kwargs.items() if v is not None})

    def add_command(self, command):
        # each item is a list ['command', name-and-options,
        #                      optional description, function]
        if isinstance(command[2], Symbol):
            command.insert(2, None)
        cmd_n_opt, doc, func = command[1:4]
        cmd = cmd_n_opt.split()[0]
        doc = doc or self.get_func_doc(func)
        cmdp = self.subparsers.add_parser(cmd, help=doc, prefix_chars='')
        cmdp.set_defaults(func=self.cmdfuncs.get(cmd,None))
        self.commands.add(cmd)
        for arg in cmd_n_opt.split()[1:]:
            cmdp.add_argument(arg[1:-1], nargs=self.get_nargs(arg))

    def parse_args(self, args=None, namespace=None):
        if self.default_command:
            if args is None:
                args = self.default_command
            elif self.commands.isdisjoint(set(args)):
                args = args + self.default_command
        return super(Commander, self).parse_args(args, namespace)


def create_argument_parser(cli_el, cmdfuncs=None):
    with open(cli_el) as cliel:
        content = cliel.read()
    tokengen = tokenizer(content)
    env = dict()
    sexp = reader(tokengen)
    while sexp is not None:
        if sexp[0] != 'commander':
            eleval(sexp, env)
        else:
            commander = sexp
        sexp = reader(tokengen)
    # Create the argumentparser
    argp = Commander(commander, env, cmdfuncs)
    return argp
