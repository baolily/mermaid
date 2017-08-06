"""
Package to create example images to test the image registration algorithms
"""

# TODO: convert everything to simple itk and its image format (including spacing)
# for now, simply get the 3D versions up and running

from abc import ABCMeta, abstractmethod
import numpy as np
import utils

class CreateExample(object):
    """
    Abstract base class.
    """
    __metaclass__ = ABCMeta

    def __init__(self,dim):
        """
        Constructor
        
        :param dim: Desired dimension of the example image 
        """
        self.dim = dim

    @abstractmethod
    def create_image_pair(self,sz=None,params=None):
        """
        Abstract method to create example image pairs
        
        :param params: Dictionary which contains parameters to create the images 
        :return: Will return two images
        """
        pass

class CreateSquares(CreateExample):
    """
    Class to create two example squares in arbitrary dimension as registration test cases
    """
    def __init__(self,dim):
        super(CreateSquares, self).__init__(dim)

    def create_image_pair(self,sz,params):
        """
        Creates two square images in dimensions 1-3
        
        :param sz: Desired size, e.g., [5,10] 
        :param params: Parameter dictionary. Uses 'len_s' and 'len_l' to define the side-length of the small and 
            the large squares which will be generated 
        :return: Returns two images of squares
        """

        I0 = np.zeros(sz, dtype='float32')
        I1 = np.zeros(sz, dtype='float32')
        # get parameters and replace with defaults if necessary

        # create a new category if it does not exist
        params[('square_example_images', {}, 'Controlling the size of a nD cube')]
        len_s = params['square_example_images'][('len_s',sz.min()/6,'Mimimum side-length of square')]
        len_l = params['square_example_images'][('len_l',sz.max()/4,'Maximum side-length of square')]

        c = sz/2 # center coordinates
        # create small and large squares
        if self.dim==1:
            I0[c[0]-len_s:c[0]+len_s]=1
            I1[c[0]-len_l:c[0]+len_l]=1
        elif self.dim==2:
            I0[c[0]-len_s:c[0]+len_s, c[1]-len_s:c[1]+len_s] = 1
            I1[c[0]-len_l:c[0]+len_l, c[1]-len_l:c[1]+len_l] = 1
        elif self.dim==3:
            I0[c[0] - len_s:c[0] + len_s, c[1] - len_s:c[1] + len_s, c[2]-len_s:c[2]+len_s] = 1
            I1[c[0] - len_l:c[0] + len_l, c[1] - len_l:c[1] + len_l, c[2]-len_l:c[2]+len_l] = 1
        else:
            raise ValueError('Square examples only supported in dimensions 1-3.')

        # now transform from single-channel to multi-channel image format
        I0 = utils.transform_image_to_NC_image_format(I0)
        I1 = utils.transform_image_to_NC_image_format(I1)

        return I0,I1

class CreateRealExampleImages(CreateExample):
    """
    Class to create two example brain images. Currently only supported in 2D
    """
    def __init__(self,dim):
        super(CreateRealExampleImages, self).__init__(dim)

    def create_image_pair(self,sz=None,params=None):
        """
        Loads the two brain images using SimpleITK, normalized them so that the 95-th percentile is as 0.95 and returns them.
        
        :param sz: Ignored 
        :param params: Ignored
        :return: Returns the two brain slices.
        """
        import SimpleITK as sitk

        # create small and large squares
        if self.dim==2:
            brain_s = sitk.ReadImage('./test_data/brain_slices/ws_slice.nrrd')
            brain_t = sitk.ReadImage('./test_data/brain_slices/wt_slice.nrrd')
            I0 = sitk.GetArrayFromImage(brain_s)
            I0 = I0.squeeze()

            I1 = sitk.GetArrayFromImage(brain_t)
            I1 = I1.squeeze()

            # normalize based on the 95-th percentile
            I0 = I0 / np.percentile(I0, 95) * 0.95
            I1 = I1 / np.percentile(I1, 95) * 0.95
        else:
            raise ValueError('Real examples only supported in dimension 2 at the moment.')

        # now transform from single-channel to multi-channel image format
        I0 = utils.transform_image_to_NC_image_format(I0)
        I1 = utils.transform_image_to_NC_image_format(I1)

        return I0,I1