import set_pyreg_paths

# first do the torch imports
import torch
from torch.autograd import Variable
from pyreg.data_wrapper import AdaptVal
import numpy as np

import pyreg.example_generation as eg
import pyreg.module_parameters as pars
import pyreg.multiscale_optimizer as MO
import pyreg.smoother_factory as SF

params = pars.ParameterDict()
#params.load_JSON('../test/json/test_svf_image_single_scale_config.json')
params.load_JSON('./svf_shooting_test.json')


example_img_len = 128
dim = 2
szEx = np.tile(example_img_len, dim)  # size of the desired images: (sz)^dim
I0, I1 = eg.CreateSquares(dim).create_image_pair(szEx, params)  # create a default image size with two sample squares
sz = np.array(I0.shape)
spacing = 1. / (sz[2::] - 1)  # the first two dimensions are batch size and number of image channels

# create the source and target image as pyTorch variables
ISource = AdaptVal(Variable(torch.from_numpy(I0.copy()), requires_grad=False))
ITarget = AdaptVal(Variable(torch.from_numpy(I1), requires_grad=False))

# smooth both a little bit
params[('image_smoothing', {}, 'image smoothing settings')]
params['image_smoothing'][('smooth_images', True, '[True|False]; smoothes the images before registration')]
params['image_smoothing'][('smoother',{},'settings for the image smoothing')]
params['image_smoothing']['smoother'][('gaussian_std', 0.05, 'how much smoothing is done')]
params['image_smoothing']['smoother'][('type', 'gaussian', "['gaussianSpatial'|'gaussian'|'diffusion']")]

cparams = params['image_smoothing']
s = SF.SmootherFactory(sz[2::], spacing).create_smoother(cparams)
ISource = s.smooth_scalar_field(ISource)
ITarget = s.smooth_scalar_field(ITarget)

so = MO.SimpleSingleScaleRegistration(ISource, ITarget, spacing, params)
so.get_optimizer().set_visualization( True )
so.get_optimizer().set_visualize_step( 10 )
so.register()

energy = so.get_energy()

print( energy )

params.write_JSON( 'regTest_settings_clean.json')
params.write_JSON_comments( 'regTest_settings_comments.json')

