# -*- coding: utf-8 -*-
__all__ = ['hostapp', 'jsonio']
__version__ = '0.3'

if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from ctentaculo.client.core import *