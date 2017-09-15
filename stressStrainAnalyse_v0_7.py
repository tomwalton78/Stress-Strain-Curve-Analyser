""" Software that takes compression test results as input, analyses it and
returns useful information
# DATAPREP: Copy stress (Mpa) & strain )% columns from excel file
(numbers only, not headings) and point to it"""

import os
from matplotlib import pyplot
import analysisFunctions as af

# GUI:
import sys
from PyQt4 import QtCore, QtGui, uic

# Gets rid of some warnings in output text
import warnings
warnings.filterwarnings("ignore")


def formatResultsString(
	outputDecimalPlaces, testType, elasticModulus, yieldStress, stressAtStrainVal,
	stressAtCertainStrain, UTS, areaUnderCurve, rString, breakingStressString):
	# PROGRAM STRING OUTPUT:
	resultsStringList = []
	resultsStringList.append(
		"Sample elastic modulus is {} MPa.\n\n".format(
			str(round(elasticModulus * 100, outputDecimalPlaces))))
	resultsStringList.append(
		"Sample 0.2 %% yield stress is {} MPa.\n\n".format(
			str(round(yieldStress, outputDecimalPlaces))))
	resultsStringList.append(
		"Sample stress at {} %% strain is {} MPa.\n\n".format(
			str(stressAtCertainStrain),
			str(round(stressAtStrainVal, outputDecimalPlaces))))
	resultsStringList.append(
		"Sample UTS (maximum stress) is {} MPa.\n\n".format(
			str(round(UTS, outputDecimalPlaces))))
	resultsStringList.append(
		"Area under curve is: {} MPa*%%.\n\n".format(
			str(round(areaUnderCurve, outputDecimalPlaces))))

	if testType == "Tensile Test":
		resultsStringList.append(breakingStressString)
	elif testType == "Compression Test":
		resultsStringList.append(rString)

	return ''.join(resultsStringList)


def ssPlot(xList, yList):
	# Plots stress-strain curve
	pyplot.plot(xList, yList)
	pyplot.xlabel("Strain (%)")
	pyplot.ylabel("Stress (MPa)")
	pyplot.show()

# GUI Stuff
# Code derived from:
# http://pythonforengineers.com/your-first-gui-app-with-python-and-pyqt/
dir_path = os.path.dirname(os.path.realpath(__file__))
qtCreatorFile = r"{}\stressStrainAnalyseMain - v0.1.ui".format(dir_path)

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)
# Initialize variables
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

		# Set variables default values
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
		# no. of decimal places to show output values to:
		outputDecimalPlaces = int(self.outputDecimalPlacesBox.text())
		# input strains at which you want stresses to be found, in list format:
		stressAtCertainStrain = float(self.stressAtStrainBox.text())

		# Parameters for finding elastic modulus
		# (%) starting strain to be analysed for finding elastic modulus:
		elasticModStart = float(self.elasticModStartBox.text())
		# step between regression calculations (higher is faster, but less accurate):
		elasticModFindingStep = int(self.elasticModFindingStepBox.text())
		# minimum rSquared value that must be attained before deviation from straight
		# line is searched for:
		rSquaredMin = float(self.rSquaredMinBox.text())
		# deviation from straight line will start to be detected this many steps
		# after rSquaredMin is hit:
		numOfStepsAfterSquaredMinIsHit = int(
			self.numOfStepsAfterSquaredMinIsHitBox.text())
		# no of steps to backtrack after finding sufficient deviation from straight
		# line trend, when finding elastic modulus:
		elasticModBacktrackValue = int(self.elasticModBacktrackValueBox.text())

		# Parameters for finding 0.2 % yield stress and yield stress at certain
		# strain determines to how many decimal places steps are on 0.2 % yield
		# stress line:
		yieldStressAccuracy = int(self.yieldStressAccuracyBox.text())
		# determines step of data points on 0.2 % yield stress line:
		yieldStressFindingStep = int(self.yieldStressFindingStepBox.text())
		# (MPa) determines cut-off for what defines a low elastic modulus:
		lowElasticModulus = float(self.lowElasticModulusBox.text())
		# (%)range of strain either side of input strain to narrow xList down to for
		# highElasticModulus case:
		highElasticModCuttingRange = float(self.highElasticModCuttingRangeBox.text())

		# Parameters for analysing plateau region
		# denotes length of list currently selected to analyse plataeau dips and
		# peaks (gradient); lower value is more 'accurate' but may pick up unwanted
		# peaks/dips; must be integer:
		plateauAnalyseSegmentLength = int(self.plateauAnalyseSegmentLengthBox.text())
		# defines end of plateau region as [this value]*yieldStress, instead of
		# requiring user input:
		plateauRegionDefiningFactor = float(
			self.plateauRegionDefiningFactorBox.text())

		inputFilePath = openFile

		XoriginalDataList, YoriginalDataList, maxDetectStress = af.importDataFunc(
			inputFilePath)
		XelasticList, YelasticList, deltaElastic = af.elasticModListGenerate(
			XoriginalDataList, YoriginalDataList, elasticModStart)
		elasticModSlope, elasticModyIntercept, elasticBreakValue = af.findElasticMod(
			XelasticList, YelasticList, elasticModFindingStep, rSquaredMin,
			numOfStepsAfterSquaredMinIsHit, elasticModBacktrackValue)
		totalDeltaIndex = deltaElastic + elasticBreakValue

		elasticModulus = elasticModSlope  # (MPa)
		yieldStress = af.findStressAtCertainStrain(
			XoriginalDataList, YoriginalDataList, elasticModSlope, elasticModyIntercept,
			0.2, maxDetectStress, totalDeltaIndex, yieldStressAccuracy,
			yieldStressFindingStep, lowElasticModulus,
			highElasticModCuttingRange)  # 0.2 because 0.2 % yield stress
		UTS = af.findMaxStress(XoriginalDataList, YoriginalDataList)
		stressAtStrainVal = af.findStressAtCertainStrain(
			XoriginalDataList, YoriginalDataList, elasticModSlope, elasticModyIntercept,
			stressAtCertainStrain, maxDetectStress, totalDeltaIndex,
			yieldStressAccuracy, yieldStressFindingStep, lowElasticModulus,
			highElasticModCuttingRange)
		areaUnderCurve = af.findAreaUnderCurve(XoriginalDataList, YoriginalDataList)

		if testType == "Tensile Test":
			breakingStressString, breakingStressValue = af.findBreakingStress(
				YoriginalDataList, outputDecimalPlaces)
			rString = None

		if testType == "Compression Test":
			rList, numDips, dipDeltaStressList, dipDeltaStrainList = af.analysePlateau(
				XoriginalDataList, YoriginalDataList, yieldStress,
				plateauRegionDefiningFactor, plateauAnalyseSegmentLength,
				outputDecimalPlaces)
			rString = ''.join(rList)
			breakingStressString = None

		resultsString = formatResultsString(
			outputDecimalPlaces, testType, elasticModulus, yieldStress,
			stressAtStrainVal, stressAtCertainStrain, UTS, areaUnderCurve,
			rString, breakingStressString)

		if self.includeCSVCheckBox.isChecked():
			tempStringList = []
			tempStringList.append(str(round(elasticModulus * 100, outputDecimalPlaces)))
			tempStringList.append(str(round(yieldStress, outputDecimalPlaces)))
			tempStringList.append(str(round(stressAtStrainVal, outputDecimalPlaces)))
			tempStringList.append(str(round(UTS, outputDecimalPlaces)))
			tempStringList.append(str(round(areaUnderCurve, outputDecimalPlaces)))
			if testType == "Tensile Test":
				tempStringList.append(str(breakingStressValue))
			if testType == 'Compression Test':
				tempStringList.append(str(numDips))
				for i in range(0, len(dipDeltaStressList)):
					tempStringList.append(str(dipDeltaStressList[i]))
			tempString = ', '.join(tempStringList)
			resultsString = ''.join([resultsString, tempString])

		self.resultsBox.setText(resultsString)

		# Graph plotting:
		if self.showGraphCheckBox.isChecked():
			ssPlot(XoriginalDataList, YoriginalDataList)

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
