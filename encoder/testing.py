# -*- coding: utf-8 -*-
"""

Usage: python -m encoder.testing
"""


# Do we want to specify .testing deps in requirements.txt and
# install_requires?
import IPython
import PIL.Image
import matplotlib.pyplot as plt
# import torchvision.utils as vutils
# from torchvision.transforms import Compose, ToTensor

from . import step


OUR_PIC = PIL.Image.open("data/our-woman.png")


# _, generated = step(OUR_PIC)
# plt.imshow(generated)
# plt.show()


# # Unusable.  TODO: clean up
# pics, latent = [], None
# for _ in range(8):
#     latent, generated = step(OUR_PIC, latent)
#     pics.append(generated)
# fig, axs = plt.subplots(2, 2)
# for ax, pic in zip(axs.flatten(), pics):
#     ax.imshow(pic)
# batches = []
# for pic in pics:
#     batches.append(Compose([ToTensor()])(pic))
# plt.imshow(vutils.make_grid(batches, 2).numpy().transpose(1, 2, 0))


if __name__ == "__main__":
    IPython.embed()
