import pkg_resources
__version__ = pkg_resources.get_distribution('iniesta').version
__author__ = 'Kwang Jin Kim'
__email__ = 'david@mymusictaste.com'

from .app import Iniesta

__all__ = ['Iniesta']