#include <Python.h>
#include <numpy/arrayobject.h>
#include "modem_aprs.h"
#include"modem_sstv.h"

// https://realpython.com/build-python-c-extension-module
// https://numpy.org/doc/stable/user/c-info.how-to-extend.html
// https://stackoverflow.com/questions/56182259/how-does-one-acces-numpy-multidimensionnal-array-in-c-extensions
// https://py3c.readthedocs.io/en/latest/guide.html
// https://github.com/PiInTheSky/pits/blob/master/tracker/aprs.c

typedef unsigned char	byte;

void * failure(PyObject *type, const char *message) {
    PyErr_SetString(type, message);
    return NULL;
}

void * success(PyObject *var){
    Py_INCREF(var);
    return var;
}

static PyObject *method_afsk(PyObject *self, PyObject *args) {
    PyObject *pList;
    PyObject *pItem;
    Py_ssize_t n;
    int samplerate = 11050;

    if (!PyArg_ParseTuple(args, "O!|i", &PyList_Type, &pList, &samplerate)) {
        PyErr_SetString(PyExc_TypeError, "parameter error.");
        return NULL;
    }

    n = PyList_Size(pList);
    char *frames[n];
    int lengths[n];
    int total_length = 0;
    for (int i=0; i<n; i++) {
        pItem = PyList_GetItem(pList, i);
        if(!PyUnicode_Check(pItem)) {
            PyErr_SetString(PyExc_TypeError, "list items must be unicode strings.");
            return NULL;
        }
        Py_ssize_t size;
        const char *ptr = PyUnicode_AsUTF8AndSize(pItem, &size);
//        printf("item %d: %s (%d)\n", i, ptr, (int)size);
        frames[i] = ptr;
        lengths[i] = size;
        total_length += size;
    }
    return makeafsk(samplerate, 1200, 1200, 2200, frames, lengths, n, total_length);
}

static PyObject *method_sstv_m1(PyObject *self, PyObject *args) {
    PyArrayObject *array = NULL;
    int samplerate = 11025;

    if (!PyArg_ParseTuple(args, "O!|i", &PyArray_Type, &array, &samplerate)){
        PyErr_SetString(PyExc_TypeError, "error reading parameters");
        return NULL;
    }

    if (array == NULL || array->nd != 3 ){
        PyErr_SetString(PyExc_TypeError, "no image or not RGB");
        return NULL;
    }

    printf("%d dimentions: ", PyArray_NDIM(array), array->nd );
    for (int i=0; i<PyArray_NDIM(array); i++)
       printf("%d, ", array->dimensions[i]);
    printf("\n");
    printf("typenum: %d\n", array->descr->type_num);
    return makesstv_m1(samplerate, array);
}

static PyObject *method_sstv_pd120(PyObject *self, PyObject *args) {
    PyArrayObject *array = NULL;
    int samplerate = 11025;

    if (!PyArg_ParseTuple(args, "O!|i", &PyArray_Type, &array, &samplerate)){
        PyErr_SetString(PyExc_TypeError, "error reading parameters");
        return NULL;
    }

    if (array == NULL || array->nd != 3 ){
        PyErr_SetString(PyExc_TypeError, "no image or not RGB");
        return NULL;
    }

    printf("%d dimentions: ", PyArray_NDIM(array), array->nd );
    for (int i=0; i<PyArray_NDIM(array); i++)
       printf("%d, ", array->dimensions[i]);
    printf("\n");
    printf("typenum: %d\n", array->descr->type_num);
    return makesstv_pd120(samplerate, array);

}


static PyMethodDef ModemsMethods[] = {
    {"encode_afsk", method_afsk, METH_VARARGS, "encode afsk message"},
    {"encode_sstv_m1", method_sstv_m1, METH_VARARGS, "encode sstv message as martin m1"},
    {"encode_sstv_pd120", method_sstv_pd120, METH_VARARGS, "encode sstv message as pd-120"},
    {NULL, NULL, 0, NULL}
};


static struct PyModuleDef modemsmodule = {
    PyModuleDef_HEAD_INIT,
    "modems",
    "Python interface for the fputs C library function",
    -1,
    ModemsMethods
};

PyMODINIT_FUNC PyInit_modems(void) {
    PyObject *module = PyModule_Create(&modemsmodule);
    if(module==NULL) return NULL;
    import_array(); // initialize numpy
    if (PyErr_Occurred()) return NULL;
    return module;
}