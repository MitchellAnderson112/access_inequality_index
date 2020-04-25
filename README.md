# Measuring inequality in urban planning:
## Case study on USA grocery store access


### Code
1. run `src/query.py`
2. run `nearest_dist.py`
3. run `add_socioeco.py`
4. then run the analysis


import nearest_dist
import add_socioeco
states = ['md','fl', 'co', 'mi', 'la', 'ga', 'or', 'wa', 'tx']#, 'il']
for state in states:
    nearest_dist.determine_nearest(state)
    add_socioeco.import_csv(state)
