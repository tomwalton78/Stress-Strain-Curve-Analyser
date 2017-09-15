import scipy
import math
import numpy as np
import statsmodels.api as sm

# Gets rid of some warnings in output text
import warnings
warnings.filterwarnings("ignore")


def importDataFunc(inputFilePath):
	with open(r"%s" % (inputFilePath), 'r') as dataFile:
		xList, yList = [], []
		line = dataFile.readline()
		while line:
			tempList = line.strip().split(',')
			noString = True
			for i, j in enumerate(tempList):
				try:
					tempList[i] = float(j)
				except(ValueError):
					noString = False
			if noString:  # handles column headings in 1st line of csv
				xList.append(tempList[0])
				yList.append(tempList[1])
			line = dataFile.readline()
		# turns data into format of xList & yList
	maxStress = float(max(yList))

	return xList, yList, maxStress


def elasticModListGenerate(xInputlist, yInputList, elasticModStart):
	"""removes values in data list that are less than specified value, to remove
	error from beginning of graph when finding elastic modulus"""
	len1 = len(xInputlist)
	xList = [x for x in xInputlist if x > elasticModStart]
	delta = len1 - len(xList)
	yList = yInputList[delta: len(yInputList) + 1: 1]

	return xList, yList, delta


def findElasticMod(
	xList, yList, elasticModFindingStep, rSquaredMin,
	numOfStepsAfterSquaredMinIsHit, elasticModBacktrackValue):
	""" finds elastic modulus by going along initial straight line and stopping
	when best fit line deviates from straight line, then it goes back a few steps
	and takes gradient"""
	rSquaredMinHit = 0
	# ^stores how many times r_squared value is above thresholdvalue
	breakValue = 0  # index where best fit line no longer fits sufficiently well
	for i in range(0, len(xList) - 1, elasticModFindingStep):
		slope, intercept, r_value, p_value, std_error = scipy.stats.linregress(
			xList[0: i + 1: 1], yList[0: i + 1: 1])
		# ^applies linear regression on current slice of xlist, ylist
		r_squared = r_value ** 2
		if r_squared > rSquaredMin:
			rSquaredMinHit += 1
		if (
			rSquaredMinHit > numOfStepsAfterSquaredMinIsHit and
			r_squared < rSquaredMin):
			breakValue = i
			break
	finalxList = xList[0: breakValue - elasticModBacktrackValue: 1]
	finalyList = yList[0: breakValue - elasticModBacktrackValue: 1]
	slope, intercept, r_value, p_value, std_error = scipy.stats.linregress(
		finalxList, finalyList)

	return slope, intercept, breakValue


def makeStraightLine(
	strainValue, deltaIndex, maxStress, inputxList, inputyList,
	yieldStressAccuracy, yieldStressFindingStep, inputSlope, inputyIntercept):
	"""Generates x, y coordinates that make up straight line which is used for
	finding stress at  certain strain, using elastic mod slope based offset"""
	# y = mx + c
	if strainValue > max(inputxList):
		print(
			"""WARNING: Selected strain value is outside range of strain values
			recorded, so following stress value will not be correct.""")
	xIntercept = (-1 * inputyIntercept) / inputSlope
	newLinexIntercept = xIntercept + strainValue
	newLineyIntercept = -1 * inputSlope * newLinexIntercept

	newLinexList = []
	newLineyList = []
	if strainValue == 0.2:
		""" uses a lower max stress value for creating line in
		case of 0.2 % yield stress, to speed up program"""
		provVal = 2 * inputyList[deltaIndex]
		if provVal < maxStress:
			maxStress = int(2 * inputyList[deltaIndex])
	for yValue in range(
		math.floor(inputyList[deltaIndex]), int(maxStress * yieldStressAccuracy),
		yieldStressFindingStep):
		"""# produces straight line; range function can only step as an integer;
		starting at deltaIndex means straight line starts at point where
		'straightness' of initial line stops"""
		yValue = yValue / yieldStressAccuracy
		xValue = (yValue - newLineyIntercept) / inputSlope
		newLinexList.append(xValue)
		newLineyList.append(yValue)

	return newLinexList, newLineyList


def createCutDownLists(
	inputSlope, lowElasticModulus, inputxList, inputyList, strainValue,
	highElasticModCuttingRange):
	"""Takes only the relevant section of the input curve, so finding
	intersection point is faster"""
	if inputSlope > lowElasticModulus:
		if strainValue >= (max(inputxList) - highElasticModCuttingRange - 1):
			""" prevents issues where lots of identical strain values near end mess up
			indexing (since .index() takes lowest index)"""
			cutDownxList = (
				[x for x in inputxList if x > (strainValue - highElasticModCuttingRange)])
			cutLowList = []
			for i in inputxList:
				if i not in cutDownxList:
					cutLowList.append(i)
				else:
					break
			numBelow = len(cutLowList)
			startingIndex = numBelow
			endingIndex = startingIndex + len(cutDownxList) + 1
			cutDownyList = inputyList[startingIndex: endingIndex - 1: 1]

		else:
			cutDownxList = (
				[x for x in inputxList if
					x > (strainValue - highElasticModCuttingRange) and
					x < (strainValue + highElasticModCuttingRange)])
			cutLowList = []
			for i in inputxList:
				if i not in cutDownxList:
					cutLowList.append(i)
				else:
					break
			numBelow = len(cutLowList)
			startingIndex = numBelow
			endingIndex = startingIndex + len(cutDownxList) + 1
			cutDownyList = inputyList[startingIndex: endingIndex - 1: 1]

		return cutDownxList, cutDownyList

	else:
		return inputxList, inputyList


def findIntersection(newLinexList, newLineyList, inputxList, inputyList):
	"""After preprocessing is complete, goes about finding intersection of
	straight line and orginal data curve by finding	point on striaght line
	that is closest to a point on data curve (brute force)"""
	mainDiffList = []
	mainDiffListDataIndexes = []
	for i, k in enumerate(newLinexList):
		"""finds point on data curve that each i is closest to
		and stores in mainDiffList"""
		subDiffList = []
		for j, m in enumerate(inputxList):
			xDiff = abs(m - k)
			yDiff = abs(inputyList[j] - newLineyList[i])
			sumDiff = xDiff + yDiff
			subDiffList.append(sumDiff)
		subMinDiff = min(subDiffList)
		subMinDiffIndex = subDiffList.index(subMinDiff)
		# ^index in main data list is stored in mainDiffListDataIndexes
		mainDiffList.append(subMinDiff)
		mainDiffListDataIndexes.append(subMinDiffIndex)
	globalMinimumDifference = min(mainDiffList)
	globalMinimumDifferenceIndex = mainDiffList.index(globalMinimumDifference)
	dataCurveIndexyieldPoint = (
		mainDiffListDataIndexes[globalMinimumDifferenceIndex])

	return (
		inputxList[dataCurveIndexyieldPoint], inputyList[dataCurveIndexyieldPoint])


def findStressAtCertainStrain(
	inputxList, inputyList, inputSlope, inputyIntercept, strainValue, maxStress,
	deltaIndex, yieldStressAccuracy, yieldStressFindingStep, lowElasticModulus,
	highElasticModCuttingRange):
	""" finds stress at certain strain (sloped up from that strain)"""

	newLinexList, newLineyList = makeStraightLine(
		strainValue, deltaIndex, maxStress, inputxList, inputyList,
		yieldStressAccuracy, yieldStressFindingStep, inputSlope, inputyIntercept)

	inputxList, inputyList = createCutDownLists(
		inputSlope, lowElasticModulus, inputxList, inputyList, strainValue,
		highElasticModCuttingRange)

	yieldStrain, yieldStress = findIntersection(
		newLinexList, newLineyList, inputxList, inputyList)

	return yieldStress


def findMaxStress(xInputlist, yInputList):
	maxStress = max(yInputList)
	maxStressIndex = yInputList.index(maxStress)
	correspondingStrain = xInputlist[maxStressIndex]

	return maxStress


def findAreaUnderCurve(xList, yList):
	area = np.trapz(yList, xList)

	return area


def trimData(yieldStress, plateauRegionDefiningFactor, xList, yList):
	"""Trims data so ~only plateau region is considered,
	to improve processing time. Specifically, it cuts off data before yield point
	and after end of plateau region (based on multiple of yield stress)"""
	plateauEndingStressValue = yieldStress * plateauRegionDefiningFactor
	cutIndexStart = yList.index(yieldStress)
	xListTrimmed = xList[cutIndexStart: len(xList): 1]
	yListTrimmed = yList[cutIndexStart: len(yList): 1]
	tempyList = []
	for element in yListTrimmed:
		if element < plateauEndingStressValue:
			tempyList.append(element)
		else:
			break
	yListTrimmed = tempyList
	xListTrimmed = xListTrimmed[0: len(yListTrimmed): 1]

	return xListTrimmed, yListTrimmed


def generateSlopeList(xListTrimmed, yListTrimmed, plateauAnalyseSegmentLength):
	""" stores gradient values over selected
	interval (plateauAnalyseSegmentLength) in slopeList"""
	slopeList = []
	for i in range(plateauAnalyseSegmentLength, len(xListTrimmed)):
		currentxList = xListTrimmed[i - plateauAnalyseSegmentLength: i + 1: 1]
		currentyList = yListTrimmed[i - plateauAnalyseSegmentLength: i + 1: 1]
		slope, intercept, r_value, p_value, std_error = scipy.stats.linregress(
			currentxList, currentyList)
		slopeList.append(slope)

	return slopeList


def findPeaksAndDips(
	slopeList, plateauAnalyseSegmentLength, xListTrimmed, yListTrimmed):
	"""Find x, y (strain, stress) cooridnates of peaks and dips"""
	peakIndexesList = []
	# ^stores indexes (wrt trimmed x,y lists) of points	where peaks occur
	dipIndexesList = []
	# ^stores indexes (wrt trimmed x,y lists) of points where dips occur
	for i in range(0, len(slopeList) - 1):
		if slopeList[i] < 0 and slopeList[i + 1] >= 0:  # i.e. sign change
			dipIndexesList.append(i + int((plateauAnalyseSegmentLength / 2)))
		elif slopeList[i] >= 0 and slopeList[i + 1] < 0:  # i.e. sign change
			peakIndexesList.append(i + int((plateauAnalyseSegmentLength / 2)))
		else:
			pass
	""" These 4 lists store x & y values for peaks and dips found,
	ready for further analysis"""
	peakxValues = [xListTrimmed[a] for a in peakIndexesList]
	peakyValues = [yListTrimmed[a] for a in peakIndexesList]
	dipxValues = [xListTrimmed[a] for a in dipIndexesList]
	dipyValues = [yListTrimmed[a] for a in dipIndexesList]

	if len(peakxValues) != len(dipyValues):
		returnStringList.append(
			"""ATTENTION: NUMBER OF PEAKS AND DIPS DO NOT MATCH.
			THIS WILL RESULT IN CODE ERROR.\n""")

	return peakxValues, peakyValues, dipxValues, dipyValues


def generateReturnStringList(
	dipxValues, dipyValues, peakxValues, peakyValues, outputDecimalPlaces):
	returnStringList = []
	numDips = str(len(dipxValues))
	returnStringList.append(
		"There are %s dips in the plateau region:\n\n" % (numDips))
	deltaStressList = []
	deltaStrainList = []

	for i, j in enumerate(peakxValues):
		deltaY = peakyValues[i] - dipyValues[i]
		deltaX = dipxValues[i] - peakxValues[i]

		returnStringList.append(
			"Difference in stress between peak {} and dip {} is {} MPa\n".format(
				str(i), str(i), str(round(deltaY, outputDecimalPlaces))))
		deltaStressList.append(str(round(deltaY, outputDecimalPlaces)))
		deltaStrainList.append(str(round(deltaX, outputDecimalPlaces)))

	return returnStringList, numDips, deltaStressList, deltaStrainList


def analysePlateau(
	xList, yList, yieldStress, plateauRegionDefiningFactor,
	plateauAnalyseSegmentLength, outputDecimalPlaces):
	"""Analyses dips and peaks in plateau region of compression curve"""

	xListTrimmed, yListTrimmed = trimData(
		yieldStress, plateauRegionDefiningFactor, xList, yList)

	slopeList = generateSlopeList(
		xListTrimmed, yListTrimmed, plateauAnalyseSegmentLength)

	peakxValues, peakyValues, dipxValues, dipyValues = findPeaksAndDips(
		slopeList, plateauAnalyseSegmentLength, xListTrimmed, yListTrimmed)

	returnStringList, numDips, delStresses, delStrains = generateReturnStringList(
		dipxValues, dipyValues, peakxValues, peakyValues, outputDecimalPlaces)

	return returnStringList, numDips, delStresses, delStrains


def findBreakingStress(yList, outputDecimalPlaces):
	value = round(yList[-1], outputDecimalPlaces)
	string = "Sample breaking stress is %s MPa.\n\n" % (str(value))

	return string, value