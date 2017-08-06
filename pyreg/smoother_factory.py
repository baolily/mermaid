'''
General purpose regularizers which can be used
'''

from abc import ABCMeta, abstractmethod

import torch
from torch.autograd import Variable
import torch.nn.functional as F
import numpy as np

import finite_differences as fd

import utils

import custom_pytorch_extensions as ce

class Smoother(object):
    __metaclass__ = ABCMeta

    def __init__(self, sz, spacing, params):
        self.sz = sz
        self.spacing = spacing
        self.fdt = fd.FD_torch( self.spacing )
        self.volumeElement = self.spacing.prod()
        self.dim = len(spacing)
        self.params = params

    @abstractmethod
    def smooth_scalar_field(self, I):
        pass

    @abstractmethod
    def inverse_smooth_scalar_field(self, I):
        pass

    def smooth_scalar_field_multiNC(self, I):
        sz = I.size()
        Is = Variable(torch.zeros(sz), requires_grad=False)
        for nrI in range(sz[0]):  # loop over all the images
            Is[nrI, ...] = self.smooth_scalar_field_multiC(I[nrI, ...])
        return Is

    def smooth_scalar_field_multiC(self, I):
        sz = I.size()
        Is = Variable(torch.zeros(sz), requires_grad=False)
        for nrC in range(sz[0]):  # loop over all the channels, just advect them all the same
            Is[nrC, ...] = self.smooth_scalar_field(I[nrC, ...])
        return Is

    def inverse_smooth_vector_field_multiN(self, v):
        sz = v.size()
        ISv = Variable(torch.FloatTensor(v.size()))
        for nrI in range(sz[0]): # loop over all images
            ISv[nrI,...] = self.inverse_smooth_vector_field(v[nrI, ...])
        return ISv

    def inverse_smooth_vector_field(self, v):
        if self.dim==1:
            return self.inverse_smooth_scalar_field(v) # if one dimensional, default to scalar-field smoothing
        else:
            ISv = Variable( torch.FloatTensor( v.size() ) )
            # smooth every dimension individually
            for d in range(0, self.dim):
                ISv[d,...] = self.inverse_smooth_scalar_field(v[d, ...])
            return ISv

    def smooth_vector_field_multiN(self, v):
        sz = v.size()
        Sv = Variable(torch.FloatTensor(v.size()))
        for nrI in range(sz[0]): #loop over all the images
            Sv[nrI,...] = self.smooth_vector_field(v[nrI, ...])
        return Sv

    def smooth_vector_field(self, v):
        if self.dim==1:
            return self.smooth_scalar_field(v) # if one dimensional, default to scalar-field smoothing
        else:
            Sv = Variable( torch.FloatTensor( v.size() ) )
            # smooth every dimension individually
            for d in range(0, self.dim):
                Sv[d,...] = self.smooth_scalar_field(v[d, ...])
            return Sv

class DiffusionSmoother(Smoother):

    def __init__(self, sz, spacing, params):
        super(DiffusionSmoother,self).__init__(sz,spacing,params)
        self.iter = params[('iter', 5, 'Number of iterations' )]

    def set_iter(self,iter):
        self.iter = iter

    def get_iter(self):
        return self.iter

    def smooth_scalar_field(self, v):
        # basically just solving the heat equation for a few steps
        Sv = v.clone()
        # now iterate and average based on the neighbors
        for i in range(0,self.iter*2**self.dim): # so that we smooth the same indepdenent of dimension
            # multiply with smallest h^2 and divide by 2^dim to assure stability
            Sv = Sv + 0.5/(2**self.dim)*self.fdt.lap(Sv)*self.spacing.min()**2 # multiply with smallest h^2 to assure stability
        return Sv

    def inverse_smooth_scalar_field(self, v):
        raise ValueError('Sorry: Inversion of smoothing only supported for Fourier-based filters at the moment')

# TODO: clean up the two Gaussian smoothers
class GaussianSmoother(Smoother):

    def __init__(self, sz, spacing, params):
        super(GaussianSmoother,self).__init__(sz,spacing,params)

class GaussianSpatialSmoother(GaussianSmoother):

    def __init__(self, sz, spacing, params):
        super(GaussianSpatialSmoother,self).__init__(sz,spacing,params)
        self.k_sz_h = params[('k_sz_h', None, 'size of the kernel' )]
        self.filter = None

    def set_k_sz_h(self,k_sz_h):
        self.k_sz_h = k_sz_h

    def get_k_sz_h(self):
        return self.k_sz_h

    def _create_filter(self):

        if self.k_sz_h is None:
            self.k_sz = (2 * 5 + 1) * np.ones(self.dim, dtype='int')  # default kernel size
        else:
            self.k_sz = k_sz_h * 2 + 1  # this is to assure that the kernel is odd size

        self.smoothingKernel = self._create_smoothing_kernel(self.k_sz)
        self.required_padding = (self.k_sz-1)/2

        if self.dim==1:
            self.filter = Variable(torch.from_numpy(self.smoothingKernel).view([sz[0],sz[1],k_sz[0]]))
        elif self.dim==2:
            self.filter = Variable(torch.from_numpy(self.smoothingKernel).view([sz[0],sz[1],k_sz[0],k_sz[1]]))
        elif self.dim==3:
            self.filter = Variable(torch.from_numpy(self.smoothingKernel).view([sz[0],sz[1],k_sz[0],k_sz[1],k_sz[2]]))
        else:
            raise ValueError('Can only create the smoothing kernel in dimensions 1-3')

        # TODO: Potentially do all of the computations in physical coordinates (for now just [-1,1]^d)
    def _create_smoothing_kernel(self, k_sz):
        mus = np.zeros(self.dim)
        stds = np.ones(self.dim)
        id = utils.identity_map(k_sz)
        g = utils.compute_normalized_gaussian(id, mus, stds)

        return g

    # TODO: See if we can avoid the clone calls somehow
    # This is likely due to the slicing along the dimension for vector-valued field
    # TODO: implement a version that can be used for multi-channel multi-image inputs
    def _filter_input_with_padding(self, I):
        if self.dim==1:
            I_4d = I.view([1,1,1]+list(I.size()))
            I_pad = F.pad(I_4d,(self.required_padding[0],self.required_padding[0],0,0),mode='replicate').view(1,1,-1)
            return F.conv1d(I_pad,self.filter).view(I.size())
        elif self.dim==2:
            I_pad = F.pad(I,(self.required_padding[0],self.required_padding[0],
                                self.required_padding[1],self.required_padding[1]),mode='replicate')
            return F.conv2d(I_pad,self.filter).view(I.size())
        elif self.dim==3:
            I_pad = F.pad(I, (self.required_padding[0], self.required_padding[0],
                                 self.required_padding[1], self.required_padding[1],
                                 self.required_padding[2], self.required_padding[2]), mode='replicate')
            return F.conv3d(I_pad, self.filter).view(I.size())
        else:
            raise ValueError('Can only perform padding in dimensions 1-3')

    def smooth_scalar_field(self, v):
        if self.filter is None:
            self._create_filter()
        # just doing a Gaussian smoothing
        return self._filter_input_with_padding(v)

    def inverse_smooth_scalar_field(self, v):
        raise ValueError('Sorry: Inversion of smoothing only supported for Fourier-based filters at the moment')


class GaussianFourierSmoother(GaussianSmoother):

    def __init__(self, sz, spacing, params):
        super(GaussianFourierSmoother,self).__init__(sz,spacing,params)
        self.gaussianStd = params[('gaussian_std', 0.15,'std for the Gaussian' )]
        self.FFilter = None

    def _create_filter(self):

        mus = np.zeros(self.dim)
        stds = self.gaussianStd*np.ones(self.dim)
        id = utils.identity_map(self.sz)
        g = utils.compute_normalized_gaussian(id, mus, stds)

        self.FFilter = ce.create_complex_fourier_filter(g, self.sz)

    def set_gaussian_std(self,gstd):
        self.gaussianStd = gstd

    def get_gaussian_std(self):
        return self.gaussianStd

    def smooth_scalar_field(self, v):
        # just doing a Gaussian smoothing
        # we need to instantiate a new filter function here every time for the autograd to work
        if self.FFilter is None:
            self._create_filter()
        return ce.fourier_convolution(v, self.FFilter)

    def inverse_smooth_scalar_field(self, v):
        if self.FFilter is None:
            self._create_filter()
        return ce.inverse_fourier_convolution(v, self.FFilter)

class SmootherFactory(object):

    __metaclass__ = ABCMeta

    def __init__(self,sz,spacing):
        self.spacing = spacing
        self.sz = sz
        self.dim = len( spacing )
        self.default_smoother_type = 'gaussian'

    def set_default_smoother_type_to_gaussian(self):
        self.default_smoother_type = 'gaussian'

    def set_default_smoother_type_to_diffusion(self):
        self.default_smoother_type = 'diffusion'

    def set_default_smoother_type_to_gaussianSpatial(self):
        self.default_smoother_type = 'gaussianSpatial'

    def create_smoother(self, params):

        cparams = params[('smoother',{})]
        smootherType = cparams[('type', self.default_smoother_type,
                                          'type of smoother (difusion/gaussian/gaussianSpatial)' )]
        if smootherType=='diffusion':
            return DiffusionSmoother(self.sz,self.spacing,cparams)
        elif smootherType=='gaussian':
            return GaussianFourierSmoother(self.sz,self.spacing,cparams)
        elif smootherType=='gaussianSpatial':
            return GaussianSpatialSmoother(self.sz,self.spacing,cparams)
        else:
            raise ValueError( 'Smoother: ' + smootherName + ' not known')