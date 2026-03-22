#!/usr/bin/env python
"""Check CSV file structure"""

import pandas as pd
import sys

filepath = r"c:\Users\aaa\Downloads\Stocks.csv"

try:
    # Try reading with skip bad lines
    df = pd.read_csv(filepath, on_bad_lines='skip')
    print(f"✅ Loaded {len(df)} rows")
    print(f"\nColumns: {df.columns.tolist()}")
    print(f"\nFirst few rows:")
    print(df.head())
    print(f"\nData types:")
    print(df.dtypes)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
