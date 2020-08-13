#!/usr/bin/env python
from eTraveler.clientAPI.connection import Connection
import re

def getvoltages( pl, pswing, sswing, rgswing ):
	pl_off = 0.0
	pu_off = 0.0
	rd_off = 0.0
	od_off = 0.0
	og_off = 0.0
	sl_off = 0.0
	sh_off = 0.0
	rgl_off = 0.0
	rgh_off = 0.0
	gd_off = 0.0
	chz = 11
	# Rules to set the voltages
	pl0 = pl			 # nominal
	pl1 = pl0 + pl_off   # corrected
	#
	pu0 = pl0 + pswing	# nominal based on pl nominal
	pu1 = pu0 + pu_off   # corrected
	#
	rd0 = pu0 + 8.0
	rd1 = rd0 + rd_off
	#
	od0 = rd0 + 11.8
	od1 = od0 + od_off
	#
	og0 = rd0 - chz - 4
	og1 = og0 + og_off
	#
	sl0 = og0 - 2.0
	sl1 = sl0 + sl_off
	#
	sh0 = sl0 + sswing
	sh1 = sh0 + sh_off
	#
	rgh0 = rd0 - 5.5
	rgh1 = rgh0 + rgh_off
	#
	rgl0 = rgh0 - rgswing
	rgl1 = rgl0 + rgl_off
	#
	gd0 = 26
	gd1 = gd0 + gd_off
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
				"gdP": gd1,
			}
		}

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
						"slot": areb["slotName"].lower().capitalize(),
						"SerialNum": rebinfo["manufacturerId"],
						"RebName": rebinfo["experimentSN"],
						"path": "R{:02d}".format(int(Baylevel["slotName"].replace("Bay","")))
					}
				)

			# RSA
			if areb['parent_hardwareTypeName']  == 'LCA-10753_RSA' and ( p.match(areb["child_hardwareTypeName"]) is not None ):
				sensorinfo =connection.getHardwareInstances(htype=areb['child_hardwareTypeName'], experimentSN=areb['child_experimentSN'])[0]
				ccds.append(
					{
						"Bay": Baylevel["slotName"],
						"Flavor": flavor,
						"Name": areb["child_experimentSN"],
						"Slot": areb["slotName"],
						"manSerNum": sensorinfo["manufacturerId"],
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
						"slot": "RebW" if areb['child_hardwareTypeName'] == 'LCA-13537' else "RebG",
						"RebName": rebinfo["experimentSN"],
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
				sensorinfo =connection.getHardwareInstances(htype=areb['child_hardwareTypeName'], experimentSN=areb['child_experimentSN'])[0]
				ccds.append(
					{
						"Bay": Baylevel["slotName"],
						"Flavor": flavor,
						"Name": areb["child_experimentSN"],
						"Slot": areb["slotName"],
						"manSerNum": sensorinfo["manufacturerId"],
						"path": "R{:02d}/Reb{}/S{}{}".format(
								int(Baylevel["slotName"].replace("Bay","")),
								slot[0].upper(),
								slot[0].upper(),
								int(slot[-1])-1
							)
					}
				)


	return rebs,ccds

def newadditions( ):
	with open("skeletons/newadditions.list") as f:
		lines = f.readlines()

	rules = {}
	for aline in lines:
		ret = aline.split("/")
		abay = ret[0]
		areb = ret[1]
		atag = "{}/{}".format(abay,areb)
		if atag in rules.keys():
			rules[atag]["item"].append(aline.rstrip())
		else:
			rules.update( { atag: { "bay": abay, "reb": areb, "item": [ aline.rstrip() ]} } )
	return rules

def buildtemplate( baynum, rebnum, primitivetemplate):
	for pattern, repl in [
			( r"R00",baynum ),
			( r"R22",baynum ),
			( r"Reb0", rebnum ),
			]:
		primitivetemplate=re.sub(pattern,repl,primitivetemplate)
		primitivetemplate=re.sub(r"(R.*)\.(Reb.)\.(.*)","\g<1>/\g<2>/\g<3>",primitivetemplate) # dot
		primitivetemplate=re.sub(r"(R.*)\.(Reb.)\/(.*)","\g<1>/\g<2>/\g<3>",primitivetemplate) # slash
		primitivetemplate=re.sub(r"Reb1/S0","Reb1/S1",primitivetemplate) # slash
		primitivetemplate=re.sub(r"Reb2/S0","Reb2/S2",primitivetemplate) # slash

		
	return primitivetemplate

def fixccdtemppath( template ):
	### TEMP stuff
	template = re.sub(r"(R.*)\.Reb(.)\.CCDTemp(.)","\g<1>/Reb\g<2>/S\g<2>\g<3>/Temp",template) ### for Science Rafts
	template = re.sub(r"(R.*)[\./]Reb(.)[\./]CCDtemp(.)","\g<1>/Reb\g<2>/S\g<2>\g<3>/Temp",template) # for corner rafts

	### Current
	template = re.sub(r"(R.*)\.Reb(.)\.CCDI(.)(.)(.)","\g<1>/Reb\g<2>/S\g<2>\g<3>/Seg\g<4>\g<5>/I",template) ### for Science Rafts
	template = re.sub(r".*OD.I.*\n","",template) ### get rid of entries for OD[01]I

	### Current
	template = re.sub(r"(R.*)\.Reb(.)\.(..)(\d)V","\g<1>/Reb\g<2>/S\g<2>\g<4>/\g<3>V",template) ### for Biases

	### ASPIC
	# R00.Reb0.Atemp1L/dbandHi
	# R10/Reb1/AspicL/Temp1/limitHi
	template = re.sub(r"(R.*)\.Reb(.)\.Atemp(\d)(\w)","\g<1>/Reb\g<2>/Aspic\g<4>/Temp\g<3>",template) ### for Science Rafts
	template = re.sub(r"(R.*)[\./]Reb(.)[\./]Atemp(\d)(\w)","\g<1>/Reb\g<2>/Aspic\g<4>/Temp\g<3>",template) # for corner rafts

	# Bias
	template = re.sub(r"Reb([GW])/(..)(\d)V","Reb\g<1>/S\g<1>\g<3>/\g<2>V",template) # for coner rafts.
	template = re.sub(r"Reb([GW])/(..)V","Reb\g<1>/S\g<1>/\g<2>V",template) # for coner rafts.

	template = re.sub(r"SW0","SW",template) # for coner rafts. this is a necesarry fix for inconsistency between RebG and RebW
	template = re.sub(r"S.\/ODV","ODV",template) # for coner rafts. this is a necesarry fix for inconsistency between RebG and RebW
#	template = re.sub(r"Reb([W])\/(..)I","Reb\g<1>/S\g<1>/\g<2>I",template) # for coner rafts. this is a necesarry fix for inconsistency between RebG and RebW
#R44/RebG/ODI/limitLo


	template = re.sub(r"RTDtemp","RTDTemp",template) # for coner rafts. this is a necesarry fix for inconsistency between RebG and RebW
	return template


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


def fixCornerRaftsSN(draft):
	with open("skeletons/crsn.list") as f:
		lines = f.readlines()

	for aline in lines:
		m = re.match(r"(.*)[\s\t]*=[\s\t]*(.*)",aline)
		path = m.group(1)
		value = m.group(2)
		print(path,value)
		draft = re.sub(
				r"(?P<path>{}.*= )(?P<original>.*)".format(path),
				"\g<path>{}".format(value),
				draft)
	return draft

def fixAspicPath(draft):
	# https://jira.slac.stanford.edu/browse/LSSTCCSRAFTS-506
	draft = re.sub(
		r"(R../Reb)(.)(/ASPIC)(.)",
		lambda x: (
			"{}{}/S{}{}{}{}".format(
				x.group(1),
				x.group(2),
				x.group(2),
				int(int(x.group(4))/2),
				x.group(3),
				(int(x.group(4))%2)
			)
		), draft)

	draft = re.sub(
		r"(R../RebW/SW)(.)(/ASPIC)(.)(/.*)",
		lambda x: (
			"{}{}{}{}{}".format(
				x.group(1),
				x.group(4),
				x.group(3),
				x.group(2),
				x.group(5)
			)
		), draft)
	return draft

def fixlimitskeleton(draft):
	with open("skeletons/science-raft.list") as f:
		lines = f.readlines()

	for aline in lines:
		m = re.match(r"(.*)[\s\t]*=[\s\t]*(.*)",aline)
		path = m.group(1)
		value = m.group(2)
		draft = re.sub(
				r"(?P<path>{}.*= )(?P<original>.*)".format(path),
				"\g<path>{}".format(value),
				draft)
	return draft

def fixbyregex(draft):
	with open("skeletons/regex.list") as f:
		lines = f.readlines()
	lines = filter( lambda x: re.match("^#.*$", x) is None, lines ) 

	for aline in lines:
		m = re.match(r"(.*)[\s\t]*=[\s\t]*(.*)",aline)
		path = m.group(1)
		value = m.group(2)
		draft = re.sub(
				r"(?P<path>{}.*= )(?P<original>.*)".format(path),
				"\g<path>{}".format(value),
				draft)
	return draft


