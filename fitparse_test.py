from fitparse import FitFile
import pandas as pd

'''
just a small test file to get myself
familiar with accessing .fit data from 
my garmin using fitparse.
'''


run = "data/23498896352_ACTIVITY.fit"
fit = FitFile(run)

columns = ["distance", "enhanced_speed", "heart_rate", "timestamp"]
entries = []
for record in fit.get_messages("record"):
    values = {field.name: field.value for field in record}
    entries.append(values)
 
run_df = pd.DataFrame(entries, columns=columns)     
for col in columns:
    print(f"type of {col}: {run_df[col].dtype}")

print(f"Record count: {len(run_df)}\n")

start = run_df["timestamp"].iloc[0]
end = run_df["timestamp"].iloc[-1]
print(f"Timespan:\n\tStart: {start}\n\tEnd: {end}\n\tTotal Time (According to activity from garmin: 44:39)\n")

print(f"Max timespan diff: {run_df["timestamp"].diff().max()}")

hr_vals = run_df["heart_rate"]
min_hr = hr_vals.min()
max_hr = hr_vals.max()
print(f"HR Range:\n\tMin HR: {min_hr}\n\tMax HR: {max_hr}\n\t")
