from fitparse import FitFile
import pandas as pd
import pathlib
import matplotlib.pyplot as plt
import numpy as np

'''
Creates a session level table loader for full activity history

Still using files like this to get used to working with fitparse.
This file will also help to set thresholds for qualifying
which runs to consider in this project.

As of 07/08/2026, here are the thresholds for qualifying
runs to consider in the model:

cadence: >= 160 spm
distance >= 4 miles
'''

files = pathlib.Path("data/raw").rglob("*.fit")

errors = 0
entries = []
fields = ['start_time', 'sport', 'sub_sport', 'total_distance','total_timer_time','total_elapsed_time','avg_heart_rate','max_heart_rate','avg_running_cadence','avg_fractional_cadence','total_ascent']
for f in files:
    try:
        file_path = str(f)
        fit = FitFile(file_path)
        gen = fit.get_messages("file_id")
        msg = next(gen) # decode genrator object, yield file_id message
        if msg.get_value('type') != 'activity':
            continue
        
        
        values = {field.name: field.value for field in next(fit.get_messages("session")) if field.name in fields}
        entries.append(values)
        
    except Exception:
        errors += 1
        print(f"Error detected: {errors} errors so far")
        
run_df = pd.DataFrame(entries, columns=fields)
        
print(f"Record count: {len(run_df)}\n")
print(f"Number of runs (according to df): {(run_df['sport'] == 'running').sum()}\n")


runs_subset = run_df[run_df['sport'] == 'running']
true_cadence = (runs_subset['avg_running_cadence'] + runs_subset['avg_fractional_cadence']) * 2
pace = (runs_subset['total_distance']) / (runs_subset['total_timer_time'])

print(f"True cadence row described: {true_cadence.describe()}\n")

print(f"Pace described: {pace.describe()}\n")
pace.describe()


plt.figure()
plt.ylabel('Number of runs')
plt.xlabel('Cadence (steps/minute)')
plt.hist(true_cadence, bins=50)


plt.figure()
plt.ylabel('Number of runs')
plt.xlabel('Pace (m/s)')
plt.hist(pace, bins=50)

plt.show()
