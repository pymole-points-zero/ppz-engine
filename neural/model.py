import numpy as np


def prepare_predict(model, field):
    field = np.reshape(field, (-1, *field.shape))
    (pi,), (v,) = model.predict(field)
    return pi, v
