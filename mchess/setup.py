from setuptools import setup, Extension

module = Extension(
    'chess_extension',
    sources=['chess_extension.c']
)

setup(
    name='ChessExtension',
    version='1.0',
    description='Extension for bottleneck functions in the chess module',
    ext_modules=[module],
)