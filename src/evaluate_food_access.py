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
file_name = 'food_des_{}'.format(beta)
weight_code = 'H7X001'

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
    city, data = get_data()
    # kappa is based on the distances from ALL states and the beta provided
    kappa = determine_kappa(data, beta, quantity='distance')
    kappa_income = determine_kappa(data, np.absolute(beta), quantity='JOIE001')
    # initialize dataframe
    results = pd.DataFrame(np.nan, index=np.arange(10), columns=['State','City', 'Kappa', 'Beta', 'Kolm-Pollak EDE', 'Atkinson EDE', 'Atkinson Adjusted EDE', 'Kolm-Pollak Index', 'Atkinson Index', 'Atkinson Adjusted Index', 'Gini Index', 'Distribution Mean', 'Distribution Max', 'Distribution Standard Deviation', 'Distribution Coefficient of Variation','Income EDE'])
    results.State = states
    results = results.set_index('State')
    # evaluate equality
    for state in states:
        # Gets the df for specific state
        df = data['{}_data'.format(state)].copy()
        # drop data that has 0 weight
        df = df.iloc[np.array(df[weight_code]) > 0].copy()
        # invert values for atkinson
        a = list(df.distance)
        at = list(1/df.distance)
        weight = list(df[weight_code])
        # adds the city name
        results.City = city
        # adds aversion params
        results.loc[state, 'Kappa'], results.loc[state, 'Beta'] = kappa, beta
        # adds all Kolm-Pollak metrics
        results.loc[state, 'Kolm-Pollak Index'], results.loc[state, 'Kolm-Pollak EDE'] = inequality_function.kolm_pollak_index(a, beta, kappa, weight), inequality_function.kolm_pollak_ede(a, beta, kappa, weight)
        # adds all normal (with inverted x) atkinson metrics
        results.loc[state, 'Atkinson Index'], results.loc[state, 'Atkinson EDE'] = inequality_function.atkinson_index(at, np.absolute(beta), weight), inequality_function.atkinson_ede(at, np.absolute(beta), weight)
        # adds all adjusted atkinson metrics
        results.loc[state, 'Atkinson Adjusted Index'], results.loc[state, 'Atkinson Adjusted EDE'] = inequality_function.atkinson_adjusted_index(a, beta, weight), inequality_function.atkinson_adjusted_ede(a, beta, weight)
        # adds gini
        results.loc[state, 'Gini Index'] = inequality_function.gini_index(a, beta, weight)
        # adds all summary stats from the distribution
        results.loc[state, 'Distribution Mean'], results.loc[state, 'Distribution Max'], results.loc[state, 'Distribution Standard Deviation'], results.loc[state, 'Distribution Coefficient of Variation'] = get_stats(df)
        # adds KP for income
        weight = [weight[i] for i in range(len(df)) if not np.isnan(df.loc[i,'JOIE001'])]
        incomes = [df.loc[i,'JOIE001'] for i in range(len(df)) if not np.isnan(df.loc[i,'JOIE001'])]
        results.loc[state, 'Income EDE'] = inequality_function.kolm_pollak_ede(incomes, kappa=kappa_income, weight=weight)

    # plot_gini(data)
    #plot_hist(data)
    # plot_scatter(results)
    plot_cdf(data)
    results.to_csv('/homedirs/man112/access_inequality_index/data/results/{}_{}.csv'.format(file_name,weight_code))


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

def get_stats(df):
    '''provides Mean, Max, STD, COV for distribution of dist and pop'''
    pop_total = df['H7X001'].sum()
    df = df.sort_values(by='distance')
    hist_data = [] #init list for distribution data
    count = 0
    for i in df['distance']:
        for pop in range(int(df['H7X001'].iloc[count])):
            hist_data.append(i) #for each person in block, appends the distance
        count += 1
    mean = np.mean(hist_data)
    max = np.max(hist_data)
    std = np.std(hist_data)
    cov = std/mean
    return(mean, max, std, cov)

###
# Plots
###
def plot_cdf(data = None):
    '''plots a cdf from a dataframe'''
    if not data:
        city, data = get_data()
    for state in states:#['tx','il']:
        for group in ['H7X001']:#,'H7X002','H7X003','H7Y003']:
            df = data['{}_data'.format(state)].copy() #gets correct dataframe
            pop_tot = df[group].sum()
            df = df.sort_values(by='distance')
            df['pop_perc'] = df[group].cumsum()/pop_tot*100 #percentage of pop
            plt.plot(df.distance, df.pop_perc, label=state+'_'+group) #plot the cdf
    # labels
    plt.ylabel('% Residents')
    plt.xlabel('Distance to the nearest supermarket (km)'.format())
    plt.legend(loc='best')
    # limits
    plt.xlim([0,10])
    plt.ylim([0,105])
    # savefig
    fig_out = '/homedirs/man112/access_inequality_index/fig/CDF_{}.pdf'.format(group)
    plt.savefig(fig_out, dpi=500, format='pdf', transparent=True, bbox_inches='tight',facecolor='w')

def plot_scatter(results):
    '''
    scatter plot the equality metrics
    '''
    ## Mean vs Gini
    x = 'Distribution Mean'; y = 'Gini Index'; lbl = 'City'
    ax = results.plot.scatter(x=x, y=y, c='#1E386A')
    results[[x,y,lbl]].apply(lambda row: ax.text(*row),axis=1);
    # labels
    plt.ylabel(y)
    plt.xlabel('Average distance to the nearest store (km)')
    # limits
    plt.xlim([0,3.5])
    plt.ylim([0,0.6])
    # savefig
    fig_out = '/homedirs/man112/access_inequality_index/fig/scatter_gini.pdf'
    plt.savefig(fig_out, dpi=500, format='pdf', transparent=True, bbox_inches='tight',facecolor='w')

    ## EDE: distance vs income
    x = 'Income EDE'; y = 'Kolm-Pollak EDE'; lbl = 'City'
    ax = results.plot.scatter(x=x, y=y, c='#1E386A')
    results[[x,y,lbl]].apply(lambda row: ax.text(*row),axis=1);
    # labels
    plt.ylabel('EDE of distance to the nearest store (km)')
    plt.xlabel('EDE of median household income ($)')
    # limits
    plt.xlim([0,70000])
    plt.ylim([0,4])
    # savefig
    fig_out = '/homedirs/man112/access_inequality_index/fig/scatter_income.pdf'
    plt.savefig(fig_out, dpi=500, format='pdf', transparent=True, bbox_inches='tight',facecolor='w')
    plt.clf()


def plot_gini(data):
    '''Takes dictionary of dataframes and plots gini on one plot'''
    for state in states:
        df = data['{}_data'.format(state)] #gets the right dataframe
        pop_tot = df.H7X001.sum()
        dist_tot = df.distance.sum()
        df = df.sort_values(by='distance')
        df['pop_perc'] = df.H7X001.cumsum()/pop_tot*100
        df['dist_perc'] = df.distance.cumsum()/dist_tot*100
        plt.plot(df.pop_perc, df.dist_perc, label=state) # plots gini curve for state
    plt.plot(np.arange(0,101,1), np.arange(0, 101, 1), '--', color='black', lw=0.5, label = 'Perfect Equality Line') # plots perfect equality line, x=y
    # labels
    plt.xlabel('% Residents')
    plt.ylabel('% Distance')
    plt.title('Gini Curve'.format(loc='center'))
    plt.legend(loc='best')
    # limits
    plt.xlim([0,None])
    plt.ylim([0,None])
    #Save figrue
    fig_out = '/homedirs/man112/access_inequality_index/data/results/GINI_test.pdf'.format()
    if os.path.isfile(fig_out):
        os.remove(fig_out)
    plt.savefig(fig_out, dpi=500, format='pdf', transparent=False)#, bbox_inches='tight')
    plt.clf()

def plot_hist(data):
    '''takes dictionary of dataframes and plots a histogram on subplots'''
    fig, axes = plt.subplots(ncols=2,nrows=5, sharex=True, sharey=True, gridspec_kw={'hspace':0.5}) #set up subplots
    print('Collecting Histogram Data')
    for state, ax in zip(states, axes.flat):
        df = data['{}_data'.format(state)] #get the right df
        pop_tot = df.H7X001.sum()
        df = df.sort_values(by='distance')
        hist_data = [] #init list for distribution data
        count = 0
        for i in tqdm((df.distance)):
            for pop in range(df.H7X001.iloc[count]):
                hist_data.append(i) #for each person in block, appends distance
        sns.distplot(hist_data, hist = True, kde = True, bins = int(100), label = state, ax=ax, color=random.choice(['red','blue','green','yellow','orange','purple', 'pink']), kde_kws={'color':'black'}) #plots hist
        ax.title.set_text(state)
    plt.xlim([0,20])
    plt.ylim([0,None])
    # save fig
    fig_out = '/homedirs/man112/access_inequality_index/data/results/HIST_test.pdf'.format()
    if os.path.isfile(fig_out):
        os.remove(fig_out)
    plt.savefig(fig_out, format='pdf')#, bbox_inches='tight')
    plt.clf()

def calc_percentiles(data=None):
    '''takes dictionary of dataframes with pop and dist. returns cdf'''
    if data is None:
        city, data = get_data()
    percentiles = pd.DataFrame()
    for state in states:
        df = data['{}_data'.format(state)] #gets correct dataframe
        pop_tot = df.H7X001.sum()
        df = df.sort_values(by='distance')
        df['pop_perc'] = df.H7X001.cumsum()/pop_tot*100 #percentage of pop
        df['state'] = state
        percentiles = percentiles.append(df[['state','distance','pop_perc']], ignore_index=True)
    # select which percentiles
    percentiles['keep'] = False
    for p in [10,50,75,90,95,100]:
        percentiles['dif'] = (percentiles.pop_perc-p).abs()
        percentiles.loc[percentiles.groupby('state')['dif'].idxmin(),'keep'] = True
    percentiles = percentiles.loc[percentiles.keep,]
    percentiles['pop_perc'] = percentiles['pop_perc'].round(0).apply(str)
    percentiles['distance'] = percentiles['distance'].round(2)
    percentiles = percentiles.drop_duplicates(["state", "pop_perc"])
    percentiles = percentiles.pivot(index='state', columns='pop_perc', values='distance')
    # save
    percentiles.to_csv('/homedirs/man112/access_inequality_index/data/results/food_des/distance_percentiles.csv')


def plot_edes(data = None):
    '''plots the ede and inequality indices'''
    if not data:
        file_name = 'food_des_{}'.format(beta)
        data = pd.read_csv('/homedirs/man112/access_inequality_index/data/results/food_des/{}_{}.csv'.format(file_name, weight_code))

    # sort the data by the KP EDE
    data = data.sort_values(by='Kolm-Pollak EDE')
    # print(data)
    # plot on a line graph
    ax = plt.axes()
    plt.locator_params(axis='y', nbins=4)
    data.plot(x="City", y=["Kolm-Pollak EDE", "Atkinson EDE", "Atkinson Adjusted EDE", "Distribution Mean"],ax=ax)
    plt.ylim([0, 4])
    plt.xticks(range(10),data.City)
    plt.xticks(rotation=90)
    plt.axhline(y = 0, color = 'black', linewidth = 1.3, alpha = .7)
    fig_out = '/homedirs/man112/access_inequality_index/fig/ede_compare.pdf'.format()
    plt.savefig(fig_out, dpi=500, format='pdf', transparent=True, bbox_inches='tight',facecolor='w')
    plt.show()
    plt.clf()

    # plot the indices on another line graph
    ax = plt.axes()
    plt.locator_params(axis='y', nbins=3)
    data.plot(x="City", y=["Kolm-Pollak Index", "Atkinson Index", "Atkinson Adjusted Index", "Distribution Coefficient of Variation", "Gini Index"],ax=ax)
    plt.ylim([0, 1])
    plt.xticks(range(10),data.City)
    plt.xticks(rotation=90)
    plt.axhline(y = 0, color = 'black', linewidth = 1.3, alpha = .7)
    fig_out = '/homedirs/man112/access_inequality_index/fig/index_compare.pdf'.format()
    plt.savefig(fig_out, dpi=500, format='pdf', transparent=True, bbox_inches='tight',facecolor='w')
    plt.show()

def plot_edes_dem():
    '''plots the ede and inequality indices'''

    # get the data
    city, data = get_data() # data is a dictionary of dataframes for each state
    kappa_data = get_kappa_data(data)
    kappa = inequality_function.calc_kappa(kappa_data, beta) # kappa is based on the distances from ALL states and the beta provided
    results = pd.DataFrame(np.nan, index=np.arange(10), columns=['State','City', 'KP_EDE_H7X001', 'KP_IE_H7X001', 'KP_EDE_H7X002', 'KP_IE_H7X002', 'KP_EDE_H7X003', 'KP_IE_H7X003','KP_EDE_H7X004', 'KP_IE_H7X004','KP_EDE_H7X005', 'KP_IE_H7X005','KP_EDE_H7Y003', 'KP_IE_H7Y003'])
    # adds the city name
    results.State = states
    results = results.set_index('State')
    results.City = city
    for state in states:
        # Gets the df for specific state
        df = data['{}_data'.format(state)].copy()
        # loop demographic
        for race in ['H7X001','H7X002','H7X003','H7X004','H7X005','H7Y003']:
            # drop data that has 0 weight
            dr = df.iloc[np.array(df[race]) > 0].copy()
            a = list(dr.distance)
            at = list(1/dr.distance)
            weight = list(dr[race])
            # adds all Kolm-Pollak metrics
            results.loc[state, 'KP_EDE_{}'.format(race)], results.loc[state, 'KP_IE_{}'.format(race)] = inequality_function.kolm_pollak_ede(a, kappa = kappa, weight = weight), inequality_function.kolm_pollak_index(a, kappa = kappa, weight = weight)

    print(results)
    results.to_csv('/homedirs/man112/access_inequality_index/data/results/food_des/ede_dems_{}.csv'.format(beta))
    # sort the data by the KP EDE
    results = results.sort_values(by='KP_EDE_H7X001')
    # plot on a line graph
    ax = plt.axes()
    plt.locator_params(axis='y', nbins=4)
    results.plot(x="City", y=["KP_EDE_H7X001", "KP_EDE_H7X002", "KP_EDE_H7X003","KP_EDE_H7Y003"],ax=ax)
    plt.ylim([0, None])
    plt.xticks(range(10),results.City)
    plt.xticks(rotation=90)
    plt.axhline(y = 0, color = 'black', linewidth = 1.3, alpha = .7)
    fig_out = '/homedirs/man112/access_inequality_index/fig/ede_race_compare.pdf'.format()
    plt.savefig(fig_out, dpi=500, format='pdf', transparent=True, bbox_inches='tight',facecolor='w')
    plt.show()
    plt.clf()

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


def city_dems():
    ''' get a table with information about the cities '''
    city, data = get_data()
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
        new_result = [cities[state], pop_total, perc_white, perc_black, perc_nindian, perc_asian, perc_latin]
        # add to results
        results.append(new_result)
    # make list to DataFrame
    results = pd.DataFrame(results, columns=['City','Population','% White','% Black','% Am. Indian','% Asian','% Latino'])
    results = results.round(1)
    results = results.set_index('City')
    results.to_csv('/homedirs/man112/access_inequality_index/data/results/food_des/city_dems.csv')
    print(results)


if __name__ == '__main__':
    main()
