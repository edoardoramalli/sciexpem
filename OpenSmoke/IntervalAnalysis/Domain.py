from scipy import integrate
import numpy as np
import pandas as pd


class Domain:

    def __init__(self, x_range, x_tickness):
        self.x_p = {x: [] for x in np.arange(start=x_range[0], stop=x_range[1] + x_tickness, step=x_tickness)}
        self.x_n = {x: [] for x in np.arange(start=x_range[0], stop=x_range[1] + x_tickness, step=x_tickness)}
        # self.y = np.arange(start=y_range[0], stop=y_range[1] + y_tick, step=y_tick)
        # self.z = np.arange(start=z_range[0], stop=z_range[1] + z_tick, step=z_tick)

        # self.matrix = np.zeros(shape=(len(self.x), len(self.y), len(self.z)))
        # self.matrix = np.zeros(shape=(len(self.x), len(self.y)))

        pass

    def add_value(self, x, value, relation):
        # x_index = np.where(self.x == min(self.x, key=lambda e: abs(e - x)))[0][0]
        # y_index = np.where(self.y == min(self.y, key=lambda e: abs(e - y)))[0][0]
        # z_index = np.where(self.z == min(self.z, key=lambda e: abs(e - z)))[0][0]
        # self.matrix[x_index, y_index, z_index] = value
        # pass
        if relation == '+':
            subject = self.x_p
        else:
            subject = self.x_n

        x_index = min(subject, key=lambda e: abs(e - x))
        subject[x_index].append(value)

    def transform(self, threshold, weight, ratio):
        # return np.arctan(weight - threshold) + 1.5

        # if weight >= threshold:
        #     return np.log(weight) + 1
        # else:
        #     return -np.log(weight - 2) + 1

        # if weight < threshold:
        #     return 1
        # else:
        #     return ratio

        if ratio > 10:
            if weight < threshold:
                return 1
            else:
                return ratio
        else:
            return ratio

    def systematic_analysis(self, exp_spline, sim_spline, x_axis, exp_id):
        x_axis = sorted(x_axis)

        domain_x = list(self.x_p.keys())

        min_x_axis = min(x_axis)
        max_x_axis = max(x_axis)

        min_domain = min(domain_x)
        max_domain = max(domain_x)

        # Non ho intersezione dei domini
        # print(x_axis, domain_x)

        if max(domain_x) < min_x_axis or min(domain_x) > max_x_axis:
            print(domain_x, max_x_axis, min_x_axis)
            raise ValueError("No x intersection")

        # dominio dei dati completamente incluso nel dominio di analisi
        elif min_domain < min_x_axis and max_domain > max_x_axis:
            tmp = {x: abs(x - x_axis[0]) for x in domain_x}
            min_tmp = min(tmp, key=tmp.get)
            x_axis[0] = min_tmp

            tmp = {x: abs(x - x_axis[-1]) for x in domain_x}
            min_tmp = min(tmp, key=tmp.get)
            x_axis[-1] = min_tmp

        elif min_domain > min_x_axis and max_domain > max_x_axis:
            # print(domain_x, x_axis)
            # raise NotImplementedError
            pass

        elif min_domain < min_x_axis and max_x_axis > max_domain:
            # print(domain_x, x_axis, exp_id, [t_x for t_x in domain_x if min(x_axis) <= t_x <= max(x_axis)])
            # raise NotImplementedError
            pass



        x_axis = [t_x for t_x in domain_x if min(x_axis) <= t_x <= max(x_axis)]



        if len(x_axis) == 1:
            # TODO con la pressione c'è un caso in cui x_domain è [1, 0.660412912, 0.661189387, 0.662152986, 0.662857293, 0.663648498, 0.664526318, 0.665116249, 1]
            print('attenzione')
            # TODO nella trasformazione tutto viene compressato in un singolo elemento vedi exp 1058
            return

        # print(x_axis)
        def exp(x: float):
            return exp_spline.evaluate(x)

        def sim(x: float):
            return sim_spline.evaluate(x)

        # print(x_axis)

        area_sim_tot, err_sim_tot = integrate.quad(sim, min(x_axis), max(x_axis))
        area_exp_tot, err_exp_tot = integrate.quad(exp, min(x_axis), max(x_axis))

        # sum = 0

        # if plot:
        #     print(f'AREA SIM: {area_sim_tot:.5f}')
        #     print(f'AREA EXP: {area_exp_tot:.5f}')

        diz_df = {'Interval': [],
                  'Area Exp Inter': [],
                  'Area Sim Inter': [],
                  'Weight Exp Inter': [],
                  'Weight Sim Inter': [],
                  # 'Value': [],
                  'Real': [],
                  'Relation': []}

        # print(x_axis)

        expected_weight = 1 / (len(x_axis) - 1)

        for index in range(0, len(x_axis) - 1):
            inf = x_axis[index]
            sup = x_axis[index + 1]

            diz_df['Interval'].append((inf, sup))

            area_sim_interval, err_sim = integrate.quad(sim, inf, sup)
            area_sim_interval = max(0, area_sim_interval)

            diz_df['Area Sim Inter'].append(area_sim_interval)

            area_exp_interval, err_exp = integrate.quad(exp, inf, sup)
            area_exp_interval = max(0, area_exp_interval)

            diz_df['Area Exp Inter'].append(area_exp_interval)

            current_weight_exp = area_exp_interval / area_exp_tot
            current_weight_sim = area_sim_interval / area_sim_tot

            diz_df['Weight Exp Inter'].append(current_weight_exp)
            diz_df['Weight Sim Inter'].append(current_weight_sim)

            # Modello sovrastima
            if area_sim_interval >= area_exp_interval:
                relation = '+'
                diz_df['Relation'].append(relation)

                try:
                    ratio = area_sim_interval / area_exp_interval
                    diz_df['Real'].append(ratio)
                except ZeroDivisionError:
                    ratio = 0
                    # print('herreee')
                    diz_df['Real'].append(np.NAN)

                # ratio = self.transform(threshold=expected_weight, weight=current_weight_exp, ratio=ratio)


            # Modello sottostima
            else:
                relation = '-'
                diz_df['Relation'].append(relation)

                try:
                    ratio = area_exp_interval / area_sim_interval
                    diz_df['Real'].append(ratio)
                except ZeroDivisionError:
                    ratio = 0
                    diz_df['Real'].append(np.NAN)

                # ratio = self.transform(threshold=expected_weight, weight=current_weight_sim, ratio=ratio)

            # diz_df['Value'].append(ratio)

            # self.add_value(x=x_axis[index], value=ratio, relation=relation)

        df = pd.DataFrame.from_dict(diz_df)

        # print(df)

        df['Value'] = ''

        # print(df)

        # Remove NaN
        NaN_indexes, _ = np.where(df.isna())




        if len(NaN_indexes) > 0:

            diff = abs(area_sim_tot - area_exp_tot)

            guess = diff / len(NaN_indexes)

            for index in NaN_indexes:
                sim_int = df.iloc[index, df.columns.get_loc('Area Exp Inter')]
                exp_int = df.iloc[index, df.columns.get_loc('Area Sim Inter')]

                if sim_int == 0 and exp_int == 0:
                    df.iloc[index, df.columns.get_loc('Value')] = 1
                elif sim_int == 0:
                    df.iloc[index, df.columns.get_loc('Value')] = guess / exp_int
                elif exp_int == 0:
                    df.iloc[index, df.columns.get_loc('Value')] = guess / sim_int



        for index, row in df.iterrows():
            weight = row['Weight Exp Inter'] if row['Relation'] == '+' else row['Weight Sim Inter']
            if row['Value'] == '':
                value = self.transform(threshold=expected_weight, weight=weight, ratio=row['Real'])
            else:
                value = self.transform(threshold=expected_weight, weight=weight, ratio=row['Value'])

            df.loc[index, 'Value'] = float(value)

            # print(row['Interval'][0], df.loc[index, 'Value'])
            if exp_id in [939]: #[943, 945, 948, 949, 951, 952, 953]:
                # print(exp_id, 'edoo', row['Interval'][0], row['Relation'], value)
                self.add_value(x=row['Interval'][0], value=value, relation=row['Relation'])
            else:
                self.add_value(x=row['Interval'][0], value=value, relation=row['Relation'])


        return df
