from SplinePoliMi import Spline
import numpy as np

from OpenSmoke.IntervalAnalysis.Domain import Domain

def process_summary(exp_id, current_summary, domain_list):
    results = {}
    for model in current_summary:
        model_name = model['model']['name']
        if model_name not in list(domain_list.keys()):  # CRECK_2003_C1C3_DME_LTHT
            continue
        #
        #
        # if exp_id == 235 and model_name == 'CRECK_2003_SYNGAS':
        #     print(model)



        for pair in model['pairs']:
            subject = pair['y_sim_name']

            # if subject != 'CO_x':
            #     continue

            # print(subject)

            if pair['x_exp_name'] == 'pressure':
                # TODO da rivedere! Suprattuto so ho lo stesso subject ma una volta con la t ed una volta con la p la x_domain non torna
                continue

            # if pair['y_unit'] != 'us':
            #     print('NOOOOOO', pair['y_unit'])
            #     # exit()

            # # If the Domain Object does not exist, create it

            x_name = pair['x_exp_name']

            if x_name not in domain_list[model_name]:
                domain_list[model_name][x_name] = {}

            if subject not in domain_list[model_name][x_name]:
                if pair['x_exp_name'] == 'temperature' and pair['y_exp_name'] == 'composition':
                    domain_list[model_name][x_name][subject] = Domain(x_range=(500, 2000), x_tickness=25)
                elif pair['x_exp_name'] == 'temperature' and pair['y_exp_name'] == 'ignition delay':
                    domain_list[model_name][x_name][subject] = Domain(x_range=(0, 1.5), x_tickness=0.025)
                elif pair['x_exp_name'] == 'pressure' and pair['y_exp_name'] == 'composition':
                    domain_list[model_name][x_name][subject] = Domain(x_range=(0, 50), x_tickness=1)
                elif pair['x_exp_name'] == 'time' and pair['y_exp_name'] == 'composition':
                    domain_list[model_name][x_name][subject] = Domain(x_range=(0, 10), x_tickness=0.2)
                elif pair['x_exp_name'] == 'equivalence ratio' and pair['y_exp_name'] == 'laminar burning velocity':
                    domain_list[model_name][x_name][subject] = Domain(x_range=(0, 50), x_tickness=0.5)
                    # print('heeereeeee')
                else:
                    raise ValueError(pair['x_exp_name'], pair['y_exp_name'])

            # print(subject, pair['x_exp_name'], pair['y_exp_name'])

            current_domain = domain_list[model_name][x_name][subject]

            x_exp, y_exp = pair['x_exp_data'], pair['y_exp_data']
            x_sim, y_sim = pair['x_sim_data'], pair['y_sim_data']

            # CODICE PER NORMALIZZAZIONE
            # x_exp = [(x - min(x_exp)) / (max(x_exp) - min(x_exp)) for x in x_exp]
            # y_exp = [(x - min(y_exp)) / (max(y_exp) - min(y_exp)) for x in y_exp]
            # x_sim = [(x - min(x_sim)) / (max(x_sim) - min(x_sim)) for x in x_sim]
            # y_sim = [(x - min(y_sim)) / (max(y_sim) - min(y_sim)) for x in y_sim]

            # GENERO SPLINE DAI DATI SPERIMENTALI E DAL MODELLO
            spline_exp = Spline(x=x_exp, y=y_exp)
            spline_model = Spline(x=x_sim, y=y_sim)

            # if plot:
            x_evaluation = np.linspace(min(x_exp), max(x_exp), 100)

            # plt.show()

            df = current_domain.systematic_analysis(exp_spline=spline_exp,
                                                    sim_spline=spline_model,
                                                    x_axis=x_exp,
                                                    exp_id=exp_id)

            # print(df)
            if x_name not in results:
                results[x_name] = {}

            if df is not None:
                results[x_name][subject] = df

    return results

