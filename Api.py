from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
import main
from main import optimize, read_data
import datetime as dt
import pandas as pd
from settings.general_settings import GeneralSettings
from time import time
from copy import deepcopy
from helpers.set_loggers import *


app = FastAPI(
    title="interstore api",
    version="0.0.1",
    contact={"name": "Miguel Preto", "email": "miguel.preto@inesctec.pt"},
    docs_url="/docs", redoc_url=None,)

# Configuração do CORS
origins = [
    "http://127.0.0.1:3000",
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/objective_function")
async def objective_function(selected_option: str = Form(...)):

    objective_function = selected_option
    return objective_function


"""@app.post("/api/settings")
async def settings(max_c_ch: float = Form(...), max_c_disch: float = Form(...), e_nom: float = Form(...), technology: float = Form(...), max_c_ch2: float = Form(...), max_c_disch2: float = Form(...), e_nom2: float = Form(...), technology2: float = Form(...), selected_option: str = Form(...), date: list = Form(...), market: list[float] = Form(...), load: list[float] = Form(...)):"""


@app.post("/api/settings")
async def settings(data: dict):
    selected_option = data.get("selected_option")
    load = data.get("load", [])
    market = data.get("market", [])
    date = data.get("date", [])

    max_c_ch = data.get("max_c_ch")
    max_c_disch = data.get("max_c_disch")
    e_nom = data.get("e_nom")
    technology = data.get("technology")
    bess_ch_eff = data.get("ch_eff")
    bess_disch_eff = data.get("disch_eff")

    max_c_ch2 = data.get("max_c_ch2")
    max_c_disch2 = data.get("max_c_disch2")
    e_nom2 = data.get("e_nom2")
    technology2 = data.get("technology2")
    bess_ch_eff2 = data.get("ch_eff2")
    bess_disch_eff2 = data.get("disch_eff2")

    # Parametros
    objective_function = selected_option

    GeneralSettings.bess_max_c_ch = max_c_ch
    GeneralSettings.bess_max_c_disch = max_c_disch
    GeneralSettings.bess_e_nom = e_nom
    GeneralSettings.technology = technology
    GeneralSettings.bess_ch_eff = bess_ch_eff
    GeneralSettings.bess_disch_eff = bess_disch_eff

    GeneralSettings.bess_max_c_ch2 = max_c_ch2
    GeneralSettings.bess_max_c_disch2 = max_c_disch2
    GeneralSettings.bess_e_nom2 = e_nom2
    GeneralSettings.technology2 = technology2
    GeneralSettings.bess_ch_eff2 = bess_ch_eff2
    GeneralSettings.bess_disch_eff2 = bess_disch_eff2

    # Converter a string de data em um objeto datetime
    table_data = pd.DataFrame(
        {'date': date, 'market': market, 'load': load}, index=None)
    table_data['date'] = pd.to_datetime(
        table_data['date'], format='%d/%m/%Y %H:%M', errors='coerce')
    table_data = table_data.set_index('date')

    step = GeneralSettings.step
    data_df = read_data(step, table_data)

    first_day = data_df.index[0]
    total_iter = len(GeneralSettings.all_days)
    iteration = 0

    for day in GeneralSettings.all_days:
        # Log the current iteration
        iteration += 1
        iter_time = time()
        logger.info(f' * Day {iteration} of {total_iter} ... * ')

        # Truncate data to present day
        first_dt = first_day + dt.timedelta(days=day)
        last_dt = first_dt + \
            dt.timedelta(hours=GeneralSettings.horizon) - \
            dt.timedelta(minutes=GeneralSettings.step)
        df = data_df.loc[first_dt:last_dt, :].copy()

        # Updates between runs
        if iteration == 1:
            degraded = 0
            degraded2 = 0
            init = first_dt
            soc = GeneralSettings.bess_initial_soc
            soc2 = GeneralSettings.bess_initial_soc2
        else:
            degraded += main.degradation
            degraded2 += main.degradation2
            init += dt.timedelta(days=1)
            main.last_soc /= (GeneralSettings.bess_e_nom - degraded) * 100
            main.last_soc2 /= (GeneralSettings.bess_e_nom2 - degraded2) * 100
            soc = main.last_soc
            soc2 = main.last_soc2

        before_init = init - dt.timedelta(hours=1)

        settings = {
            'pccLimitValue': GeneralSettings.pcc_limit_value,
            'addOnInv': GeneralSettings.add_on_inv,
            'addOnSoc': GeneralSettings.add_on_soc,
        }

        original_test_data = deepcopy(GeneralSettings.bess_test_data)
        original_test_data2 = deepcopy(GeneralSettings.bess_test_data2)

        bess_asset = {
            'actualENom': GeneralSettings.bess_e_nom - degraded,
            'chEff': GeneralSettings.bess_ch_eff,
            'degCurve': GeneralSettings.bess_deg_curve,
            'dischEff': GeneralSettings.bess_disch_eff,
            'eNom': GeneralSettings.bess_e_nom,
            'eolCriterion': GeneralSettings.bess_eol_criterion,
            'invMaxIDC': GeneralSettings.bess_inv_max_idc,
            'invSNom': GeneralSettings.bess_inv_s_nom,
            'invVNom': GeneralSettings.bess_inv_v_nom,
            'maxCCh': GeneralSettings.bess_max_c_ch,
            'maxCDch': GeneralSettings.bess_max_c_disch,
            'maxSoc': GeneralSettings.bess_max_soc,
            'minPCh': GeneralSettings.bess_min_p_ch,
            'minPDch': GeneralSettings.bess_min_p_disch,
            'minSoc': GeneralSettings.bess_min_soc,
            'reserveSoc': GeneralSettings.bess_reserve_soc,
            'testData': GeneralSettings.bess_test_data,
            'vNom': GeneralSettings.bess_v_nom,
        }

        bess_asset2 = {
            'actualENom': GeneralSettings.bess_e_nom2 - degraded2,
            'chEff': GeneralSettings.bess_ch_eff2,
            'degCurve': GeneralSettings.bess_deg_curve2,
            'dischEff': GeneralSettings.bess_disch_eff2,
            'eNom': GeneralSettings.bess_e_nom2,
            'eolCriterion': GeneralSettings.bess_eol_criterion2,
            'invMaxIDC': GeneralSettings.bess_inv_max_idc2,
            'invSNom': GeneralSettings.bess_inv_s_nom2,
            'invVNom': GeneralSettings.bess_inv_v_nom2,
            'maxCCh': GeneralSettings.bess_max_c_ch2,
            'maxCDch': GeneralSettings.bess_max_c_disch2,
            'maxSoc': GeneralSettings.bess_max_soc2,
            'minPCh': GeneralSettings.bess_min_p_ch2,
            'minPDch': GeneralSettings.bess_min_p_disch2,
            'minSoc': GeneralSettings.bess_min_soc2,
            'reserveSoc': GeneralSettings.bess_reserve_soc2,
            'testData': original_test_data2,
            'vNom': GeneralSettings.bess_v_nom2,
        }

        milp_params = {
            'mipgap': GeneralSettings.mipgap,
            'timeout': GeneralSettings.timeout,
            'init': init,
            'horizon': GeneralSettings.horizon,
            'step': GeneralSettings.step,
        }

        measures = {
            'bessSoC': soc,
        }

        measures2 = {
            'bessSoC': soc2,
        }

        forecasts_and_other_arrays = {
            'loadForecasts': df['load'].values,
            'marketPrices': df['market'].values,
        }

        t0 = time()
        prob_obj = optimize(settings, bess_asset, bess_asset2, milp_params, measures, measures2,
                            forecasts_and_other_arrays, objective_function)
        t1 = time() - t0

        # Get the needed outputs
        outputs = prob_obj.outputs
        outputs.pop('milpStatus')

        # -- get a single dataframe from all outputs
        col_names = outputs.keys()
        for i, col in enumerate(col_names):
            aux_df = pd.DataFrame(outputs[col])
            aux_df.columns = ['date', col]
            aux_df.set_index('date', inplace=True)
            df = aux_df if i == 0 else df.join(aux_df)

        # -- if first day, create df, else append to existing df
        # if main.daily_outputs is not None:
        #     main.daily_outputs = main.daily_outputs_append(df)
        # else:
        #     main.daily_outputs = df
        main.daily_outputs = df

        status = prob_obj.stat
        logger.warning(f'{status}')
        main.expected_revenues += pd.DataFrame(
            outputs.get('expectRevs')).sum().get('setpoint')
        main.last_soc += pd.DataFrame(outputs['eBess']
                                      ).loc[prob_obj.time_intervals - 1, 'setpoint']
        main.last_soc2 += pd.DataFrame(outputs['eBess2']
                                       ).loc[prob_obj.time_intervals - 1, 'setpoint']
        main.degradation += pd.DataFrame(outputs['eDeg']).sum().get('setpoint')
        main.degradation2 += pd.DataFrame(
            outputs['eDeg2']).sum().get('setpoint')
        main.total_degradation += pd.DataFrame(
            outputs.get('Totaldeg')).sum().get('setpoint')
        main.total += pd.DataFrame(outputs.get('Total')).sum().get('setpoint')
        main.first_dt_text = dt.datetime.strftime(
            first_dt, '%Y-%m-%d %H:%M:%S')

        with open(f'{prob_obj.common_fname}-pulp.sol', newline='\n') as csvfile:
            init_text = csvfile.read(50)
            status_real = init_text.split(sep=' - ')[0]

        # Clean unnecessary files from "core" folder
        prob_obj.final_folder_cleaning()

        main.final_outputs['date'].append(main.first_dt_text)
        main.final_outputs['status'].append(status)
        main.final_outputs['status_real'].append(status_real)
        main.final_outputs['expected_revenues'].append(main.expected_revenues)
        main.final_outputs['degradation'].append(main.degradation)
        main.final_outputs['degradation2'].append(main.degradation2)
        main.final_outputs['total_degradation'].append(main.total_degradation)
        main.final_outputs['total'].append(main.total)
        main.final_outputs['last_soc'].append(main.last_soc)
        main.final_outputs['time'].append(t1)

        logger.info(
            f' * Day {iteration} of {total_iter} ... OK! ({iter_time - time():.3f}s) * ')

    # Save the outputs to a csv file
    # TODO: create a folder for the outputs if non existent
    # dir = os.path.join(ROOT_PATH, 'outputs')

    main.daily_outputs.to_csv(rf'outputs/{prob_obj.common_fname}_setpoints.csv',
                              sep=';', decimal=',', index=True)
    pd.DataFrame(main.final_outputs).to_csv(rf'outputs/{prob_obj.common_fname}_main_outputs.csv',
                                            sep=';', decimal=',', index=True)

    # Remove the log file handler
    # remove_logfile_handler(main.logfile_handler_id)
    return main.daily_outputs


@app.get("/api/get_data_for_chart")
async def get_data_for_chart():
    technology = GeneralSettings.technology
    technology2 = GeneralSettings.technology2
    return main.daily_outputs['Merge'], main.daily_outputs['Merge2'], main.final_outputs, technology, technology2

# if __name__ == "__main__":
#     uvicorn.run(app, host="127.0.0.1", port=8000)
