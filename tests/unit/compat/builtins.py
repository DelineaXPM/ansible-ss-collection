# -*- coding: utf-8 -*-
# Copyright: (c) 2023, Delinea <https://delinea.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

#
# Compat for python2.7
#

# One unittest needs to import builtins via __import__() so we need to have
# the string that represents it
try:
    import __builtin__  # noqa: F401, pylint: disable=unused-import
except ImportError:
    BUILTINS = 'builtins'
else:
    BUILTINS = '__builtin__'
