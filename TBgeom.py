"""
Created on Monday April 20, 2015

@author: Andrew Horsfield

This module manages the geometry of the system (atomic coordinates etc)
"""
#
# Import modules

import TBIO


def init(JobClass):
	"""initialise the geometry."""
	global NAtom, Pos, AtomType
	#
	# Read in the geometry from file
	NAtom, Pos, AtomType = TBIO.ReadGeom(JobClass.JobDef['gy_file'])
	#
	# Write out the geometry
	TBIO.WriteXYZ(NAtom, 'Hello', AtomType, Pos)
	#
	# Transfer geometry to the JobClass
	JobClass.NAtom    = NAtom
	JobClass.Pos      = Pos
	JobClass.AtomType = AtomType