# -*- coding: utf-8 -*-
__all__ = ['install']

import sys, os

plugin_dir = os.path.dirname(os.path.abspath(__file__))
if not plugin_dir in sys.path:
	sys.path.append(plugin_dir)

if __name__ == '__main__' and __package__ is None:
	sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
