# (Yet another) StyleGAN encoder

TODO:
* cover with tests
* refactor questionable parts
    * CLI
    * losses
    * that madness (grep code for "madness" to see which)
* cache instance method calls
    * _MaskMaker.process
    * _LossCalculator._to_features
* import `unpack_bz2` from somewhere

## How to use

```python
from encoder import Encoder

latent = _Encoder(**params).encode(
    image,
    continue_=lambda i: i < inputs.iterations
)
```
