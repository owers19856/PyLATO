#!/usr/bin/env python
# -*- coding: utf-8 -*- 
"""
Created on Thursday, June 18, 2015

@author: Andrew Horsfield and Marc Coury

Orthogonal model for hydrocarbons, based on:

Computational materials synthesis. I. A tight-binding scheme for hydrocarbons
A. P. Horsfield, P. D. Godwin, D. G. Pettifor, and A. P. Sutton
PHYSICAL REVIEW B VOLUME 54, NUMBER 22 1 DECEMBER 1996-II

"""
#
# Import the modules that will be needed
import os, sys
import numpy as np
from scipy.interpolate import interp1d
import math
import commentjson

class GoodWin:
	def __init__(self, v0 = 0, r0 = 0, rc = 0, rcut = 0, r1 = 0, n = 0, nc = 0):

		self.v0   = v0
		self.r0   = r0
		self.rc   = rc
		self.rcut = rcut
		self.r1   = r1
		self.n    = n
		self.nc   = nc

		dr = rcut - r1

		self.c0 = self.radial(r1)
		self.c1 = -n * (1 + nc * np.power(r1/rc, nc)) * self.radial(r1)/r1
		self.c2 = -2*self.c1 / dr - 3*self.c0 / dr/dr
		self.c3 = self.c1 / dr/dr + 2*self.c0 / dr/dr/dr

	def radial(self, r):
		if r <= self.r1:
			return self.v0 * np.power(self.r0/r, self.n) * np.exp(self.n * 
				(-np.power(r/self.rc, self.nc) + np.power(self.r0/self.rc, self.nc)))
		if self.rcut > r > self.r1:
			x = r - self.r1
			return self.c0 + x*(self.c1 + x*(self.c2 + x*self.c3))
		else:
			return 0.0

class MatrixElements:
	"""Tight binding model for model hamiltonian"""
	def __init__(self, modelpath):
		"""Import model data, initialise orbital pair index matrix."""

		# Catch invalid model path
		if os.path.exists(modelpath) == False:
		    print "ERROR: Unable to open tight binding model file:", modelpath
		    sys.exit()

		# Import the tight binding model parameters
		with open(modelpath, 'r') as modelfile:
			modeldata = commentjson.loads(modelfile.read())

		self.atomic = modeldata['species']
		self.data = modeldata['hamiltonian']
		self.pairpotentials = modeldata['pairpotentials']
		self.embedded = modeldata['embedding']

		# Allocate space for the five hamiltonian matrix elements.
		self.v = np.zeros(5, dtype='double')

		# Generate pair of indices for each pair of shells, showing which values
		# of v to use
		v_bgn = np.zeros((2, 2), dtype='double')
		v_end = np.zeros((2, 2), dtype='double')
		#
		# ss
		v_bgn[0, 0] = 0
		v_end[0, 0] = 1
		#
		# sp
		v_bgn[0, 1] = 1
		v_end[0, 1] = 2
		#
		# ps
		v_bgn[1, 0] = 2
		v_end[1, 0] = 3
		#
		# pp
		v_bgn[1, 1] = 3
		v_end[1, 1] = 5

		self.v_bgn = v_bgn
		self.v_end = v_end

		rvalues = np.arange(0.5, 2.6, 0.005, dtype='double')

		# HH parameters
		hh_sss = GoodWin(**self.data[0][0]).radial

		# HC parameters
		hc_sss = GoodWin(**self.data[1][0]).radial
		hc_sps = GoodWin(**self.data[1][1]).radial
		hc_pss = GoodWin(**self.data[1][2]).radial

		# CH parameters
		ch_sss = GoodWin(**self.data[2][0]).radial
		ch_sps = GoodWin(**self.data[2][1]).radial
		ch_pss = GoodWin(**self.data[2][2]).radial

		# CC parameters
		cc_sss = GoodWin(**self.data[3][0]).radial
		cc_sps = GoodWin(**self.data[3][1]).radial
		cc_pss = GoodWin(**self.data[3][2]).radial
		cc_pps = GoodWin(**self.data[3][3]).radial
		cc_ppp = GoodWin(**self.data[3][4]).radial

		# Pair potentials
		hh_pap = GoodWin(**self.pairpotentials[0]).radial
		hc_pap = GoodWin(**self.pairpotentials[1]).radial
		ch_pap = GoodWin(**self.pairpotentials[2]).radial
		cc_pap = GoodWin(**self.pairpotentials[3]).radial


		# Pair potential embedded function
		embed = lambda x: x*(self.embedded['a1'] + x*(self.embedded['a2'] + x*(self.embedded['a3'] + x*self.embedded['a4'])))

		# Embed pair potentials
		hh_pap2 = lambda x: embed(hh_pap(x))
		hc_pap2 = lambda x: embed(hc_pap(x))
		ch_pap2 = lambda x: embed(ch_pap(x))
		cc_pap2 = lambda x: embed(cc_pap(x))		

		# Interpolate radial functions with cubic polynomials
		hh_sss = interp1d(rvalues, [hh_sss(r) for r in rvalues], copy=False, bounds_error=False, fill_value=0.0)
		
		hc_sss = interp1d(rvalues, [hc_sss(r) for r in rvalues], kind='cubic', copy=False, bounds_error=False, fill_value=0.0)
		hc_sps = interp1d(rvalues, [hc_sps(r) for r in rvalues], kind='cubic', copy=False, bounds_error=False, fill_value=0.0)
		hc_pss = interp1d(rvalues, [hc_pss(r) for r in rvalues], kind='cubic', copy=False, bounds_error=False, fill_value=0.0)
		
		ch_sss = interp1d(rvalues, [ch_sss(r) for r in rvalues], kind='cubic', copy=False, bounds_error=False, fill_value=0.0)
		ch_sps = interp1d(rvalues, [ch_sps(r) for r in rvalues], kind='cubic', copy=False, bounds_error=False, fill_value=0.0)
		ch_pss = interp1d(rvalues, [ch_pss(r) for r in rvalues], kind='cubic', copy=False, bounds_error=False, fill_value=0.0)
		
		cc_sss = interp1d(rvalues, [cc_sss(r) for r in rvalues], kind='cubic', copy=False, bounds_error=False, fill_value=0.0)
		cc_sps = interp1d(rvalues, [cc_sps(r) for r in rvalues], kind='cubic', copy=False, bounds_error=False, fill_value=0.0)
		cc_pss = interp1d(rvalues, [cc_pss(r) for r in rvalues], kind='cubic', copy=False, bounds_error=False, fill_value=0.0)
		cc_pps = interp1d(rvalues, [cc_pps(r) for r in rvalues], kind='cubic', copy=False, bounds_error=False, fill_value=0.0)
		cc_ppp = interp1d(rvalues, [cc_ppp(r) for r in rvalues], kind='cubic', copy=False, bounds_error=False, fill_value=0.0)
			
		# Store the radial functions in the function grid. index 0 is hydrogen, index 1 is carbon
		# Hence:  0,0 = hh; 0,1 = hc; 1,0 = ch; 1,1 = cc
		self.function_grid = [[[hh_sss], [hc_sss, hc_sps]], [[ch_sss, ch_sps], [cc_sss, cc_sps, cc_pss, cc_pps, cc_ppp]]]
		self.pairpotential_grid = [[hh_pap2, hc_pap2], [ch_pap2, cc_pap2]]

	def helements(self, r, atomicspecies_1, atomicspecies_2):
		"""Orthogonal model for hydrocarbons."""

		# Pick out the right functions for the bond
		funcs = self.function_grid[atomicspecies_1][atomicspecies_2]

		# Compute the hopping integrals for the reference geometry
		for i, radial_function in enumerate(funcs):
			self.v[i] = radial_function(r)

		# Return integrals and indices
		return self.v, self.v_bgn, self.v_end

	def pairpotential(self, r, atomicspecies_1, atomicspecies_2):
		"""Embedded pairpotentials for hydrocarbons."""

		radial_function = self.pairpotential_grid[atomicspecies_1][atomicspecies_2]
		return radial_function(r)

if __name__ == "__main__":
	# Print out some matrix elements if run as a script.

	model = MatrixElements("TBhydrocarbons.json")

	xvals = np.arange(0.5, 3, 0.01)
	#yvals = np.array([model.helements(x, 1, 1)[0] for x in xvals])
	yvals = np.array([model.pairpotential_grid[1][1](x) for x in xvals])

	for i,j in enumerate(xvals):
		print xvals[i], yvals[i]



