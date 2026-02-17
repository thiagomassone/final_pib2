from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple, Union
from compression.huffman_core import HuffmanEncoding, HuffmanDec


import numpy as np

MAGIC = b"HUF1"

@dataclass
class HuffmanPackage:
    shape: Tuple[int, int]
    padding_bits: int
    codes: Dict[int, str]
    data: bytes


def _pack_bits(bitstring: str) -> Tuple[bytes, int]:
    """Pack '0'/'1' string to bytes. Returns (data_bytes, padding_bits)."""
    if not bitstring:
        return b"", 0
    padding = (8 - (len(bitstring) % 8)) % 8
    bitstring_padded = bitstring + ("0" * padding)
    as_int = int(bitstring_padded, 2)
    data = as_int.to_bytes(len(bitstring_padded) // 8, byteorder="big")
    return data, padding


def _unpack_bits(data: bytes, padding_bits: int) -> str:
    """Unpack bytes to bitstring and remove padding bits."""
    if not data:
        return ""
    bit_len = len(data) * 8
    as_int = int.from_bytes(data, byteorder="big")
    bitstring = bin(as_int)[2:].zfill(bit_len)
    if padding_bits:
        bitstring = bitstring[:-padding_bits]
    return bitstring


def encode_image(img: np.ndarray) -> HuffmanPackage:
    """
    Encode uint8 2D image to HuffmanPackage.
    Requiere tus funciones HuffmanEncoding/histograma/findCode (o equivalente).
    """
    if img.ndim != 2:
        raise ValueError("encode_image espera imagen 2D (grayscale).")
    if img.dtype != np.uint8:
        img = img.astype(np.uint8)

    comprimida_bits, dicc, ish, _ = HuffmanEncoding(img)

    data_bytes, padding_bits = _pack_bits(comprimida_bits)
    return HuffmanPackage(shape=ish, padding_bits=padding_bits, codes=dicc, data=data_bytes)


def decode_image(pkg: HuffmanPackage) -> np.ndarray:
    """
    Decode HuffmanPackage back to uint8 2D image.
    Requiere tu HuffmanDec(comprimida_bits, dicc, shape).
    """
    bits = _unpack_bits(pkg.data, pkg.padding_bits)
    img = HuffmanDec(bits, pkg.codes, pkg.shape)
    # Asegurar dtype/shape
    img = np.array(img, dtype=np.uint8).reshape(pkg.shape)
    return img


def save_huf(pkg: HuffmanPackage, path: Union[str, Path]) -> None:
    path = Path(path)
    payload = pickle.dumps(pkg, protocol=pickle.HIGHEST_PROTOCOL)
    with open(path, "wb") as f:
        f.write(MAGIC)
        f.write(payload)


def load_huf(path: Union[str, Path]) -> HuffmanPackage:
    path = Path(path)
    with open(path, "rb") as f:
        magic = f.read(4)
        if magic != MAGIC:
            raise ValueError("Archivo .huf inválido (magic no coincide).")
        payload = f.read()
    pkg = pickle.loads(payload)
    if not isinstance(pkg, HuffmanPackage):
        raise ValueError("Archivo .huf corrupto o formato inesperado.")
    return pkg


def compress_image_to_huf_file(img: np.ndarray, out_path: Union[str, Path]) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pkg = encode_image(img)
    save_huf(pkg, out_path)
    return out_path


def decompress_huf_file_to_image(huf_path: Union[str, Path]) -> np.ndarray:
    pkg = load_huf(huf_path)
    return decode_image(pkg)
