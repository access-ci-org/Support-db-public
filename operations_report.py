##
##
## This code is provided by the Operations team to obtain software data
## We also use it to obtain info about different RPs and their groups/ids
## original code can be found here: https://github.com/access-ci-org/software_modules

import argparse
import collections
import datetime
import json
import logging
import pathlib
import requests
# from . import libutil

import pprint


# Module level resources
resources = {}


def get_args( params=None ):
    key = 'args'
    if key not in resources:
        constructor_args = {
            'formatter_class': argparse.RawDescriptionHelpFormatter,
            'description': 'Software modules per resourceid or groupid',
        }
        parser = argparse.ArgumentParser( **constructor_args )
        parser.add_argument( '-d', '--debug', action='store_true' )
        parser.add_argument( '-v', '--verbose', action='store_true' )
        parser.add_argument( '-f', '--force', action='store_true',
            help='Force update cache from web API'
            )
        parser.add_argument( '-t', '--cache_timeout',
            type=int,
            default=1,
            help='Max age, in days, to use cached data (default: %(default)s)'
            )
        parser.add_argument( '-p', '--pretty', action='store_true',
            help='Print pretty, human readable, json output' )
        # parser.add_argument( '-o', '--output',
        #     choices=['text', 'csv'],
        #     default='text',
        #     )
        args = parser.parse_args( params )
        resources[key] = args
    return resources[key]


def get_session():
    key = 'session'
    if key not in resources:
        resources[key] = requests.Session()
    return resources[key]


def get_json_file( fn ):
    if not fn:
        raise UserWarning( 'missing json filename' )
    key = f'{fn}.json'
    if key not in resources:
        resources[key] = pathlib.Path( key )
    return resources[key]


def grab_api_resources( key, server, path, params ):
    logging.info( f'get {key} resources' )
    if key not in resources:
        fn = pathlib.Path(f"data/{get_json_file( key )}")
        update_needed = True
        if fn.exists():
            logging.debug( f"cache file '{fn}' found" )
            # check age
            args = get_args()
            delta = datetime.timedelta( seconds = (args.cache_timeout * 86400) )
            min_age = ( datetime.datetime.now() - delta ).timestamp()
            cache_age = fn.stat().st_mtime
            if cache_age > min_age:
                update_needed = False
                logging.debug( f"cache update not needed" )
        if update_needed:
            # get data from api
            url = f'https://{server}/{path}'
            logging.debug( f"fetching cache update from '{url}'" )
            response = api_get( url, params )
            data = response.json()
            # write the new data to file
            with fn.open( mode='w' ) as fh:
                json.dump( data, fh, indent=2 )
            logging.debug( "cache update successful" )
            # save the new data directly since we already have it
            resources[key] = data
        else:
            # Read data from cache file
            logging.debug( f"loading cached data for resource '{key}'" )
            with fn.open() as fh:
                json_data = json.load( fh )
                resources[key] = json_data
    return resources[key]


def api_go( method, url, **kw ):
    logging.debug( f'{method} {url}, {pprint.pformat(kw)}' )
    s = get_session()
    # to use personal access token, must disable netrc function in requests
    # s.trust_env = False
    # s.headers = {
    #     "Accept": "application/json",
    #     "Content-Type": "application/json",
    #     }
    r = s.request( method, url, **kw )
    logging.debug( f'RETURN CODE .. {r}' )
    # logging.debug( f'RETURN HEADERS .. {r.headers}' )
    r.raise_for_status()
    return r


def api_get( url, params=None ):
    return api_go( method='GET', url=url, params=params, timeout=600 )


def get_RP_groups():
    key = 'rp_groups'
    server = 'operations-api.access-ci.org'
    path = 'wh2/cider/v1/access-active-groups/'
    params = { 'format': 'json' }
    return grab_api_resources( key, server, path, params )


def get_sw_fast():
    key = 'sw_fast'
    server = 'operations-api.access-ci.org'
    path = 'wh2/glue2/v1/software_fast/'
    params = { 'format': 'json' }
    return grab_api_resources( key, server, path, params )


def process_rp_groups( data ):
    compute_resources = []
    for rp in data['results']['resources']:
        if rp['cider_type'] == "Compute":
            compute_resources.append( rp['info_resourceid'] )
    resource_groups = {}
    for grp in data['results']['active_groups']:
        group_name = grp['info_groupid']
        resource_ids = grp['rollup_info_resourceids']
        resource_names = []
        for name in resource_ids:
            if name in compute_resources:
                resource_names.append( name )
        if len( resource_names ) > 0:
            resource_groups[ group_name ] = resource_names
    return resource_groups


def process_sw_modules( data ):
    modules_per_rp = collections.defaultdict( list )
    for module in data['results']:
        rp = module['ResourceID']
        module_id = module['ID']
        modules_per_rp[rp].append( module )
    return modules_per_rp


def populate_empty_RPs( groups, modules_per_rp ):
    ''' For each RP with no modules reported, copy the list of modules from another
        resource. Choose the first option that has modules, in the order:
        1. group (info_groupid) (this is the default set of software)
        2. another RP (info_resourceid) with name matching the group name
        3. another RP from the same group
        Returns nothing (modules_per_rp is modified in place).
    '''
    for grp, resource_providers in groups.items():
        grp_count = 0
        if grp in modules_per_rp:
            grp_count = len(modules_per_rp[grp])
        logging.debug( f'GROUP: {grp} : {grp_count}' )
        for rp in resource_providers:
            # note, modules_per_rp is a defaultdict, so if rp isn't yet a key,
            # this access will create the key with an empty list as the val
            rp_count = len(modules_per_rp[rp])
            logging.debug( f"\t{rp} : {rp_count}" )
            if rp_count < 1:
                if grp_count > 0:
                    # option 1, use modules from the info_groupid
                    modules_per_rp[rp] = modules_per_rp[grp]
                    logging.info( f"using modules from group '{grp}' for RP '{rp}'" )
                else:
                    # option 2, if another RP in the group has a name matching
                    #           the group name
                    # actually, this option isn't any different from option 1,
                    # given the current data format the modules_per_rp doesn't
                    # differentiate between group and resource_provider
                    #
                    # so, move onto ...
                    # option 3
                    for rp2 in resource_providers:
                        # this access attempt will also create an entry
                        # if it didn't already exist
                        rp2_count = len(modules_per_rp[rp2])
                        if rp2_count > 0:
                            modules_per_rp[rp] = modules_per_rp[rp2]
                            logging.info( f"using modules from RP '{rp2}' for RP '{rp}'" )
                            break


def print_module_counts( modules_per_rp ):
    msg = "REPORT MODULES COUNT BY RP"
    print( '-' * len(msg) )
    print( msg )
    print( '-' * len(msg) )
    for rp in sorted( modules_per_rp.keys() ):
        print( f"\t{rp} : {len(modules_per_rp[rp])}" )
    print( 'END' )
    print( '-' * len(msg) )


def duplicate_names_vers( data ):
    ''' Scan software module data for duplicate software by name + version
    '''
    modules_per_rp = {}
    duplicates = {}
    for module in data['results']:
        name = module['AppName']
        ver = module['AppVersion']
        rp = module['ResourceID']
        name_ver = ''.join( [ x.strip() for x in (f'{name}:{ver}').split() ] )
        if len( name_ver ) < 2:
            logging.warning( f'empty name+ver for {pprint.pformat(module)}' )
            continue
        mpr = modules_per_rp.setdefault( rp, {} )
        if name_ver in mpr:
            logging.warning( f"duplicate entry: '{name_ver}' in '{rp}'" )
            dups = duplicates.setdefault( rp, {} )
            if name_ver not in dups:
                # get the first copy added, before we knew there were dups
                first = mpr[name_ver]
                dups[name_ver] = [ first ]
            # add the duplicate we just found
            dups[name_ver].append( module )
            continue
        mpr[ name_ver ] = module
    return duplicates


def run(save_file: pathlib.Path = './data/operations_data.json'):
    # args = get_args()
    # logging.debug( pprint.pformat( args ) )

    rp_groups = get_RP_groups()
    resource_groups = process_rp_groups( rp_groups )
    # pprint.pp(resource_groups)

    sw_fast = get_sw_fast()
    modules_per_rp = process_sw_modules( sw_fast )

    populate_empty_RPs( resource_groups, modules_per_rp )
    # if args.debug:
    #     print_module_counts( modules_per_rp )

    # parms = {}
    # if args.pretty:
    #     parms['indent'] = 2
    with open(save_file, 'w', encoding='utf-8') as sf:
        json.dump( modules_per_rp, sf, indent=2 )
    # print( json.dumps( modules_per_rp, indent=2 ) )

    # duplicates = duplicate_names_vers( sw_fast )
    # pprint.pprint( duplicates )
    # raise SystemExit()


if __name__ == '__main__':
    args = get_args()
    # libutil.setup_logging( args )
    run()