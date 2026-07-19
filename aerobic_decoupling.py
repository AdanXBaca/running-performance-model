from fitparse import FitFile
import pandas as pd
import matplotlib.pyplot as plt
from session_table import build_session_table, filter_running, apply_coarse_filter,\
    compute_running_metrics, root_dir, fields, distance_thresh, cadence_thresh

'''
This file creates the record level fine screen running on top of 
session_table.py's coarse screen. It computes aerobic decoupling
as a data quality filter before a run's efficiency factor (EF) 
is trusted.

The decoupling percentage evaluates how the aerobic efficients 
ratio shifts over the course of a run. The sign tells you about
the efficiency across the run: negative means the ratio drops in the
second half, slower for the same heart rate or higher heart rate
for the same speed, which is to be expected with exhaustion during
a run. A positive value would be unusual, indicating that you
are getting more efficient as the run continues. 

Magnitude of the percentage indicates trustworthiness. As of
07/19/2026, I've decided that ~5% indicates a clean run and can
be trusted for an EF sample, where ~10% may indicate some drift
and the run should be either dropped or downweighted. Further
this ~5-10% band isn't a fully pinned down decision yet,
still will be taking more into consideration when getting to the
pass/fail logic.

Uses the field `enhanced_speed` from the fit record since `speed`
and `enhanced_avg_speed` are unpopulated at the record level

'''

# obtain session table and metrics from session_table.py
run_df = build_session_table(root_dir, fields)
runs_subset = filter_running(run_df)
true_cadence, pace = compute_running_metrics(runs_subset)
good_runs = apply_coarse_filter(runs_subset, true_cadence, cadence_thresh, distance_thresh)

run = good_runs.iloc[50]['file_path']
fit = FitFile(run)

entries = []
columns = ["distance", "heart_rate", "timestamp", "enhanced_speed"]
for record in fit.get_messages("record"):
    values = {field.name: field.value for field in record}
    entries.append(values)
 
run_record_df = pd.DataFrame(entries, columns=columns)
for col in columns:
    print(f"type of {col}: {run_record_df[col].dtype}")

print(f"Record count: {len(run_record_df)}\n")

print(run_record_df.head())
print(run_record_df.tail())

# made the decision to trim entries at the beginning of the dataframe
# that have 'enhanced_speed' as 0, since they are a recording artifact from
# starting the watch activity. we will be keeping zero-speed rows that 
# occur later in the run since these can serve as real mid-run signals
first_valid_index = run_record_df[run_record_df['enhanced_speed'] > 0].index[0]
run_record_trimmed = run_record_df[first_valid_index:].reset_index(drop=True)


# split by position instead of timestamp since count window represents
# actual moving time regardless of time elapsed
mid = len(run_record_trimmed) // 2
first_half = run_record_trimmed.iloc[:mid]
second_half = run_record_trimmed.iloc[mid:]

# use ratio of averages since it is consistent with EF definition and
# it is more robust to HR sensor glitches, where a bad HR reading could
# explode a per-record ratio if it's near zero
first_half_ratio = (first_half['enhanced_speed']).mean() / (first_half['heart_rate']).mean()
second_half_ratio = (second_half['enhanced_speed']).mean() / (second_half['heart_rate']).mean()


# NOTE: decoupling != EF, this ratio below is a diagnostic quantity. It is the 
# difference between the second halfs speed/HR ratio and the first half's. 
# it evaluates how the aerobic efficients ratio shifts over the course of the run
decoupling_pct = (second_half_ratio - first_half_ratio) / first_half_ratio * 100
print(f"Decoupling percentage: {decoupling_pct}")


fig, ax1 = plt.subplots()
first_ten_min = run_record_trimmed[:600]
ax1.plot(first_ten_min['timestamp'], first_ten_min['heart_rate'], color='blue', label='HR')
ax1.set_xlabel('Time')
ax1.set_ylabel("Heart Rate (bpm)", color='blue')
ax1.tick_params(axis='y', labelcolor='blue')
ax1.legend()

ax2 = ax1.twinx()
ax2.plot(first_ten_min['timestamp'], first_ten_min['enhanced_speed'], color='red', label='Speed')
ax2.set_ylabel("Speed (m/s)", color='red')
ax2.tick_params(axis='y', labelcolor='red')
ax2.legend()

plt.show()
