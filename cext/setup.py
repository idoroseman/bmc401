from distutils.core import setup, Extension
import numpy

#run: python3 setup.py install

def main():
    setup(name="modems",
          version="1.0.0",
          description="Python interface for various modems C functions",
          author="ido roseman",
          author_email="ido.roseman@gmail.com",
          ext_modules=[Extension("modems", ["modems.c", "modem_aprs.c", "modem_sstv.c"],
                                 include_dirs=[numpy.get_include()],
                                 define_macros=[('NPY_NO_DEPRECATED_API',)]
                                 )])

if __name__ == "__main__":
    main()