#####INSTRUCTIONS FOR USE#####

This program is designed to take stress-strain data as the input and output useful information such as 0.2 %
yield stress, toughness (area under curve), ultimate tensile strength, breaking strength, etc.
This program aims to speed up rate at which stress-strain data can be analysed.

Setup:
1. Install python 3:
>Get it here: https://www.python.org/downloads/
2. Install modules: scipy, statsmodels, numpy, matplotlib, PyQt4 (install SIP first)
>How to*: https://programminghistorian.org/lessons/installing-python-modules-pip#mac-and-linux-instructions
*If pip install method does not work (using Windows), download releavant module from here: http://www.lfd.uci.edu/~gohlke/pythonlibs/
Then navigate to downloads folder in command prompt using: cd downloadsFolderPath
Then type: py -m pip install downloadedFileName.whl


Using program:
1. Run python file
2. Click on browse to select data file
>Data file must be in csv format, with strain (in %) column on left, stress (in MPa) column on right
3. Select test type (compression/tensile) from dropdown box
4. Adjust other settings as necessary to tune accuracy and suit your preferences (see 'Program Details.txt' for
more information.
5. Click 'Run Analysis' button to start analysis.
>It usually takes less than 10 seconds to perform the analysis using default settings.

NOTE: It is strongly recommended that you visually check the results produced by this program against what you 
expect from looking at the stress-strain curve.
