'''
For given beta and states, will take data from SQL with population and distance and provide:
    Kolm-Pollak Index & EDE
    Atkinson Index & EDE
    Adjusted Atkinson Index and EDE
    Gini Index
    Plot of Gini, CDF and Distribution
    Distribution summary statistics
'''

# User defined variables
beta = -1.0
states = ['md','fl', 'co', 'mi', 'la', 'ga', 'or', 'il', 'wa', 'tx']
cities = {'md':'baltimore','fl':'miami','co':'denver','mi':'detroit','la':'new orleans','ga':'atlanta','or':'portland','il':'chicago','wa':'seattle','tx':'houston'}

# Imports
import utils
from config import *
import inequality_function
import matplotlib
from tqdm import tqdm
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
import matplotlib.style as style
style.use('fivethirtyeight')
w = 5
h = w/1.618

def main():
    '''Calculates the EDE for different subgroups'''
    city, data = get_data()
    # kappa is based on the distances from ALL states and the beta provided
    kappa = determine_kappa(data, beta, quantity='distance')
    # subgroups to investigate
    subgroups = ['H7X001','H7X002','H7X003','H7X004','H7X005','H7Y003',
                 'poverty','not_poverty','vehicle_access','no_vehicle_access']
    # calculate two subgroups
    for state in states:
        data['{}_data'.format(state)] = estimate_poverty(data['{}_data'.format(state)])
        data['{}_data'.format(state)] = estimate_vehicle(data['{}_data'.format(state)])
    # initialize dataframe
    results = []
    # evaluate equality
    for state in tqdm(states):
        # loop through the subgroups
        for group in subgroups:
            # Gets the df for specific state
            df = data['{}_data'.format(state)].copy()
            # drop data that has 0 weight
            df = df.iloc[np.array(df[group]) > 0].copy()
            # calculate the ede
            ede = inequality_function.kolm_pollak_ede(list(df.distance), kappa = kappa, weights = list(df[group]))
            # new result
            result_i = [cities[state], group, ede]
            results.append(result_i)
    # make list of lists a dataframe
    results = pd.DataFrame(results, columns = ['city','group','ede'])
    # save result
    results.to_csv('/homedirs/man112/access_inequality_index/data/results/ede_subgroups_{}.csv'.format(beta))
    # plots
    plot_race(results)
    # plot_poverty(results)
    plot_vehicle(results)
    city_dems(data)


def get_data():
    '''fills a dictionary of dataframes for each state'''
    data = {} # init empty dictionary
    city = [] #init empty list of cities to return for the results
    for state in states:
        db, context = cfg_init(state)
        cursor = db['con'].cursor()
        sql = 'SELECT * FROM distxdem'
        data["{}_data".format(state)] = pd.read_sql(sql, db["con"])
        db['con'].close()
        city.append(context['city'])
        df = data['{}_data'.format(state)]
        df = df.loc[df['distance'] !=0] # removes all rows with 0 distance
        df = df.loc[df['H7X001'] !=0] # removes all rows with 0 population
        df.distance = df.distance/1000 # converts from meters to Kms
        # drop outliers (errors in the distance calculations) -> this would be better if it was identifying the neighbors and averaging
        Q1 = df.distance.quantile(0.25)
        Q3 = df.distance.quantile(0.75)
        IQR = Q3 - Q1
        is_outlier = (df.distance > (Q3 + 4 * IQR))
        df = df[~is_outlier]
        data['{}_data'.format(state)] = df # replaces the dataframe in the dictionary
    return(city, data)

def determine_kappa(data, beta, quantity):
    '''takes dictionary of dataframes and beta, minimised the sum of squares for all data to return kappa'''
    # prepare the data
    kappa_data = [] # init empty list for each distance
    for state in states:
        df = data['{}_data'.format(state)]
        count = 0
        for i in df[quantity]: #takes each distance
            if not np.isnan(i):
                for pop in range(int(df['H7X001'].iloc[count])): #adds the distance to the list as many times as there are people in the block
                    kappa_data.append(i)
                count += 1
    # calculate the kappa
    kappa = inequality_function.calc_kappa(kappa_data, beta)
    return(kappa)

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
    df['no_vehicle_access'] = percentage * df['H7X001']
    df['vehicle_access'] = (1-percentage) * df['H7X001']
    df['no_vehicle_access'] = df['no_vehicle_access'].fillna(0)
    df['vehicle_access'] = df['vehicle_access'].fillna(0)
    df['no_vehicle_access'] = df['no_vehicle_access'].astype(int)
    df['vehicle_access'] = df['vehicle_access'].astype(int)
    return df

###
# Plots
###
def plot_race(results):
    '''plots the ede for different racial groups'''
    results = results.pivot(index='city', columns='group', values='ede')
    # sort the data by the KP EDE
    results = results.sort_values(by='H7X001')
    # plot on a line graph
    ax = plt.axes()
    plt.locator_params(axis='y', nbins=5)
    results.plot(y=["H7X001", "H7X002", "H7X003"],ax=ax) #,"H7Y003"
    plt.ylim([0, 5])
    plt.xticks(range(10),results.index.values)
    plt.xticks(rotation=90)
    plt.xlabel('')
    plt.ylabel('Distance (km)')
    plt.axhline(y = 0, color = 'black', linewidth = 1.3, alpha = .7)
    fig_out = '/homedirs/man112/access_inequality_index/fig/ede_subgroup_race_{}.pdf'.format(beta)
    plt.savefig(fig_out, dpi=500, format='pdf', transparent=True, bbox_inches='tight',facecolor='w')
    plt.show()
    plt.clf()

def plot_vehicle(results):
    '''plots the ede for whether people have access to vehicles'''
    results = results.pivot(index='city', columns='group', values='ede')
    # sort the data by the KP EDE
    results = results.sort_values(by='H7X001')
    # plot on a line graph
    ax = plt.axes()
    plt.locator_params(axis='y', nbins=5)
    results.plot(y=["H7X001", "vehicle_access", "no_vehicle_access"],ax=ax)
    plt.ylim([0, 5])
    plt.xticks(range(10),results.index.values)
    plt.xticks(rotation=90)
    plt.xlabel('')
    plt.axhline(y = 0, color = 'black', linewidth = 1.3, alpha = .7)
    fig_out = '/homedirs/man112/access_inequality_index/fig/ede_subgroup_vehicle_{}.pdf'.format(beta)
    plt.savefig(fig_out, dpi=500, format='pdf', transparent=True, bbox_inches='tight',facecolor='w')
    plt.show()
    plt.clf()

def plot_poverty(results):
    '''plots the ede for poverty status'''
    results = results.pivot(index='city', columns='group', values='ede')
    # sort the data by the KP EDE
    results = results.sort_values(by='H7X001')
    # plot on a line graph
    ax = plt.axes()
    plt.locator_params(axis='y', nbins=4)
    results.plot(y=["H7X001", "not_poverty", "poverty"],ax=ax)
    plt.ylim([0, None])
    plt.xticks(range(10),results.index.values)
    plt.xticks(rotation=90)
    plt.axhline(y = 0, color = 'black', linewidth = 1.3, alpha = .7)
    fig_out = '/homedirs/man112/access_inequality_index/fig/ede_subgroup_poverty_{}.pdf'.format(beta)
    plt.savefig(fig_out, dpi=500, format='pdf', transparent=True, bbox_inches='tight',facecolor='w')
    plt.show()
    plt.clf()

def plot_ie(results):
    # this won't work unless you calculate the KP IE (currently the code is just calculating EDE)
    results = results.sort_values(by='KP_EDE_H7X001')
    # plot the indices on another line graph
    ax = plt.axes()
    plt.locator_params(axis='y', nbins=3)
    results.plot(x="City", y=["KP_IE_H7X001", "KP_IE_H7X002", "KP_IE_H7X003", "KP_IE_H7Y003"],ax=ax)
    plt.ylim([0, 1])
    plt.xticks(range(10),results.City)
    plt.xticks(rotation=90)
    plt.axhline(y = 0, color = 'black', linewidth = 1.3, alpha = .7)
    fig_out = '/homedirs/man112/access_inequality_index/fig/index_race_compare.pdf'.format()
    # plt.show()
    plt.savefig(fig_out, dpi=500, format='pdf', transparent=True, bbox_inches='tight',facecolor='w')


def city_dems(data):
    ''' get a table with information about the cities '''
    # initiate list
    results = list()
    # loop the states/cities
    for state in states:
        df = data['{}_data'.format(state)].copy()
        pop_total = df['H7X001'].sum()
        perc_white = df['H7X002'].sum()/pop_total*100
        perc_black = df['H7X003'].sum()/pop_total*100
        perc_nindian = df['H7X004'].sum()/pop_total*100
        perc_asian = df['H7X005'].sum()/pop_total*100
        perc_latin = df['H7Y003'].sum()/pop_total*100
        per_poverty = df['poverty'].sum()/pop_total*100
        per_no_car = df['no_vehicle_access'].sum()/pop_total*100
        new_result = [cities[state], pop_total, perc_white, perc_black, perc_nindian, perc_asian, perc_latin, per_poverty, per_no_car]
        # add to results
        results.append(new_result)
    # make list to DataFrame
    results = pd.DataFrame(results, columns=['City','Population','% White','% Black','% Am. Indian','% Asian','% Latino', '% Poverty','% No Vehicle'])
    results = results.round(1)
    results = results.set_index('City')
    results.to_csv('/homedirs/man112/access_inequality_index/data/results/city_dems.csv')
    print(results)


if __name__ == '__main__':
    main()
