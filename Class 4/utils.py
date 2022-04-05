import numpy as np
import gstools as gs

def generate_tempgrad(scale):
    # the grid -- this defines our world, now two dimensinoal!!
    nd = 100 #how many dimensions?
    x = np.linspace(0, 1, nd)
    y = np.linspace(0, 1, nd)


    #this is just a convenient way of getting out a heatmap -- TODO get rid of this code, added complexity isnt needed
    st_model = gs.covmodel.JBessel(dim = 2, len_scale = scale, var = 5, angles = [0, 0])
    srf = gs.SRF(st_model, seed=19841203)
    srf((x, y), mesh_type="structured");
    return srf    

def generate_vectorfield(scale, xlim = 1, ylim = 1):
    ndx = 100 #how many dimensions?
    ndy = 100
    
    x = np.linspace(0, xlim, ndx)
    y = np.linspace(0, ylim, ndy)
    

    model = gs.covmodel.JBessel(dim = 2, len_scale = scale, var = 5, angles = [0, 0])
    srf = gs.SRF(model, generator='VectorField', seed=19841203)
    srf((x, y), mesh_type='structured')
    
    return srf