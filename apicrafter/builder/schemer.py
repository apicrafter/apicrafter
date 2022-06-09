import datetime
import bson
import logging
from pymongo import MongoClient

def merge_schemes(alist, novalue=True):
    """Merge cerberus schemes of two objects. Used to create schema from multiple objects of collection"""
    if len(alist) == 0:
        return None
    obj = alist[0]
    okeys = obj.keys()
    for item in alist[1:]:
        for k in item.keys():
            #            print(obj[k]['type'])
            if k not in okeys:
                obj[k] = item[k]
            elif obj[k]['type'] in ['integer', 'float', 'string', 'datetime']:
                if not novalue:
                    obj[k]['value'] += item[k]['value']
            elif obj[k]['type'] == 'dict':
                if not novalue:
                    obj[k]['value'] += item[k]['value']
                if 'schema' in item[k].keys():
                    obj[k]['schema'] = merge_schemes([obj[k]['schema'], item[k]['schema']])
            elif obj[k]['type'] == 'array':
                #                if 'subtype' not in obj[k].keys():
                #                   logging.info(str(obj[k]))
                if 'subtype' in obj[k].keys() and obj[k]['subtype'] == 'dict':
                    if not novalue:
                        obj[k]['value'] += item[k]['value']
                    if 'schema' in item[k].keys():
                        obj[k]['schema'] = merge_schemes([obj[k]['schema'], item[k]['schema']])
                else:
                    if not novalue:
                        obj[k]['value'] += item['value']
    return obj

OTYPES_MAP = [[type(""), 'string'],
              [type(u""), 'string'],
              [datetime.datetime, 'datetime'],
              [int, 'integer'],
              [bool, 'boolean'],
              [float, 'float'],
              [str, 'string'],
              [bson.int64.Int64, 'integer'],
              [bson.objectid.ObjectId, 'string'],
              [type([]), 'array']
              ]


def get_schemes(alist):
    """Returns list of schemes from list of objects"""
    results = []
    for o in alist:
        results.append(get_schema(o))
    return results

def get_schema(obj, novalue=True):
    """Returns scheme of the object"""
    result = {}
    for k in obj.keys():
        tt = type(obj[k])
        if obj[k] is None:
            result[k] = {'type': 'string', 'value' : 1}
        elif tt == type("") or tt == type(u"") or isinstance(obj[k], str):
            result[k] = {'type': 'string', 'value' : 1}
        elif isinstance(obj[k], str):
            result[k] = {'type': 'string', 'value': 1}
        elif tt == datetime.datetime:
            result[k] = {'type': 'datetime', 'value' : 1}
        elif tt == bool:
            result[k] = {'type': 'boolean', 'value' : 1}
        elif tt == float:
            result[k] = {'type': 'float', 'value' : 1}
        elif tt == int:
            result[k] = {'type': 'integer', 'value' : 1}
        elif tt == bson.int64.Int64:
            result[k] = {'type': 'integer', 'value' : 1}
        elif tt == bson.objectid.ObjectId:
            result[k] = {'type': 'string', 'value' : 1}
        elif tt == type({}):
            result[k] = {'type': 'dict', 'value' : 1, 'schema' : get_schema(obj[k])}
        elif tt == type([]):
            result[k] = {'type': 'array', 'value' : 1}
            if len(obj[k]) == 0:
                result[k]['type'] = 'string'
            else:
                found = False
                for otype, oname in OTYPES_MAP:
                    if type(obj[k][0]) == otype:
                        result[k]['type'] = oname
                        found = True
                if not found:
                    if type(obj[k][0]) == type({}):
                        result[k]['type'] = 'dict'
                        result[k]['schema'] =  merge_schemes(get_schemes(obj[k]))
                    else:
                        print('Unknown')
        else:
            logging.info("Unknown object %s type %s" % (k, str(type(obj[k]))))
            result[k] = {'type': 'string', 'value' : 1}
        if novalue:
            del result[k]['value']
    return result

def extract_keys(obj, parent=None, text=None, level=1):
    """Builds schema text for Python-Eve"""
    keys = []
    text = ''
    if not parent:
        text = "'schema': {\n"
    for k in obj.keys():
        if type(obj[k]) == type({}):
            text += "\t" * level + "'%s' : {'type' : 'dict', 'schema' : {\n" % (k)
            text += extract_keys(obj[k], k, text, level+1)
            text += "\t" * level + "}},\n"
        elif type(obj[k]) == type([]):
            text += "\t" * level + "'%s' : {'type' : 'list', 'schema' : { 'type' : 'dict', 'schema' : {\n" % (k)
            if len(obj[k]) > 0:
                item = obj[k][0]
                if type(item) == type({}):
                    text += extract_keys(item, k, text, level+1)
                else:
                    text += "\t" * level + "'%s' : {'type' : 'string'},\n" % (k)
            text += "\t" * level + "}}},\n"
        else:
            logging.info(str(type(obj[k])))
            text += "\t" * level + "'%s' : {'type' : 'string'},\n" % (k)
    if not parent:
        text += "}"
    return text

def generate_scheme(client, dbname, collname, alimit=1000, verbose=0):
    """Generates Python-Eve schema from Mongo collection"""
    db = client[dbname]
    coll = db[collname]
    cursor = coll.find().limit(alimit)
    records = []
    if verbose > 0:
        logging.info('Preparing data from db %s collection %s' % (dbname, collname))
    n = 0
    scheme = None
    for r in cursor:
        n += 1
        if scheme is None:
            scheme = get_schema(r)
        else:
            scheme = merge_schemes([scheme, get_schema(r)])
    return scheme
