#!/usr/bin/python3
import sys
import math
from PIL import Image, ImageDraw, ImageFont
import os
from os import listdir
from os.path import isfile, join
import statistics

def extract_data(path, env='buit'):
	print("Extracting " + env  + " data")

	estimations_dir = path + "/" + env
	
	files = [ f for f in listdir(estimations_dir) if isfile(join(estimations_dir,f)) ]
	
	estimations_dict = dict()
	for file_name in files:
		file_path = estimations_dir + "/" + file_name
		f = open(file_path)
	
		#Skip path of the test file
		line = f.readline().replace("\n", "")
		#Skip algrithm ID
		line = f.readline().replace("\n", "")
		#Algorithm name
		algorithm = f.readline().replace("\n", "")
		#Algorithm parameter
		algorithm_settings = f.readline().replace("\n", "")
		#Skip pre-data header
		line = f.readline().replace("\n", "")
		
		if algorithm not in estimations_dict:
			estimations_dict[algorithm] = dict()
	
		if algorithm_settings not in estimations_dict[algorithm]:
			print("\tAnalyzing data for " + algorithm + " algorithm with parameter " + algorithm_settings)
			line = f.readline().replace("\n", "")
			
			point_info = dict()
			while line != "":
				[point_number, real_x, real_y, est_x, est_y, error] = line.rsplit()
				
				real_point = (float(real_x), float(real_y))
				
				if real_point not in point_info:
					point_info[real_point] = dict()
					point_info[real_point]['id'] = point_number
					point_info[real_point]['calcx'] = []
					point_info[real_point]['calcy'] = []
					point_info[real_point]['calcerror'] = []
				
				point_info[real_point]['calcx'].append(float(est_x))
				point_info[real_point]['calcy'].append(float(est_y))
				point_info[real_point]['calcerror'].append(float(error))
				line = f.readline().replace("\n", "")
		
			estimations_dict[algorithm][algorithm_settings] = point_info
	
	print("Done extracting " + env  + " data")
	return estimations_dict



def calculate_statistics(estimations_dict, env='buit'):
	print("Calculating " + env  + " statistics")
	for algorithm in estimations_dict:
		for algorithm_settings in estimations_dict[algorithm]:
			for real_point in estimations_dict[algorithm][algorithm_settings]:
				calcx = estimations_dict[algorithm][algorithm_settings][real_point]['calcx']
				calcy = estimations_dict[algorithm][algorithm_settings][real_point]['calcy']
				
				#Mean estimated point
				p_mitja_x = statistics.mean(calcx)
				p_mitja_y = statistics.mean(calcy)
				estimations_dict[algorithm][algorithm_settings][real_point]['calc_mitja'] = [p_mitja_x, p_mitja_y]
				
				#Mean individual error
				m_ind_error = statistics.mean(estimations_dict[algorithm][algorithm_settings][real_point]['calcerror'])
				estimations_dict[algorithm][algorithm_settings][real_point]['error_ind_mitja'] = m_ind_error
				
				#Error to mean estimated point
				m_point_error = distance(real_point, [p_mitja_x, p_mitja_y])
				estimations_dict[algorithm][algorithm_settings][real_point]['error_punt_mitja'] = m_ind_error
				
				#Mean deviation (from individual estimated points o mean estimated points
				est_deviations = [distance([p_mitja_x, p_mitja_y], [calcx[i], calcy[i]]) for i in range(len(calcx))]
				mean_deviation = statistics.mean(est_deviations)
				estimations_dict[algorithm][algorithm_settings][real_point]['desviacio_mitjana'] = m_ind_error
	
	print("Done calculating " + env  + " statistics")
	return estimations_dict



def create_summaries(reports_path, original_plan_path, plan_settings_path, estimations_dict, env='buit'):
	print("Creating " + env  + " summaries")
	est_path = reports_path + '/estimations'
	if not os.path.exists(est_path):
		print("\tDirectory " + est_path + " does not exist, creating...")
		os.makedirs(est_path)
	
	save_path = est_path + "/" + env
	if not os.path.exists(save_path):
		print("\tDirectory " + save_path + " does not exist, creating...")
		os.makedirs(save_path)
	
	out = open(save_path + "/resum.txt", 'w')
	out.write("Resum de l'anàlisi de les proves en un entorn " + env + "\n")
	out.write("---------------------------------------------------\n\n")
	for algorithm in estimations_dict:
		out.write("Algorisme: " + algorithm + "\n")
		
		alg_path = save_path + "/" + algorithm
		if not os.path.exists(alg_path):
			print("\tDirectory " + alg_path + " does not exist, creating...")
			os.makedirs(alg_path)
		
		for algorithm_settings in estimations_dict[algorithm]:
			out.write("\tValor del paràmetre principal de l'algorisme: " + algorithm_settings + "\n")
			
			plan_path = alg_path + "/" + algorithm_settings + ".png"
			draw_points_in_map(original_plan_path, plan_settings_path, plan_path, estimations_dict[algorithm][algorithm_settings])
			
			error_mitja = 0.0
			m_desviacio_mitjana = 0.0
			for point in estimations_dict[algorithm][algorithm_settings]:
				error_mitja += estimations_dict[algorithm][algorithm_settings][point]['error_ind_mitja']
				m_desviacio_mitjana += estimations_dict[algorithm][algorithm_settings][point]['desviacio_mitjana']
			
			error_mitja /= len(estimations_dict[algorithm][algorithm_settings])
			m_desviacio_mitjana /= len(estimations_dict[algorithm][algorithm_settings])
			
			out.write("\t\tMitja de l'error de les estimacions: " + str(error_mitja) + "\n")
			out.write("\t\tMitja de la desviació mitjana de les estimacions: " + str(m_desviacio_mitjana) + "\n\n")
		
		out.write("\n\n")
	out.close()
	print("Done creating " + env  + " summaries")



def draw_points_in_map(original_plan_path, plan_settings_path, plan_path, point_dict):
	print("Drawing points in map")
	
	radi = 5
	text_size = 20;
	color_punt = (0,0,0)
	color_est  = (255,0,0)
	color_disk = (255,0,0)
	color_rad  = (255,128,128)
	color_bord = (255,0,0)
	
	im = Image.open(original_plan_path)
	dimensions = load_actual_dimensions(plan_settings_path)
	draw = ImageDraw.Draw(im)
	
	scale_x = im.size[0] / dimensions['width']
	scale_y = im.size[1] / dimensions['height']
	
	for point in point_dict:
		estimated = point_dict[point]['calc_mitja']
		radi_rad  = point_dict[point]['desviacio_mitjana'] * scale_x
		radi_disk = point_dict[point]['desviacio_mitjana'] * scale_x + 4
		
		x = point[0] * scale_x
		y = point[1] * scale_y
		
		est_x = estimated[0] * scale_x
		est_y = estimated[1] * scale_y
		
		#Draw radar disk and circle
		bbox = (est_x - radi_disk/2, est_y - radi_disk/2, est_x + radi_disk/2, est_y + radi_disk/2)
		draw.ellipse(bbox, fill=color_disk)
		bbox = (est_x - radi_rad/2, est_y - radi_rad/2, est_x + radi_rad/2, est_y + radi_rad/2)
		draw.ellipse(bbox, fill=color_rad)
		
		#Draw actual point
		bbox = (x - radi/2, y - radi/2, x + radi/2, y + radi/2)
		draw.ellipse(bbox, fill=color_punt)
		
		#Draw estimated point
		bbox = (est_x - radi/2, est_y - radi/2, est_x + radi/2, est_y + radi/2)
		draw.ellipse(bbox, fill=color_est)
		
		#Draw line to relate points
		draw.line((x, y, est_x, est_y), fill=(255, 255, 0))
		
	
	im.save(plan_path, "PNG")
	print("Finished drawing points in map")

def load_actual_dimensions(plan_settings_path):
	dimensions = dict()
	f = open(plan_settings_path)
	
	line = f.readline()
	dimensions['width'] = float(line.rsplit()[1])
	line = f.readline()
	dimensions['height'] = float(line.rsplit()[1])
	return dimensions

def distance(p1, p2) :
	return math.sqrt((p1[0] - p2[0])**2+(p1[1] - p2[1])**2)



def main(root, report = ''):
	estimations_path = root + "/estimations"
	original_plan_path = root + '/plans/planoGlories.png'
	plan_settings_path = root + '/plans/planoGlories.config'
	
	if report == '':
		reports_path = root + "/analisi"
	else:
		reports_path = report

	if not os.path.exists(reports_path):
		print("\tDirectory " + reports_path + " does not exist, creating...")
		os.makedirs(reports_path)

	estimations_dict = extract_data(estimations_path)
	estimations_dict = calculate_statistics(estimations_dict)
	create_summaries(reports_path, original_plan_path, plan_settings_path, estimations_dict)
	
	#estimations_dict = extract_data(estimations_path, 'ple')
	#estimations_dict = calculate_statistics(estimations_dict, 'ple')
	#create_summaries(reports_path, original_plan_path, plan_settings_path, estimations_dict, 'ple')


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
	
