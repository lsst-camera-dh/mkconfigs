#!/usr/bin/env python
from mkconfigs import *
import newformula as formula
import params
import re


# RaftLimits -- not support e2v case
# a path to serial number needs to be formatted

### Write out HardwareId.properties
rebs, ccds = PrepareInfo()

### Write out Rafts.properties
# build a primitive template from skeleton, this script will repeat this set for every raft

with open("skeletons/RTM-005_BPtestSM3_TS8Subsystem__Rafts.skeleton") as f:
	lines = f.readlines()
primitivetemplate_e2v = "\n".join([ line.rstrip() for line in filter( lambda x: re.search( r"^R00.Reb0", x ) is not None, lines )])
primitivetemplate_e2v = BiasShiftFix(primitivetemplate_e2v)

with open("skeletons/RTM-018_TS8Subsystem__Rafts.skeleton") as f:
	lines = f.readlines()
primitivetemplate_itl = "\n".join([ line.rstrip() for line in filter( lambda x: re.search( r"^R00.Reb0", x ) is not None, lines )])
primitivetemplate_itl = BiasShiftFix(primitivetemplate_itl)

### RaftsLimits
with open("skeletons/RTM-005_BPtestSM3_TS8Subsystem__RaftsLimits.skeleton") as f:
	lines = f.readlines()
raftslimitprimitivetemplate_e2v = "\n".join([ line.rstrip() for line in filter( lambda x: re.search( r"^R00.Reb0", x ) is not None, lines )])
with open("skeletons/ts8-fp_defaultInitial_RaftsLimits.skeleton") as f:
	lines = f.readlines()
raftslimitprimitivetemplate_itl = "\n".join([ line.rstrip() for line in filter( lambda x: re.search( r"^R22/Reb0", x ) is not None, lines )])

### Limits
with open("skeletons/ts8-fp_defaultInitial_Limits.skeleton") as f:
	lines = f.readlines()
limitprimitivetemplate_itl = "\n".join([ line.rstrip() for line in filter( lambda x: re.search( r"^R22/Reb0", x ) is not None, lines )])
limitprimitivetemplate_itl = fixccdtemppath( fixlimitskeleton(limitprimitivetemplate_itl))
with open("skeletons/RTM-005_BPtestSM3_TS8Subsystem__Limits.skeleton") as f:
	lines = f.readlines()
limitprimitivetemplate_e2v = "\n".join([ line.rstrip() for line in filter( lambda x: re.search( r"^R00.Reb0", x ) is not None, lines )])
limitprimitivetemplate_e2v = fixccdtemppath( fixlimitskeleton(limitprimitivetemplate_e2v))

### RaftsPower
with open("skeletons/focal-plane_defaultInitial_RaftsPower.properties") as f:
	lines = f.readlines()
powerprimitivetemplate_e2v = "\n".join([ line.rstrip() for line in filter( lambda x: re.search( r"^R22/Reb0", x ) is not None, lines )])
with open("skeletons/focal-plane_defaultInitial_RaftsPower.properties") as f:
	lines = f.readlines()
powerprimitivetemplate_itl = "\n".join([ line.rstrip() for line in filter( lambda x: re.search( r"^R10/Reb0", x ) is not None, lines )])

### CornerRafts: This came from /opt/lsst/ccs/20190726/ccs-test-configurations-master/IR2/lsst-ir2daq01/CRTM-0002
with open("skeletons/cr-raft__Rafts.skeleton") as f:
	lines = f.readlines()
grebprimitivetemplate = "\n".join( [ "R22/"+re.sub(r"GREB[\./]", "RebG/", aline.rstrip()) for aline in filter( lambda x: re.search( r"GREB", x ) is not None, lines ) ] )
grebprimitivetemplate = BiasShiftFix(grebprimitivetemplate)
wrebprimitivetemplate = "\n".join( [ "R22/"+re.sub(r"WREB[\./]", "RebW/", aline.rstrip()) for aline in filter( lambda x: re.search( r"WREB", x ) is not None, lines ) ] )
wrebprimitivetemplate = BiasShiftFix(wrebprimitivetemplate)

with open("skeletons/cr-raft__RaftsLimits.skeleton") as f:
	lines = f.readlines()
grebraftslimitprimitivetemplate = "\n".join( [ "R00/"+re.sub(r"GREB[\./]", "RebG/", aline.rstrip()) for aline in filter( lambda x: re.search( r"^GREB", x ) is not None, lines ) ] )
wrebraftslimitprimitivetemplate = "\n".join( [ "R00/"+re.sub(r"WREB[\./]", "RebW/", aline.rstrip()) for aline in filter( lambda x: re.search( r"^WREB", x ) is not None, lines ) ] )

with open("skeletons/cr-raft__RaftsPower.skeleton") as f:
	lines = f.readlines()
grebpowerprimitivetemplate = "\n".join( [ "R00/"+re.sub(r"GREB[\./]", "RebG/", aline.rstrip()) for aline in filter( lambda x: re.search( r"^GREB", x ) is not None, lines ) ] )
wrebpowerprimitivetemplate = "\n".join( [ "R00/"+re.sub(r"WREB[\./]", "RebW/", aline.rstrip()) for aline in filter( lambda x: re.search( r"^WREB", x ) is not None, lines ) ] )

with open("skeletons/cr-raft__Limits.skeleton") as f:
	lines = f.readlines()
greblimitprimitivetemplate = "\n".join( [ "R00/"+re.sub(r"GREB[\./]", "RebG/", aline.rstrip()) for aline in filter( lambda x: re.search( r"^GREB", x ) is not None, lines ) ] )
greblimitprimitivetemplate = fixccdtemppath( fixlimitskeleton(greblimitprimitivetemplate ) )
wreblimitprimitivetemplate = "\n".join( [ "R00/"+re.sub(r"WREB[\./]", "RebW/", aline.rstrip()) for aline in filter( lambda x: re.search( r"^WREB", x ) is not None, lines ) ] )
wreblimitprimitivetemplate = fixccdtemppath( fixlimitskeleton(wreblimitprimitivetemplate ) )


#######


for inputparams in params.params: 
	mastername = "output/focal-plane_{}_".format(inputparams["tag"])

	### manipulate a template
	with    open("{}Rafts.properties".format(mastername),"w") as f, \
		open("{}RaftsLimits.properties".format(mastername),"w") as raftslimit, \
		open("{}Limits.properties".format(mastername),"w") as limit, \
		open("{}RaftsPower.properties".format(mastername),"w") as power:
		f.write("#### {}\n".format(inputparams))
		for areb in rebs:
			for output in [ f, raftslimit, limit, power ]:
				output.write("### {} \n".format(areb))
			if areb["Slot"] == "GREB":
				draft = buildtemplate( areb["path"], "RebG", grebprimitivetemplate )
				raftslimitdraft = buildtemplate( areb["path"], "RebG", grebraftslimitprimitivetemplate)
				powerdraft = buildtemplate(areb["path"], "RebG", grebpowerprimitivetemplate)
				limitdraft = buildtemplate(areb["path"], areb["Slot"], greblimitprimitivetemplate)
			elif areb["Slot"] == "WREB":
				draft = buildtemplate( areb["path"], "RebW", wrebprimitivetemplate )
				raftslimitdraft = buildtemplate( areb["path"], "RebW", wrebraftslimitprimitivetemplate)
				powerdraft = buildtemplate(areb["path"], "RebW", wrebpowerprimitivetemplate)
				limitdraft = buildtemplate(areb["path"], areb["Slot"], wreblimitprimitivetemplate)
			else:
				if areb["Flavor"] == "E2V":
					draft = buildtemplate( areb["path"], areb["Slot"], primitivetemplate_e2v )
					raftslimitdraft = buildtemplate(areb["path"], areb["Slot"], raftslimitprimitivetemplate_e2v)
					powerdraft = buildtemplate(areb["path"], areb["Slot"], powerprimitivetemplate_e2v)
					limitdraft = buildtemplate(areb["path"], areb["Slot"], limitprimitivetemplate_e2v)
				else:
					draft = buildtemplate( areb["path"], areb["Slot"], primitivetemplate_itl )
					raftslimitdraft = buildtemplate(areb["path"], areb["Slot"], raftslimitprimitivetemplate_itl)
					powerdraft = buildtemplate(areb["path"], areb["Slot"], powerprimitivetemplate_itl)
					limitdraft = buildtemplate(areb["path"], areb["Slot"], limitprimitivetemplate_itl)

			### convert serialNum to hex
			draft = re.sub(
					r"(?P<path>.*serialNum = )(.*)",
					"\g<path>{}".format(int(areb["SerialNum"],16)),
					draft
				)

			### Inserting new additions
			rules = newadditions()
			atag = "{}/{}".format(areb["path"],areb["slot"])
			if atag in rules.keys():
				draft = draft +"\n"+"\n".join(rules[atag]["item"])

			if areb["Flavor"] == "E2V":
				wanted = formula.getvoltages( **inputparams["E2V"] )
			else:
				wanted = inputparams["ITL"]

			### change voltages based on the relation defined for e2v, the exceptions defined for ITL
			for k, v in dict(**wanted["DAC"],**wanted["Bias"]).items():
				draft = re.sub(
					r"(?P<path>.*{} = )(.*)".format(k),
					"\g<path>{:.1f}".format(v),
					draft 
				)
				raftslimitdraft = re.sub(
					r"(?P<path>.*{} = )(.*)".format(k.replace("P","Max")),
					"\g<path>{:.1f}".format(v+1.0),
					raftslimitdraft	
				)
				raftslimitdraft = re.sub(
					r"(?P<path>.*{} = )(.*)".format(k.replace("P","Min")),
					"\g<path>{:.1f}".format(v-1.0),
					raftslimitdraft	
				)

			draft = fixbyregex(fixAspicPath(fixCornerRaftsSN(draft)),inputparams["regex"])
			draft = draft.split("\n")
			draft.sort()
			draft = "\n".join(draft)
			
			f.write("{}\n".format(draft))
			raftslimit.write("{}\n".format(fixraftslimitbyregex(raftslimitdraft,inputparams["regex"])))
			power.write("{}\n".format(powerdraft))
			limit.write("{}\n".format(limitdraft))
			
	HardwareProperties(rebs,ccds,mastername)
