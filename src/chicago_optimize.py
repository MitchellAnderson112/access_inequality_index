
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

# get distances
dist = pd.read_sql("SELECT id_orig, distance FROM nearest_dist WHERE service = 'Market_20'", db['con'])
# merge the distances with the demographic data
dist = pd.merge(dist, demograph, left_on='id_orig', right_on='geoid10')
# drop blocks with zero pop
dist = dist.loc[dist['H7X001'] !=0]
# converts from meters to Kms
dist.distance = dist.distance/1000
dist_current = dist

# calculate kappa
beta = -1.0
kappa = inequality_function.calc_kappa(dist_current.distance,
                                        beta, weights = dist_current['H7X001'])

# all distances
sql = 'SELECT * FROM block2blockgroup'
block2bg = pd.read_sql(sql, db["con"])
block2bg = block2bg.rename(columns={'id_orig':'geoid10'})
block2bg = block2bg.set_index('id_dest', drop=False)
block2bg = block2bg.sort_index()

bg_selected = []
ede_selected = []
bg_candidates = np.unique(block2bg.index)

for i in tqdm(range(5)):
    ede_candidates = []
    for candidate in bg_candidates:
        # get the new distances
        dist_new = block2bg[block2bg.index.isin([candidate] + bg_selected)]
        # dist_new = block2bg[block2bg.id_dest == candidate]
        # add to the current distances
        dist_concat = pd.concat([dist_current, dist_new])
        # determine the new minimum distances
        dist_min = dist_concat.groupby('geoid10').min()
        dist_min = dist_min[~np.isnan(dist_min[group])]
        if optimizer == 'mean':
            # calculate the mean
            ede = np.average(dist_min.distance,
                                weights = dist_min[group])
        else:
            # calculate the new EDE
            ede = inequality_function.kolm_pollak_ede(dist_min.distance,
                                                    kappa = kappa,
                                                    weights = dist_min[group])
        # store EDE and candidate node
        ede_candidates += [ede]
    # select candidate with minimum EDE
    index_min = np.argmin(ede_candidates)
    bg_chosen = bg_candidates[index_min]
    bg_selected += [bg_chosen]
    ede_selected += [ede_candidates[index_min]]
    print(ede_selected)
    # repeat for remaining candidates
    bg_candidates = np.delete(bg_candidates, index_min)



# save to bg and ede to file:
import csv
fn = '/homedirs/man112/access_inequality_index/data/results/chicago_supermarkets_optimize_{}.csv'.format(optimizer)
with open(fn, 'w', newline='') as myfile:
     wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
     wr.writerow(bg_selected)

# add the results to the csv
year = 'optimize_{}'.format(optimizer)
fn ='/homedirs/man112/access_inequality_index/data/results/chicago_supermarkets_{}.csv'.format(beta)
df = pd.read_csv(fn)
df = df.drop(['Unnamed: 0'], axis=1)

# determine new distance
dist_new = block2bg[block2bg.index.isin(bg_selected)]
dist_concat = pd.concat([dist_current, dist_new])
dist_min = dist_concat.groupby('geoid10').min()
dist_min = dist_min[~np.isnan(dist_min[group])]

# calculate poverty
percentage_poverty = (dist_min['JOCE002'] + dist_min['JOCE003'])/dist_min['JOCE001']
dist_min['poverty'] = percentage_poverty * dist_min['H7X001']
dist_min['poverty'] = dist_min['poverty'].fillna(0)
dist_min['poverty'] = dist_min['poverty'].astype(int)

# no vehicle access
percentage = (dist_min['JSNE003'] + dist_min['JSNE010'])/dist_min['JSNE001']
dist_min['no_vehicle'] = percentage * dist_min['H7X001']
dist_min['no_vehicle'] = dist_min['no_vehicle'].fillna(0)
dist_min['no_vehicle'] = dist_min['no_vehicle'].astype(int)

# calculate the edes
subgroups = ['H7X001','H7X002','H7X003','H7X004','H7X005','H7Y003',
             'poverty','no_vehicle']

results = []
for group in subgroups:
    # calculate the ede
    ede = inequality_function.kolm_pollak_ede(dist_min.distance,
                                                kappa = kappa,
                                                weights = dist_min[group])
    # new result
    result_i = [year, group, ede]
    results.append(result_i)

results = pd.DataFrame(results, columns = ['year','group','ede'])
results.ede = results.ede/1000

df = pd.concat([df,results])
df.to_csv(fn)
# inequality_function.kolm_pollak_ede(dist_current.distance, kappa = kappa, weights = dist_current['H7X001'])
#
#
# import time
#
# t = time.process_time()
# block2bg.index.isin([candidate])
# # block2bg.id_dest == candidate
# elapsed_time = time.process_time() - t
#
