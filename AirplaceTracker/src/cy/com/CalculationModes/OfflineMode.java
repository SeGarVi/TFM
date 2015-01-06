/*
 * AirPlace:  The Airplace Project is an OpenSource Indoor and Outdoor
 * Localization solution using WiFi RSS (Receive Signal Strength).
 * The AirPlace Project consists of three parts:
 *
 *  1) The AirPlace Logger (Ideal for collecting RSS Logs)
 *  2) The AirPlace Server (Ideal for transforming the collected RSS logs
 *  to meaningful RadioMap files)
 *  3) The AirPlace Tracker (Ideal for using the RadioMap files for
 *  indoor localization)
 *
 * It is ideal for spaces where GPS signal is not sufficient.
 *
 * Authors:
 * C. Laoudias, G.Larkou, G. Constantinou, M. Constantinides, S. Nicolaou,
 *
 * Supervisors:
 * D. Zeinalipour-Yazti and C. G. Panayiotou
 *
 * Copyright (c) 2011, KIOS Research Center and Data Management Systems Lab (DMSL),
 * University of Cyprus. All rights reserved.
 *
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * Υou should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
*/

package cy.com.CalculationModes;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.OutputStreamWriter;
import java.security.acl.Owner;
import java.util.ArrayList;
import java.util.Calendar;

import android.content.Context;
import android.os.Handler;
import cy.com.airplace.Algorithms;
import cy.com.airplace.LogRecord;
import cy.com.airplace.RadioMap;
import cy.com.airplace.WeightRecord;

public class OfflineMode extends Thread {

	private String errMsg = null;
	private Handler handler;
	private final RadioMap RM;
	private final File test_data_file;
	private final int algorithm_selection;

	private double average_pos_err, average_exe_time;

	private String algorithmName;
	private boolean storeData;
	private Context context;
	
	private boolean multipleParallel;
	
	// The scan list to use for offline
	private ArrayList<LogRecord> OfflineScanList;

	public OfflineMode(RadioMap RM, File test_data_file,
			int algorithm_selection, Handler handler,
			String algorithmName, boolean storeData,
			boolean multipleParallel, Context context) {
		this.RM = RM;
		this.test_data_file = test_data_file;
		this.handler = handler;
		this.algorithm_selection = algorithm_selection;
		this.OfflineScanList = new ArrayList<LogRecord>();
		this.algorithmName = algorithmName;
		this.storeData = storeData;
		this.context = context;
		this.multipleParallel = multipleParallel;
	}

	public void run() {
		FileOutputStream   fOut = null;
		OutputStreamWriter osw  = null;
		File file = null;
		
		if (!test_data_file.isFile() || !test_data_file.exists() || !test_data_file.canRead()) {
			errMsg = test_data_file + " does not exist or is not readable";
			handler.sendEmptyMessage(-1);
			return;
		}

		OfflineScanList.clear();

		BufferedReader reader = null;
		String line;
		String[] temp;
		double[] ptemp = {0.0, 0.0};

		String test_geo;
		int count_test_pos = 0;
		double pos_error;
		double sum_pos_error = 0;

		long bytesRead = 0;
		long bytesTotal = test_data_file.length();
		int perc = 0;
		int pcounter = 0;

		long start = 0;
		long finish = 0;
		long total = 0;

		ArrayList<String> MacAdressList = new ArrayList<String>();

		try {

			reader = new BufferedReader(new FileReader(test_data_file));

			/* Read the first line */
			line = reader.readLine();

			// Must exists
			if (line == null) {
				errMsg = test_data_file + " file is corrupted";
				handler.sendEmptyMessage(-1);
				return;
			}

			bytesRead += line.length() + 1;

			if (perc < (int) (((float) bytesRead / (float) bytesTotal) * 100)) {
				perc = (int) (((float) bytesRead / (float) bytesTotal) * 100);
				if (multipleParallel)
					handler.sendEmptyMessage(perc + algorithm_selection * 100);
				else
					handler.sendEmptyMessage(perc);
			}

			/* Store the Mac Addresses */
			if (line.startsWith("#")) {
				line = line.replace(", ", " ");
				temp = line.split(" ");

				// Must have more than 4 fields
				if (temp.length < 4) {
					errMsg = test_data_file + " file is corrupted";
					handler.sendEmptyMessage(-1);
					return;
				}

				// Store all Mac Addresses
				for (int i = 3; i < temp.length; ++i)
					MacAdressList.add(temp[i]);
			} else {
				errMsg = test_data_file + " file is corrupted";
				handler.sendEmptyMessage(-1);
				return;
			}

			count_test_pos = 0;

			if (storeData) {
				String path = test_data_file.getParent() + "/" + Calendar.getInstance().getTimeInMillis() + ".txt";
				file = new File(path);
				fOut = new FileOutputStream(file);
				osw = new OutputStreamWriter(fOut);
				
				osw.write("Test file: " + test_data_file.getPath() + "\n");
				osw.write(algorithm_selection + "\n");
				osw.write(algorithmName + "\n");
				osw.write(Algorithms.readParameter(RM.getRadiomapMean_File(), algorithm_selection) + "\n");
				osw.write("Point#, ActualX, ActualY, PredictedX, PredictedY, Error" + "\n");
			}
			
			while ((line = reader.readLine()) != null) {

				bytesRead += line.length() + 1;

				line = line.trim().replace(", ", " ");
				temp = line.split(" ");

				if (temp.length < 3) {
					errMsg = test_data_file + " file is corrupted";
					handler.sendEmptyMessage(-1);
					return;
				}

				if (MacAdressList.size() != temp.length - 2) {
					errMsg = test_data_file + " file is corrupted";
					handler.sendEmptyMessage(-1);
					return;
				}

				if (ptemp[0] != Double.parseDouble(temp[0]) ||
						ptemp[1] != Double.parseDouble(temp[1])) {
					pcounter++;
					ptemp[0] = Double.parseDouble(temp[0]);
					ptemp[1] = Double.parseDouble(temp[1]);
				}
				
				for (int i = 2; i < temp.length; ++i) {
					LogRecord lr = new LogRecord(MacAdressList.get(i - 2), Integer.parseInt(temp[i]));
					OfflineScanList.add(lr);
				}

				if (perc < (int) (((float) bytesRead / (float) bytesTotal) * 100)) {
					perc = (int) (((float) bytesRead / (float) bytesTotal) * 100);
					if (multipleParallel)
						handler.sendEmptyMessage(perc + algorithm_selection * 100);
					else
						handler.sendEmptyMessage(perc);
				}

				start = System.currentTimeMillis();

				test_geo = Algorithms.ProcessingAlgorithms(OfflineScanList, RM, algorithm_selection);

				if (test_geo == null) {
					errMsg = "Can't calculate a location. Check that test data and radio map files refer to the same area.";
					handler.sendEmptyMessage(-1);
					return;
				}

				finish = System.currentTimeMillis();

				total += (finish - start);

				OfflineScanList.clear();

				pos_error = calculateEuclideanDistance(temp[0] + " " + temp[1], test_geo);

				if (storeData) {
					osw.write(pcounter + " " + temp[0] + " " + temp[1] + " " + test_geo + " " + pos_error + "\n");
				}
				
				if (pos_error != -1) {
					sum_pos_error += pos_error;
					count_test_pos++;
				}
			}

			reader.close();
			
			if (storeData) {
				osw.close();
				fOut.close();
				
				if (multipleParallel) {
					handler.sendEmptyMessage(100 + algorithm_selection * 100);
					handler.sendEmptyMessage(-3 - algorithm_selection);
				} else if (algorithm_selection == 4) {
					handler.sendEmptyMessage(100);
					handler.sendEmptyMessage(-3);
				}
			} else {
				handler.sendEmptyMessage(100);
	
				average_pos_err = sum_pos_error / (double) count_test_pos;
				average_exe_time = total / (double) count_test_pos;
	
				handler.sendEmptyMessage(-1);
			}
			errMsg = null;
		} catch (Exception ex) {
			errMsg = "Can't calculate a location.\nError: " + ex.getMessage() + "." + "\nCheck that test data and radio map files are not corrupted.";
			handler.sendEmptyMessage(-1);
		}
	}

	private double calculateEuclideanDistance(String real, String estimate) {

		double pos_error;
		String[] temp_real;
		String[] temp_estimate;
		double x1, x2;

		temp_real = real.split(" ");
		temp_estimate = estimate.split(" ");

		try {
			x1 = Math.pow((Double.parseDouble(temp_real[0]) - Double.parseDouble(temp_estimate[0])), 2);
			x2 = Math.pow((Double.parseDouble(temp_real[1]) - Double.parseDouble(temp_estimate[1])), 2);
		} catch (Exception e) {
			return -1;
		}

		pos_error = Math.sqrt((x1 + x2));

		return pos_error;
	}

	public String getErrMsg() {
		return errMsg;
	}

	public double getAverage_pos_err() {
		return average_pos_err;
	}

	public double getAverage_exe_time() {
		return average_exe_time;
	}

}
