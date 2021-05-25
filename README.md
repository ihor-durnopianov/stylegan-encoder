# (Yet another) StyleGAN encoder

**To do**:
* make usable
* improve
    * cover with tests
    * refactor questionable parts
        * CLI
        * losses
        * that madness (grep code for "madness" to see which)
    * cache instance method calls
        * _MaskMaker.process
        * _LossCalculator._to_features
    * import `unpack_bz2` from somewhere

## How to use (outdated)

```python
from encoder import Encoder

latent = Encoder(params).encode(
    image,
    continue_=lambda i: i < inputs.iterations
)
```
