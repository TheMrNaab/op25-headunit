import csv
from collections import defaultdict

filename = "control_scan.csv"
signal_data = defaultdict(list)

with open(filename, newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        if len(row) < 7:
            continue  # Skip bad lines
        freq_start = float(row[2])
        freq_step = float(row[4])
        db_values = list(map(float, row[6:]))
        for i, db in enumerate(db_values):
            freq = freq_start + i * freq_step
            signal_data[freq].append(db)

# Average signal strength per frequency bin
averages = {
    freq: sum(values)/len(values) for freq, values in signal_data.items()
}

# Sort by signal strength (strongest = least negative)
top = sorted(averages.items(), key=lambda x: x[1], reverse=True)

# Show top 10 frequencies
for freq, avg_db in top[:10]:
    print(f"{freq/1e6:.4f} MHz => {avg_db:.2f} dB")