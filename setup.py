# -*- coding: utf-8 -*-
""""""


from setuptools import setup, find_packages


setup(
    name="stylegan-encoder",
    version="0.0.0",
    description="StyleGAN encoder",
    # packages=find_packages(),
    py_modules=["encoder"],
    python_requires='>=3.6',
    install_requires=[
        "Pillow",
        "opencv-python",
        "numpy",
        "torch",
        "torchvision",
        "dlib",
        # Keras==2.3.0
        # tensorflow==2.1.0
        "imutils",
        "kornia",
        "lpips-pytorch @ git+https://github.com/S-aiueo32/lpips-pytorch@d94711e",
        "pytorch_stylegan_encoder @ git+https://github.com/ihor-durnopianov/pytorch_stylegan_encoder@0ea0f88",
        "pytorch-ssim @ git+https://github.com/Po-Hsun-Su/pytorch-ssim@d6adfb5",
        "style_gan @ git+https://github.com/ihor-durnopianov/style_gan@4686dcf",
        # Indirect.  TODO: get rid of
        "ipython",
    ],
    # entry_points={
    #     "console_scripts": [
    #         # "deliverable-run=deliverable.__main__:main"
    #     ]
    # },
)
