from __future__ import print_function
from sys import argv
import os.path
import cv2
import numpy as np
import argparse


def round_to_nearest_dithering2(src_path, dst_path, threshold=128):

    src = cv2.imread(src_path)
    assert src is not None

    if len(src.shape) > 2:
        src = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    y_size, x_size = src.shape
    dst = np.zeros(src.shape, dtype=np.uint8)

    for y in range(y_size):
        for x in range(x_size):
            dst[y, x] = 255 if src[y, x] > threshold else 0

    cv2.imwrite(dst_path, dst)
    return


def round_random_dithering2(src_path, dst_path):
    src = cv2.imread(src_path)
    assert src is not None

    if len(src.shape) > 2:
        src = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    y_size, x_size = src.shape
    dst = src

    for y in range(y_size):
        for x in range(x_size):
            threshold = np.random.randint(0, 256, dtype=np.uint8)
            dst[y, x] = 255 if src[y, x] > threshold else 0

    cv2.imwrite(dst_path, dst)


def get_dithering_matrix(sz):
    if sz == 2:
        return np.matrix([[0, 2], [3, 1]], dtype=np.uint8)
    elif sz == 3:
        return np.matrix([[0, 7, 3], [6, 5, 2], [4, 1, 8]], dtype=np.uint8)
    else:
        m_rec = 4 * get_dithering_matrix(sz//2)
        m_unit = np.ones([sz//2, sz//2], dtype=np.uint8)
        m_res = np.vstack([np.hstack([m_rec, m_rec + 2*m_unit]),
                          np.hstack([m_rec + 3*m_unit, m_rec + m_unit])])
        return m_res


def round_ordered_dithering2(src_path, dst_path, dith_size=16):
    src = cv2.imread(src_path)
    assert src is not None

    if len(src.shape) > 2:
        src = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    y_size, x_size = src.shape
    dst = np.zeros(src.shape, dtype=np.uint8)
    dith_mat = get_dithering_matrix(dith_size)

    coef = dith_size * dith_size / 255
    for y in range(y_size):
        d_y = y % dith_size
        for x in range(x_size):
            d_x = x % dith_size
            dst[y, x] = 255 if coef * src[y, x] > dith_mat[d_y, d_x] else 0

    cv2.imwrite(dst_path, dst)
    return


def round_error_diff_fwd(src_path, dst_path):
    src = cv2.imread(src_path)
    assert src is not None

    if len(src.shape) > 2:
        src = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    y_size, x_size = src.shape
    dst = np.zeros(src.shape)

    for y in range(y_size):
        error = 0
        for x in range(x_size):
            if int(src[y, x]) + error > 128:
                error = (int(src[y, x]) + error) - 255
                dst[y, x] = 255
            else:
                error = int(src[y, x]) + error
                dst[y, x] = 0

    cv2.imwrite(dst_path, dst)
    return


def round_error_diff_fwd_bwd(src_path, dst_path):
    src = cv2.imread(src_path)
    assert src is not None

    if len(src.shape) > 2:
        src = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    y_size, x_size = src.shape
    dst = np.zeros(src.shape)

    for y in range(y_size):
        error = 0
        c_range = range(x_size - 1, -1, -1) if y % 2 else range(x_size)
        for x in c_range:
            if int(src[y, x]) + error > 128:
                error = (int(src[y, x]) + error) - 255
                dst[y, x] = 255
            else:
                error = int(src[y, x]) + error
                dst[y, x] = 0

    cv2.imwrite(dst_path, dst)
    return


def round_error_diff_floyd_steinberg(src_path, dst_path):
    src = cv2.imread(src_path)
    assert src is not None

    if len(src.shape) > 2:
        src = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    y_size, x_size = src.shape
    src = src.astype(int)
    dst = np.zeros(src.shape)

    error = 0
    for y in range(y_size):
        is_even = 1 - 2 * (y % 2)
        c_range = range(x_size-1, -1, -1) if is_even else range(x_size)

        for x in c_range:
            if src[y, x] > 128:
                error = src[y, x] - 255
                dst[y, x] = 255
            else:
                error = src[y, x]
                dst[y, x] = 0

            if y < y_size-1:
                src[y+1, x] += (5*error) >> 4
                if 0 <= x+is_even < x_size:
                    src[y+1, x+is_even] += error >> 4
                    src[y, x+is_even] += (7*error) >> 4
                if 0 <= x-is_even < x_size:
                    src[y+1, x-is_even] += (3*error) >> 4

    cv2.imwrite(dst_path, dst)
    return


algoritms = {'thresh': round_to_nearest_dithering2,
             'rdith': round_random_dithering2,
             'odith': round_ordered_dithering2,
             'ediff1': round_error_diff_fwd,
             'ediff2': round_error_diff_fwd_bwd,
             'floyd-stein': round_error_diff_floyd_steinberg
             }


def run_algorithm(args):
    src_path = args.input
    assert os.path.exists(src_path)

    dst_path = args.output

    dst_file, dst_ext = os.path.basename(dst_path).split('.')
    dst_file = '{}_{}.{}'.format(dst_file, args.alg, dst_ext)

    dst_dir = os.path.dirname(dst_path)
    dst_path = os.path.join(dst_dir, dst_file)

    algoritms[args.alg](src_path, dst_path)
    return


def parse_args():
    m = argparse.ArgumentParser(description="Comparison semitone image binary approximation algorithms")
    m.add_argument("--input", "-i", type=str,
                   help="Input image", required=True)

    m.add_argument("--output", "-o", type=str, required=True,
                   help="Image-result")
    m.add_argument("--alg", "-a", type=str, choices=['thresh', 'rdith', 'odith',
                                                     'ediff1', 'ediff2', 'floyd-stein'],
                   help="Select algorithm to use", default='thresh')

    args = m.parse_args()
    return args


if __name__ == '__main__':

    options = parse_args()
    run_algorithm(options)

    exit(0)