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
import math
from PIL import Image, ImageDraw, ImageFont
import random
import matplotlib.pyplot as plt
import os
from datetime import datetime
from multiprocessing import Pool

def extract_data(path, env='log'):
	print("Extracting " + env  + " data")

	log_path = path + "/" + env + "/rss-log-glories"
	if env == 'log':
		prefix = 'P'
	elif env == 'test':
		prefix = 'PT'
	elif env == 'test-buit':
		prefix = 'PTB'
	elif env == 'test-ple':
		prefix = 'PTP'
		
	f = open(log_path)
	
	line = f.readline()
	places_dict = dict()
	min_strength = 0
	max_strength = -200
	while line != "":
		components = line.rsplit()
		
		if int(components[4]) < min_strength:
			min_strength = int(components[4])

		if int(components[4]) > max_strength:
			max_strength = int(components[4])
		
		value = [ int(components[0])/1000, components[4] ]
		if (components[1], components[2]) not in places_dict.keys():
			places_dict[(components[1], components[2])] = dict()
		if components[3] not in  places_dict[(components[1], components[2])].keys():
			places_dict[(components[1], components[2])][components[3]] = []
		places_dict[(components[1], components[2])][components[3]].append(value)
		line = f.readline()
	
	f.close()

	keys = [key for key in places_dict.keys()]
	
	count = 0
	point_dict = dict()
	moment_dict = dict()
	for point in keys:
		if count < 10:
			point_dict[(point[0], point[1])] = prefix + '0' + str(count)
		else :
			point_dict[(point[0], point[1])] = prefix + str(count)
		
		minimum = 1420070400
		current = 1420070400
		for mac in places_dict[point]:
			current = int(min(places_dict[point][mac])[0])
			if current < minimum:
				minimum = current
	 	
		data = datetime.fromtimestamp(minimum)
		key = (data.day, data.month, data.year)
		hora = data.ctime().split()[3]
		
		if key not in moment_dict:
			moment_dict[key] = []
		moment_dict [key].append([components[0], hora, point_dict[(point[0], point[1])], (point[0], point[1])])
		
		count += 1


	print("Done extracting " + env  + " data")
	return (places_dict, point_dict, moment_dict, min_strength, max_strength)

def generate_csv(places_dict, point_dict, report_path, env='log'):
	print("Generating " + env  + " signal strengh CSV files")
	
	csv_path = report_path + "/rss_values/" + env
	
	if not os.path.exists(csv_path):
		print("\tDirectory " + csv_path + " does not exist, creating...")
		os.makedirs(csv_path)
	
	count = 0
	for loc in places_dict:
		out = open(csv_path + "/" + point_dict[loc] + ".csv", 'w')
		out.write('\n\n')
		out.write(str(loc))
		out.write('\n\n')
		for mac in places_dict[loc]:
			out.write('\n')
			out.write(mac)
			out.write('\n')
			init = int(min(places_dict[loc][mac])[0])
			data =  places_dict[loc][mac]
			data.sort()
			for timestamp, signal in data:
				interval = int(timestamp) - init
				out.write(str(interval) + '$' + signal)
				out.write('\n')
		out.close()
		count += 1
	print("Done generating " + env  + " signal strengh CSV files")

def generate_distances_matrix(places_dict, point_dict, report_path, env='log'):
	print("Generating " + env  + " distance matrix CSV files")
	
	distances_path = report_path + "/distancies/" + env
	
	if not os.path.exists(distances_path):
		print("\tDirectory " + distances_path + " does not exist, creating...")
		os.makedirs(distances_path)
	
	matrix=[]
	i = 0

	matrix = [[calculate_distance(p1, p2) for p2 in places_dict.keys()] for p1 in places_dict.keys()]
	
	out = open(distances_path + "/" + "distances.csv", 'w')
	
	keys = [key for key in places_dict.keys()]
	
	out.write('Punt$Coordenades\n')
	for coordenades in point_dict.keys():
		out.write(point_dict[coordenades] + '$' + str(coordenades) + '\n')
	out.write('\n')

	out.write('$')
	for point in keys:
		out.write(point_dict[(point[0], point[1])] + '$')
	
	out.write('$Min')
	out.write('\n')
	maxima = 0
	minimum_acum = 0
	for row in matrix:
		out.write(point_dict[(keys[matrix.index(row)][0], keys[matrix.index(row)][1])] + '$')
		for col in row:
			out.write(str(col) + '$')
		row_norm = row
		row_norm.remove(0.0)
		minimum = min(row_norm)
		minimum_acum += minimum
		if minimum > maxima:
			maxima = minimum
		out.write('$' + str(minimum))
		out.write('\n')
	out.write('\n')
	out.write('$' * (len(keys)+1))
	mitjana = minimum_acum/float(len(keys))
	out.write('Mitjana$' + str(mitjana))
	out.close()
	print("Done generating " + env  + " distance matrix CSV files")
	return (point_dict, mitjana, maxima)

def generate_summary(report_path, point_dict, moment_dict, minima, maxima, env='log'):
	print("Generating summary for " + env)
	filename = report_path + "/resum.txt"	

	if not os.path.exists(filename):
		out = open(filename, 'w')
	else:
		out = open(filename, 'a')
		out.write("\n\n")

	if env == 'log':
		out.write("INFORME DE PRESA DE DADES\n")
		out.write("-------------------------\n")
	
	out.write("\n" + env + ":\n")
	out.write("Nombre de punts: " + str(len(point_dict)) + "\n")
	out.write("Distància mínima mitjana entre punts: " + str(minima) + "\n")
	out.write("Distancia mínima màxima entre punts: " + str(maxima) + "\n\n")
	out.write("Diari de la presa: " + str(maxima) + "\n\n")

	for data in sorted(moment_dict.keys()):
		out.write("\tDia " + str(data[0]) + " de " + str(data[1]) + " de " + str(data[2]) + ", ")
		out.write("des de les " + min(moment_dict[data])[1])
		out.write(" fins les " + max(moment_dict[data])[1] + "\n\t\t")
		for point in moment_dict[data]:
			out.write(point[2] + ", ")
		out.write("\n\n")
	out.write("\n")

	

def draw_points_in_map(plan_path, plan_settings_path, point_dict, report_path, env='log'):
	print("Drawing " + env  + " points in map")
	
	point_plan_path = report_path + "/planol/" + env
	if env == 'test':
		rss_plan_path = report_path + "/planol/log"
	if env == 'test-ple':
		rss_plan_path = report_path + "/planol/test-buit" 
	
	if not os.path.exists(point_plan_path):
		print("\tDirectory " + point_plan_path + " does not exist, creating...")
		os.makedirs(point_plan_path)

	path_components = plan_path.split("/")
	basename = path_components[len(path_components) - 1 ]
	
	save_path = point_plan_path + "/" + basename

	radi = 5
	text_size = 20;
	im = Image.open(plan_path)
	dimensions = load_actual_dimensions(plan_settings_path)
	draw = ImageDraw.Draw(im)

	if env == 'test' or env == 'test-ple':
		im_over   = Image.open(rss_plan_path + "/" + basename)
		draw_over = ImageDraw.Draw(im_over)

	x = 20
	y = 20

	scale_x = im.size[0] / dimensions['width']
	scale_y = im.size[1] / dimensions['height']
	
	if env == 'log':
		color =(0,0,0)
	elif env == 'test':
		color = (255, 50, 50)
	elif env == 'test-buit':
		color = (30, 35, 255)
	elif env == 'test-ple':
		color = (108, 114, 0)

	for (x, y) in point_dict:
		bbox =  (float(x)*scale_x - radi/2, float(y)*scale_y - radi/2, float(x)*scale_x + radi/2, float(y)*scale_y + radi/2)
		text = point_dict[(x, y)]
		font = ImageFont.truetype("DroidSans-Bold.ttf", text_size)
		
		if (float(x)*scale_x + radi + 5 + text_size * 3) > im.size[0] :
			text_pos = (float(x)*scale_x + radi - 5 - text_size * 2.3 , float(y)*scale_y - text_size/2 - radi/2)
		else:
			text_pos = (float(x)*scale_x + radi + 5 , float(y)*scale_y - text_size/2 - radi/2)
		draw.ellipse(bbox, fill=color)
		draw.text(text_pos, text, fill=color, font=font)

		if env == 'test' or env == 'test-ple':
			draw_over.ellipse(bbox, fill=color)
			draw_over.text(text_pos, text, fill=color, font=font)

	
	im.save(save_path, "PNG")

	if env == 'test':
		im_over.save(report_path + "/" + basename, "PNG")
	elif env == 'test-ple':
		im_over.save(report_path + "/test_" + basename, "PNG")
	
	print("Finished drawing " + env  + " points in map")

def draw_points_in_map_per_day(plan_path, plan_settings_path, point_dict, moments_dict, report_path, env='log'):
	print("Drawing " + env  + " points in map")
	
	per_day_point_plan_path = report_path + "/planol/" + env + "/per_day"
	incremental_point_plan_path = report_path + "/planol/" + env +"/incremental"
	
	if not os.path.exists(per_day_point_plan_path) :
		print("\tDirectory " + per_day_point_plan_path + " does not exist, creating...")
		os.makedirs(per_day_point_plan_path)
	
	if not os.path.exists(incremental_point_plan_path) :
		print("\tDirectory " + incremental_point_plan_path + " does not exist, creating...")
		os.makedirs(incremental_point_plan_path)

	path_components = plan_path.split("/")
	basename = path_components[len(path_components) - 1 ]
	
	radi = 5
	text_size = 20;
	dimensions = load_actual_dimensions(plan_settings_path)

	x = 20
	y = 20

	im = Image.open(plan_path)
	scale_x = im.size[0] / dimensions['width']
	scale_y = im.size[1] / dimensions['height']
	
	if env == 'log':
		color =(0,0,0)
	elif env == 'test':
		color = (255, 50, 50)
	elif env == 'test-buit':
		color = (232, 117, 202)
	elif env == 'test-ple':
		color = (202, 213, 0)

	acum_path = plan_path
	for (day, month, year) in sorted(moments_dict):
		im = Image.open(plan_path)
		draw = ImageDraw.Draw(im)
		
		acum_im = Image.open(acum_path)
		acum_draw = ImageDraw.Draw(acum_im)
		
		for loc in moments_dict[(day, month, year)]:
			(x, y) = loc[3]
			bbox =  (float(x)*scale_x - radi/2, float(y)*scale_y - radi/2, float(x)*scale_x + radi/2, float(y)*scale_y + radi/2)
			text = loc[2]
			font = ImageFont.truetype("DroidSans-Bold.ttf", text_size)
		
			if (float(loc[0])*scale_x + radi + 5 + text_size * 3) > im.size[0] :
				text_pos = (float(x)*scale_x + radi - 5 - text_size * 2.3 , float(y)*scale_y - text_size/2 - radi/2)
			else:
				text_pos = (float(x)*scale_x + radi + 5 , float(y)*scale_y - text_size/2 - radi/2)
			draw.ellipse(bbox, fill=color)
			draw.text(text_pos, text, fill=color, font=font)
			acum_draw.ellipse(bbox, fill=color)
			acum_draw.text(text_pos, text, fill=color, font=font)

		im.save(per_day_point_plan_path + "/" + str(day) + "-" + str(month) + "-" + str(year) + ".png", "PNG")
		acum_im.save(incremental_point_plan_path + "/" + str(day) + "-" + str(month) + "-" + str(year) +".png", "PNG")
		acum_path = incremental_point_plan_path + "/" + str(day) + "-" + str(month) + "-" + str(year) + ".png";
 
	print("Finished drawing " + env  + " points in map")

def create_rss_plots(parameters):
	(places_dict, point_dict, report_path, min_strength, max_strength, env) = parameters
	print("Creating " + env  + " rss plots")
	
	rss_plots_path = report_path + "/plots/" + env
	
	if not os.path.exists(rss_plots_path):
		print("\tDirectory " + rss_plots_path + " does not exist, creating...")
		os.makedirs(rss_plots_path)

	for loc in places_dict:
		loc_path = rss_plots_path + "/" + point_dict[loc]
		if not os.path.exists(loc_path):
			print("\t\tDirectory " + loc_path + " does not exist, creating...")
			os.makedirs(loc_path)

		for mac in places_dict[loc]:
			plt.figure()
			init = int(min(places_dict[loc][mac])[0])
			x_series = [(int(data[0]) - init)/1000 for data in places_dict[loc][mac]]
			y_series = [int(data[1]) for data in places_dict[loc][mac]]
			plt.title("Potència del senyal al punt " + point_dict[loc] + " emissor " + mac)
			plt.xlabel("Instant")
			plt.ylabel("Potència (dbm)")
			plt.ylim(min_strength, max_strength)
			plt.plot(x_series, y_series)
			plt.savefig(loc_path + "/" + mac + ".png")
			plt.close()
		
	print("Done creating " + env  + " rss plots")

def load_actual_dimensions(plan_settings_path):
	dimensions = dict()
	f = open(plan_settings_path)
	
	line = f.readline()
	dimensions['width'] = float(line.rsplit()[1])
	line = f.readline()
	dimensions['height'] = float(line.rsplit()[1])
	return dimensions

def calculate_distance(p1, p2):
	dx = float(p1[0]) - float(p2[0])
	dy = float(p1[1]) - float(p2[1])
	return math.sqrt((dx**2)+(dy**2))

def main(root, report = ''):
	rsslog_path = root + 'rsslogs'
	testlog_path = root + 'testlogs'
	plan_path = root + 'plans/planoGlories.png'
	plan_settings_path = root + 'plans/planoGlories.config'
	
	if report == '':
		reports_path = root + "/analisi"
	else:
		reports_path = report

	if not os.path.exists(reports_path):
		print("\tDirectory " + reports_path + " does not exist, creating...")
		os.makedirs(reports_path)

	(places_dict_log, point_dict_log, moment_dict_log, min_strength_log, max_strength_log) = extract_data(rsslog_path)
	generate_csv(places_dict_log, point_dict_log, reports_path)
	(point_dict_log, minima_log, maxima_log) = generate_distances_matrix(places_dict_log, point_dict_log, reports_path)
	generate_summary(reports_path, point_dict_log, moment_dict_log, minima_log, maxima_log)
	draw_points_in_map(plan_path, plan_settings_path, point_dict_log, reports_path)
	draw_points_in_map_per_day(plan_path, plan_settings_path, point_dict_log, moment_dict_log, reports_path)
	#create_rss_plots((places_dict_log, point_dict_log, reports_path, min_strength_log, max_strength_log, 'log'))

	(places_dict_test, point_dict_test, moment_dict_test, min_strength_test, max_strength_test) = extract_data(rsslog_path, 'test')
	generate_csv(places_dict_test, point_dict_test, reports_path, 'test')
	(point_dict_test, minima_test, maxima_test) = generate_distances_matrix(places_dict_test, point_dict_test, reports_path, 'test')
	generate_summary(reports_path, point_dict_test, moment_dict_test, minima_test, maxima_test, 'test')
	draw_points_in_map(plan_path, plan_settings_path, point_dict_test, reports_path, 'test')
	draw_points_in_map_per_day(plan_path, plan_settings_path, point_dict_test, moment_dict_test, reports_path, 'test')
	#create_rss_plots(places_dict_test, point_dict_test, reports_path, min_strength_test, max_strength_test, 'test')
	
	(places_dict_buit, point_dict_buit, moment_dict_buit, min_strength_buit, max_strength_buit) = extract_data(testlog_path, 'test-buit')
	generate_csv(places_dict_buit, point_dict_buit, reports_path, 'test-buit')
	(point_dict_buit, minima_buit, maxima_buit) = generate_distances_matrix(places_dict_buit, point_dict_buit, reports_path, 'test-buit')
	generate_summary(reports_path, point_dict_buit, moment_dict_buit, minima_buit, maxima_buit, 'test-buit')
	draw_points_in_map(plan_path, plan_settings_path, point_dict_buit, reports_path, 'test-buit')
	draw_points_in_map_per_day(plan_path, plan_settings_path, point_dict_buit, moment_dict_buit, reports_path, 'test-buit')
	#create_rss_plots(places_dict_buit, point_dict_buit, reports_path, min_strength_buit, max_strength_buit, 'test-buit')
	
	(places_dict_ple, point_dict_ple, moment_dict_ple, min_strength_ple, max_strength_ple) = extract_data(testlog_path, 'test-ple')
	generate_csv(places_dict_ple, point_dict_ple, reports_path, 'test-ple')
	(point_dict_ple, minima_ple, maxima_ple) = generate_distances_matrix(places_dict_ple, point_dict_ple, reports_path, 'test-ple')
	generate_summary(reports_path, point_dict_ple, moment_dict_ple, minima_ple, maxima_ple, 'test-ple')
	draw_points_in_map(plan_path, plan_settings_path, point_dict_ple, reports_path, 'test-ple')
	draw_points_in_map_per_day(plan_path, plan_settings_path, point_dict_ple, moment_dict_ple, reports_path, 'test-ple')
	#create_rss_plots(places_dict_ple, point_dict_ple, reports_path, min_strength_ple, max_strength_ple, 'test-ple')
	
	p = Pool(4)
	p.map(create_rss_plots, [(places_dict_log, point_dict_log, reports_path, min_strength_log, max_strength_log, 'log'), (places_dict_test, point_dict_test, reports_path, min_strength_test, max_strength_test, 'test'), (places_dict_buit, point_dict_buit, reports_path, min_strength_buit, max_strength_buit, 'test-buit'), (places_dict_ple, point_dict_ple, reports_path, min_strength_ple, max_strength_ple, 'test-ple')])

def print_use_message():
	print("Quantitat errònia de paràmetres.\n")
	print("Ús:\n")
	print("\t ./rsslog2csv.py <path al fitxer de log RSS> [<path al directori de resultats>]")

if __name__ == "__main__":
	if len(sys.argv) < 2 or len(sys.argv) > 3:
		print_use_message()
	else:
		if len(sys.argv) == 3:
			main(sys.argv[1], sys.argv[2])
		else:
			main(sys.argv[1])
	
