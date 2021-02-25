import json

class JsonHandler:

    def dump_all(self, max_static, mean_static, max_dynamic, mean_dynamic, sample1, sample2, test_mode, forces):
        if sample2.name == "":
            dic = {"Company Name:": sample1.company_name,
                   "Operator Name:": sample1.operator_name,
                   "Testing Weight(gr):": sample1.testing_weight,
                   "Test Mode:": test_mode,
                   "Sample Name:": sample1.name,
                   "Sample Width(mm)": float(sample1.width),
                   "Sample Height(mm):": float(sample1.height),
                   "Sample Age(months):": float(sample1.age),
                   "Max Static Coefficient of Friction:": max_static,
                   "Mean Static Coefficient of Friction:": mean_static,
                   "Max Dynamic Coefficient of Friction:": max_dynamic,
                   "Mean Dynamic Coefficient of Friction:": mean_dynamic,
                   "Forces:": forces
                   }
        else:
            dic = {"Company Name:": sample1.company_name,
                   "Operator Name:": sample1.operator_name,
                   "Testing Weight(gr):": sample1.testing_weight,
                   "Test Mode:": test_mode,
                   "First Sample Name:": sample1.name,
                   "First Sample Width(mm)": float(sample1.width),
                   "First Sample Height(mm):": float(sample1.height),
                   "First Sample Age(months):": float(sample1.age),
                   "Second Sample Name:": sample2.name,
                   "Second Sample Width(mm)": float(sample2.width),
                   "Second Sample Height(mm):": float(sample2.height),
                   "Second Sample Age(months):": float(sample2.age),
                   "Max Static Coefficient of Friction:": max_static,
                   "Mean Static Coefficient of Friction:": mean_static,
                   "Max Dynamic Coefficient of Friction:": max_dynamic,
                   "Mean Dynamic Coefficient of Friction:": mean_dynamic,
                   "Forces:": forces
                   }
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(dic, f, ensure_ascii=False, indent=2)

    def dump_time(self, max_static, mean_static, max_dynamic, mean_dynamic, sample1, sample2, test_mode, forces, date_and_time):
        if sample2.name == "":
            dic = {"Company Name:": sample1.company_name,
                   "Operator Name:": sample1.operator_name,
                   "Testing Weight(gr):": sample1.testing_weight,
                   "Test Mode:": test_mode,
                   "Sample Name:": sample1.name,
                   "Sample Width(mm)": float(sample1.width),
                   "Sample Height(mm):": float(sample1.height),
                   "Sample Age(months):": float(sample1.age),
                   "Max Static Coefficient of Friction:": max_static,
                   "Mean Static Coefficient of Friction:": mean_static,
                   "Max Dynamic Coefficient of Friction:": max_dynamic,
                   "Mean Dynamic Coefficient of Friction:": mean_dynamic,
                   "Forces:": forces
                   }
        else:
            dic = {"Company Name:": sample1.company_name,
                   "Operator Name:": sample1.operator_name,
                   "Testing Weight(gr):": sample1.testing_weight,
                   "Test Mode:": test_mode,
                   "First Sample Name:": sample1.name,
                   "First Sample Width(mm)": float(sample1.width),
                   "First Sample Height(mm):": float(sample1.height),
                   "First Sample Age(months):": float(sample1.age),
                   "Second Sample Name:": sample2.name,
                   "Second Sample Width(mm)": float(sample2.width),
                   "Second Sample Height(mm):": float(sample2.height),
                   "Second Sample Age(months):": float(sample2.age),
                   "Max Static Coefficient of Friction:": max_static,
                   "Mean Static Coefficient of Friction:": mean_static,
                   "Max Dynamic Coefficient of Friction:": max_dynamic,
                   "Mean Dynamic Coefficient of Friction:": mean_dynamic,
                   "Forces:": forces
                   }

        file_name = "COF Test " + date_and_time + ".json"
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(dic, f, ensure_ascii=False, indent=2)

    def dump_calib_save(self, distance, speed, normal_force, sample_time, calib):
        dic = {"Distance:":distance,
               "Speed:":speed,
               "Normal_Force:":normal_force,
               "Sample_Time:":sample_time,
               "Calibration value:":calib
               }

        file_name = "calibration_save.json"
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(dic, f, ensure_ascii=False, indent=2)

    def import_save(self):
        file_name = "calibration_save.json"
        with open(file_name) as json_file:
            data = json.load(json_file)
            return data["Distance:"], data["Speed:"], data["Normal_Force:"], data["Sample_Time:"], data["Calibration value:"]