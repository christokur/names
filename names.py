#!/usr/bin/env python3
#
# names.py - a library for naming using the ASIM conventions for
#
'''This file provides support for the ohm naming conventions library
which are based on ASIM which in turn are b ased on Powercorp
Hungarian. The principles are fairly simple, in particular a name
defines:

1. The units for the device, e.g. any name finishing in *P must be in kW.
2. The names are in CamelCase and each component is a shortened version of
   the name, e.g. Gen => Generator.
3. Device names may include a device number, e.g. Gen2 is Generator #2.
4. Names without a device number should be totals or averages of the device
   values, e.g.
   GenP = Gen1P +
   Gen2P + ... whilst Fed1U voltage is the average of Fed1U12, Fed1U23 Fed1U31.
5. Unit names follow IEC/IEEE/SI standards, e.g. kvar not kVAr regardless of
   local conventions.

The benefit of all of this is that a name defines the type, units and
meaning directly rather than having associated metadata which may or
may not be correct. All units unit of the same type can be combined
and compared since the units are the same.

As well as names such as Gen1P which are big names we also have little
names, e.g. t_step which are used for modelling things like time. More
to follow. (Is this a good idea).

'''

# Copyright, 2018, Phil Maker <philip.maker@gmail.com>>>, All Rights Reserved.

import re
import csv
import fnmatch
import docopt
# python standards say all imports at top which is a bit silly IMHO
from hypothesis import given, note  # , assume, Verbosity
import hypothesis.strategies as st
from hypothesis import settings


# regular expressions for parsing names
RE_NAME = re.compile(r'\A([A-Za-z_0-9]*)+\Z')
RE_PARTNAME = re.compile(r'[A-Z_][a-z0-9]*')
RE_SPLITPREFIX = re.compile(r'\A([A-Z][a-z]+)[_]?([0-9]*)')

# state space for the entire module


def clear_names():
    'clear the namespace of names,etc'
    global named, partnamed, ruled, unitd, shortd, longd
    named = dict()
    partnamed = dict()
    ruled = dict()
    unitd = dict()
    shortd = dict()
    longd = dict()


clear_names()

# __all__.append(['name']) # export part of namespace later on?
def name(nm, un, sh, lo):
    '''Create a variable named nm with attributes'''
    assert valid_name(nm)
    named[nm] = True
    unitd[nm] = un
    shortd[nm] = sh
    longd[nm] = lo


def show():
    '''show the names to stdout'''
    nm_max = un_max = sh_max = 0
    for nm in named:
        nm_max = max(nm_max, len(nm))
        un_max = max(un_max, len(unitd[nm]))
        sh_max = max(sh_max, len(shortd[nm]))

    for nm in named:
        print(nm.ljust(nm_max + 2),
              units(nm).ljust(un_max+2),
              short(nm).ljust(sh_max+2),
              long(nm), sep=' | ')
def parts(nm):
    '''Return the parts of a name
    >>> parts('Gen1P')
    ['Gen1', 'P']

    >>> parts('Pv1U12')
    ['Pv1', 'U12']

    >>> parts('0A')
    ['0', 'A']

    >>> parts('P')
    ['P']

    >>> parts('Gen1U1n')
    ['Gen1', 'U1n']

    >>> parts('gammadog')
    ['gammadog']

    >>> parts('A1A')
    ['A1', 'A']

    >>> parts('A1')
    ['A1']
    '''

    p = re.sub(r'([A-Z][a-z]*[0-9a-z]*)', '_\\1_', nm).split('_')
    return [pn for pn in p if pn != '']


def parts_join(pnl):
    '''Return the join of the patnames in list pnl

    >>> parts_join(['Gen', 'P'])
    'GenP'
    '''
    return ''.join(pnl)


def names(only='*', excludes='', device_pat='*', onlybig=False):
    'return a list of names which match the arguments'
    global named
    f = lambda v: match(v, only) and \
        not match(v, excludes) and \
        match(device(v), device_pat) and \
        (bigname(v) if onlybig else True)
    r = sorted(filter(f, named))
    return r


def bigname(nm):
    'is this a big name'
    return nm[0].isupper()


def short(nm):
    'return the short description for nm'
    r = []
    for pn in parts(nm):
        r.append(shortd[pn] if pn in shortd else pn)
    return " ".join(r)


def long(nm):
    'return the long description for nm'
    return longd[nm] if nm in longd else ""


def units(nm):
    'return the units for nm'
    return unitd[kind(nm)]


def valid_name(nm):
    '''return true iff nm is a valid nm

    >>> valid_name('Abc')
    True
    '''
    return True


def device(nm):
    '''return the device name for nm
    >>> device('Ess1DcP')
    'Ess1'

    >>> device('Pv1001')
    'Pv1001'

    >>> device('A1A')
    'A1'
    '''
    return parts(nm)[0]


def device_number(nm):
    '''Return the device number for nm.

    >>> assert device_number('Gen1P') == 1
    >>> assert device_number('Pv11U12') == 11
    >>> assert device_number('Pv12') == 12
    '''
    nd = device(nm)
    digits = [i for i in range(0, len(nd)) if nd[i].isdigit()]
    n = int(device(nd)[digits[0]:])
    return n


def is_parameter(nm):
    '''Returns True iff this name a parameter

    >>> is_parameter('GenP')
    False

    >>> is_parameter('Pv1MaxPPa')
    True
    '''
    return parts(nm)[-1] == 'Pa'


def kind(nm):
    '''Return the kind of name, e.g. P or Q | U12
    >>> kind('Gen1P')
    'P'

    >>> kind('Pv1U12')
    'U12'

    >>> kind('Pv1MaxPPa')
    'P'

    >>> kind('Pv1U1n')
    'U1n'
    '''
    if is_parameter(nm):
        r = parts(nm)[-2]
    else:
        r = parts(nm)[-1]
    return r

# this block of functions is intended to convert between different name
# formats, e.g. CamelCase to wtg_P to wtg[1].p to ...
# currently we only use _ names.
def name_to_lower(nm):
    '''returns a lower_case versio  of name

    >>> name_to_lower('Gen1P')
    'gen1_p'

    >>> name_to_lower('Wtg1InvInlet2InvTemp')
    'wtg1_inv_inlet2_inv_temp'
    '''
    assert(valid_name(nm))
    return '_'.join(parts(nm)).lower()

def lower_to_name(nm):
    '''return a name from a lower_case name

    >>> lower_to_name('gen1_p')
    'Gen1P'
    '''
    u = True
    r = ''
    for c in nm:
        if c == '_':
            u = True
        else:
            if u:
                r += c.upper()
            else:
                r += c
            u = False
    return r
            
    
def fatal(m):
    '''print a fatal error message and exit'''
    print('* fatal error:' + m)
    assert False

# string matching tools


def match(n, pat):
    '''Returns True iff match n against pat does a glob match with the
    extension of choice (|). The syntax includes * = everything, ? any
    single charactor, [seq] and [!seq]

    >>> match('A.c', '*.c')
    True

    '''
    for p in pat.split('|'):
        if fnmatch.fnmatchcase(n, p):
            return True
    return False


def strip(s):
    return s.lstrip().rstrip()

# bnf sentence expansion


def expand_bnf(grammar, start):
    '''Returns a list of sentences matching grammar starting with
    non-terminal start

    >>> expand_bnf('<s> ::= hello\\n', '<s>')
    ['hello']

    >>> expand_bnf('<s> ::= hello<world>\\n<world> ::= world', '<s>')
    ['helloworld']

    >>> expand_bnf('<s> ::= hello|world\\n', '<s>')
    ['hello', 'world']

    >>> expand_bnf('<s> ::= \\n', '<s>')
    ['']

    >>> # note that rules override each other, i.e. only the last <s> is used
    >>> expand_bnf('<s> ::= hello\\n<s> ::= world', '<s>')
    ['world']

    '''
    return sorted(expand_rules(bnf_to_rules(grammar), start))


def bnf_to_rules(grammar):
    '''Returns a dictionary representation of grammar.

    >>> bnf_to_rules('<a> ::= b|c')
    {'<a>': 'b|c'}

    Note: <a> ::= b <a> ::= c ends up as <a> ::= c
    '''
    def lrstrip(s):
        return s.lstrip().rstrip()

    g = dict()
    for _ in grammar.splitlines():
        _ = _.lstrip().rstrip()
        if _ != '' and _[0] != '#':
            _ = _.split('::=', 2)
            if len(_) == 2:
                g[lrstrip(_[0])] = lrstrip(_[1])
            else:
                print('bnf_to_rules: expecting ::= in', _)
    return g


def finished(s):
    '''Returns true if there is nothing more to expand in s

    >>> assert finished('Lollipop')
    >>> assert not finished('hello|<nt>')
    >>> assert not finished('pink elephants|b')
    '''
    return s.find('<') == -1 and s.find('|') == -1


def expand_rules(rules, s):
    '''expand_rules expands a set of BNF rules into a dictionary'''
    # print('expand_rules', s)
    if finished(s):
        return {s}
    else:
        results = set()
        # print(results)
        for lhs, rhs in rules.items():
            for c in rhs.split('|'):
                u = s.replace(lhs, c, 1)
                if u != s:
                    results = results.union(expand_rules(rules, u))
                else:
                    pass
        return results


def print_rules(g):
    for nt in g:
        info('* rule', nt, '::=', g[nt])

# read a description in


def read_description(fn):
    global partnamed, ruled, unitd, shortd, longd
    g = dict()
    fd = open(fn)
    csv_reader = csv.reader(fd, delimiter=',')
    line = 0
    for row in csv_reader:
        line += 1
        if len(row) == 0:
            continue
        if len(row) == 4:
            row.append("")
        # print(line, row)
        if len(row) != 5:
            print('fatal error: expected 5 columns got', len(row), 'from', row)
            exit(1)
        if line == 1:
            continue
        nm = strip(row[0])
        rl = strip(row[1])
        un = strip(row[2])
        sh = strip(row[3])
        lo = strip(row[4])
        # print('/', nm, rl, un, sh, lo, sep='/')
        if len(nm) > 0 and nm[0] == '#':
            # print('comment: ', nm)
            pass
        elif '<' in nm:  # its a grammar rule
            # print('its a grammar rule')
            if len(rl) and rl[0] == '|':        # add the choice to the end
                if nm not in g or g[nm] == '':  # empty production so assign
                    g[nm] = rl[1:]
                else:
                    g[nm] = g[nm] + rl
            else:   # override existing production
                g[nm] = rl
        elif '<' in rl:   # its a new rule
            # print('adding' , rl)
            if rl in g:
                g[rl] += '|' + nm
            else:
                g[rl] = nm
        else:   # its a description
            # print(row, 'default')
            partnamed[nm] = strip(nm)
            ruled[nm] = strip(rl)
        # process un
        if un != '':
            unitd[nm] = un
        if sh != '':
            shortd[nm] = sh
        if lo != '':
            longd[nm] = lo
    return g


# command line variant where we run this standalone

main_opts = """

Usage: names [-v] <rules>...

Options:
  <rules>          Rules
  -t               Run the internal tests [default: False]
  -v               Verbose logging [default: False]
"""

options = {
    '-v': False
}

def main():
    global main_opts, options
    options = docopt.docopt(main_opts)
    process_rules(options['<rules>'])
    

def info(*args):
    global options
    # print(options)
    if '-v' in options and options['-v']:
        for s in args:
            print(s, sep=' ', end=' ')
        print('')

def process_rules(rules):
    '''Process each ruleset in rules'''
    g = dict()
    for rule in rules:
        if match(rule, '*.txt'):  # its a grammar file
            info('* process', rule)
            g = {**g, **bnf_to_rules(open(rule).read())}
        elif match(rule, '*.csv'):  # its a csv description file
            info('* process csv', rule)
            g = {**g, **read_description(rule)}
        else:
            print('did not expect', rule)
            exit(101)
    print_rules(g)
    names = expand_rules(g, '<Names>')
    for u in unitd:
        info('* units', u, unitd[u])
    ofn = 'all_names.csv'
    cfd = open(ofn, mode='w')
    cw = csv.writer(cfd)
    cw.writerow(['Name', 'Units', 'Short', 'Long'])
    for n in sorted(names):
        info('* names', n, units(n), short(n), long(n))
        name(n, units(n), short(n), long(n))
        cw.writerow([n, units(n), short(n), long(n)])
    cfd.close()
    info('* see ', ofn, 'with all generated names')

#
# hypothesis based testing which is based on Haskells Quickcheck, this
#   is a bit of overkill but it is a nice way to write tests.
#


if True:
    test_names = ['P', 'GenP', 'Wtg1P', 'Ess1MaxPPa', 'EssQ',
                  'hello', 'p_q', '']
    ts = settings(max_examples=1000,
                  deadline=1000,   # aka 1s/test
                  derandomize=True,
                  database=None)
    # verbosity=Verbosity.verbose,

    @settings(ts)
    @given(st.one_of(st.from_regex(RE_NAME),
                     st.sampled_from(test_names),
                     st.text()))
    def test_parts_identity(nm):
        note('check that parts_join(parts(nm)) is an identity')
        if '_' not in nm:
            assert parts_join(parts(nm)) == nm

    @settings(ts)
    @given(st.from_regex(r'\A[A-Z][a-z]*\Z'),
           st.integers(1, 100),
           st.from_regex(r'\A[A-Z_]*\Z'))
    def test_device_number(p, n, s):
        nm = p + str(n) + s
        assert device_number(nm) == n

    @settings(ts)
    @given(st.from_regex(r'\A[A-Z][a-z]*\Z'),
           st.integers(1, 100),
           st.from_regex(r'\A[A-Z_]*\Z'))
    def test_device(p, n, s):
        nm = p + str(n) + s
        exp = p + str(n)
        note('device(nm) expected ' + exp + ' got ' + device(nm))
        assert device(nm) == exp
        assert is_parameter(nm + 'Pa')
        assert kind(nm + 'Pa') == kind(nm)

    @settings(ts)
    @given(st.from_regex(r'\A[_A-Za-z0-9]*\Z'), st.text())
    def test_match(s, t):
        assert match(s, s)
        assert match(s, s + '|' + t)
        assert match(s, t + '|' + s)
        assert match(t, '*')
        assert not match(t, t + 'x')

    @settings(ts)
    @given(st.from_regex(r'\A[ ]*\Z'),
           st.from_regex(r'\A[^ \n][^\n]*[^ \n]\Z'),
           st.from_regex(r'\A[ ]*\Z'))
    def test_strip(a, b, c):
        assert strip(a + b + c) == b

    @settings(ts)
    @given(st.from_regex(r'\A[A-Z][A-Za-z0-9]*\Z'))
    def test_name_to_lower(nm):
        assert lower_to_name(name_to_lower(nm)) == nm

    if False: # disabled for now
        @settings(ts)
        @given(st.from_regex(r'\A[a-z]+(_[a-z_0-9]+)*\Z'))
        def test_lower_to_name(nm):
            assert name_to_lower(lower_to_name(nm)) == nm

        
if __name__ == '__main__':
    # note: we use pytest to run the doctest code above, see Makefile
    main()
