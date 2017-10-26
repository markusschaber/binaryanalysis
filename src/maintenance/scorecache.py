#!/usr/bin/python

## Binary Analysis Tool
## Copyright 2014-2015 Armijn Hemel for Tjaldur Software Governance Solutions
## Licensed under Apache 2.0, see LICENSE file for details

'''
Script to initiate the score caches in the database.
'''

import sys, os, os.path
import psycopg2, ConfigParser
from optparse import OptionParser

def main(argv):
	alpha = 5.0
	config = ConfigParser.ConfigParser()

	parser = OptionParser()
	parser.add_option("-d", "--config", action="store", dest="cfg", help="path to caching database", metavar="FILE")
	(options, args) = parser.parse_args()
	# if options.db == None:
		# parser.error("Path to caching database")
	# if not os.path.exists(options.db):
		# print >>sys.stderr, "Caching database %s does not exist" % options.db
		# sys.exit(1)
	try:
		configfile = open(options.cfg, 'r')
	except:
		parser.error("Configuration file not readable")
	config.readfp(configfile)
	configfile.close()

	for section in config.sections():
		if section == "extractconfig":
			try:
				postgresql_user = config.get(section, 'postgresql_user')
				postgresql_password = config.get(section, 'postgresql_password')
				postgresql_db = config.get(section, 'postgresql_db')

				## check to see if a host (IP-address) was supplied either
				## as host or hostaddr. hostaddr is not supported on older
				## versions of psycopg2, for example CentOS 6.6, so it is not
				## used at the moment.
				try:
					postgresql_host = config.get(section, 'postgresql_host')
				except:
					postgresql_host = None
				try:
					postgresql_hostaddr = config.get(section, 'postgresql_hostaddr')
				except:
					postgresql_hostaddr = None

				## check to see if a port was specified. If not, default to 'None'
				try:
					postgresql_port = config.get(section, 'postgresql_port')
				except Exception, e:
					postgresql_port = None
			except:
				print >>sys.stderr, "Database connection not defined in configuration file. Exiting..."
				sys.stderr.flush()
				sys.exit(1)
		if section == "supportedlanguages":
			try:
				supported_languages = set()
				if config.get(section, 'C'):
					supported_languages.add('c',)
				if config.get(section, 'CSharp'):
					supported_languages.add('csharp',)
				if config.get(section, 'Java'):
					supported_languages.add('java',)
				if config.get(section, 'JavaScript'):
					supported_languages.add('javascript',)
				if config.get(section, 'Php'):
					supported_languages.add('php',)
				if config.get(section, 'Python'):
					supported_languages.add('python',)
				if config.get(section, 'Ruby'):
					supported_languages.add('ruby',)
				if config.get(section, 'ActionScript'):
					supported_languages.add('actionscript',)
			except Exception, e:
				print >>sys.stderr, "Malformed configuration file. Exiting..."
				print e
				sys.stderr.flush()
				sys.exit(1)
		
	try:
		conn = psycopg2.connect(database=postgresql_db, user=postgresql_user, password=postgresql_password, host=postgresql_host, port=postgresql_port)

		c = conn.cursor()
		c2 = conn.cursor()
	except:
		print >>sys.stderr, "Database not running or misconfigured"
		sys.exit(1)
		

	for language in supported_languages:
		try:
			query = "create table if not exists scores_%s (stringidentifier text, packages int, score real)" % (language)
			c.execute(query)
			query = "create index if not exists scores_%s_index on scores_%s(stringidentifier)" % (language, language)
			c.execute(query)
			conn.commit()

			query = "select distinct stringidentifier from stringscache_%s" % (language)
			c.execute(query)
			programstrings = c.fetchmany(10000)
			while programstrings != []:
				for p in programstrings:
					pkgs = {}
					filenames = {}

					query = "select distinct package, filename from stringscache_" + language + " where stringidentifier=%s"
					c2.execute(query,  p)
					pfs = c2.fetchall()
					packages = set(map(lambda x: x[0], pfs))
	
					if len(packages) == 1:
						score = float(len(p[0]))
					else:
						for pf in pfs:
							(package, filename) = pf
							if not filenames.has_key(filename):
								filenames[filename] = [package]
							else:   
								filenames[filename] = list(set(filenames[filename] + [package]))
						try:
							score = float(len(p[0])) / pow(alpha, (len(filenames) - 1))
						except Exception, e:
							score = len(p[0]) / sys.maxint
						## cut off for for example postgresql
						if score < 1e-37:
							score = 0.0
					query = "insert into scores_" + language + "(stringidentifier, packages, score) values (%s,%s,%s)"
					c2.execute(query, (p[0], len(packages), float(score)))
				programstrings = c.fetchmany(10000)
			conn.commit()
			print "Scores added for scores_%s" % (language)
		except Exception, e:
			print e
			print "Scores-Update failed for scores_%s" % (language)
	c2.close()
	# print "vacuuming"
	# c.execute("vacuum")
	conn.commit()
	c.close()
	conn.close()
	
if __name__ == "__main__":
	main(sys.argv)
