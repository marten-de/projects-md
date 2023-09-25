#include <Python.h>

/*
static PyObject* sum_of_squares(PyObject* self, PyObject* args) {
    int n, i, result = 0;
    if (!PyArg_ParseTuple(args, "i", &n))
        return NULL;
    for (i = 0; i < n; i++) {
        result += i * i;
    }
    return Py_BuildValue("i", result);
}



static PyObject* my_extension_hello(PyObject* self, PyObject* args) {
    const char* name;
    PyObject *testo;

    if (!PyArg_ParseTuple(args, "sO", &name, &testo)) {
        return NULL;
    }

    printf("Hello, %s!\n", name);

    PyObject *testlist = PyList_New(0);

    PyObject *iter = PyObject_GetIter(testo);
    if (!iter) {
        printf("error not iterator");
        return NULL;
    // error not iterator
    }

    while (1) {
    PyObject *next = PyIter_Next(iter);
    if (!next) {
        // nothing left in the iterator
        break;
    }

    if (!PyLong_Check(next)) {
        printf("no int");
        break;
        // error, we were expecting a floating point value
    }

    int foo = PyLong_AsLong(next);
    printf("%d", foo);
    PyList_Append(testlist, PyLong_FromLong(foo));
    // do something with foo
    }

    return testlist;
    //Py_RETURN_NONE;
}

*/

struct coord { int y; int x; };

int matrix[2][3] = { {1, 4, 2}, {3, 6, 8} };

struct coord mat[2] = { {4, 2}, {6, 8} };


static PyObject* king_capt(PyObject* self, PyObject* args) {
    // reading in the passed arguments
    PyObject *piece_loc, *board;
    int color;
    if (!PyArg_ParseTuple(args, "OOi", &piece_loc, &board, &color))
        return NULL;

    // iterating through piece_loc
    PyObject *iter = PyObject_GetIter(piece_loc);
    if (!iter) {
        return NULL; // error in case no iterator
    }

    int test;
    test = mat[1].y;


    return Py_BuildValue("i", test);
}

static PyMethodDef ChessExtensionMethods[] = {
    {"check_possible_king_capt", king_capt, METH_VARARGS, "Checks if the king could be captured"},
    {NULL, NULL, 0, NULL} /* Sentinel */
};

static struct PyModuleDef chess_extension_module = {
    PyModuleDef_HEAD_INIT,
    "chess_extension", /* name of module */
    NULL,           /* module documentation, may be NULL */
    -1,             /* size of per-interpreter state of the module, or -1 if the module keeps state in global variables. */
    ChessExtensionMethods
};

PyMODINIT_FUNC PyInit_chess_extension(void) {
    return PyModule_Create(&chess_extension_module);
}