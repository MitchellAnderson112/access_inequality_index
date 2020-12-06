import nearest_dist
import add_socioeco
import init_osrm
import query
import yaml
import subprocess
# functions - logging
import logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

def single_region():
    # establish config filename
    config_filename = input('Insert Config Filename (filename.yaml): ')
    if ('yaml' in config_filename) == True:
        config_filename = config_filename[:-5]
    # run
    query_osrm(config_filename)


def multi_regions():
    # establish config filenames
    states = ['wa', 'tx','il','md','fl', 'co', 'mi', 'la', 'ga', 'or']
    for state in states:
        config_filename = state
        # calculate the distances
        query_osrm(config_filename)
        # determine the nearest distance
        logger.info('determine the nearest distance for {}'.format(state))
        nearest_dist.determine_nearest(state)
        # merge with socioeconomic data
        logger.info('merge with socioeconomic data')
        add_socioeco.import_csv(state)



def query_osrm(config_filename):
    # import config file
    with open('./src/config/{}.yaml'.format(config_filename)) as file:
        config = yaml.load(file)

    # initialize the OSRM server
    logger.info('Initialize the OSRM server for {} to {} in {}'.format(config['transport_mode'], config['services'],config['location']['city']))
    init_osrm.main(config, logger)
    logger.info('OSRM server initialized')

    # query the OSRM server
    query.main(config)

    # shutdown the OSRM server
    if config['OSRM']['shutdown']:
        shell_commands = [
                            'docker stop osrm-{}'.format(config['location']['state']),
                            'docker rm osrm-{}'.format(config['location']['state']),
                            ]
        for com in shell_commands:
            com = com.split()
            subprocess.run(com)
    logger.info('OSRM server shutdown and removed')

if __name__ == '__main__':
    multi_regions()
