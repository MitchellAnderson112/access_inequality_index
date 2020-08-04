import utils
from config import *

states = ['md','fl', 'co', 'mi', 'la', 'ga', 'or', 'il', 'wa', 'tx']
cities = {'md':'baltimore','fl':'miami','co':'denver','mi':'detroit','la':'new orleans','ga':'atlanta','or':'portland','il':'chicago','wa':'seattle','tx':'houston'}
distances = []

for state in states:
    # connect to the psql database
    db, context = cfg_init(state)
    # download the data for the city
    sql = 'SELECT distance, "H7X001", "H7X002", "H7X003", "H7X004", "H7X005", "H7Y003" FROM distxdem;'
    city_dist = pd.read_sql(sql, db["con"])
    # add city
    city_dist['city'] = cities[state]
    # record
    distances.append(city_dist)

df = pd.concat(distances)
df.to_csv('../data/results/supermarket_distance.csv')
