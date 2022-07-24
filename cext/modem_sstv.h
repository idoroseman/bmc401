#include <Python.h>
#include <numpy/arrayobject.h>

PyObject *makesstv_m1(int samplerate, PyArrayObject *array);
PyObject *makesstv_pd120(int samplerate, PyArrayObject *array);