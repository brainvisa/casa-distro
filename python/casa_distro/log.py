# -*- coding: utf-8 -*-

from __future__ import absolute_import

import ast
import io
import types
import sys

from casa_distro import six


def verbose_bool(verbose_string):
    '''
    Return True or False if verbose can be interpreted as a boolean
    or None in other cases. Booleans are recognized from bool, int
    and strings '0', '1', 'true', 'false' (case insensitive)
    '''
    if isinstance(verbose_string, (int, bool)):
        return bool(verbose_string)
    elif isinstance(verbose_string, six.string_types):
        try:
            # Try to interpret string as boolean or integer values
            return bool(ast.literal_eval(verbose_string))
        except:
            pass
    return None


def verbose_file(verbose, openmode='w+'):
    verbose = verbose_bool(verbose)
    if verbose is not None:
        return (sys.stdout if verbose else None)
    if isinstance(verbose, six.string_types):
        # Try to open file from given string
        try:
            verbose = open(verbose, openmode)
        except:
            return None

    if ((sys.version_info[0] >= 3 and 
         isinstance(verbose, io.IOBase)) or
        (sys.version_info[0] < 3 and 
         isinstance(verbose, types.FileType))):
        return verbose

    return None
