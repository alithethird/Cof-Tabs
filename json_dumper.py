import json

class JsonDumper:

    def dump_all(self, static, dynamic, sample1, sample2, test_mode, forces):
        if sample2.name == "":
            dic = {"Company Name:": sample1.company_name,
                   "Operator Name:": sample1.operator_name,
                   "Testing Weight(gr):": sample1.testing_weight,
                   "Test Mode:": test_mode,
                   "Sample Name:": sample1.name,
                   "Sample Width(mm)": float(sample1.width),
                   "Sample Height(mm):": float(sample1.height),
                   "Sample Age(months):": float(sample1.age),
                   "Static Coefficient of Friction:": float(static),
                   "Dynamic Coefficient of Friction:": float(dynamic),
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
                   "Static Coefficient of Friction:": float(static),
                   "Dynamic Coefficient of Friction:": float(dynamic),
                   "Forces:": forces
                   }
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(dic, f, ensure_ascii=False, indent=2)
