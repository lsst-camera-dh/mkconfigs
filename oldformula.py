def getvoltages( pl, pswing ):
	pl_off = 0.0
	pu_off = 0.0
	rd_off = 0.0
	od_off = 0.0
	og_off = 0.0
	sl_off = 0.0
	sh_off = 0.0
	rgl_off = 0.0
	rgh_off = 0.0
	# Rules to set the voltages
	pl0 = pl			 # nominal
	pl1 = pl0 + pl_off   # corrected
	#
	pu0 = pl0 + pswing	# nominal based on pl nominal
	pu1 = pu0 + pu_off   # corrected
	#
	rd0 = pu0 - 0.8 * pswing + 16.72
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
				"gdP": 26.0,
			}
		}
