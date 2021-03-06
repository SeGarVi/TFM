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
import os
from os import listdir
from os.path import isfile, join
import statistics


tenda = set([1, 4, 7, 10, 11, 13, 14, 16, 17, 18, 19, 20, 22, 23, 25, 26, 28, 33, 40, 41, 42, 43, 47, 52, 57, 59, 61, 66, 67, 68, 73, 74, 75, 78, 84, 93, 94, 98, 105, 108, 109, 113])

def extract_data(path, env='buit'):
    print("Extracting " + env + " data")

    estimations_dir = path + "/" + env

    files = [f for f in listdir(estimations_dir) if isfile(join(estimations_dir, f))]

    estimations_dict = dict()
    for file_name in files:
        file_path = estimations_dir + "/" + file_name
        f = open(file_path)

        # Skip path of the test file
        line = f.readline().replace("\n", "")
        # Skip algrithm ID
        line = f.readline().replace("\n", "")
        # Algorithm name
        algorithm = f.readline().replace("\n", "")
        # Algorithm parameter
        algorithm_settings = f.readline().replace("\n", "")
        # Skip pre-data header
        line = f.readline().replace("\n", "")

        if algorithm not in estimations_dict:
            estimations_dict[algorithm] = dict()

        if algorithm_settings not in estimations_dict[algorithm]:
            print("\tAnalyzing data for " + algorithm + " algorithm with parameter " + algorithm_settings)
            line = f.readline().replace("\n", "")

            point_info = dict()
            while line != "":
                [point_number, real_x, real_y, est_x, est_y, error] = line.rsplit()

                if est_x != 'NaN' and est_y != 'NaN' and error != 'NaN':
                    real_point = (float(real_x), float(real_y))

                    if real_point not in point_info:
                        point_info[real_point] = dict()
                        point_info[real_point]['id'] = int(point_number)
                        point_info[real_point]['calcx'] = []
                        point_info[real_point]['calcy'] = []
                        point_info[real_point]['calcerror'] = []

                    point_info[real_point]['calcx'].append(float(est_x))
                    point_info[real_point]['calcy'].append(float(est_y))
                    point_info[real_point]['calcerror'].append(float(error))

                line = f.readline().replace("\n", "")

            estimations_dict[algorithm][int(float(algorithm_settings))] = point_info

    print("Done extracting " + env + " data")
    return estimations_dict


def label_points(estimations_dict, existing_point_label_dict, env='buit'):
    point_label_dict = dict()
    settings = estimations_dict[list(estimations_dict.keys())[0]]
    #point_info = settings[list(settings.keys())[0]]
    
    point_info = []
    for setting in settings:
      if point_info == [] or len(list(settings[setting].keys())) > len(list(point_info.keys())):
        point_info = settings[setting]
    
    
    print ("Found " + str(len(list(point_info.keys()))) + " points")
    
    if env == 'buit':
        for point in point_info:
            point_label_dict[point] = point_info[point]['id']
    else:
        for point in point_info:
            n_distance = 2000000
            nearest = (2000, 2000)
            for existing_point in existing_point_label_dict:
                dist = distance(point, existing_point)
                if dist < n_distance:
                    n_distance = dist
                    nearest = existing_point
            point_label_dict[point] = existing_point_label_dict[nearest]

    return point_label_dict


def calculate_statistics(estimations_dict, env='buit'):
    print("Calculating " + env + " statistics")
    for algorithm in estimations_dict:
        for algorithm_settings in estimations_dict[algorithm]:
            for real_point in estimations_dict[algorithm][algorithm_settings]:
                calcx = estimations_dict[algorithm][algorithm_settings][real_point]['calcx']
                calcy = estimations_dict[algorithm][algorithm_settings][real_point]['calcy']

                # Mean estimated point
                p_mitja_x = statistics.mean(calcx)
                p_mitja_y = statistics.mean(calcy)
                estimations_dict[algorithm][algorithm_settings][real_point]['calc_mitja'] = [p_mitja_x, p_mitja_y]

                # Mean individual error
                m_ind_error = statistics.mean(estimations_dict[algorithm][algorithm_settings][real_point]['calcerror'])
                estimations_dict[algorithm][algorithm_settings][real_point]['error_ind_mitja'] = m_ind_error

                # Error to mean estimated point
                m_point_error = distance(real_point, [p_mitja_x, p_mitja_y])
                estimations_dict[algorithm][algorithm_settings][real_point]['error_punt_mitja'] = m_point_error

                # Mean deviation (from individual estimated points o mean estimated points
                est_deviations = [distance([p_mitja_x, p_mitja_y], [calcx[i], calcy[i]]) for i in range(len(calcx))]
                mean_deviation = statistics.mean(est_deviations)
                estimations_dict[algorithm][algorithm_settings][real_point]['desviacio_mitjana'] = mean_deviation

    print("Done calculating " + env + " statistics")
    return estimations_dict


def classify_error(estimations_dict, error_dict, reverse_point_label_dict, situacio='tots', env='buit'):
    if error_dict is None:
        error_dict = dict()

    for algorithm in estimations_dict:
        if algorithm not in error_dict:
            error_dict[algorithm] = dict()

        if 'mitja_error_' + env not in error_dict[algorithm]:
            error_dict[algorithm]['mitja_error_' + env] = []

        if 'mediana_error_' + env not in error_dict[algorithm]:
            error_dict[algorithm]['mediana_error_' + env] = []

        if 'desviacio_' + env not in error_dict[algorithm]:
            error_dict[algorithm]['desviacio_' + env] = []

        for k in sorted(list(estimations_dict[algorithm].keys())):
            if situacio == 'tots':
                errors = [estimations_dict[algorithm][k][point]['error_ind_mitja'] for point in estimations_dict[algorithm][k]]
                desviacions = [estimations_dict[algorithm][k][point]['desviacio_mitjana'] for point in estimations_dict[algorithm][k]]
            elif situacio == 'tenda':
                errors = []
                desviacions = []
                for point in estimations_dict[algorithm][k]:
                    if reverse_point_label_dict[point] in tenda :
                        errors.append(estimations_dict[algorithm][k][point]['error_ind_mitja'])
                        desviacions.append(estimations_dict[algorithm][k][point]['desviacio_mitjana'])
            elif situacio == 'passadis':
                print("p")
                errors = []
                desviacions = []
                for point in estimations_dict[algorithm][k]:
                    if reverse_point_label_dict[point] not in tenda :
                        errors.append(estimations_dict[algorithm][k][point]['error_ind_mitja'])
                        desviacions.append(estimations_dict[algorithm][k][point]['desviacio_mitjana'])

            if len(errors) > 0 :
                error_mitja = statistics.mean(errors)
                error_media = errors[int(len(errors)/2)]
            else:
                error_mitja = 'No data'
                error_media = 'No data'

            if len(errors) > 0 :
                m_desviacio_mitjana = statistics.mean(desviacions)
            else:
                m_desviacio_mitjana = 'No data'

            error_dict[algorithm]['mitja_error_' + env].append(error_mitja)
            error_dict[algorithm]['mediana_error_' + env].append(error_media)
            error_dict[algorithm]['desviacio_' + env].append(m_desviacio_mitjana)

    return error_dict


def create_error_summary(estimations_path, error_dict, situacio, dades):
    if dades == 'mitja_error':
        out = open(estimations_path + "/resum_" + situacio + ".csv", 'w')
        out.write('ERROR MITJÀ\n\n')
    elif dades == 'mediana_error':
        out = open(estimations_path + "/resum_" + situacio + ".csv", 'a')
        out.write('ERROR MEDIÀ\n\n')
    else:
        out = open(estimations_path + "/resum_" + situacio + ".csv", 'a')
        out.write('DESVIACIÓ MITJANA\n\n')

    out.write('$')

    for algorithm in sorted(list(error_dict.keys())):
        n_elements=len(error_dict[algorithm][dades + '_buit'])
        out.write(algorithm + '$$$')

    out.write('\n')
    out.write('K$')
    out.write('Buit$Ple$Increment$' * len(error_dict))
    out.write('\n')

    for k in range(n_elements):
        out.write(str(k + 2) + '$')
        for algorithm in sorted(list(error_dict.keys())):
            out.write(str(error_dict[algorithm][dades + '_buit'][k]) + '$')
            out.write(str(error_dict[algorithm][dades + '_ple'][k]) + '$')
            if not isinstance(error_dict[algorithm][dades + '_ple'][k], str) and error_dict[algorithm][dades + '_ple'][k] > 0:
                increment = (error_dict[algorithm][dades + '_ple'][k] / error_dict[algorithm][dades + '_buit'][k] - 1) * 100
                out.write(str(increment) + '%$')
        out.write('\n')
    out.write('\n\n')
    out.close()


def create_algorithm_summaries(reports_path, original_plan_path, plan_settings_path, estimations_dict, point_label_dict, env='buit'):
    print("Creating " + env + " summaries")
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
            out.write("\tValor del paràmetre principal de l'algorisme: " + str(algorithm_settings) + "\n")

            plan_path = alg_path + "/" + str(algorithm_settings)
            #draw_points_in_map(original_plan_path, plan_settings_path, plan_path, estimations_dict[algorithm][algorithm_settings], point_label_dict)

            errors = [estimations_dict[algorithm][algorithm_settings][point]['error_ind_mitja'] for point in estimations_dict[algorithm][algorithm_settings]]
            desviacions = [estimations_dict[algorithm][algorithm_settings][point]['desviacio_mitjana'] for point in estimations_dict[algorithm][algorithm_settings]]

            error_mitja = statistics.mean(errors)
            error_media = errors[int(len(errors)/2)]
            m_desviacio_mitjana = statistics.mean(desviacions)

            out.write("\t\tMitja de l'error de les estimacions: " + str(error_mitja) + "\n")
            out.write("\t\tMediana de l'error de les estimacions: " + str(error_media) + "\n")
            out.write("\t\tMitja de la desviació mitjana de les estimacions: " + str(m_desviacio_mitjana) + "\n\n")

        out.write("\n\n")
    out.close()
    print("Done creating " + env + " summaries")


def draw_points_in_map(original_plan_path, plan_settings_path, plan_path, point_dict, point_label_dict):
    print("Drawing points in map")

    if not os.path.exists(plan_path):
        print("\tDirectory " + plan_path + " does not exist, creating...")
        os.makedirs(plan_path)

    radi = 5
    text_size  = 20;
    color_punt = (0, 0, 0)
    color_est  = (255, 0, 0)
    color_disk = (255, 0, 0)
    color_mask = (255, 128, 128)
    color_bord = (255, 0, 0)
    color_ind  = (80, 80, 255)

    im = Image.open(original_plan_path)
    dimensions = load_actual_dimensions(plan_settings_path)
    draw = ImageDraw.Draw(im)

    scale_x = im.size[0] / dimensions['width']
    scale_y = im.size[1] / dimensions['height']

    for point in point_dict:
        # Create directory for individual estimated points
        per_point_path = plan_path + "/per_point"
        if not os.path.exists(per_point_path):
            print("\tDirectory " + per_point_path + " does not exist, creating...")
            os.makedirs(per_point_path)

        # Load image for individual estimated points
        pp_im = Image.open(original_plan_path)
        pp_draw = ImageDraw.Draw(pp_im)


        estimated = point_dict[point]['calc_mitja']
        radi_mask = point_dict[point]['desviacio_mitjana'] * scale_x
        radi_disk = point_dict[point]['desviacio_mitjana'] * scale_x + 4

        x = point[0] * scale_x
        y = point[1] * scale_y

        est_x = estimated[0] * scale_x
        est_y = estimated[1] * scale_y

        # Draw radar disk and circle
        bbox = (est_x - radi_disk/2, est_y - radi_disk/2, est_x + radi_disk/2, est_y + radi_disk/2)
        draw.ellipse(bbox, fill=color_disk)
        pp_draw.ellipse(bbox, fill=color_disk)
        bbox = (est_x - radi_mask/2, est_y - radi_mask/2, est_x + radi_mask/2, est_y + radi_mask/2)
        draw.ellipse(bbox, fill=color_mask)
        pp_draw.ellipse(bbox, fill=color_mask)

        # Draw actual point
        bbox = (x - radi/2, y - radi/2, x + radi/2, y + radi/2)
        draw.ellipse(bbox, fill=color_punt)
        pp_draw.ellipse(bbox, fill=color_punt)

        # Draw estimated point
        bbox = (est_x - radi/2, est_y - radi/2, est_x + radi/2, est_y + radi/2)
        draw.ellipse(bbox, fill=color_est)
        pp_draw.ellipse(bbox, fill=color_est)

        # Draw line to relate points
        draw.line((x, y, est_x, est_y), fill=(255, 255, 0))
        pp_draw.line((x, y, est_x, est_y), fill=(255, 255, 0))

        # Draw individual estimated points
        for i in range(len(point_dict[point]['calcx'])):
            est_x = point_dict[point]['calcx'][i] * scale_x
            est_y = point_dict[point]['calcy'][i] * scale_y
            bbox = (est_x - radi/2, est_y - radi/2, est_x + radi/2, est_y + radi/2)
            pp_draw.ellipse(bbox, fill=color_ind)
        pp_im.save(per_point_path + "/" + str(point_label_dict[point]) + ".png", "PNG")

    im.save(plan_path + "/plan.png", "PNG")
    print("Finished drawing points in map")


def load_actual_dimensions(plan_settings_path):
    dimensions = dict()
    f = open(plan_settings_path)

    line = f.readline()
    dimensions['width'] = float(line.rsplit()[1])
    line = f.readline()
    dimensions['height'] = float(line.rsplit()[1])
    return dimensions


def distance(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2+(p1[1] - p2[1])**2)


def main(root, report=''):
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
    point_label_dict_buit = label_points(estimations_dict, None)
    estimations_dict = calculate_statistics(estimations_dict)
    error_dict = classify_error(estimations_dict, None, point_label_dict_buit)
    #print(error_dict)
    create_algorithm_summaries(reports_path, original_plan_path, plan_settings_path, estimations_dict, point_label_dict_buit)

    estimations_dict_ple = extract_data(estimations_path, 'ple')
    point_label_dict_ple = label_points(estimations_dict_ple, point_label_dict_buit, 'ple')
    estimations_dict_ple = calculate_statistics(estimations_dict_ple, 'ple')
    error_dict = classify_error(estimations_dict_ple, error_dict, point_label_dict_ple, 'tots', 'ple')
    #print(error_dict)
    create_algorithm_summaries(reports_path, original_plan_path, plan_settings_path, estimations_dict_ple, point_label_dict_ple, 'ple')

    create_error_summary(reports_path + '/estimations', error_dict, 'tots', 'mitja_error')
    create_error_summary(reports_path + '/estimations', error_dict, 'tots', 'mediana_error')
    create_error_summary(reports_path + '/estimations', error_dict, 'tots', 'desviacio')

    error_dict = classify_error(estimations_dict, None, point_label_dict_buit, 'tenda', 'buit')
    error_dict = classify_error(estimations_dict_ple, error_dict, point_label_dict_ple, 'tenda', 'ple')
    create_error_summary(reports_path + '/estimations', error_dict, 'tenda', 'mitja_error')
    create_error_summary(reports_path + '/estimations', error_dict, 'tenda', 'mediana_error')
    create_error_summary(reports_path + '/estimations', error_dict, 'tenda', 'desviacio')

    error_dict = classify_error(estimations_dict, None, point_label_dict_buit, 'passadis', 'buit')
    error_dict = classify_error(estimations_dict_ple, error_dict, point_label_dict_ple, 'passadis', 'ple')
    create_error_summary(reports_path + '/estimations', error_dict, 'passadis', 'mitja_error')
    create_error_summary(reports_path + '/estimations', error_dict, 'passadis', 'mediana_error')
    create_error_summary(reports_path + '/estimations', error_dict, 'passadis', 'desviacio')

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

