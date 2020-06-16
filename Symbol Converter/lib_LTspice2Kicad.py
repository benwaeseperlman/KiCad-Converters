#! usr/bin/python
# -*- coding: ISO-8859-1 -*-

#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.

#  Written by : Ben Waese-Perlman
#  last change: 2020, June 1.
#
# usage examples : python lib_LTspice2Kicad.py /LTC/LTspiceXVII/lib/sym
#				   python lib_LTspice2Kicad.py /LTC/LTspiceXVII/lib/sym/Comparators
#	   Those examples will create the files : LTspice_sym.libs  and  LTspice_Comparators.libs
#

import sys, re, os, codecs, nltk, math
import numpy as np

#constants
SCALE_CONVERSION_FACTOR = (50.0/16.0)
ARC_RESOLUTION = 20

# nltk.download('punkt') # done in the bash script so not needed here. If using python script by itself delete first hash

# return the radius of an ellipse at a specific angle with a given width and height
def ellipse_rad (angle, width, height) :
	# find the semi major and semi minor axis
	a = abs(width)/2.0
	b = abs(height)/2.0

	r = (a*b) / math.sqrt(a**2 * math.sin(angle)**2 + b**2 * math.cos(angle)**2) #equation for radius of ellipse
	return r

# returns the unit vector in cartesian coordinates at a given polar coordinate angle (no need for the magnitude in polar as it's a unit vector)
def unit_vector (angle) :
	return np.array([math.cos(angle), math.sin(angle)])

def get_angle (unit_vector) : 
	angle = np.arctan2(unit_vector[1], unit_vector[0])
	return angle

# approxomates an arc or circle as a multi point polyline and returns a string in the KiCad .lib output format	 
def line_arc(center, size, angle1, angle2):
	while angle2 >= angle1: angle2 -= math.pi * 2
	
	#make the list of points
	points = []
	num_lines = (2*math.pi*math.sqrt((size**2).sum()/2))/ARC_RESOLUTION # divide the circumference by resolution to get number of lines needed for the whole circle
	num_lines *= (angle1 - angle2)/(2*math.pi) # multiply lines for whole circle by fraction covered (calculated by difference of angles divided by full circle)
	num_lines = int(num_lines) # make sure that we're drawing an integer number of lines
	for i in range(num_lines + 1) : 
		current_angle = angle1 + i*(angle2-angle1)/num_lines
		current_radius = ellipse_rad(current_angle, size[0], size[1])
		current_point = center + current_radius*unit_vector(current_angle)
		points.append(list(current_point.astype(int).astype(str)))
	
	#output the polyline
	polyline = "P " + str(len(points)) + " 0 0 0"
	for i in points :
		polyline += " " + " ".join(i)
	
	return polyline

# command line parameters
directory = os.path.abspath(sys.argv[1])
output_directory = os.path.abspath('./output')
files = os.listdir(directory)

# create the list of .asy files to put into the current .lib
files_to_convert = []
for component in files:
	if (component[-4:]==".asy") : files_to_convert.append(component)

print(directory)
if len(files_to_convert) == 0: exit(0)

indir = os.path.basename(directory)
out_file_name = os.path.join(output_directory,"LTspice_" + indir + ".lib") # create output .lib file in target folder
print(out_file_name)
outfl = codecs.open(out_file_name,"w",'utf-8') # open the file with write and utf-8 encoding
outfl.write("EESchema-LIBRARY Version 2.4\n#encoding utf-8\n#\n")

# actual parsing and output
for component in files_to_convert :
	print(component)
	in_file = os.path.join(directory, component)
	lines = []

	try:
		infl_utf_8 = open(in_file,"r")
		lines = infl_utf_8.readlines()
		infl_utf_8.close()
	except UnicodeDecodeError :
		infl_utf_16 = codecs.open(in_file,"r",encoding='utf-16-le')
		lines = infl_utf_16.readlines()
		infl_utf_16.close()

	# tokenize the lines
	for line in range(0, len(lines)) :
		lines[line] = lines[line].split(" ")
		
	
			
	drw_lin = list()
	# pin stuff
	pin_position_xy = []
	pin_justification = []
	pin_name = []
	pin_number = []
	pin_off = []
	
	Name_visibilty = "I"
	Reference_visibility = "I"
	Value = "NULL"
	XY_coords = "0 0"
	Orientation = "H"
	Text_justification = "L"
	Reference = "NULL"
	Reference_XY = "0 100"
	Reference_orientation = "H"
	Reference_justification = "L"
	Description = "NULL"
	SpiceModel = ""

	# read the LTspice .asy file line by line :
	for current_line in lines:
		# reading data

		# by structuring this as a if elif block future conditions aren't checked if one is evaluated to true, leading to time savings when running on large libraries

		# properties/setup
		if current_line[0] == "SYMATTR":
			# parse Reference
			if current_line[1] == "Prefix":
				Reference_visibility = "V"
				Reference = current_line[2][0]
			# parse "Value" (usually the name of the symbol)
			elif current_line[1] == "Value":
				Value = current_line[2]
			elif current_line[1] == "Value2":
				Value = current_line[2]
			# parse Description
			elif current_line[1] == "Description":
				Description = current_line[2]
			# parse Description
			elif current_line[1] == "SpiceModel":
				SpiceModel = current_line[2]
		
		# field text
		elif current_line[0] == "WINDOW":
			# parse 
			if current_line[1] == "0":
				Reference_XY = str(int(SCALE_CONVERSION_FACTOR*int(current_line[2]))) + " " + str(-int(SCALE_CONVERSION_FACTOR*int(current_line[3])))
				Reference_orientation = "H"
				Reference_justification = current_line[4][0]
				if Reference_justification=="V" :
					Reference_orientation = "V"
					Reference_justification = current_line[4][1]
			# parse
			elif current_line[1] == "3":
				XY_coords = str(int(SCALE_CONVERSION_FACTOR*int(current_line[2]))) + " " + str(-int(SCALE_CONVERSION_FACTOR*int(current_line[3])))
				Orientation = "H"
				Name_visibilty = "V"
				Text_justification = current_line[4][0]
				if Text_justification=="V" :
					Orientation = "V"
					Text_justification = current_line[4][1]

		# parsing drawn objects (lines and shapes)

#		P Nb parts convert thickness x0 y0 x1 y1 xi yi cc
#		With:
#		• Nb = a number of points. (2 for a line)
#		• unit = 0 if common to the parts; if not, number of part (1. .n).
#		• convert = 0 if common to the 2 representations, if not 1 or 2.
#		• thickness = line thickness.
#		• xi yi coordinates of end i.
#		• cc = N F or F ( F = filled polygon; f = . filled polygon, N = transparent background)

		# parse lines
		elif current_line[0] == "LINE":
			if len(current_line) == 6 :
				drw_lin.append("P 2 0 0 0 " + str(int(SCALE_CONVERSION_FACTOR*int(current_line[2]))) + " " + str(-int(SCALE_CONVERSION_FACTOR*int(current_line[3]))) + " " + str(int(SCALE_CONVERSION_FACTOR*int(current_line[4]))) + " " + str(-int(SCALE_CONVERSION_FACTOR*int(current_line[5][0:]))))
			

#		S startx starty endx endy unit convert thickness cc
#		With
#		• unit = 0 if common to the parts; if not, number of part (1. .n).
#		• convert = 0 if common to all parts. If not, number of the part (1. .n).
#		• thickness = thickness of the outline.
#		• cc = N F or F ( F = filled Rectangle,; f = . filled Rectangle, N = transparent background)

		# parse rectangles
		elif current_line[0] == "RECTANGLE":
			if len(current_line) == 6 :
				drw_lin.append("S " + str(int(SCALE_CONVERSION_FACTOR*int(current_line[2]))) + " " + str(-int(SCALE_CONVERSION_FACTOR*int(current_line[3]))) + " " + str(int(SCALE_CONVERSION_FACTOR*int(current_line[4]))) + " " + str(-int(SCALE_CONVERSION_FACTOR*int(current_line[5]))) + " 0 0 0 f")
			
# KiCad is incapable of drawing an ellipse, it can only do perfect circles and arcs that are subsectons of a perfect circle
# Since LTspice can draw both ellipses and elliptical arcs, to convert these to KiCad they are approxomated with some math and a long polyline
# Because both circles and ellipses are drawn with the same name in LTspice, even normal circles are drawn with these approximations in KiCad

#   NOTE: this documentation is for the KiCad circle format, what is actually used in this program is the line format above
#		C posx posy radius unit convert thickness cc
#		With
#		• posx posy = circle center position
#		• unit = 0 if common to the parts; if not, number of part (1. .n).
#		• convert = 0 if common to all parts. If not, number of the part (1. .n).
#		• thickness = thickness of the outline.
#		• cc = N F or F ( F = filled circle,; f = . filled circle, N = transparent background)

		# parse circles
		elif current_line[0] == "CIRCLE":
			if len(current_line) == 6 :
				p1 = SCALE_CONVERSION_FACTOR*np.array([
					float(current_line[2]),
					-float(current_line[3])
				])

				p2 = SCALE_CONVERSION_FACTOR*np.array([
					float(current_line[4]),
					-float(current_line[5])
				])
				drw_lin.append(line_arc((p1 + p2) / 2.0, np.abs(p2 - p1), math.pi, -math.pi))

				# old circle output, does not work for ellipses but does use the circle tool, unlike the method used above which approximates it with a polyline
				#drw_lin.append("C " + str(int(0.5*SCALE_CONVERSION_FACTOR*(int(current_line[2]) + int(current_line[4])))) + " " + str(-int(0.5*SCALE_CONVERSION_FACTOR*(int(current_line[3]) + int(current_line[5])))) + " " + str(int(0.5*SCALE_CONVERSION_FACTOR*abs(int(current_line[2]) - int(current_line[4])))) + " 0 0 0 N")
			
#   NOTE: this documentation is for the KiCad arc format, what is actually used in this program is the line format above
#		A posx posy radius start end part convert thickness cc start_pointX start_pointY end_pointX end_pointY.
#		With:
#		• posx posy = arc center position
#		• start = angle of the starting point (in 0,1 degrees).
#		• end = angle of the end point (in 0,1 degrees).
#		• unit = 0 if common to all parts; if not, number of the part (1. .n).
#		• convert = 0 if common to the representations, if not 1 or 2.
#		• thickness = thickness of the outline or 0 to use the default line thickness.
#		• cc = N F or F ( F = filled arc,; f = . filled arc, N = transparent background)
#		• start_pointX start_pointY = coordinate of the starting point (role similar to start)

		# parse arc
		elif current_line[0] == "ARC":
			#
			p1 = SCALE_CONVERSION_FACTOR*np.array([
				float(current_line[2]),
				-float(current_line[3])
			])

			p2 = SCALE_CONVERSION_FACTOR*np.array([
				float(current_line[4]),
				-float(current_line[5])
			])

			center = (p1 + p2)/2.0

			size = np.abs((p2-p1))

			p3 = SCALE_CONVERSION_FACTOR*np.array([
				float(current_line[6]),
				-float(current_line[7])
			])

			p4 = SCALE_CONVERSION_FACTOR*np.array([
				float(current_line[8]),
				-float(current_line[9])
			])


			angle1 = get_angle(p4 - center)
			angle2 = get_angle(p3 - center)
			drw_lin.append(line_arc(center, size, angle1, angle2))


#   NOTE: This doccumentation is out of date, more fields were found through testing
#		T orientation posx posy dimension unit convert Text **type** **bold** **horizontal_justification** **vertical_justification** 
#		With:
#		• orientation = horizontal orientation (=0) or vertical (=1).
#		• type = always 0.
#		• unit = 0 if common to the parts. If not, the number of the part (1. .n).
#		• convert = 0 if common to the representations, if not 1 or 2.

#		Following the Text field are another 4 fields that aren't in the documentation. Through testing they were found to be:
#		• type = "Normal" or "Italic"
#		• bold = 0 for not bold or 1 for bold
# 		• horizontal_justification = "L" for left, "C for center" or "R" for right
# 		• vertical_justification = "T" for top, "C for center" or "B" for bottom


		#parse text
		elif current_line[0] == "TEXT":
			text_justif_LR = "C "
			text_justif_TB = "C"

			if current_line[3][0] == "V": # V for Vertical
				text_orientation = "900 "
				# if vertical, the justification has an extra V in front so we want the second character
				if current_line[3][1] == "L" or current_line[3][1] == "R" :
					text_justif_LR = current_line[3][1] + " "
				elif current_line[3][1] == "T" or current_line[3][1] == "B" :
					text_justif_TB = current_line[3][1]
			
			else :
				text_orientation = "0 "
				# since it's horizontal we don't need to worry about the second character and just take the first
				if current_line[3][0] == "L" or current_line[3][0] == "R" :
					text_justif_LR = current_line[3][0] + " "
				elif current_line[3][0] == "T" or current_line[3][0] == "B" :
					text_justif_TB = current_line[3][0]

			# NOTE: while KiCad can do italics and bold text, LTspice cannot so we can just hard coode the values as "Normal" and "0"
			drw_lin.append("T " + text_orientation + str(int(SCALE_CONVERSION_FACTOR*int(current_line[1]))) + " " + str(-int(SCALE_CONVERSION_FACTOR*int(current_line[2]))) + " 50 0 0 1 \"" + " ".join(current_line[5:])[:-1] + "\" Normal 0 " + text_justif_LR + text_justif_TB) # remove the last character of the text to deal with newlines 


#		X name number posx posy length orientation Snum Snom unit convert Etype [shape].
#		With:
#		• orientation = U (up) D (down) R (right) L (left).
#		• name = name (without space) of the pin. if ~: no name
#		• number = n pin number (4 characters maximum).
#		• length = pin length.
#		• Snum = pin number text size.
#		• Snom = pin name text size.
#		• unit = 0 if common to all parts. If not, number of the part (1. .n).
#		• convert = 0 if common to the representations, if not 1 or 2.
#		• Etype = electric type (1 character)
#		• shape = if present: pin shape (clock, inversion…).

		# parse pins
		elif current_line[0] == "PIN":
			pin_position_xy.append(str(int(SCALE_CONVERSION_FACTOR*int(current_line[1]))) + " " + str(-int(SCALE_CONVERSION_FACTOR*int(current_line[2]))))
			pin_off.append(str(int(SCALE_CONVERSION_FACTOR*int(current_line[4]))))
			
			# the pin orientations in LTspice are TOP/BOTTOM/LEFT/RIGHT and vertical or horizontal
			# if vertical it's VTOP/VBOTTOM/VLEFT/VRIGHT so we want the second character
			if current_line[3][0] == "V":
				pin_justification.append(current_line[3][1])
			else:
				pin_justification.append(current_line[3][0])


		elif current_line[0] == "PINATTR":
			#pin name
			if current_line[1] == "PinName":
				pin_name.append(" ".join(current_line[2:]).rstrip(" \n\r"))

			#pin number
			if current_line[1] == "SpiceOrder":
				pin_number.append(current_line[2].rstrip(" \n\r"))
				#since in the .asy files pin number is the line after pin name if we have a longer pin_number array that means that there is no pin name for the pin -  so we fill the spot with a ~ following KiCad's formatting
				if len(pin_name) < len(pin_number) :
					pin_name.append("~")
					






	#------------------------------------------------------------------------ output the data in Kicad format -----------------------------------------------------------------------





	outfl.write("#   " + component[0:len(component)-4] + "\n")
	if Description != "":
		outfl.write("# " + Description + "\n")
	if SpiceModel != "":
		outfl.write("# SpiceModel : " + SpiceModel + "\n")
	outfl.write("#\n")


	# Properties

#	DEF name reference unused text_offset draw_pinnumber draw_pinname unit_count units_locked Option_flag
#	• name = component name in library (74LS02 ...)
#	• reference = Reference ( U, R, IC .., which become U3, U8, R1, R45, IC4...)
#	• unused = 0 (reserved)
#	• text_offset = offset for pin name position
#	• draw_pinnumber = Y (display pin number) or N (do not display pin number).
#	• draw_pinname = Y (display pin name) or N (do not display pin name).
#	• unit_count = Number of part ( or section) in a component package.
#	• units_locked = = L (units are not identical and cannot be swapped) or F (units are identical and therefore can be swapped) (Used only if unit_count > 1)
#	• Option_flag = N (normal) or P (component type "power")

	outfl.write("DEF "+ component[0:len(component)-4].replace(" ", "_") + " " + Reference + " 0 40 N Y 1 F N" + "\n")

	# Fields

#	F n “text” posx posy dimension orientation visibility hjustify vjustify/italic/bold “name” with:
#	• n = field number :
#		• reference = 0.
#		• value = 1.
#		• Pcb FootPrint = 2.
#		• User doc link = 3. At present time: not used
#	• n = 4..11 = fields 1 to 8 (since January 2009 more than 8 field allowed, so n can be > 11.
#	• text (delimited by double quotes)
#	• position X and Y
#	• dimension (default = 50)
#	• orientation = H (horizontal) or V (vertical).
#	• Visibility = V (visible) or I (invisible)
#	• hjustify vjustify = L R C B or T
#		• L= left
#		• R = Right
#		• C = centre
#		• B = bottom
#		• T = Top
#	• Style: Italic = I or N (since January 2009)
#	• Style Bold = B or N (since January 2009)
#	• Name of the field (delimited by double quotes) (only if it is not the default name)

	# F0 is the name of the schematic, first property field in KiCad editor

	if ((Reference_justification == "B") or (Reference_justification == "T")):
		outfl.write("F0 \"" + Reference + "\" " + Reference_XY + " 50 " + Reference_orientation + " " + Reference_visibility + " C " + Reference_justification + "NN\n")
	else :
		outfl.write("F0 \"" + Reference + "\" " + Reference_XY + " 50 " + Reference_orientation + " " + Reference_visibility + " " + Reference_justification + " C " + "CNN\n")
	
	# F1 is value, second property field in KiCad editor, default component name
	if ((Text_justification == "B") or (Text_justification == "T")):
		outfl.write("F1 \"" + component[0:len(component)-4] + "\" " + XY_coords + " 50 " + Orientation + " " + Name_visibilty + " C " + Text_justification + "NN\n")
	else :
		outfl.write("F1 \"" + component[0:len(component)-4] + "\" " + XY_coords + " 50 " + Orientation + " " + Name_visibilty + " " + Text_justification + " C " + "CNN\n")
	
	# the value is transferd to F5 instead of F1 because F1 text should be the component name 
	if Value != "" :
		if ((Text_justification == "B") or (Text_justification == "T")):
			outfl.write("F5 \"" + Value + "\" " + XY_coords + " 50 " + Orientation + " I C " + Text_justification + "NN\n")
		#else :
		#	outfl.write("F5 \"" + Value + "\" " + XY_coords + " 50 " + Orientation + " I " + Text_justification + " CNN\n")
		
	outfl.write("$FPLIST\n " + Reference + "_*\n$ENDFPLIST\n")
	
	#DRAWINGS and PINS
	outfl.write("DRAW\n")
	for i in range(0,len(drw_lin)) :
		outfl.write(drw_lin[i] + "\n")

	# Pins

#	X name number posx posy length orientation Snum Snom unit convert Etype [shape].
#	With:
#	• orientation = U (up) D (down) R (right) L (left).
#	• name = name (without space) of the pin. if ~: no name
#	• number = n pin number (4 characters maximum).
#	• length = pin length.
#	• Snum = pin number text size.
#	• Snom = pin name text size.
#	• unit = 0 if common to all parts. If not, number of the part (1. .n).
#	• convert = 0 if common to the representations, if not 1 or 2.
#	• Etype = electric type (1 character)
#	• shape = if present: pin shape (clock, inversion…).
	for i in range(0,len(pin_number)) :
		pinjustif = pin_justification[i]
		if pin_justification[i] == "L" : pinjustif = "R"
		elif pin_justification[i] == "R" : pinjustif = "L"
		elif pin_justification[i] == "T" : pinjustif = "D"
		elif pin_justification[i] == "B" : pinjustif = "U"
		elif pin_justification[i] == "N" : pinjustif = "L" # sometimes the .asy files will have "NONE" as the pin justification, in this case just use left justification since size is zero

		outfl.write("X " + pin_name[i].replace(" ", "_") + " " + pin_number[i] + " " + pin_position_xy[i] + " 0 " + pinjustif + " 50 50 1 0 U\n")

	outfl.write("ENDDRAW\nENDDEF\n#\n")

outfl.close()