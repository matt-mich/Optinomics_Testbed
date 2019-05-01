import numpy as np
def mat_mask(n):
    cent = int(n/2)
    y,x = np.ogrid[-cent:n-cent, -cent:n-cent]

    mask = x**2 + y**2 <= cent*cent

    array = np.zeros((n, n))
    array[mask] = 255
    print(mat_mask)
    return array


print(mat_mask(11))