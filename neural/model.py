import numpy as np


def prepare_predict(model, field):
    field = np.reshape(field, (-1, *field.shape))
    (pi,), (v,) = model.predict(field)
    return pi, v


def prepare_predict_on_batch(model, fields):
    prepared_fields = [np.reshape(field, (-1, *field.shape)) for field in fields]
    results = model.predict_on_batch(prepared_fields)
    results = [(results[i][0], results[i+1][0][0]) for i in range(0, len(results)//2, 2)]
    return results
