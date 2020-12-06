state = 'il'
from config import *
db, context = cfg_init(state)
import inequality_function
import numpy as np

group = 'H7X001'
# optimizer = 'ede_{}'.format(group)
optimizer = 'mean'
print(group, optimizer)

# get demographics
demograph = pd.read_sql('SELECT * FROM distxdem', db["con"])
demograph = demograph.drop(columns=['distance'])
# save demographics
demograph.to_csv('../data/export/{}_demographics.csv'.format(context['city']))

# get distances
dist = pd.read_sql("SELECT id_orig, distance FROM nearest_dist WHERE service = 'Market_20'", db['con'])
# merge the distances with the demographic data
dist = pd.merge(dist, demograph, left_on='id_orig', right_on='geoid10')
# drop blocks with zero pop
dist = dist.loc[dist['H7X001'] !=0]
# converts from meters to Kms
dist.distance = dist.distance/1000
dist_current = dist
# save distances
dist.to_csv('../data/export/{}_distance_current.csv'.format(context['city']))



# all distances
sql = 'SELECT * FROM block2blockgroup'
block2bg = pd.read_sql(sql, db["con"])
block2bg = block2bg.rename(columns={'id_orig':'geoid10'})
block2bg = block2bg.set_index('id_dest', drop=False)
block2bg = block2bg.sort_index()
# save distances
block2bg.to_csv('../data/export/{}_distance_candidates.csv'.format(context['city']))
