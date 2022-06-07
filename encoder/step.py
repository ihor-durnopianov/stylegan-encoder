# -*- coding: utf-8 -*-
""""""


from typing import Tuple
import argparse

import PIL.Image
import numpy as np
import torch
from torchvision.transforms import (
    Compose,
    ToPILImage,
)

from .core import (
    Encoder,
    _from_batch,
    _minmax_scale,
)


encoder = Encoder(argparse.Namespace(
    use_gpu=torch.cuda.is_available(),
    lr=0.0625,
))


def step(
    target: PIL.Image.Image, latent: np.ndarray = None
) -> Tuple[np.ndarray, PIL.Image.Image]:
    updated = encoder.encode(
        target, latent, continue_=lambda i: i < 1, test=False
    )
    return updated, _generate_image(updated)


def _generate_image(latent: np.ndarray) -> PIL.Image.Image:
    tensor = torch.from_numpy(latent)
    with torch.no_grad():
        generated = encoder._synthesis(tensor)
    return Compose([
        _from_batch,
        _minmax_scale,
        lambda tensor: tensor.cpu(),
        ToPILImage(),
    ])(generated)
