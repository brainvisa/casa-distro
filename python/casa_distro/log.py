# -*- coding: utf-8 -*-

from __future__ import absolute_import

import ast
import io
import types
import sys

from casa_distro import six


def boolean_value(value):
    '''
    Return True or False if value can be interpreted as a boolean
    or None in other cases. Booleans are recognized from bool, int
    and strings '0', '1', 'true', 'false', 'yes' and 'no' (case 
    insensitive)
    '''
    if isinstance(value, (int, bool)):
        return bool(value)
    elif isinstance(value, six.string_types):
        value = value.lower()
        if value in ('true', 'yes', '1'):
            return True
        if value in ('false', 'no', '0'):
            return False
    return None


def verbose_file(verbose, openmode='w+'):
    verbose = boolean_value(verbose)
    if verbose is not None:
        return (sys.stdout if verbose else None)
    if isinstance(verbose, six.string_types):
        # Try to open file from given string
        try:
            verbose = open(verbose, openmode)
        except IOError:
            return None

    if ((sys.version_info[0] >= 3 and 
         isinstance(verbose, io.IOBase)) or
        (sys.version_info[0] < 3 and 
         isinstance(verbose, types.FileType))):
        return verbose

    return None
