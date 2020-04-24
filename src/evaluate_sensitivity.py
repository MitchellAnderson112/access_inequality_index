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
states = ['md','fl', 'co', 'mi', 'la', 'ga', 'or', 'il', 'wa', 'tx']
cities = {'md':'baltimore','fl':'miami','co':'denver','mi':'detroit','la':'new orleans','ga':'atlanta','or':'portland','il':'chicago','wa':'seattle','tx':'houston'}
weight_code = 'H7X001'

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
    '''Changes aversion parameter and calculates result'''
    city, data = get_data()
    results_fn = '/homedirs/man112/access_inequality_index/data/results/EDEs_{}.csv'.format(weight_code)
    if os.path.isfile(results_fn):
        results = pd.read_csv(results_fn)
    else:
        # initiate list
        results = list()
        # loop through beta values
        for beta in tqdm(np.concatenate(([0,-0.25,-0.5,-0.75, -1.5, -2],np.logspace(0,1)*-1),axis=None)):
            # calculate kappa from beta -- kappa is based on the distances from ALL states and the beta provided
            kappa = determine_kappa(data, beta, quantity='distance')
            # calculate the ede for each city
            for state in states:
                # get the data subset
                df = data['{}_data'.format(state)].copy()
                # calculate the values
                ede = inequality_function.kolm_pollak_ede(list(df.distance), kappa = kappa, weight = list(df['H7X001']))
                # add to list
                new_result = [cities[state], beta, ede]
                results.append(new_result)
        # make list of lists a dataframe
        results = pd.DataFrame(results, columns = ['city','beta','ede'])
        # save result
        results.to_csv(results_fn)
    # plots
    plot_aversion_continuous(results)
    # plot_aversion_discrete(results)
    plot_mean_ede_bycity(results, data)


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

###
# Plots
###
def plot_aversion_continuous(results):
    # pivot the dataset
    results_ede = results.pivot(index='beta', columns='city', values='ede')
    # plot the results
    ax = plt.axes()
    plt.locator_params(axis='y', nbins=4)
    results_ede.plot(ax=ax)
    plt.ylim([0, 20])
    plt.gca().invert_xaxis()
    fig_out = '/homedirs/man112/access_inequality_index/fig/sensitivity_aversion.pdf'
    plt.savefig(fig_out, dpi=800, format='pdf', transparent=True, bbox_inches='tight',facecolor='w')
    plt.clf()

def plot_aversion_discrete(results):
    # plot a selection of betas
    results_beta = results.copy()
    results_beta['beta'] = results_beta['beta'].round(2).apply(str)
    results_beta = results_beta.pivot(index='city', columns='beta', values='ede')
    results_beta = results_beta.sort_values(by='-0.5')
    ax = plt.axes()
    plt.locator_params(axis='y', nbins=3)
    results_beta.plot(y=['-0.25','-0.5','-0.75','-1.0','-1.5','-2.0'],ax=ax)
    plt.xticks(range(10),results_beta.index)
    plt.xticks(rotation=90)
    plt.ylim([0, 9])
    plt.yticks([0,3,6,9])
    fig_out = '/homedirs/man112/access_inequality_index/fig/sensitivity_aversion_cities.pdf'
    plt.savefig(fig_out, dpi=800, format='pdf', transparent=True, bbox_inches='tight',facecolor='w')

# def plot_mean_ede(results, data):
#     # calculate the mean for each city
#     results_mean = []
#     for state in states:
#         # get the data subset
#         df = data['{}_data'.format(state)].copy()
#         # calculate the values
#         value = np.average(list(df.distance), weights = list(df['H7X001']))
#         # add to list
#         new_result = [cities[state], 'mean', value]
#         results_mean.append(new_result)
#     results_mean = pd.DataFrame(results_mean, columns = ['city','beta','mean'])
#     results_mean = results_mean.pivot(index='city', columns='beta', values='mean')
#     # add mean to EDE table
#     results = pd.merge(results,results_mean, on='city')
#     # format for plot
#     results_beta = results.copy()
#     results_beta['beta'] = results_beta['beta'].round(2).apply(str)
#     print(results_beta)
#     results_beta = results_beta.pivot(index='mean', columns='beta', values='ede')
#     # results_beta = results_beta.sort_values(by='-0.5')
#     ax = plt.axes()
#     # plt.locator_params(axis='y', nbins=5)
#     results_beta.plot(y=['-0.25','-0.5','-0.75','-1.0','-1.5','-2.0'],ax=ax,style='o-')
#     plt.ylim([0, None])
#     plt.xlim([0, None])
#     plt.xlabel('Average distance to nearest store')
#     plt.ylabel('EDE distance to nearest store')
#     fig_out = '/homedirs/man112/access_inequality_index/fig/mean_ede.pdf'
#     plt.savefig(fig_out, dpi=800, format='pdf', transparent=True, bbox_inches='tight',facecolor='w')

def plot_mean_ede_bycity(results, data):
    # calculate the mean for each city
    results_mean = []
    for state in states:
        # get the data subset
        df = data['{}_data'.format(state)].copy()
        # calculate the values
        value = np.average(list(df.distance), weights = list(df['H7X001']))
        # add to list
        new_result = [cities[state], 'mean', value]
        results_mean.append(new_result)
    results_mean = pd.DataFrame(results_mean, columns = ['city','beta','mean'])
    results_mean = results_mean.pivot(index='city', columns='beta', values='mean')
    # add mean to EDE table
    results = pd.merge(results,results_mean, on='city')
    # format for plot
    results_beta = results.copy()
    results_beta['beta'] = results_beta['beta'].round(2).apply(str)
    results_beta = results_beta[results_beta.beta.isin(['-0.25','-0.5','-0.75','-1.0','-1.5','-2.0'])]
    ax = plt.axes()
    results_beta.groupby('city').plot(y='mean',x='ede',ax=ax,style='o-',label='city',linewidth=1)
    # results_beta = results_beta.pivot(index='mean', columns='city', values='ede')
    # results_beta = results_beta.sort_values(by='-0.5')
    # import code
    # code.interact(local=locals())
    # plt.locator_params(axis='y', nbins=5)
    # results_beta.plot(y=['-0.25','-0.5','-0.75','-1.0','-1.5','-2.0'],ax=ax,style='o-')
    L=plt.legend()
    cities_alph = list(cities.values())
    cities_alph.sort()
    [L.get_texts()[i].set_text(cities_alph[i]) for i in range(len(cities_alph))]

    plt.ylim([0, 3])
    plt.ylabel('Average distance to nearest store')
    plt.xlabel('EDE distance to nearest store')
    xy_line = (0,np.max(results_beta.ede))
    ax.plot(xy_line,xy_line, 'k--',linewidth=0.5)
    fig_out = '/homedirs/man112/access_inequality_index/fig/mean_ede.pdf'
    plt.savefig(fig_out, dpi=800, format='pdf', transparent=True, bbox_inches='tight',facecolor='w')


if __name__ == '__main__':
    main()
