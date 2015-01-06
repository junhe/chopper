from ConfigParser import SafeConfigParser

confpath = "../conf/h0.conf"

def get_configparser():
    confparser = SafeConfigParser()
    try:
        confparser.readfp(open(confpath, 'r'))
    except:
        print "unable to read config file:", confpath
        exit(1)
    return confparser

parser = get_configparser()


