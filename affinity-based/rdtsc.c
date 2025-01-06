#include <Python.h>

static PyObject* rdtsc(PyObject* self, PyObject* args) {
    unsigned int lo, hi;
    __asm__ __volatile__ ("rdtsc" : "=a" (lo), "=d" (hi));
    return Py_BuildValue("K", ((unsigned long long)hi << 32) | lo);
}

static PyMethodDef rdtsc_methods[] = {
    {"rdtsc", rdtsc, METH_VARARGS, "Read the Time Stamp Counter"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef rdtsc_module = {
    PyModuleDef_HEAD_INIT,
    "rdtsc",
    "Read the Time Stamp Counter",
    -1,
    rdtsc_methods
};

PyMODINIT_FUNC PyInit_rdtsc(void) {
    return PyModule_Create(&rdtsc_module);
}