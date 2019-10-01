#!/usr/bin/env python
from eTraveler.clientAPI.connection import Connection
import re

def getvoltages( pl, swing ):
	# Offset averages for RTM-006
	pl_off = 0.20
	pu_off = -0.16
	rd_off = 0.05
	od_off = -0.15
	og_off = 0.12
	sl_off = 0.16
	sh_off = -0.20
	rgl_off = 0.05
	rgh_off = -0.24
	# Rules to set the voltages
	pl0 = pl			 # nominal
	pl1 = pl0 + pl_off   # corrected
	#
	pu0 = pl0 + swing	# nominal based on pl nominal
	pu1 = pu0 + pu_off   # corrected
	#
	rd0 = pu0 - 0.8 * swing + 16.72
	rd1 = rd0 + rd_off
	#
	od0 = rd0 + 11.8
	od1 = od0 + od_off
	#
	og0 = rd0 - 15
	og1 = og0 + og_off
	#
	sl0 = og0 - 2.0
	sl1 = sl0 + sl_off
	#
	sh0 = sl0 + 9.3
	sh1 = sh0 + sh_off
	#
	rgh0 = rd0 - 6.0
	rgh1 = rgh0 + rgh_off
	#
	rgl0 = rgh0 - 10.1
	rgl1 = rgl0 + rgl_off
	#
	# Apply the offsets
	# pl = pl + pl_off
	# pu = pu + pu_off
	# rd = rd + rd_off
	# od = od + od_off
	# og = og + og_off
	# sl = sl + sl_off
	# sh = sh + sh_off
	# rgh = rgh + rgh_off
	# rgl = rgl + rgl_off
	# ----------
	return {
			"DAC": {
				"pclkHighP": pu1,
				"pclkLowP": pl1,
				"sclkHighP": sh1,
				"sclkLowP": sl1,
				"rgHighP": rgh1,
				"rgLowP": rgl1,
			},
			"Bias": {
				"rdP": rd1,
				"odP": od1,
				"ogP": og1,
			}
		}
def buildtemplate( baynum, rebnum, primitivetemplate):
	for pattern, repl in [
			( r"R00",baynum ),
			( r"R22",baynum ),
			( r"Reb0", rebnum ),
			]:
		primitivetemplate=re.sub(pattern,repl,primitivetemplate)
		primitivetemplate=re.sub(r"(R.*)\.(Reb.)\.(.*)","\g<1>/\g<2>/\g<3>",primitivetemplate)
		primitivetemplate=re.sub(r"(R.*)\.(Reb.)\/(.*)","\g<1>/\g<2>/\g<3>",primitivetemplate)
	return primitivetemplate

def fixccdtemppath( template ):
	template = re.sub(r"(R.*)\.(Reb.)\.CCDTemp(.)","\g<1>/\g<2>/S0\g<3>/Temp",template) ### for Science Rafts
	template = re.sub(r"(R.*)[\./]Reb(.)[\./]CCDtemp(.)","\g<1>/Reb\g<2>/S\g<2>\g<3>/Temp",template) # for corner rafts
	template = re.sub(r"SW0","SW",template) # for coner rafts. this is a necesarry fix for inconsistency between RebG and RebW
	return template

def PrepareInfo():
	### Prepare necesarry information from eTraveler
	p = re.compile(r".*CCD")

	connection = Connection(operator="youtsumi", db='Prod', exp='LSST-CAMERA', prodServer=True, localServer=False, appSuffix='', cnfPath='~/.ssh/.etapi.cnf' )

	experimentSN = "LCA-10134_Cryostat-0001"
	htype = "LCA-10134_Cryostat"
	results = connection.getHardwareHierarchy(experimentSN=experimentSN, htype=htype)

	rebs = []
	ccds = []

	for Baylevel in results:
		if Baylevel['child_hardwareTypeName'] not in ( 'LCA-11021_RTM', 'LCA-10692_CRTM' ):
			continue
		Bayinfo  =connection.getHardwareInstances(htype=Baylevel['child_hardwareTypeName'], experimentSN=Baylevel['child_experimentSN'])[0]
		if Baylevel['child_hardwareTypeName'] == 'LCA-11021_RTM':
			flavor = (Bayinfo["model"].split("-")[2])
		else:
			flavor = "ITL"
		print ("#############")
		print (Bayinfo, Baylevel, flavor)
		print ("#############")
			
		sub = connection.getHardwareHierarchy(experimentSN=Baylevel["child_experimentSN"], htype=Baylevel["child_hardwareTypeName"])

		
		for areb in sub:
			# REB
			if areb['child_hardwareTypeName'] == 'LCA-13574':
				rebinfo =connection.getHardwareInstances(htype=areb['child_hardwareTypeName'], experimentSN=areb['child_experimentSN'])[0]
				rebs.append(
					{
						"Bay": Baylevel["slotName"],
						"Flavor": flavor,
						"Name": Baylevel['child_experimentSN'],
						"Slot": areb["slotName"].lower().capitalize(),
						"SerialNum": rebinfo["manufacturerId"],
						"path": "R{:02d}".format(int(Baylevel["slotName"].replace("Bay","")))
					}
				)

			# RSA
			if areb['parent_hardwareTypeName']  == 'LCA-10753_RSA' and ( p.match(areb["child_hardwareTypeName"]) is not None ):
				ccds.append(
					{
						"Bay": Baylevel["slotName"],
						"Flavor": flavor,
						"Name": areb["child_experimentSN"],
						"Slot": areb["slotName"],
						"path": "R{:02d}/Reb{:01d}/{}".format(
								int(Baylevel["slotName"].replace("Bay","")),
								int(areb["slotName"][1]),
								areb["slotName"]
							)
					}
				)
			# WGREB
			if areb['child_hardwareTypeName'] in [
								'LCA-13537', # WREB
								'LCA-13540'  # GREB
								]:
				rebinfo =connection.getHardwareInstances(htype=areb['child_hardwareTypeName'], experimentSN=areb['child_experimentSN'])[0]
				rebs.append(
					{
						"Bay": Baylevel["slotName"],
						"Flavor": flavor,
						"Name": Baylevel['child_experimentSN'],
						"Slot": "WREB" if areb['child_hardwareTypeName'] == 'LCA-13537' else "GREB",
						"SerialNum": rebinfo["manufacturerId"],
						"path": "R{:02d}".format(int(Baylevel["slotName"].replace("Bay","")))
					}
				)
			# CRSA
			print (areb)
			if ( areb['child_hardwareTypeName'] == "ITL-CCD" and areb["parent_hardwareTypeName"] == "LCA-10628" ) or \
			   ( areb['child_hardwareTypeName'] == "ITL-Wavefront-CCD" and areb["parent_hardwareTypeName"] == "LCA-10626" ):
				ccdhier =  connection.getContainingHardware(htype=areb['child_hardwareTypeName'], experimentSN=areb['child_experimentSN'])
				if areb["parent_hardwareTypeName"] == "LCA-10628":
					# G
					slot = (ccdhier[1]["slotName"])
				else:
					# W
					slot = "W{}".format((ccdhier[0]["slotName"])[-1])
				ccds.append(
					{
						"Bay": Baylevel["slotName"],
						"Flavor": flavor,
						"Name": areb["child_experimentSN"],
						"Slot": areb["slotName"],
						"path": "R{:02d}/Reb{}/S{}{}".format(
								int(Baylevel["slotName"].replace("Bay","")),
								slot[0].upper(),
								slot[0].upper(),
								int(slot[-1])-1
							)
					}
				)


	return rebs,ccds

def BiasShiftFix( primitivetemplate ):
	### Bias shift mitigation tweak
	for  pattern, repl in [
			( "gain", 0 ),
			( "rc", 3 )
			]:
		primitivetemplate = re.sub(
				r"(?P<path>.*{} = )(.*)".format(pattern),
				"\g<path>{}".format(repl),
				primitivetemplate
			)
	return primitivetemplate

def HardwareProperties( rebs, ccds ):
	with open("FocalPlaneSubsystem__HardwareId.properties","w") as f:
		for line in sorted(
			list(
				set(
					[ "{}/name: {}\n".format(reb["path"], reb["Name"]) for reb in rebs ]+
					[ "{}/name: {}\n".format(accd["path"], accd["Name"]) for accd in ccds ]
				)
			)
		):
			f.write(line)


if __name__ == "__main__":
# RaftLimits -- not support e2v case
# a path to serial number needs to be formatted
	### Parameters for e2v
#	pl = -6.0
	pl = -5.8
	dp  = 9.6 
	
	### Write out HardwareId.properties
	rebs, ccds = PrepareInfo()
	HardwareProperties(rebs,ccds)

	### Write out Rafts.properties
	# build a primitive template from skeleton, this script will repeat this set for every raft

	with open("skeletons/FocalPlaneSubsystem__Rafts.skeleton") as f:
		lines = f.readlines()
	primitivetemplate = "\n".join([ line.rstrip() for line in filter( lambda x: re.search( r"^R22.Reb0", x ) is not None, lines )])
	primitivetemplate = BiasShiftFix(primitivetemplate)


	### RaftsLimits
	with open("skeletons/RTM-005_BPtestSM3_TS8Subsystem__RaftsLimits.skeleton") as f:
		lines = f.readlines()
	raftslimitprimitivetemplate_e2v = "\n".join([ line.rstrip() for line in filter( lambda x: re.search( r"^R00.Reb0", x ) is not None, lines )])
	with open("skeletons/RTM-023_TS8Subsystem__RaftsLimits.skeleton") as f:
		lines = f.readlines()
	raftslimitprimitivetemplate_itl = "\n".join([ line.rstrip() for line in filter( lambda x: re.search( r"^R00.Reb0", x ) is not None, lines )])

	### Limits
	with open("skeletons/RTM-018_TS8Subsystem__Limits.skeleton") as f:
		lines = f.readlines()
	limitprimitivetemplate_itl = "\n".join([ line.rstrip() for line in filter( lambda x: re.search( r"^R00.Reb0", x ) is not None, lines )])
	limitprimitivetemplate_itl = fixccdtemppath( limitprimitivetemplate_itl)
	with open("skeletons/RTM-005_BPtestSM3_TS8Subsystem__Limits.skeleton") as f:
		lines = f.readlines()
	limitprimitivetemplate_e2v = "\n".join([ line.rstrip() for line in filter( lambda x: re.search( r"^R00.Reb0", x ) is not None, lines )])
	limitprimitivetemplate_e2v = fixccdtemppath( limitprimitivetemplate_e2v)

	### RaftsPower
	with open("skeletons/RTM-005_BPtestSM3_TS8Subsystem__RaftsPower.skeleton") as f:
		lines = f.readlines()
	powerprimitivetemplate_e2v = "\n".join([ line.rstrip() for line in filter( lambda x: re.search( r"^R00.Reb0", x ) is not None, lines )])
	with open("skeletons/RTM-018_TS8Subsystem__RaftsPower.skeleton") as f:
		lines = f.readlines()
	powerprimitivetemplate_itl = "\n".join([ line.rstrip() for line in filter( lambda x: re.search( r"^R00.Reb0", x ) is not None, lines )])

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
	greblimitprimitivetemplate = fixccdtemppath( greblimitprimitivetemplate )
	wreblimitprimitivetemplate = "\n".join( [ "R00/"+re.sub(r"WREB[\./]", "RebW/", aline.rstrip()) for aline in filter( lambda x: re.search( r"^WREB", x ) is not None, lines ) ] )
	wreblimitprimitivetemplate = fixccdtemppath( wreblimitprimitivetemplate )

	### manipulate a template
	mastername = "focal-plane__"
	with open("{}Rafts.properties".format(mastername),"w") as f, \
		open("{}RaftsLimits.properties".format(mastername),"w") as raftslimit, \
		open("{}Limits.properties".format(mastername),"w") as limit, \
		open("{}RaftsPower.properties".format(mastername),"w") as power:
		for areb in rebs:
			f.write("### {} \n".format(areb))
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
				draft = buildtemplate( areb["path"], areb["Slot"], primitivetemplate )
				if areb["Flavor"] == "E2V":
					raftslimitdraft = buildtemplate(areb["path"], areb["Slot"], raftslimitprimitivetemplate_e2v)
					powerdraft = buildtemplate(areb["path"], areb["Slot"], powerprimitivetemplate_e2v)
					limitdraft = buildtemplate(areb["path"], areb["Slot"], limitprimitivetemplate_e2v)
				else:
					raftslimitdraft = buildtemplate(areb["path"], areb["Slot"], raftslimitprimitivetemplate_itl)
					powerdraft = buildtemplate(areb["path"], areb["Slot"], powerprimitivetemplate_itl)
					limitdraft = buildtemplate(areb["path"], areb["Slot"], limitprimitivetemplate_itl)

			draft = re.sub(
					r"(?P<path>.*serialNum = )(.*)",
					"\g<path>{}".format(int(areb["SerialNum"],16)),
					draft
				)

			if areb["Flavor"] == "E2V":
				wanted = getvoltages( pl = pl, swing = dp )
				for k, v in dict(**wanted["DAC"],**wanted["Bias"]).items():
					draft = re.sub(
						r"(?P<path>.*{} = )(.*)".format(k),
						"\g<path>{:.2f}".format(v),
						draft 
					)
			
			f.write("{}\n".format(draft))
			raftslimit.write("{}\n".format(raftslimitdraft))
			power.write("{}\n".format(powerdraft))
			limit.write("{}\n".format(limitdraft))
			
