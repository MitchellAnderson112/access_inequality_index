# user defined variables
from config import *

def import_csv(state):
    '''
    import a csv into the postgres db
    '''
    db, context = cfg_init(state)

    county_codes = {'md':'510', 'wa':'033','nc':'129','il':'031','tx':'201',
                    'or':'051','ga':'121','la':'071','mi':'163','co':'031','fl':'086'}
    county = county_codes[state]

    # import distances
    dist = pd.read_sql("SELECT id_orig, distance FROM nearest_dist WHERE service = 'supermarket'", db['con'])
    dist = dist.loc[dist['distance']!=0]
    dist['geoid10'] = dist['id_orig']
    # import race and ethnicity
    file_name = '/file/Research/CivilSystems/data/usa/{}/{}/demo/demo.csv'.format(state, context['city_code'])
    demo = pd.read_csv(file_name, dtype = {'STATEA':str, 'COUNTYA':str,'TRACTA':str,'BLKGRPA':str,'BLOCKA':str, 'H7X001':int, 'H7X002':int, 'H7X003':int, 'H7X004':int, 'H7X005':int, 'H7Y003':int})
    demo = demo.loc[demo['H7X001']!=0] # remove zero pop blocks
    demo['geoid10'] = demo['STATEA'] + demo['COUNTYA'] + demo['TRACTA'] + demo['BLOCKA']
    demo['id_bg'] = demo['STATEA'] + demo['COUNTYA'] + demo['TRACTA'] + demo['BLKGRPA']

    # import income, poverty, and vehicle ownership
    file_name = '/file/Research/CivilSystems/data/usa/{}/ds176_20105_2010_blck_grp.csv'.format(state)
    # JOIE001 - median household income
    # JSNE001 - total housing units; JSNE003 - owner occupied houses with no vehicles, JDNE010 - renter occupied, no vehicles
    # JOCE001 - block group population; JOCE002 - poverty ratio < 0.5; JOCE003 - poverty ratio [0.5,1)
    demo_bg = pd.read_csv(file_name, dtype = {'STATEA':str, 'COUNTYA':str,'TRACTA':str,'BLKGRPA':str, 'JOIE001':float, 'JOCE001':int, 'JOCE002':int, 'JOCE003':int, 'JSNE001':int, 'JSNE003':int, 'JSNE010':int})
    demo_bg['id_bg'] = demo_bg['STATEA'] + demo_bg['COUNTYA'] + demo_bg['TRACTA'] + demo_bg['BLKGRPA']


    # join the dataframes
    demo = pd.merge(demo, demo_bg, on='id_bg', how='inner')
    dem_cols = ['geoid10','H7X001', 'H7X002', 'H7X003', 'H7X004', 'H7X005',
                'H7Y003', 'JOIE001', 'JOCE001', 'JOCE002', 'JOCE003', 'JSNE001',
                'JSNE003', 'JSNE010']
    distxdem = pd.merge(dist[['geoid10','distance']], demo[dem_cols], on='geoid10', how='inner')

    # upload to sql
    distxdem.to_sql('distxdem', db['engine'], if_exists='replace')
    cursor = db['con'].cursor()
    # commit
    db['con'].commit()


if __name__ == '__main__':
    state = input('State: ')
    import_csv(state)
