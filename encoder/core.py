# -*- coding: utf-8 -*-
""""""


import argparse
import sys
import os
import pathlib
from pathlib import Path
import functools
from functools import partial
import contextlib
import logging
import io
import itertools

import numpy as np
import torch
from torch import (
    nn,
    optim,
)
from PIL import Image
from torchvision import models
from torchvision.transforms import (
    ToPILImage,
    Compose,
    ToTensor,
    Normalize,
)

from style_gan import g_all as g

from models.image_to_latent import ImageToLatent as Initializer

import dlib
import bz2
from imutils import face_utils
import cv2

from kornia.filters.laplacian import (
    laplacian,
    get_laplacian_kernel2d,
    Laplacian,
)

# from kornia.filters import spatial_gradient

from pytorch_ssim import ssim

from lpips_pytorch import LPIPS, lpips

# from kornia.filters.blur import BoxBlur


MEAN, STD = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)


# def main():
#     inputs = _define_inputs()
#     # Monitoring
#     logging.basicConfig(
#         level=inputs.logging_level, format="%(levelname)s - %(message)s"
#     )
#     # Endmonitoring
#     latent = Encoder(argparse.Namespace(**{
#         k: v for k, v in inputs.__dict__.items()
#         if k not in {
#             "target_image", "guess", "iterations", "test", "logging_level"
#         }
#     })).encode(
#         Image.open(inputs.target_image),
#         np.load(inputs.guess) if inputs.guess is not None else None,
#         lambda i: i < inputs.iterations,
#         inputs.test
#     )
#     np.save(
#         "%s.npy" % (
#             lambda path: path.parent / path.stem
#         )(Path(inputs.target_image)),
#         latent.detach().cpu().numpy()
#     )


def unpack_bz2(src_path):
    data = bz2.BZ2File(src_path).read()
    dst_path = src_path[:-4]
    with open(dst_path, 'wb') as fp:
        fp.write(data)
    return dst_path


class _LossCalculator:

    def __init__(self, device="cpu"):
        extractor = (
            models.vgg16(pretrained=True)
                .features
                [:12]
                .eval()
                .requires_grad_(False)
                .to(device)
        )
        self._to_features = Compose([
            nn.AdaptiveAvgPool2d((256, 256)),
            extractor,
        ])
        # self._l2 = nn.MSELoss()
        self._mask_maker = _MaskMaker()
        self._mask = None
        # self._laplacian = (
        #     Laplacian(3)
        #         .to(device)
        # )
        # self._laplacians = (
        #     Laplacian(3)
        #         .to(device),
        #     Laplacian(5)
        #         .to(device),
        #     Laplacian(7)
        #         .to(device),
        #     Laplacian(9)
        #         .to(device),
        # )
        self._lpips = (
            LPIPS(
                # "vgg" # scary
                "alex"
            )
                .eval()
                .requires_grad_(False)
                .to(device)
        )
        # self._to_edges = lambda tensor: (
        #     (spatial_gradient(tensor) ** 2).sum(axis=2).sqrt()
        # )
        # self._blur = BoxBlur((48, 48))

    def calculate_loss(self, guess_and_generated, target):
        # Poor way to cache
        if self._mask is None:
            self._mask = self._mask_maker.process(target)
        guess, generated = guess_and_generated
        # target, generated = (self._to_edges(tensor) for tensor in (
        #     target, generated
        # ))
        # generated = self._blur(generated)
        return (
            # L1/L2/logcosh on features
            nn.MSELoss()
            # nn.L1Loss()
            # (lambda y_hat, y: torch.mean(torch.log(torch.cosh(y_hat - y))))
            (
                self._to_features(self._mask * generated),
                self._to_features(self._mask * target)
            )
            # + 5 * -torch.log(torch.var(self._laplacian(generated)))
            # + 0.05 * -torch.log(
            #     torch.var(self._laplacians[0](generated))
            #     + torch.var(self._laplacians[1](generated))
            #     + torch.var(self._laplacians[2](generated))
            #     + torch.var(self._laplacians[3](generated))
            # )
            # logcosh on pixels
            + 1.5 * (lambda y_hat, y: (
                torch.mean(torch.log(torch.cosh(y_hat - y)))
            ))
            (
                self._mask *
                generated,
                self._mask *
                target
            )
            # ssim
            + 200 * torch.mean(1 - ssim(
                self._mask *
                target,
                self._mask *
                generated
            ))
            # lpips
            + 100 * torch.mean(self._lpips(
                self._mask *
                target,
                self._mask *
                generated
            ))
            # L1 penalty on generator input
            + (
                0.5
                # 50
                # 500 # scary
            ) * torch.mean(torch.abs(guess - torch.mean(guess,
                axis=2, keepdim=True
            )))
        )


class _MaskMaker:

    def __init__(self):
        self._detector = dlib.get_frontal_face_detector()
        # Takes forever to import keras, pushed to runtime
        import keras
        self._predictor = dlib.shape_predictor(unpack_bz2(keras.utils.get_file(
            "shape_predictor_68_face_landmarks.dat.bz2",
            "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2",
            cache_subdir="temp"
        )))

    def process(self, target):
        assert len(target.shape) == 4, "input should be of batch-like shape"
        assert target.size(0) == 1, "only one-image batches are supported"
        as_array = Compose([
            _from_batch,
            lambda tensor: tensor.cpu().numpy(),
            partial(np.transpose, axes=(1, 2, 0)),
            partial(_minmax_scale, range_=(0, 255)),
            lambda array: array.astype(np.uint8)
        ])(target)
        rectangles = self._detector(as_array, upsample_num_times=0)
        assert rectangles, "no face detected"
        assert len(rectangles) == 1, "multiple faces detected, expect one"
        rectangle = next(rectangle for rectangle in rectangles)
        return Compose([
            torch.from_numpy,
            lambda tensor: tensor.type(target.type()),
            # Add channel dimension, for shape consistency with input
            lambda tensor: tensor.unsqueeze(0),
            _to_batch,
        ])(
            cv2.fillConvexPoly(
                np.zeros(as_array.shape[:-1], np.uint8),
                Compose([
                    partial(self._predictor, box=rectangle),
                    face_utils.shape_to_np,
                    cv2.convexHull
                ])(as_array),
                1
            )
        )


class Encoder:

    def __init__(self, params):
        self._params = params
        self._device = torch.device("cuda" if params.use_gpu else "cpu")
        self._initializer = (
            _load_model(
                Initializer(),
                Path(os.environ["HOME"])
                / "Software/pytorch_stylegan_encoder/image_to_latent.pt",
                map_location=self._device
            )
                .eval()
                .requires_grad_(False)
                .to(self._device)
        )
        self._calc = _LossCalculator(self._device)
        # Monitoring
        self._logger = logging.getLogger(__name__)
        # Endmonitoring
        self._synthesis = (
            _load_model(
                g,
                Path(os.environ["HOME"])
                / "Pretrained/karras2019stylegan-ffhq-1024x1024.for_g_all.pt",
                map_location=self._device
            )
                .g_synthesis
                .eval()
                .requires_grad_(False)
                .to(self._device)
        )

    def encode(
        self, image, guess=None, continue_=lambda i: i < 1, test=True,
        return_byproducts=False
    ):
        target = _image_to_batch(image).to(self._device)
        if guess is None:
            guess = Compose([
                nn.AdaptiveAvgPool2d((256, 256)),
                self._initializer,
                # lambda tensor: tensor.std() * torch.randn_like(tensor) + tensor,
                lambda tensor: tensor.requires_grad_()
            ])(target)
        else:
            guess = Compose([
                torch.from_numpy,
                lambda tensor: tensor.to(self._device),
                lambda tensor: tensor.requires_grad_(),
            ])(guess)
        optimizer = optim.SGD([guess], self._params.lr)
        # # NOTE: blurry makes little sense if guess is not None
        # blurry = _Blurry()
        for i in itertools.count():
            if not continue_(i):
                break
            # Monitoring
            self._logger.info("step %i", i)
            # Endmonitoring
            with _clean_step_of(optimizer):
                generated = self._synthesis(guess)
                loss = self._calc.calculate_loss((guess, generated), target)
                loss.backward()
                # Monitoring
                with io.BytesIO() as buffer:
                    torch.save(guess, buffer)
                    self._logger.debug("guess - %s", buffer.getvalue())
                self._logger.info("loss - %.4f", loss.item())
                # self._logger.info(
                #     "relative blur - %f", blurry.estimate(generated)
                # )
                # Endmonitoring
            if test:
                break
        if return_byproducts:
            return guess, tuple(
                Compose([
                    _from_batch,
                    _minmax_scale,
                    lambda tensor: tensor.cpu(),
                    ToPILImage(),
                ])(tensor) for tensor in (generated, self._calc._mask)
            )
        return guess


class _Blurry:

    def __init__(self):
        self._initial = None
        self._laplacian = Laplacian(3)

    def estimate(self, image):
        # Expects tensor of size 1
        if self._initial is None:
            self._initial = self._compute_variance_of_laplacian(image)
            return 1.0
        return self._compute_variance_of_laplacian(image) / self._initial

    def _compute_variance_of_laplacian(self, image):
        return self._laplacian(image).var().item()


class _Parser(argparse.ArgumentParser):

    def specify_args(self):
        # This is madness!
        # return argparse.Namespace(
        args = argparse.Namespace(
            target_image="002464_01.png",
            guess=None,
            iterations=32,
            lr=0.0002,
            test=1,
            use_gpu=0,
            logging_level="INFO",
        )
        for key, value in args.__dict__.items():
            self.add_argument(
                f"--{key}", type=type(value) if value is not None else str,
                default=value, help=f"defaults to {value}"
            )
        return self


def _load_model(model, filename, map_location=None):
    model.load_state_dict(torch.load(filename, map_location=map_location))
    return model


def _minmax_scale(tensor, range_=(0, 1)):
    min_, max_ = sorted(range_)
    return (
        (tensor - tensor.min()) / (tensor.max() - tensor.min()) * (max_ - min_)
        + min_
    )


@contextlib.contextmanager
def _clean_step_of(optimizer):
    optimizer.zero_grad()
    yield
    optimizer.step()


def _define_inputs():
    parser_or_namespace = _Parser().specify_args()
    try:
        return parser_or_namespace.parse_args()
    except AttributeError:
        return parser_or_namespace


# def _to_batch(tensor):
#     return tensor.unsqueeze(0)
# def _from_batch(one_item_batch):
#     # One-itemness NOT enforced
#     return one_item_batch.squeeze(0)
_to_batch = functools.partial(torch.unsqueeze, dim=0)
_from_batch = functools.partial(torch.squeeze, dim=0)


_image_to_batch = Compose([
    ToTensor(),
    Normalize(MEAN, STD),
    _to_batch,
])


# if __name__ == "__main__":
#     main()
