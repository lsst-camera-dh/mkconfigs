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
			( r"R22", baynum ),
			( r"Reb0", rebnum ),
			]:
		primitivetemplate=re.sub(pattern,repl,primitivetemplate)
	return primitivetemplate

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
		if Baylevel['child_hardwareTypeName'] != 'LCA-11021_RTM':
			continue
		Bayinfo  =connection.getHardwareInstances(htype=Baylevel['child_hardwareTypeName'], experimentSN=Baylevel['child_experimentSN'])[0]
		flavor = (Bayinfo["model"].split("-")[2])
		sub = connection.getHardwareHierarchy(experimentSN=Baylevel["child_experimentSN"], htype=Baylevel["child_hardwareTypeName"])

		
		for areb in sub:
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
	### Parameters for e2v
	pl = -6.0
	dp  = 9.0 
	
	### Write out HardwareId.properties
	rebs, ccds = PrepareInfo()
	HardwareProperties(rebs,ccds)

	### Write out Rafts.properties
	# build a primitive template from skelton, this script will repeat this set for every raft

	with open("FocalPlaneSubsystem__Rafts.skelton") as f:
		lines = f.readlines()

	primitivetemplate = "\n".join([ line.rstrip() for line in filter( lambda x: re.search( r"R22.Reb0", x ) is not None, lines )])

	primitivetemplate = BiasShiftFix(primitivetemplate)

	### manuplate a template
	with open("FocalPlaneSubsystem__Rafts.properties","w") as f:
		for areb in rebs:
			f.write("### {} \n".format(areb))
			draft = buildtemplate( areb["path"], areb["Slot"], primitivetemplate )
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
			
