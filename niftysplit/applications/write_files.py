# coding=utf-8
"""
Wrapper for an image which consists of one or more subimages

Author: Tom Doel
Copyright UCL 2017

"""
from niftysplit.image.combined_image import CombinedImage


def write_files(descriptors_in, descriptors_out, file_factory):
    """Creates a set of output files from the input files"""

    input_combined = CombinedImage(descriptors_in, file_factory)
    output_combined = CombinedImage(descriptors_out, file_factory)
    output_combined.write_image_file(input_combined)

    input_combined.close()
    output_combined.close()
