import stressStrainAnalyse_v0_6 as ssa
import os


def importDataFuncTest():
	#Compares values found by function with known values for datset found using excel
	xList, yList, maxStress = ssa.importDataFunc(os.path.dirname(os.path.realpath(__file__)) + r"\testData.csv")
	localErrorCount = 0
	if maxStress != 50.80061983:
		print("ERROR in importDataFunc, maxStress is not being calculated correctly.")
		localErrorCount += 1
	if len(xList) != len(yList):
		print("ERROR in importDataFunc, lengths of x and y data lists are not the same.")
		localErrorCount += 1
	if len(xList) != 28927 or len(yList) != 28927:
		print("ERROR in importDataFunc, not all data has been imported into lists.")
		localErrorCount += 1
	if round(sum(xList),5) != round(1355694.73636531, 5):
		print("ERORR in importDataFunc, x data values imported incorrectly.")
		localErrorCount += 1
	if round(sum(yList), 5) != round(540479.094033514, 5):
		print("ERORR in importDataFunc, y data values imported incorrectly.")
		localErrorCount += 1
	print("%s errors found in importDataFunc function." % (localErrorCount))
	return xList, yList, maxStress, localErrorCount

def elasticModListGenerateTest(xList, yList):
	#Values determined in excel for dataset, compared to values produced by function
	sxList, syList, change = ssa.elasticModListGenerate(xList, yList)
	localErrorCount = 0
	if len(sxList) != len(syList):
		print("ERROR in elasticModListGenerate, shortened lists produced are not the same length.")
		localErrorCount += 1
	if change != 530:
		print("ERROR in elasticModListGenerate, lists were not shortened by the correct amount.")
		localErrorCount += 1
	if sxList[0] != 0.504545455:
		print("ERROR in elasticModListGenerate, xList has not been sliced in correct place.")
		localErrorCount += 1
	if syList[0] != 1.339913223:
		print("ERROR in elasticModListGenerate, yList has not been sliced in correct place.")
		localErrorCount += 1
	print("%s errors found in elasticModListGenerate function." % (localErrorCount))
	return sxList, syList, change, localErrorCount

def findElasticModTest(xList, yList):
	#Equivalent values for slope and intercept have been found for dataset using Excel and are tested against program results
	localErrorCount = 0
	slope, intercept, breakValue = ssa.findElasticMod(xList, yList)
	if round(slope, 0) != round(2.9573, 0):
		print("ERROR in findElasticMod, slope value found is incorrect.")
		localErrorCount += 1
	if round(intercept, 1) != round(-0.1656, 1):
		print("ERROR in findElasticMod, intercept value found is incorrect.")
		localErrorCount += 1
	print("%s errors found in elasticModListGenerate function." % (localErrorCount))
	return slope, intercept, breakValue, localErrorCount

def findStressAtCertainStrainTest(inputxList, inputyList, inputSlope, inputyIntercept, maxStress, deltaIndex):
	#Compares values produced by function to those found manually (using Excel), for testData
	localErrorCount = 0
	resultStress1 = ssa.findStressAtCertainStrain(inputxList, inputyList, inputSlope, inputyIntercept, 0.2, maxStress, deltaIndex)
	resultStress2 = ssa.findStressAtCertainStrain(inputxList, inputyList, inputSlope, inputyIntercept, 40, maxStress, deltaIndex)
	if round(resultStress1, 1) != 8.8:
		print("ERROR in findStressAtCertainStrain, yield stress value found is incorrect.")
		localErrorCount += 1
	if round(resultStress2, 1) != 6.7:
		print("ERROR in findStressAtCertainStrain, stress value at 40 %% strain found is incorrect.")
		localErrorCount += 1
	print("%s errors found in findStressAtCertainStrain function." % (localErrorCount))
	return resultStress1, localErrorCount

def findMaxStressTest(xList, yList):
	#Compares max stress value produced by function to those found manually (using Excel), for testData
	maxStress = ssa.findMaxStress(xList, yList)
	localErrorCount = 0
	if maxStress != 50.80061983:
		print("ERROR in findMaxStress, maxStress is not being calculated correctly.")
		localErrorCount += 1
	print("%s errors found in findMaxStress function." % (localErrorCount))
	return localErrorCount

def findAreaUnderCurveTest(xList, yList):
	#Compares value produced to function to value produced by MATLAB
	localErrorCount = 0
	area = ssa.findAreaUnderCurve(xList, yList)
	if round(area, 1) != 910.1:
		print("ERROR in findAreaUnderCurve, area is not being calculated correctly.")
		localErrorCount += 1
	print("%s errors found in findAreaUnderCurve function." % (localErrorCount))
	return localErrorCount

def analyseplateauTest(xList,yList,yieldStress):
	#Checked visually against graph to verify values, then verifies that function reaches similar values for future tests on this dataset
	localErrorCount = 0
	plateauAnalyseSegmentLength = 500
	stringList, numDips, deltaStressList, deltaStrainList = ssa.analysePlateau(xList,yList,yieldStress)
	deltaStressList, deltaStrainList = [round(float(x), 1) for x in deltaStressList], [round(float(y), 1) for y in deltaStrainList]
	if int(numDips) != 3:
		print("ERROR in analyseplateau, number of dips is not being determined correctly.")
		localErrorCount += 1
	if deltaStressList != [3.5, 0.7, 0.1]:
		print("ERROR in analyseplateau, difference in stress between peaks and dips is not being determined correctly.")
		localErrorCount += 1
	if deltaStrainList != [12.4, 6.8, 3.8]:
		print("ERROR in analyseplateau, difference in stress between peaks and dips is not being determined correctly.")
		localErrorCount += 1
	print("%s errors found in analyseplateau function." % (localErrorCount))
	return localErrorCount

def findBreakingStressTest(yList):
	#Compares value found to last stress value in dataset (via Excel)
	localErrorCount = 0
	string, value = ssa.findBreakingStress(yList)
	if  value != 44.604:
		print("ERROR in findbreakingStress, breaking stress not calculated correctly.")
		localErrorCount += 1
	print("%s errors found in findbreakingStress function." % (localErrorCount))
	return localErrorCount

def runAllTests():
	#Runs all unit tests one after the other. Some tests require previous tests for input data, so cannot necessarily just comment out some tests (this avoids storing long lists in program for data verification though)
	xList, yList, maxStress, e1 = importDataFuncTest()
	sxList, syList, deltaElastic, e2 = elasticModListGenerateTest(xList, yList)
	slope, intercept, breakValue, e3 = findElasticModTest(sxList, syList)
	yieldStress, e4 = findStressAtCertainStrainTest(xList, yList, slope, intercept, maxStress, deltaElastic + breakValue)
	yieldStress = 8.798285124 
	e5 = findMaxStressTest(xList, yList)
	e6 = findAreaUnderCurveTest(xList, yList)
	e7 = analyseplateauTest(xList,yList,yieldStress)
	e8 = findBreakingStressTest(yList)

	print("\nIn total, there were %s errors found in the program." % (sum([e1,e2,e3,e4,e5,e6,e7,e8])))

runAllTests()