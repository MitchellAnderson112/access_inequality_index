'''
For Chicago in 2007, 2011, 2014, 2020 return:
    Kolm-Pollak Index & EDE
    Plot CDF and Distribution
'''

# User defined variables
beta = -1.0
file_name = 'chicago_{}'.format(beta)

# Imports
import utils
from config import *
import inequality_function
import matplotlib
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
import matplotlib.style as style
style.use('fivethirtyeight')
w = 5
h = w/1.618

def main():
    '''Creates dataframe and adds data for each city before plotting and exporting CSV'''
    state = 'il'
    db, context = cfg_init(state)
    years = ['07','11','14','20']
    data = get_data(db, context, years)
    # kappa is based on the distances from ALL states and the beta provided
    kappa = determine_kappa(data, beta, quantity='distance', years=years)
    # subgroups to investigate
    subgroups = ['H7X001','H7X002','H7X003','H7X004','H7X005','H7Y003',
                 'poverty','not_poverty','vehicle','no_vehicle']
    # calculate two subgroups
    for year in years:
        data['{}_data'.format(year)] = estimate_poverty(data['{}_data'.format(year)])
        data['{}_data'.format(year)] = estimate_vehicle(data['{}_data'.format(year)])
    # initialize dataframe
    results = []
    # evaluate equality
    for year in tqdm(years):
        # loop through the subgroups
        for group in subgroups:
            # Gets the df for specific state
            df = data['{}_data'.format(year)].copy()
            # drop data that has 0 weight
            df = df.iloc[np.array(df[group]) > 0].copy()
            # calculate the ede
            ede = inequality_function.kolm_pollak_ede(list(df.distance), kappa = kappa, weight = list(df[group]))
            # new result
            result_i = [year, group, ede]
            results.append(result_i)
    # make list of lists a dataframe
    results = pd.DataFrame(results, columns = ['year','group','ede'])
    # save result
    results.to_csv('/homedirs/man112/access_inequality_index/data/results/chicago_supermarkets_{}.csv'.format(beta))

    # plots
    plot_cdf(data)
    map_files(db, data)


def get_data(db, context, years):
    '''fills a dictionary of dataframes for each state'''
    data = {} # init empty dictionary

    cursor = db['con'].cursor()
    # import the demographic data
    demograph = pd.read_sql('SELECT * FROM distxdem', db["con"])
    demograph = demograph.drop(columns=['distance'])
    for year in years:
        # import the distances for that year
        dist = pd.read_sql("SELECT id_orig, distance FROM nearest_dist WHERE service = 'Market_{}'".format(year), db['con'])
        # merge the distances with the demographic data
        dist = pd.merge(dist, demograph, left_on='id_orig', right_on='geoid10')
        # drop blocks with zero pop
        dist = dist.loc[dist['H7X001'] !=0]
        # converts from meters to Kms
        dist.distance = dist.distance/1000
        # store
        data["{}_data".format(year)] = dist
    return(data)

def determine_kappa(data, beta, quantity, years):
    '''takes dictionary of dataframes and beta, minimised the sum of squares for all data to return kappa'''
    # prepare the data
    kappa_data = [] # init empty list for each distance
    for year in years:
        df = data['{}_data'.format(year)]
        count = 0
        for i in df[quantity]: #takes each distance
            if not np.isnan(i):
                for pop in range(int(df['H7X001'].iloc[count])): #adds the distance to the list as many times as there are people in the block
                    kappa_data.append(i)
                count += 1
    # calculate the kappa
    kappa = inequality_function.calc_kappa(kappa_data, beta)
    return(kappa)

###
# Plots
###
def plot_cdf(data):
    '''plots a cdf from a dataframe'''
    years = ['07','11','14','20']
    for year in years:#['tx','il']:
        for group in ['H7X001']:#,'H7X002','H7X003','H7Y003']:
            df = data['{}_data'.format(year)].copy() #gets correct dataframe
            pop_tot = df[group].sum()
            df = df.sort_values(by='distance')
            df['pop_perc'] = df[group].cumsum()/pop_tot*100 #percentage of pop
            plt.plot(df.distance, df.pop_perc, label='20'+year) #plot the cdf
    # labels
    plt.ylabel('% Residents')
    plt.xlabel('Distance to the nearest supermarket (km)'.format())
    plt.legend(loc='best')
    # limits
    plt.xlim([0,4])
    plt.ylim([0,100])
    # savefig
    fig_out = '/homedirs/man112/access_inequality_index/fig/chicago_CDF_{}.pdf'.format(group)
    plt.savefig(fig_out, dpi=500, format='pdf', transparent=True, bbox_inches='tight',facecolor='w')

def map_files(db, data):
    '''output shapefiles for maps'''
    years = ['07','11','14','20']

    # import the block information
    sql = "SELECT * FROM block"
    blocks = gpd.GeoDataFrame.from_postgis(sql, db['con'], geom_col='geom')
    blocks = blocks[['geoid10','geom']]

    for year in years:
        df = data['{}_data'.format(year)].copy()
        # merge with the block data
        gdf = blocks.merge(df, on='geoid10')
        #Specifies the projection
        # gdf.crs= "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
        #exports file to my folder
        gdf.to_file(driver='ESRI Shapefile', filename='/homedirs/man112/access_inequality_index/fig/chicago_distance_{}.shp'.format(year))

### demographic
def estimate_poverty(df):
    # JOCE001 - block group population; JOCE002 - poverty ratio < 0.5; JOCE003 - poverty ratio [0.5,1)
    percentage_poverty = (df['JOCE002'] + df['JOCE003'])/df['JOCE001']
    df['poverty'] = percentage_poverty * df['H7X001']
    df['not_poverty'] = (1-percentage_poverty) * df['H7X001']
    df['poverty'] = df['poverty'].fillna(0)
    df['not_poverty'] = df['not_poverty'].fillna(0)
    df['poverty'] = df['poverty'].astype(int)
    df['not_poverty'] = df['not_poverty'].astype(int)
    return df

def estimate_vehicle(df):
    # JSNE001 - total housing units; JSNE003 - owner occupied houses with no vehicles, JSNE010 - renter occupied, no vehicles
    percentage = (df['JSNE003'] + df['JSNE010'])/df['JSNE001']
    df['no_vehicle'] = percentage * df['H7X001']
    df['vehicle'] = (1-percentage) * df['H7X001']
    df['no_vehicle'] = df['no_vehicle'].fillna(0)
    df['vehicle'] = df['vehicle'].fillna(0)
    df['no_vehicle'] = df['no_vehicle'].astype(int)
    df['vehicle'] = df['vehicle'].astype(int)
    return df


if __name__ == '__main__':
    main()
