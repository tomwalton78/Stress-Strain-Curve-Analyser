#Software that takes compression test results as input, analyses it and returns useful information
#DATAPREP: Copy stress (Mpa) & strain (%) columns from excel file and point to it;

#currently stress at x % strain uses elasticMod slope intersection starting from where original elastic mod slope intersecs
#x-axis + x %
#currently put in as either .csv or .txt, as 2 columns of data (strain on left, stress on right), with words at top allowed

import scipy
import math
import statsmodels.api as sm
import os
import numpy as np
from matplotlib import pyplot

#GUI:
import sys
from PyQt4 import QtCore, QtGui, uic

#Gets rid of some warnings in output text
import warnings
warnings.filterwarnings("ignore")


#Initialize parameters
#don't change these, for the sake of tests working
outputDecimalPlaces, stressAtCertainStrain, elasticModStart, elasticModFindingStep, rSquaredMin, numOfStepsAfterSquaredMinIsHit, elasticModBacktrackValue = 3, 40, 0.5, 1, 0.99, 20, 30
yieldStressAccuracy, yieldStressFindingStep, lowElasticModulus, highElasticModCuttingRange, plateauAnalyseSegmentLength, plateauRegionDefiningFactor = 100, 1, 1, 10, 500, 1.7

def importDataFunc(inputFilePath):
	with open(r"%s" % (inputFilePath), 'r') as dataFile:
		xList, yList = [], []
		line = dataFile.readline()
		while line:
			tempList = line.strip().split(',')
			noString = True
			for i in range(0,len(tempList)):
				try:
					tempList[i] = float(tempList[i])
				except(ValueError):
					noString = False
			if noString:
				xList.append(tempList[0])
				yList.append(tempList[1])
			line = dataFile.readline()
		#turns data into format of xList & yList
	maxStress = float(max(yList))
	return xList, yList, maxStress

def elasticModListGenerate(xInputlist, yInputList): #removes values in data list that are less than specified value, to remove error from beginning of graph when finding elastic modulus
	len1 = len(xInputlist)
	xList = [x for x in xInputlist if x > elasticModStart]
	delta = len1 - len(xList)
	yList = yInputList[delta : len(yInputList) + 1 : 1]
	return xList, yList, delta

def findElasticMod(xList, yList): #finds elastic modulus by going along initial straight line and stopping when best fit line deviates from straight line, then it goes back a few steps and takes gradient
	rSquaredMinHit = 0 #stores how many times r_squared value is above threshold value
	breakValue = 0 #index where best fit line no longer fits sufficiently well
	for i in range(0,len(xList)-1, elasticModFindingStep):
		slope, intercept, r_value, p_value, std_error = scipy.stats.linregress(xList[0 : i+1 : 1], yList[0 : i+1 : 1]) #applies linear regression on current slice of xlist, ylist
		r_squared = r_value ** 2
		if r_squared > rSquaredMin:
			rSquaredMinHit += 1
		if rSquaredMinHit > numOfStepsAfterSquaredMinIsHit and r_squared < rSquaredMin:
			breakValue = i
			break
	finalxList = xList[0 : breakValue - elasticModBacktrackValue : 1]
	finalyList = yList[0 : breakValue - elasticModBacktrackValue : 1]
	slope, intercept, r_value, p_value, std_error = scipy.stats.linregress(finalxList, finalyList)
	return slope, intercept, breakValue

def findStressAtCertainStrain(inputxList, inputyList, inputSlope, inputyIntercept, strainValue, maxStress, deltaIndex): #finds stress at certain strain (sloped up from that strain)
	#y = mx + c
	if strainValue > max(inputxList):
		print("WARNING: Selected strain value is outside range of strain values recorded, so following stress value will not be correct.")
	xIntercept = (-1 * inputyIntercept) / inputSlope
	newLinexIntercept = xIntercept + strainValue #
	newLineyIntercept = -1 * inputSlope * newLinexIntercept
	newLinexList = []
	newLineyList = []

	if strainValue == 0.2: #uses a lower max stress value for creating line in case of 0.2 % yield stress, to speed up program
		provVal = 2 * inputyList[deltaIndex]
		if provVal < maxStress:
			maxStress = int(2 * inputyList[deltaIndex])
	for yValue in range(math.floor(inputyList[deltaIndex]), int(maxStress * yieldStressAccuracy),yieldStressFindingStep): #produces straight line; range function can only step as an integer; starting at deltaIndex means straight line starts at point where 'straightness' of initial line stops
		yValue = yValue / yieldStressAccuracy
		xValue = (yValue - newLineyIntercept) / inputSlope
		newLinexList.append(xValue)
		newLineyList.append(yValue)

	if inputSlope > lowElasticModulus:
		if strainValue >= (max(inputxList) - highElasticModCuttingRange - 1): #prevents issues where lots of identical strain values near end mess up indexing (since .index() takes lowest index)
			cutDownxList = [x for x in inputxList if x > (strainValue - highElasticModCuttingRange)]
			cutLowList = []
			for i in inputxList:
				if i not in cutDownxList:
					cutLowList.append(i)
				else:
					break
			numBelow = len(cutLowList)
			startingIndex = numBelow
			endingIndex = startingIndex + len(cutDownxList) + 1
			cutDownyList = inputyList[startingIndex : endingIndex - 1 : 1]

		else:
			cutDownxList = [x for x in inputxList if x > (strainValue - highElasticModCuttingRange) and x < (strainValue + highElasticModCuttingRange)]
			cutLowList = []
			for i in inputxList:
				if i not in cutDownxList:
					cutLowList.append(i)
				else:
					break
			numBelow = len(cutLowList)
			startingIndex = numBelow
			endingIndex = startingIndex + len(cutDownxList) + 1
			cutDownyList = inputyList[startingIndex : endingIndex - 1 : 1]
		inputxList, inputyList = cutDownxList, cutDownyList
	mainDiffList = []
	mainDiffListDataIndexes = []
	for i in range(0,len(newLinexList)): # finds point on data curve that each i is closest to and stores in mainDiffList
		subDiffList = []
		for j in range(0,len(inputxList)):
			xDiff = abs(inputxList[j] - newLinexList[i])
			yDiff = abs(inputyList[j] - newLineyList[i])
			sumDiff = xDiff + yDiff
			subDiffList.append(sumDiff)
		subMinDiff = min(subDiffList)
		subMinDiffIndex = subDiffList.index(subMinDiff) #index in main data list is stored in mainDiffListDataIndexes
		mainDiffList.append(subMinDiff)
		mainDiffListDataIndexes.append(subMinDiffIndex)
	globalMinimumDifference = min(mainDiffList)
	globalMinimumDifferenceIndex = mainDiffList.index(globalMinimumDifference)
	dataCurveIndexyieldPoint = mainDiffListDataIndexes[globalMinimumDifferenceIndex]
	yieldStrain = inputxList[dataCurveIndexyieldPoint]
	yieldStress = inputyList[dataCurveIndexyieldPoint]
	return yieldStress

def findMaxStress(xInputlist, yInputList):
	maxStress = max(yInputList)
	maxStressIndex = yInputList.index(maxStress)
	correspondingStrain = xInputlist[maxStressIndex]
	return maxStress

def findAreaUnderCurve(xList, yList):
	area = np.trapz(yList,xList)
	return area

def analysePlateau(xList,yList,yieldStress):
	returnStringList = []
	plateauEndingStressValue = yieldStress * plateauRegionDefiningFactor
	#cuts off data before yield point and after end of plateau region (based on multiple of yield stress:
	cutIndexStart = yList.index(yieldStress)
	xListTrimmed = xList[cutIndexStart : len(xList) : 1]
	yListTrimmed = yList[cutIndexStart : len(yList) : 1]
	tempyList = []
	for element in yListTrimmed:
		if element < plateauEndingStressValue:
			tempyList.append(element)
		else:
			break
	yListTrimmed = tempyList
	xListTrimmed = xListTrimmed[0 : len(yListTrimmed) : 1]

	slopeList = [] #stores gradient values over selected interval (plateauAnalyseSegmentLength)
	for i in range(plateauAnalyseSegmentLength,len(xListTrimmed)):
		currentxList = xListTrimmed[i - plateauAnalyseSegmentLength : i+1 : 1]
		currentyList = yListTrimmed[i - plateauAnalyseSegmentLength : i+1 : 1]
		slope, intercept, r_value, p_value, std_error = scipy.stats.linregress(currentxList, currentyList)
		slopeList.append(slope)

	peakIndexesList = []	#stores indexes (wrt trimmed x,y lists) of points where peaks occur
	dipIndexesList = []		#stores indexes (wrt trimmed x,y lists) of points where dips occur
	for i in range(0,len(slopeList)-1):
		if slopeList[i] < 0 and slopeList[i+1] >= 0: #i.e. sign change
			dipIndexesList.append(i + int((plateauAnalyseSegmentLength / 2)))
		elif slopeList[i] >= 0 and slopeList[i+1] < 0: #i.e. sign change
			peakIndexesList.append(i + int((plateauAnalyseSegmentLength / 2)))
		else:
			pass
	#These 4 lists store x & y values for peaks and dips found, ready for further analysis
	peakxValues = [xListTrimmed[a] for a in peakIndexesList]
	peakyValues = [yListTrimmed[a] for a in peakIndexesList]
	dipxValues = [xListTrimmed[a] for a in dipIndexesList]
	dipyValues = [yListTrimmed[a] for a in dipIndexesList]

	if len(peakxValues) != len(dipyValues):
		returnStringList.append("ATTENTION: NUMBER OF PEAKS AND DIPS DO NOT MATCH. THIS WILL RESULT IN CODE ERROR.\n")

	numDips = str(len(dipxValues))
	returnStringList.append("There are %s dips in the plateau region:\n\n" % (numDips))
	deltaStressList = []
	deltaStrainList = []

	for i in range(0,len(peakxValues)):
		deltaY = peakyValues[i] - dipyValues[i]
		deltaX = dipxValues[i] - peakxValues[i]

		returnStringList.append("Difference in stress between peak %s and dip %s is %s MPa\n" % (str(i), str(i), str(round(deltaY, outputDecimalPlaces))))
		deltaStressList.append(str(round(deltaY, outputDecimalPlaces)))
		deltaStrainList.append(str(round(deltaX, outputDecimalPlaces)))
	return returnStringList, numDips, deltaStressList, deltaStrainList

def findBreakingStress(yList):
	value = round(yList[-1], outputDecimalPlaces)
	string = "Sample breaking stress is %s MPa.\n\n" % (str(value))
	return string, value

#GUI Stuff
#Code from: http://pythonforengineers.com/your-first-gui-app-with-python-and-pyqt/
dir_path = os.path.dirname(os.path.realpath(__file__))
qtCreatorFile = r"%s\stressStrainAnalyseMain.ui" % (dir_path)

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)
#Initialize variables
openFile = ""
testType = "Compression Test"
class MyApp(QtGui.QMainWindow, Ui_MainWindow):
	filePath = ""
	def __init__(self):
		QtGui.QMainWindow.__init__(self)
		Ui_MainWindow.__init__(self)
		self.setupUi(self)
		self.fileBrowseButton.clicked.connect(self.selectFile)
		self.runAnalysisButton.clicked.connect(self.runAnalysis)
		self.testTypeBox.activated.connect(self.testTypeDropdown)

		#Set variables default values
		self.outputDecimalPlacesBox.setText("3")
		self.stressAtStrainBox.setText("40")

		self.elasticModStartBox.setText("0.5")
		self.elasticModFindingStepBox.setText("1")
		self.rSquaredMinBox.setText("0.999")
		self.numOfStepsAfterSquaredMinIsHitBox.setText("20")
		self.elasticModBacktrackValueBox.setText("30")

		self.yieldStressAccuracyBox.setText("100")
		self.yieldStressFindingStepBox.setText("1")
		self.lowElasticModulusBox.setText("1")
		self.highElasticModCuttingRangeBox.setText("10")

		self.plateauAnalyseSegmentLengthBox.setText("400")
		self.plateauRegionDefiningFactorBox.setText("1.7")

	def runAnalysis(self):
		global outputDecimalPlaces, stressAtCertainStrain, elasticModStart, elasticModFindingStep, rSquaredMin, numOfStepsAfterSquaredMinIsHit, elasticModBacktrackValue
		global yieldStressAccuracy, yieldStressFindingStep, lowElasticModulus, highElasticModCuttingRange, plateauAnalyseSegmentLength, plateauRegionDefiningFactor
		outputDecimalPlaces = int(self.outputDecimalPlacesBox.text()) #no. of decimal places to show output values to
		stressAtCertainStrain = float(self.stressAtStrainBox.text()) #input strains at which you want stresses to be found, in list format
		#Parameters for finding elastic modulus
		elasticModStart = float(self.elasticModStartBox.text()) #(%) starting strain to be analysed for finding elastic modulus
		elasticModFindingStep = int(self.elasticModFindingStepBox.text()) #step between regression calculations (higher is faster, but less accurate)
		rSquaredMin = float(self.rSquaredMinBox.text()) #minimum rSquared value that must be attained before deviation from straight line is searched for
		numOfStepsAfterSquaredMinIsHit = int(self.numOfStepsAfterSquaredMinIsHitBox.text()) # deviation from straight line will start to be detected this many steps after rSquaredMin is hit
		elasticModBacktrackValue = int(self.elasticModBacktrackValueBox.text()) # no of steps to backtrack after finding sufficient deviation from straight line trend, when finding elastic modulus

		#Parameters for finding 0.2 % yield stress and yield stress at certain strain
		yieldStressAccuracy = int(self.yieldStressAccuracyBox.text()) #determines to how many decimal places steps are on 0.2 % yield stress line
		#min 100 recommended
		yieldStressFindingStep = int(self.yieldStressFindingStepBox.text()) #determines step of data points on 0.2 % yield stress line
		lowElasticModulus = float(self.lowElasticModulusBox.text()) #(MPa) determines cut-off for what defines a low elastic modulus
		highElasticModCuttingRange = float(self.highElasticModCuttingRangeBox.text()) #(%)range of strain either side of input strain to narrow xList down to for highElasticModulus case

		#Parameters for analysing plateau region
		plateauAnalyseSegmentLength = int(self.plateauAnalyseSegmentLengthBox.text()) #denotes length of list currently selected to analyse plataeau dips and peaks (gradient); lower value is more 'accurate' but may pick up unwanted peaks/dips; must be integer
		plateauRegionDefiningFactor = float(self.plateauRegionDefiningFactorBox.text()) #defines end of plateau region as [this value]*yieldStress, instead of requiring user input


		inputFilePath = openFile

		XoriginalDataList, YoriginalDataList, maxDetectableStress = importDataFunc(inputFilePath)
		XelasticList, YelasticList, deltaElastic = elasticModListGenerate(XoriginalDataList, YoriginalDataList)
		elasticModSlope, elasticModyIntercept, elasticBreakValue = findElasticMod(XelasticList, YelasticList)
		totalDeltaIndex = deltaElastic + elasticBreakValue

		elasticModulus = elasticModSlope #(MPa)
		yieldStress = findStressAtCertainStrain(XoriginalDataList, YoriginalDataList, elasticModSlope, elasticModyIntercept, 0.2, maxDetectableStress, totalDeltaIndex) #0.2 because 0.2 % yield stress
		UTS = findMaxStress(XoriginalDataList, YoriginalDataList)


		#PROGRAM OUTPUT:
		resultsString = ""
		resultsString += "Sample elastic modulus is %s MPa.\n\n" % (str(round(elasticModulus,outputDecimalPlaces)))

		resultsString +="Sample 0.2 %% yield stress is %s MPa.\n\n" % (str(round(yieldStress,outputDecimalPlaces)))

		stressAtStrainVal = findStressAtCertainStrain(XoriginalDataList, YoriginalDataList, elasticModSlope, elasticModyIntercept, stressAtCertainStrain, maxDetectableStress, totalDeltaIndex)
		resultsString += "Sample stress at %s %% strain is %s MPa.\n\n" % (str(stressAtCertainStrain),str(round(stressAtStrainVal,outputDecimalPlaces)))
		
		resultsString += "Sample UTS (maximum stress) is %s MPa.\n\n" % (str(round(UTS,outputDecimalPlaces)))

		areaUnderCurve = findAreaUnderCurve(XoriginalDataList, YoriginalDataList)
		resultsString += "Area under curve is: %s MPa*%%.\n\n" % (str(round(areaUnderCurve,outputDecimalPlaces)))

		if testType == "Tensile Test":
			breakingStressString, breakingStressValue = findBreakingStress(YoriginalDataList)
			resultsString += breakingStressString

		if testType == "Compression Test":
			plateauAnalysisStringList, numPlateauDips, dipDeltaStressList, dipDeltaStrainList = analysePlateau(XoriginalDataList, YoriginalDataList, yieldStress)
			for i in plateauAnalysisStringList:
				resultsString += i

		if self.includeCSVCheckBox.isChecked():
			tempString = ""
			tempString += str(round(elasticModulus,outputDecimalPlaces)) + ', '
			tempString += str(round(yieldStress,outputDecimalPlaces)) + ', '
			tempString += str(round(stressAtStrainVal,outputDecimalPlaces)) + ', '
			tempString += str(round(UTS,outputDecimalPlaces)) + ', '
			tempString += str(round(areaUnderCurve,outputDecimalPlaces)) + ', '
			if testType == "Tensile Test":
				tempString += breakingStress
			if testType == 'Compression Test':
				tempString += numPlateauDips + ', '
				for i in range(0, len(dipDeltaStressList)):
					tempString += dipDeltaStressList[i]
					if i != len(dipDeltaStressList) - 1:
						tempString += ', '
			resultsString += tempString

		self.resultsBox.setText(resultsString)

		#Graph plotting:
		if self.showGraphCheckBox.isChecked():
			pyplot.plot(XoriginalDataList, YoriginalDataList)
			pyplot.xlabel("Strain (%)")
			pyplot.ylabel("Stress (MPa)")
			pyplot.show()

	def selectFile(self):
		global openFile
		openFile = QtGui.QFileDialog.getOpenFileName(self)
		self.selectedFileViewBox.setText(openFile)

	def testTypeDropdown(self):
		global testType
		testType = str(self.testTypeBox.currentText())


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())