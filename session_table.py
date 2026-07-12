from fitparse import FitFile
import pandas as pd
import pathlib
import matplotlib.pyplot as plt

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

def load_activity(file_path, fields): 
    file_path = str(file_path)
    fit = FitFile(file_path)
    gen = fit.get_messages("file_id")
    msg = next(gen) # decode genrator object, yield file_id message
    if msg.get_value('type') != 'activity':
        return None
        
    values = {field.name: field.value for field in next(fit.get_messages("session")) if field.name in fields}
    return values
    
def build_session_table(root_dir, fields):
    errors = 0
    entries = []
    files = pathlib.Path(root_dir).rglob("*.fit")
    for f in files:
        try:
            values = load_activity(f, fields)
            if values is not None:  
                entries.append(values)
                
        except Exception:
            errors += 1
            print(f"Error detected: {errors} errors so far")
    
    run_df = pd.DataFrame(entries, columns=fields)
    return run_df

def filter_running(run_df):
    return run_df[run_df['sport'] == 'running']

def compute_running_metrics(runs_subset):
    true_cadence = (runs_subset['avg_running_cadence'] + runs_subset['avg_fractional_cadence']) * 2
    pace = (runs_subset['total_distance']) / (runs_subset['total_timer_time'])
    return true_cadence, pace

def apply_coarse_filter(runs_subset, true_cadence, cadence_thresh, distance_thresh):
    distance_mask = runs_subset['total_distance'] >= distance_thresh
    cadence_mask = true_cadence >= cadence_thresh
    good_runs = runs_subset[distance_mask & cadence_mask]
    return good_runs

def print_summary(run_df, true_cadence, pace, good_runs):
    print(f"Record count: {len(run_df)}\n")
    print(f"Number of runs (according to df): {(run_df['sport'] == 'running').sum()}\n")
    
    print(f"True cadence row described: {true_cadence.describe()}\n")

    print(f"Pace described: {pace.describe()}\n")
    
    print(f"Num of filtered runs from thresholds: {len(good_runs)}\n")

def plot_distributions(true_cadence, pace):
    plt.figure()
    plt.ylabel('Number of runs')
    plt.xlabel('Cadence (steps/minute)')
    plt.hist(true_cadence, bins=50)

    plt.figure()
    plt.ylabel('Number of runs')
    plt.xlabel('Pace (m/s)')
    plt.hist(pace, bins=50)

    plt.show()
    
def main():
    root_dir = "data/raw"
    fields = ['start_time', 'sport', 'sub_sport', 'total_distance','total_timer_time','total_elapsed_time','avg_heart_rate','max_heart_rate','avg_running_cadence','avg_fractional_cadence','total_ascent']
    # filtering runs based on determined threshold
    distance_thresh = 6437.376 # 4 miles
    cadence_thresh = 160
    
    run_df = build_session_table(root_dir, fields)
    runs_subset = filter_running(run_df)
    true_cadence, pace = compute_running_metrics(runs_subset)
    good_runs = apply_coarse_filter(runs_subset, true_cadence, cadence_thresh, distance_thresh)
    
    print_summary(run_df, true_cadence, pace, good_runs)
    plot_distributions(true_cadence, pace)

if __name__ == "__main__":
    main()