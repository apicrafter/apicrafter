# -*- coding: utf-8 -*-
import errno
import logging

import yaml
import json
import uuid
import pkg_resources
from pymongo import MongoClient

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
import os
import glob

from ..builder.evebuilder import EveBuilder
from ..builder.schemer import generate_scheme
from ..utils import filehash

def load_config(filename):
    f = open(filename, 'r', encoding='utf8')
    data = yaml.load(f, Loader=Loader)
    f.close()
    return data

DB_STOP_LIST = ['admin', ]

class Project:
    def __init__(self, project_path=None, noload=False):
        """Init project class"""
        self.project = None
        self.project_path = os.getcwd() if project_path is None else project_path
        dpath = os.path.join(self.project_path)
        self.schemes = os.path.join(dpath, "schemes")
        self.cache = os.path.join(dpath, "cache")
        self.temp = os.path.join(dpath, "temp")
        self.logp = os.path.join(dpath, "log")
        self.project_filename = os.path.join(self.project_path, 'apicrafter.yml')

        self.logfile = os.path.join(self.logp, 'apicrafter.log')
        self.cache_file = os.path.join(self.cache, 'project_cache.json')
        self.project_hash_file = os.path.join(self.cache, 'project_hash.txt')
        if not noload:
            self.__read_project_file(self.project_filename)
            self.enable_logging()

    def enable_logging(self):
        """Enable logging to file and stderr"""
        logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
        rootLogger = logging.getLogger()

        fileHandler = logging.FileHandler("{0}".format(self.logfile))
        fileHandler.setLevel(logging.DEBUG)
        fileHandler.setFormatter(logFormatter)
        rootLogger.addHandler(fileHandler)

        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(logFormatter)
        rootLogger.addHandler(consoleHandler)

    def __read_project_file(self, filename):
        """Reads project file content"""
        self.project = None
        if os.path.exists(self.project_filename):
            self.project = load_config(self.project_filename)
        else:
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), self.project_filename)

    def init(self):
        """Initialize project. Creates required dirs if they do not exists"""
        logging.info('Initialize project. Create required directories')
        # Create dirs if not exists
        for k in [
            self.cache,
            self.schemes,
            self.temp,
            self.logp
        ]:
            try:
                os.makedirs(k)
            except Exception as e:
                logging.info("Directory %s can't be created" % (k))
                pass

    def log(self):
        # FIXME! Logging outside system logging
        pass


    def is_rebuild_needed(self):
        """Verifies if rebuild needed"""
        if os.path.exists(self.project_hash_file):
            f = open(self.project_hash_file, 'r', encoding='utf8')
            old_hash = f.read()
            f.close()
            hash = filehash(self.project_filename)
            if old_hash == hash:
                return False
        return True


    def build(self, force=False):
        """Builds and cache"""
        if not force:
            if not self.is_rebuild_needed():
                return
        builder = EveBuilder(self.project)
        builder.build(self.cache_file)
        pass


    def clean(self, basepath=None, clean_storage=False):
        """Clean up temporary data"""
        logging.info('Clean project data. Clean storage: %s' % (str(clean_storage)))

        for dirname, msg in [(self.cache, 'cache dir'), (self.temp, 'tempdir') ]:
            logging.info('Cleaning %s' % (msg))
            filelist = glob.glob(os.path.join(self.project_path, dirname, "*.*"))
            for f in filelist:
                logging.debug('Remove %s from %s' % (f, basepath))
                os.remove(f)
        pass

    def discover(self, host, port, dbname=None, username=None, password=None, dbtype='mongodb', update=False):
        """Create data schemas and endpoints for single or multiple tables"""
        if not update:
            self.init()
        known_routes_filename = pkg_resources.resource_filename('apicrafter', 'data/template.yml')
        f = open(known_routes_filename, 'r', encoding='utf8')
        data = yaml.load(f, Loader=Loader)
        f.close()
        if username:
            client = MongoClient('mongodb://%s:%s@%s:%d/'  %(username, password, host, port))
        else:
            client = MongoClient(host, port)
        group = {'host' : host, 'port' : port}
        if dbname:
            databases = [dbname, ]
        else:
            databases = []
            dblist = client.list_databases()
            for db in dblist:
                if db['name'] in DB_STOP_LIST:
                    continue
                databases.append(db['name'])
        for dbname in databases:
            db = client[dbname]
            collections = db.list_collections()
            endpoints = []
            for coll in collections:
                name = coll['name']
                scheme_filename = '%s_%s.json' % (dbname, name.replace('/', '_').replace('\\', '_'))
                scheme = generate_scheme(client, dbname, collname=name, alimit=10000)
                if scheme:
                    f = open(os.path.join(self.schemes, scheme_filename), 'w', encoding='utf8')
                    f.write(json.dumps(scheme, indent=4))
                    f.close()
                    index_list = db[name].index_information()
                    afilters = []
                    for key, value in index_list.items():
                        for k in value['key']:
                            if k[0] not in afilters:
                                afilters.append(k[0])
                    endpoints.append({'id' : name, 'dbname' : dbname, 'source' : name, 'item_title' : name, 'allowed_filters' : afilters, 'schema_file' : 'schemes/%s' % (scheme_filename) })
                    print('Added db %s collection %s' % (dbname, name))
        group['endpoints'] = endpoints
        data['group'] = group
        data['project-id'] = str(uuid.uuid4())
        f = open('apicrafter.yml', 'w', encoding='utf8')
        f.write(yaml.dump(data))
        f.close()
        print('Wrote apicrafter.yml')


    def run(self):
        """Run server"""
        from eve import Eve
        from eve_swagger import add_documentation, swagger
        if os.path.exists(self.cache_file):
            f = open(self.cache_file, 'r', encoding='utf8')
            settings = json.load(f)
            f.close()
            app = Eve(settings=settings)
            app.register_blueprint(swagger.get_swagger_blueprint())
            app.config['SWAGGER_INFO'] = self.project['openapi']['config']

            app.config['SWAGGER_EXAMPLE_FIELD_REMOVE'] = True
            # optional. Will use flask.request.host if missing.
            app.config['SWAGGER_HOST'] = '127.0.0.1'

        if 'logging' in self.project.keys():
            if 'logfile' in self.project['logging'].keys():
                handler = logging.FileHandler(self.project['logging']['logfile'], mode='a')

                handler.setFormatter(logging.Formatter(
                        '%(asctime)s %(levelname)s: %(message)s '
                        '[in %(filename)s:%(lineno)d] -- ip: %(clientip)s, '
                        'url: %(url)s, method:%(method)s'))

                app.logger.setLevel(logging.DEBUG)

            # append the handler to the default application logger
        app.logger.addHandler(handler)

        app.run(host=self.project['server']['host'], port=self.project['server']['port'], debug=True)



