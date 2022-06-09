import json
import logging

class EveBuilder:
    def __init__(self, project):
        self.project = project
        self.glob_sett = {}
        if 'eve_config' in self.project.keys():
            for key, value in self.project['eve_config'].items():
                if key == 'rate_limit_get':
                    self.glob_sett[key.upper()] = eval(value)
                else:
                    self.glob_sett[key.upper()] = value

    def generate_domain(self):
        domain = {}
        PREFIX_NUM = 1
        logging.info('Generating domain for Eve configuration')

#        if not 'group' in self.project['group'] or not 'endpoints' in self.project['group'].keys():
#            raise ValueError
        group = self.project['group']
        print(group)
        for endpoint in self.project['group']['endpoints']:
            print(endpoint)
            f = open(endpoint['schema_file'], 'r', encoding='utf8')
            schema = json.load(f)
            f.close()
            if schema == None:
                logging.debug('Skipped %s table for Eve domain. Empty schema' % (endpoint['id']))
                continue
            logging.debug('Adding %s table to Eve domain' % (endpoint['id']))
            self.glob_sett['MONGO%d_HOST' % PREFIX_NUM] = group['host']
            self.glob_sett['MONGO%d_DBNAME' % PREFIX_NUM] = endpoint['dbname']
            self.glob_sett['MONGO%d_PORT' % PREFIX_NUM] = group['port']
            rec = {    'item_title': endpoint['item_title'],
            'mongo_prefix' : 'MONGO%d' % (PREFIX_NUM),
            'allowed_filters' : list(endpoint['allowed_filters']),
            'datasource' : {'source' : endpoint['source']},
                               'schema' : schema}
            domain['%s/%s' % (endpoint['dbname'], endpoint['source'])] = rec
            PREFIX_NUM += 1

        self.glob_sett['DOMAIN'] = domain
        return domain

    def build(self, output=None):
        self.generate_domain()
        if output:
            f = open(output, 'w', encoding='utf8')
            f.write(json.dumps(self.glob_sett, indent=4))
            f.close()
        return self.glob_sett
