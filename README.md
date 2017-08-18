# Analyzing Cloud Optical Properties Using Sky Cameras

With the spirit of reproducible research, this repository contains all the codes required to produce the results in the manuscript: S. Manandhar, S. Dev, Y. H. Lee and Y. S. Meng, Analyzing Cloud Optical Properties Using Sky Cameras, *Proc. Progress In Electromagnetics Research Symposium (PIERS)*, 2017. 

Please cite the above paper if you intend to use whole/part of the code. This code is only for academic and research purposes.

![alt text](https://github.com/Soumyabrata/cloud-optical-thickness/blob/master/figs/cot-result.png "COT  analysis")

## Code Organization
The codes are written in python. Thanks to <a href="https://www.linkedin.com/in/joseph-lemaitre-93a74412b/">Joseph Lemaitre</a> for providing the scripts to process MODIS multi bands images. 

### Dataset
The cloud optical thickness data from MODIS satellite images are present in the folder `COT`, the average luminance data from sky cameras are present in the folder `average_luminance`, and the generated result is provided in the folder `figs`. 

### Core functionality
* `calculate_luminance.py` Calculates the average luminance from the sky camera images. 
* `normalize_array.py` Normalizes a numpy array into the range [0,1]. 
The remaining python scripts are various helper functions used in the script `calculate_luminance.py`.

### Reproducibility 
In addition to all the related codes, we have shared the analysis figure in the folder `./figs`.

Please run the notebook `main.ipynb` to generate the result mentioned in the paper.


