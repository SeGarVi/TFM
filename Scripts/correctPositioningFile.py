#    Copyright (C) 2015 Sergio García Villalonga (yayalose@gmail.com)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

#!/usr/bin/python3
import sys

def correct_log(path, env='log'):
	f = open(path, 'r')
	
	line = f.readline()
	out = open(path + ".correct", 'w')
	previous_t = '0'
	while line != "":
		components = line.rsplit()
		
		if components[0] != previous_t :
			out.write("# Timestamp, X, Y, MAC Address of AP, RSS\n");
		out.write(line);
		previous_t = components[0]
		line = f.readline()
	
	f.close()

def main(file_path):
	correct_log(file_path)

def print_use_message():
	print("Quantitat errònia de paràmetres.\n")
	print("Ús:\n")
	print("\t ./rsslog2csv.py <path al fitxer de log RSS>")

if __name__ == "__main__":
	if len(sys.argv) != 2 :
		print_use_message()
	else:
		main(sys.argv[1])
	
