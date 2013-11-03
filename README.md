pySART
======

Tomographic reconstruction using the Simultaneous Algebraic Reconstruction Technique (SART) implemented in python.

Refrence: Ch7. Kak & Slaney http://www.slaney.org/pct/pct-toc.html

Quickstart:

from pySART import pysart
from skimage.transform import radon, iradon
import phantom
import numpy as np


# Generate test data
```
def generate_phantom():
    theta = range(0,180)
    data = np.rot90(radon(phantom.phantom(n=100),theta=theta))
    data1 = np.zeros((data.shape[0],1,data.shape[1]))
    data1[:,0,:] = data
    return theta, data1
```
# Reconstruct the whole dataset
```
pysart = pysart(*generate_phantom())
pysart.sart()
```

# OR Reconstruct a single slice for 100 iterations (default:50)
```
pysart = pysart(*generate_phantom(), plsice = 10, iteration=100)
pysart.sart()
```