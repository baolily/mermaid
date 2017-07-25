"""
Finite difference class to support numpy (FD_np) and pyTorch (FD_torch)
"""

from abc import ABCMeta, abstractmethod

import torch
from torch.autograd import Variable

import numpy as np

class FD(object):
    __metaclass__ = ABCMeta

    def __init__(self, spacing, bcNeumannZero=True):

        self.dim = spacing.size
        self.spacing = np.ones( self.dim )
        self.bcNeumannZero = bcNeumannZero # if false then linear interpolation
        if spacing.size==1:
            self.spacing[0] = spacing[0]
        elif spacing.size==2:
            self.spacing[0] = spacing[0]
            self.spacing[1] = spacing[1]
        elif spacing.size==3:
            self.spacing = spacing
        else:
            raise ValueError('Finite differences are only supported in dimensions 1 to 3')

    def dXb(self,I):
        return (I-self.xm(I))/self.spacing[0]

    def dXf(self,I):
        return (self.xp(I)-I)/self.spacing[0]

    def dXc(self,I):
        return (self.xp(I)-self.xm(I))/(2*self.spacing[0])

    def ddXc(self,I):
        return (self.xp(I)-2*I+self.xm(I))/(self.spacing[0]**2)

    def dYb(self,I):
        return (I-self.ym(I))/self.spacing[1]

    def dYf(self,I):
        return (self.yp(I)-I)/self.spacing[1]

    def dYc(self,I):
        return (self.yp(I)-self.ym(I))/(2*self.spacing[1])

    def ddYc(self,I):
        return (self.yp(I)-2*I+self.ym(I))/(self.spacing[1]**2)

    def dZb(self,I):
        return (I - self.zm(I))/self.spacing[2]

    def dZf(self, I):
        return (self.zp(I)-I)/self.spacing[2]

    def dZc(self, I):
        return (self.zp(I)-self.zm(I))/(2*self.spacing[2])

    def ddZc(self,I):
        return (self.zp(I)-2*I+self.zm(I))/(self.spacing[2]**2)

    def lap(self, I):
        ndim = self.getdimension(I)
        if ndim == 1:
            return self.ddXc(I)
        elif ndim == 2:
            return (self.ddXc(I) + self.ddYc(I))
        elif ndim == 3:
            return (self.ddXc(I) + self.ddYc(I) + self.ddZc(I))
        else:
            raise ValueError('Finite differences are only supported in dimensions 1 to 3')

    @abstractmethod
    def getdimension(self,I):
        # returns the dimension of the array
        pass

    @abstractmethod
    def create_zero_array(self, sz):
        pass

    @abstractmethod
    def get_size_of_array(self, A):
        pass

    # We are assuming linear interpolation for the values outside the bounds here
    # TODO: Offer other boundary conditions if desired

    def xp(self,I):
        # returns x values to the right
        rxp = self.create_zero_array( self.get_size_of_array( I ) )
        ndim = self.getdimension(I)
        if ndim == 1:
            rxp[0:-1] = I[1:]
            if self.bcNeumannZero:
                rxp[-1] = I[-1]
            else:
                rxp[-1] = 2*I[-1]-I[-2]
        elif ndim == 2:
            rxp[0:-1,:] = I[1:,:]
            if self.bcNeumannZero:
                rxp[-1,:] = I[-1,:]
            else:
                rxp[-1,:] = 2*I[-1,:]-I[-2,:]
        elif ndim == 3:
            rxp[0:-1,:,:] = I[1:,:,:]
            if self.bcNeumannZero:
                rxp[-1,:,:] = I[-1,:,:]
            else:
                rxp[-1,:,:] = 2*I[-1,:,:]-I[-2,:,:]
        else:
            raise ValueError('Finite differences are only supported in dimensions 1 to 3')
        return rxp

    def xm(self,I):
        # returns x values to the left
        rxm = self.create_zero_array( self.get_size_of_array( I ) )
        ndim = self.getdimension(I)
        if ndim == 1:
            rxm[1:] = I[0:-1]
            if self.bcNeumannZero:
                rxm[0] = I[0]
            else:
                rxm[0] = 2*I[0]-I[1]
        elif ndim == 2:
            rxm[1:,:] = I[0:-1,:]
            if self.bcNeumannZero:
                rxm[0,:] = I[0,:]
            else:
                rxm[0,:] = 2*I[0,:]-I[1,:]
        elif ndim == 3:
            rxm[1:,:,:] = I[0:-1,:,:]
            if self.bcNeumannZero:
                rxm[0,:,:] = I[0,:,:]
            else:
                rxm[0,:,:] = 2*I[0,:,:]-I[1,:,:]
        else:
            raise ValueError('Finite differences are only supported in dimensions 1 to 3')
        return rxm

    def yp(self, I):
        # returns y values to the right
        ryp = self.create_zero_array( self.get_size_of_array( I ) )
        ndim = self.getdimension(I)
        if ndim == 2:
            ryp[:,0:-1] = I[:,1:]
            if self.bcNeumannZero:
                ryp[:,-1] = I[:,-1]
            else:
                ryp[:,-1] = 2*I[:,-1]-I[:,-2]
        elif ndim == 3:
            ryp[:,0:-1,:] = I[:,1:,:]
            if self.bcNeumannZero:
                ryp[:,-1,:] = I[:,-1,:]
            else:
                ryp[:,-1,:] = 2*I[:,-1,:]-I[:,-2,:]
        else:
            raise ValueError('Finite differences are only supported in dimensions 1 to 3')
        return ryp

    def ym(self, I):
        # returns y values to the left
        rym = self.create_zero_array( self.get_size_of_array( I ) )
        ndim = self.getdimension(I)
        if ndim == 2:
            rym[:,1:] = I[:,0:-1]
            if self.bcNeumannZero:
                rym[:,0] = I[:,0]
            else:
                rym[:,0] = 2*I[:,0]-I[:,1]
        elif ndim == 3:
            rym[:,1:,:] = I[:,0:-1,:]
            if self.bcNeumannZero:
                rym[:,0,:] = I[:,0,:]
            else:
                rym[:,0,:] = 2*I[:,0,:]-I[:,1,:]
        else:
            raise ValueError('Finite differences are only supported in dimensions 1 to 3')
        return rym

    def zp(self, I):
        # returns z values to the right
        rzp = self.create_zero_array( self.get_size_of_array( I ) )
        ndim = self.getdimension(I)
        if ndim == 3:
            rzp[:,:,0:-1] = I[:,:,1:]
            if self.bcNeumannZero:
                rzp[:,:,-1] = I[:,:,-1]
            else:
                rzp[:,:,-1] = 2*I[:,:,-1]-I[:,:,-2]
        else:
            raise ValueError('Finite differences are only supported in dimensions 1 to 3')
        return rzp

    def zm(self, I):
        # returns z values to the left
        rzm = self.create_zero_array( self.get_size_of_array( I ) )
        ndim = self.getdimension(I)
        if ndim == 3:
            rzm[:,:,1:] = I[:,:,0:-1]
            if self.bcNeumannZero:
                rzm[:,:,0] = I[:,:,0]
            else:
                rzm[:,:,0] = 2*I[:,:,0]-I[:,:,1]
        else:
            raise ValueError('Finite differences are only supported in dimensions 1 to 3')
        return rzm


class FD_np(FD):

    def __init__(self,spacing):
        super(FD_np, self).__init__(spacing)

    def getdimension(self,I):
        return I.ndim

    def create_zero_array(self, sz):
        return np.zeros( sz )

    def get_size_of_array(self, A):
        return A.shape


class FD_torch(FD):

    def __init__(self,spacing):
        super(FD_torch, self).__init__(spacing)

    def getdimension(self,I):
        return I.dim()

    def create_zero_array(self, sz):
        return Variable( torch.zeros( sz ), requires_grad=False )

    def get_size_of_array(self, A):
        return A.size()