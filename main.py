import pandas as pd
from helpers.set_loggers import *
from module.core.Optimizer import Optimizer
from settings.general_settings import GeneralSettings
from time import time

def read_data(step, table_data):
	
	"""Reader and parser for forecasted data:
	- generation (normalized 0-1),
	- load (inflexible; normalized 0-1),
	- price for energy consumed from the retailer (€/kWh) and
	- tariff for energy sold to the retailer (€/kWh)
	:param step: data and forecast step in minutes
	:type step: int
	:return: parsed dataframe with forecasts
	:rtype: pandas.core.frame.DataFrame"""

	t = time()
	logger.info('Reading and parsing forecasts ... ')

	data = pd.DataFrame(table_data)

	# Fix lacking market and feed-in values
	data['market'].replace(to_replace=0, method='ffill', inplace=True)

	data['load'] *= GeneralSettings.scale_load  # Load nominal power in kW - load set points now in kWh

	# Resample data to step
	# To up-sample (H -> min) a last row must be included with the last index hour + 1
	# e.g. when upsampling from [01/01/2022 00:00, 01/01/2022 23:00] to a 15' step, [02/01/2022 00:00]
	# must be added so that the resample does not end at [01/01/2022 23:00] but at [01/01/2022 23:45]
	idx_freq = pd.infer_freq(data.index)
	new_entry_idx = data.index[-1] + pd.Timedelta(1, unit=idx_freq)
	data.loc[new_entry_idx, :] = data.loc[data.index[-1]]
	data = data.resample(f'{step}T').ffill()
	data = data.iloc[:-1]

	logger.info(f'Reading and parsing forecasts ... OK! ({time()-t:.3f}s)')

	return data

def optimize(_settings, _assets, _assets2, _milp_params, _measures, _measures2, _forecasts, a):
	"""
	Main optimization orchestrator.
	:param _settings:
	:param _assets:
	:param _assets2:
	:param _milp_params:
	:param _measures:
	:param _measures2:
	:param _forecasts:

	:return:
	"""
	config_t = time()
	logger.info(f'Configuring data for MILP...')
	problem = Optimizer(plot=GeneralSettings.plot, solver='CBC')
	problem.initialize(_settings, _assets, _assets2, _milp_params, _measures, _measures2, _forecasts)
	logger.info(f'Configuring data for MILP ... OK! ({time() - config_t:.3f}s)')

	solve_t = time()
	logger.info(f'Solving MILP ...')
	problem.solve_milp(a, _assets, _assets2)
	logger.info(f'Solving MILP ... OK! ({time() - solve_t:.3f}s)')

	outputs_t = time()
	logger.info(f'Generating outputs ...')
	problem.generate_outputs(a, _assets, _assets2 )
	logger.info(f'Generating outputs ... OK! ({time() - outputs_t:.3f}s)')

	return problem

# Set paths
ROOT_PATH = os.path.abspath(os.path.join(__file__, '..'))
JSON_PATH = os.path.join(ROOT_PATH, 'json')
HELPERS_PATH = os.path.join(ROOT_PATH, 'helpers')

# Set loggers
set_stdout_logger()
logfile_handler_id = set_logfile_handler()

# Create a variable to store the setpoints
daily_outputs = None
# Create a variable to store the main results
final_outputs = None

expected_revenues = 0
last_soc = 0
last_soc2 = 0
degradation = 0
degradation2 = 0
total_degradation = 0
total = 0
first_dt_text = 0

# Create a final outputs JSON (for future API purposes)
final_outputs = {
	'date': [],
	'status': [],
	'status_real': [],
	'expected_revenues': [],
	'degradation': [],
	'degradation2': [],
	'total_degradation': [],
	'total': [],
	'last_soc': [],
	'time': [],
}

