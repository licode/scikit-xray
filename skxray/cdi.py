# ######################################################################
# Copyright (c) 2014, Brookhaven Science Associates, Brookhaven        #
# National Laboratory. All rights reserved.                            #
#                                                                      #
# @author: Li Li (lili@bnl.gov)                                        #
# created on 03/27/2015                                                #
#                                                                      #
# Original code from Xiaojing Huang (xjhuang@bnl.gov) and Li Li        #
#                                                                      #
# Redistribution and use in source and binary forms, with or without   #
# modification, are permitted provided that the following conditions   #
# are met:                                                             #
#                                                                      #
# * Redistributions of source code must retain the above copyright     #
#   notice, this list of conditions and the following disclaimer.      #
#                                                                      #
# * Redistributions in binary form must reproduce the above copyright  #
#   notice this list of conditions and the following disclaimer in     #
#   the documentation and/or other materials provided with the         #
#   distribution.                                                      #
#                                                                      #
# * Neither the name of the Brookhaven Science Associates, Brookhaven  #
#   National Laboratory nor the names of its contributors may be used  #
#   to endorse or promote products derived from this software without  #
#   specific prior written permission.                                 #
#                                                                      #
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS  #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT    #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS    #
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE       #
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,           #
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES   #
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR   #
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)   #
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,  #
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OTHERWISE) ARISING   #
# IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE   #
# POSSIBILITY OF SUCH DAMAGE.                                          #
########################################################################


from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import six
import numpy as np
import time
from scipy import signal
from scipy.ndimage.filters import gaussian_filter

import logging
logger = logging.getLogger(__name__)


def _dist(dims):
    """
    Create array with pixel value equals to the distance from array center.

    Parameters
    ----------
    dims : list or tuple
        shape of array to create

    Returns
    -------
    arr : np.ndarray
        ND array whose pixels are equal to the distance from the center
        of the array of shape `dims`
    """
    dist_sum = []
    shape = np.ones(len(dims))
    for idx, d in enumerate(dims):
        vec = (np.arange(d) - d // 2) ** 2
        shape[idx] = -1
        vec = vec.reshape(*shape)
        shape[idx] = 1
        dist_sum.append(vec)

    return np.sqrt(np.sum(dist_sum, axis=0))


def gauss(dims, sigma):
    """
    Generate Gaussian function in 2D or 3D.

    Parameters
    ----------
    dims : list or tuple
        shape of the data
    sigma : float
        standard deviation of gaussian function

    Returns
    -------
    arr : array
        ND gaussian
    """
    x = _dist(dims)
    y = np.exp(-(x / sigma)**2 / 2)
    return y / np.sum(y)


_fft_helper = lambda x: np.fft.ifftshift(np.fft.fftn(np.fft.fftshift(x)))
_ifft_helper = lambda x: np.fft.ifftshift(np.fft.ifftn(np.fft.fftshift(x)))


def pi_modulus(recon_pattern,
               diffracted_pattern,
               offset_v=1e-12):
    """
    Transfer sample from real space to q space.
    Use constraint based on diffraction pattern from experiments.

    Parameters
    ----------
    recon_pattern : array
        reconstructed pattern in real space
    diffracted_pattern : array
        diffraction pattern from experiments
    offset_v : float
        add small value to avoid the case of dividing something by zero

    Returns
    -------
    arr : array
        updated pattern in q space
    """
    diff_tmp = _fft_helper(recon_pattern) / np.sqrt(np.size(recon_pattern))
    index = diffracted_pattern > 0
    diff_tmp[index] = (diffracted_pattern[index] *
                       diff_tmp[index] / (np.abs(diff_tmp[index]) + offset_v))
    return _ifft_helper(diff_tmp) * np.sqrt(np.size(diffracted_pattern))


def find_support(sample_obj,
                 sw_sigma, sw_threshold):
    """
    Update sample area based on thresholds.

    Parameters
    ----------
    sample_obj : array
        sample for reconstruction
    sw_sigma : float
        sigma for gaussian in shrinkwrap method
    sw_threshold : float
        threshold used in shrinkwrap method

    Returns
    -------
    new_sup : array
        updated sample support
    """

    sample_obj = np.abs(sample_obj)
    conv_fun = gaussian_filter(sample_obj, sw_sigma)

    conv_max = np.max(conv_fun)

    s_index = conv_fun >= (sw_threshold*conv_max)

    new_sup = np.zeros_like(sample_obj)
    new_sup[s_index] = 1

    return new_sup


def pi_support(sample_obj, index_v):
    """
    Define sample shape by cutting unnecessary values.

    Parameters
    ----------
    sample_obj : array
        sample data
    index_v : array
        index to define sample area

    Returns
    -------
    sample_obj : array
        sample object with proper cut.
    """
    sample_obj = np.array(sample_obj)
    sample_obj[index_v] = 0
    return sample_obj


def cal_relative_error(x_old, x_new):
    """
    Relative error is calculated as the ratio of the difference between the new and
    the original arrays to the norm of the original array.

    Parameters
    ----------
    x_old : array
        previous data set
    x_new : array
        new data set

    Returns
    -------
    float :
        relative error
    """
    return np.linalg.norm(x_new - x_old)/np.linalg.norm(x_old)


def cal_diff_error(sample_obj, diffracted_pattern):
    """
    Calculate the error in q space.

    Parameters
    ----------
    sample_obj : array
        sample data
    diffracted_pattern : array
        diffraction pattern from experiments

    Returns
    -------
    float :
        relative error in q space
    """
    new_diff = np.abs(_fft_helper(sample_obj)) / np.sqrt(np.size(sample_obj))
    return cal_relative_error(diffracted_pattern, new_diff)


def generate_random_phase_field(diffracted_pattern):
    """
    Initiate random phase.

    Parameters
    ----------
    diffracted_pattern : array
        diffraction pattern from experiments

    Returns
    -------
    sample_obj : array
        sample information with phase
    """
    pha_tmp = np.random.uniform(0, 2*np.pi, diffracted_pattern.shape)
    sample_obj = (_ifft_helper(diffracted_pattern * np.exp(1j*pha_tmp))
                  * np.sqrt(np.size(diffracted_pattern)))
    return sample_obj


def generate_box_support(sup_radius, shape_v):
    """
    Generate support area as a box for either 2D or 3D cases.

    Parameters
    ----------
    sup_radius : float
        radius of support
    shape_v : list
        shape of diffraction pattern, which can be either 2D or 3D case.

    Returns
    -------
    sup : array
        support with a box area
    """
    slc_list = [slice(s//2 - sup_radius, s//2 + sup_radius) for s in shape_v]
    sup = np.zeros(shape_v)
    sup[slc_list] = 1
    return sup


def generate_disk_support(sup_radius, shape_v):
    """
    Generate support area as a disk for either 2D or 3D cases.

    Parameters
    ----------
    sup_radius : float
        radius of support
    shape_v : list
        shape of diffraction pattern, which can be either 2D or 3D case.

    Returns
    -------
    sup : array
        support with a disk area
    """
    sup = np.zeros(shape_v)
    dummy = _dist(shape_v)
    sup[dummy < sup_radius] = 1
    return sup


def cdi_recon(diffracted_pattern, sample_obj, sup,
              beta=1.15, start_avg=0.8, pi_modulus_flag='Complex',
              sw_flag=True, sw_sigma=0.5, sw_threshold=0.1, sw_start=0.2,
              sw_end=0.8, sw_step=10, n_iterations=1000):
    """
    Run reconstruction with difference map algorithm.

    Parameters
    ---------
    diffracted_pattern : array
        diffraction pattern from experiments
    sample_obj : array
        initial sample with phase
    sup : array
        initial support
    beta : float, optional
        feedback parameter for difference map algorithm.
        default is 1.15.
    start_avg : float, optional
        define the point to start doing average.
        default is 0.8.
    pi_modulus_flag : str, optional
        'Complex' or 'Real', defining the way to perform pi_modulus calculation.
        default is 'Complex'.
    sw_flag : Bool, optional
        flag to use shrinkwrap algorithm or not.
        default is True.
    sw_sigma : float, optional
        gaussian width used in sw algorithm.
        default is 0.5.
    sw_threshold : float, optional
        shreshold cut in sw algorithm.
        default is 0.1.
    sw_start : float, optional
        at which point to start to do shrinkwrap.
        defualt is 0.2
    sw_end : float, optional
        at which point to stop shrinkwrap.
        defualt is 0.8
    sw_step : float, optional
        the frequency to perform sw algorithm.
        defualt is 10
    n_iterations : int, optional
        number of iterations to run.
        default is 1000.

    Returns
    -------
    obj_avg : array
        reconstructed sample object
    error_dict : dict
        Error information for all iterations. The dict keys include
        obj_error, diff_error and sup_error. Obj_error is a list of
        the relative error of sample object. Diff_error is calculated as
        the difference between new diffraction pattern and the original
        diffraction pattern. And sup_error stores the size of the
        sample support.
    """

    diffracted_pattern = np.array(diffracted_pattern)     # diffraction data

    gamma_1 = -1/beta
    gamma_2 = 1/beta

    # get support index
    sup_out_index = sup < 1

    error_dict = {}
    obj_error = np.zeros(n_iterations)
    diff_error = np.zeros(n_iterations)
    sup_error = np.zeros(n_iterations)

    sup_old = np.zeros_like(diffracted_pattern)
    obj_avg = np.zeros_like(diffracted_pattern).astype(complex)
    avg_i = 0

    time_start = time.time()
    for n in range(n_iterations):
        obj_old = np.array(sample_obj)

        obj_a = pi_modulus(sample_obj, diffracted_pattern)
        if pi_modulus_flag.lower() == 'real':
            obj_a = np.abs(obj_a)

        obj_a = (1 + gamma_2) * obj_a - gamma_2 * sample_obj
        obj_a = pi_support(obj_a, sup_out_index)

        obj_b = pi_support(sample_obj, sup_out_index)
        obj_b = (1 + gamma_1) * obj_b - gamma_1 * sample_obj

        obj_b = pi_modulus(obj_b, diffracted_pattern)
        if pi_modulus_flag.lower() == 'real':
            obj_b = np.abs(obj_b)

        sample_obj += beta * (obj_a - obj_b)

        # calculate errors
        obj_error[n] = cal_relative_error(obj_old, sample_obj)
        diff_error[n] = cal_diff_error(sample_obj, diffracted_pattern)

        if sw_flag:
            if((n >= (sw_start * n_iterations)) and (n <= (sw_end * n_iterations))):
                if np.mod(n, sw_step) == 0:
                    logger.info('Refine support with shrinkwrap')
                    sup = find_support(sample_obj, sw_sigma, sw_threshold)
                    sup_out_index = sup < 1
                    sup_error[n] = np.sum(sup_old)
                    sup_old = np.array(sup)

        if n > start_avg*n_iterations:
            obj_avg += sample_obj
            avg_i += 1

        logger.info('{} object_chi= {}, diff_chi={}'.format(n, obj_error[n],
                                                            diff_error[n]))

    obj_avg = obj_avg / avg_i
    time_end = time.time()

    logger.info('object size: {}'.format(np.shape(diffracted_pattern)))
    logger.info('{} iterations takes {} sec'.format(n_iterations,
                                                    time_end - time_start))

    error_dict['obj_error'] = obj_error
    error_dict['diff_error'] = diff_error
    error_dict['sup_error'] = sup_error

    return obj_avg, error_dict
