


#def fits_plot(file_location):
 #   hdul = fits.open(file_location)
 #   data = hdul[0].data
 #   print(data.shape)
 #   medianed = np.mean(data,axis=0)
 #   
 #   plt.imshow(medianed, origin = 'lower')
 #   plt.colorbar()
 #   plt.title("Slice 0")
 #   plt.show()
#lens_diameter = int(input("what is the diameter of the lens? "))
#lens_focal_length = int(input("what is the focal length of the lens? "))
#camera_pixel_size = int(input("what is the pixel size on the camera? "))

#(arcsec/pixel)
#scale = 206265*camera_pixel_size/lens_focal_length



from astropy.io import fits
import matplotlib.pyplot as plt
import numpy as np

# the inputs, images, files (incomplete)
# how are we getting the data? in fits cubes?
# really depends on how the data is organized and how we want to access it
def input_function():
    master_folder = input("what is the folder name where you have all the data? ")
    
def data_reformation(data):
    return(data)


def find_star_center(file_location):
    
    hdul = fits.open(file_location)
    data = hdul[0].data
    
    averaged_image = np.mean(data, axis = 0)
    total_light = np.sum(averaged_image)
    print(total_light, "is the total light")
    
    x,y = np.indices(averaged_image.shape)
    x_sum = np.sum(x*averaged_image)
    y_sum = np.sum(y*averaged_image)
    
    x_center = float(x_sum / total_light)
    y_center = float(y_sum / total_light)
    center = (x_center, y_center)
    return(center)

#removes the trend from the star positioning
def trend_removing(center):
    return(center)


def calculations(K, lambda_num, zenith, telescope_diameter):
    
    r0 = ((0.358 * lambda_num ** 2) / stellar_center_displacement_variance) * (1/telescope_diameter) ** 0.2
    FWHM_rad = 0.98 * lambda_num / r0
    FWHM_arcsec = FWHM_rad * 206265
    

    
#fits_plot(r"C:\Users\mlabr\Downloads\my_cube_0.fits")
find_star_center(r"C:\Users\mlabr\Downloads\my_cube_0.fits")





def main():
    # the inputs, images, files (incomplete)
    # how are we getting the data? in fits cubes?
    input_function()

    # reads the data and transforms data into proper form (incomplete)
    data_reformation()

    # finds the precise star center from a collection of images by weighted averaging (works)
    find_star_center(file_location)

    # removing the trend (unclear how to proceed)
    trend_removing()

    # perform the calculations to find variance of X and Y (incomplete)
    calculate_variance()

    # calculate seeing parameters and other things (incomplete)
    calculations()

