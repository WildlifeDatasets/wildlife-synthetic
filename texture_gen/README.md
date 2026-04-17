# Texture generation

This module generates new textures for 3D animal models.  
It is based on the Paint-it [paper](https://arxiv.org/pdf/2312.11360) and [repository](https://github.com/kaist-ami/Paint-it).



### Environment installation

> ⚠️ This setup requires a GPU with CUDA 11.3.  
> The dependency versions are intentionally pinned for compatibility with Paint-it.

```bash
conda create -n paint_it python=3.8
conda activate paint_it

# pytorch installation
pip install torch==1.12.0+cu113 torchvision==0.13.0+cu113 torchaudio==0.12.0 --extra-index-url https://download.pytorch.org/whl/cu113

# for pytorch3d installation
conda install -c fvcore -c iopath -c conda-forge fvcore iopath
# for python3.8, cuda 11.3, pytorch 1.12 (py38_cu113_pyt1120) -> need to install pytorch3d-0.7.2
pip install --no-index --no-cache-dir pytorch3d -f https://dl.fbaipublicfiles.com/pytorch3d/packaging/wheels/py38_cu113_pyt1120/download.html

pip install git+https://github.com/NVlabs/nvdiffrast/
pip install diffusers==0.12.1 huggingface-hub==0.11.1 transformers==4.21.1 sentence-transformers==2.2.2
pip install PyOpenGL PyOpenGL_accelerate accelerate rich ninja scipy trimesh imageio matplotlib chumpy opencv-python
pip install numpy==1.23.1
```

## Generate textures:

```bash
python paint_it.py \
--path "data/cat_model/12221_Cat_v1_l3.obj" \
--caption "A Rosette Lynx with rosette-shaped markings, consisting of dark outlines surrounding clusters of lighter fur, resembling the spots of a leopard" \

```

`prompts.json` contains a library of prompts for lynx and other felines.


## Acknowledgement
This module derived from the original Paint-it repository https://github.com/kaist-ami/Paint-it
If you use this code, please cite their original work:

```bibtex
@inproceedings{youwang2024paintit,
    title = {Paint-it: Text-to-Texture Synthesis via Deep Convolutional Texture Map Optimization and Physically-Based Rendering},
    author = {Youwang, Kim and Oh, Tae-Hyun and Pons-Moll, Gerard},
    booktitle = {IEEE Conference on Computer Vision and Pattern Recognition (CVPR)},
    year = {2024}
}
```
