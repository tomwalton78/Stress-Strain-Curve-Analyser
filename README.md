#####INSTRUCTIONS FOR USE#####

This program is designed to take stress-strain data as the input and output useful information such as 0.2 %
yield stress, toughness (area under curve), ultimate tensile strength, breaking strength, etc.
This program aims to speed up rate at which stress-strain data can be analysed.

Setup:
1. Install python 3
2. Install modules: scipy, statsmodels, numpy, matplotlib, PyQt4 (instal SIP first)

Using program:
1. Run stressStrainAnalyse python file
2. Click on browse to select data file
>Data file must be in csv format, with strain (in %) column on left, stress (in MPa) column on right
3. Select test type (compression/tensile) from dropdown box
4. Adjust other settings as necessary to tune accuracy and suit your preferences (see 'Program Details.txt' for
more information.
5. Click 'Run Analysis' button to start analysis.
>It usually takes less than 10 seconds to perform the analysis using default settings.

NOTE: It is strongly recommended that you visually check the results produced by this program against what you 
expect from looking at the stress-strain curve.