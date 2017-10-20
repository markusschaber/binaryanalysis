#!/usr/bin/python

'''
This script clears the avgstringscaches
and reinitiates them with new values.
'''

import sys, os, os.path
import psycopg2, ConfigParser
from optparse import OptionParser

def main(argv):
	config = ConfigParser.ConfigParser()

	parser = OptionParser()
	parser.add_option("-d", "--config", action="store", dest="cfg", help="path to caching database", metavar="FILE")
	(options, args) = parser.parse_args()
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
	try:
		conn = psycopg2.connect(database=postgresql_db, user=postgresql_user, password=postgresql_password, host=postgresql_host, port=postgresql_port)

		c = conn.cursor()
	except:
		print >>sys.stderr, "Database not running or misconfigured"
		sys.exit(1)
	
	try:
		query = "DELETE FROM avgstringscache_actionscript"
		c.execute(query)
		query = "DELETE FROM avgstringscache_c"
		c.execute(query)
		query = "DELETE FROM avgstringscache_csharp"
		c.execute(query)
		query = "DELETE FROM avgstringscache_java"
		c.execute(query)
		query = "DELETE FROM avgstringscache_javascript"
		c.execute(query)
		query = "DELETE FROM avgstringscache_php"
		c.execute(query)
		query = "DELETE FROM avgstringscache_python"
		c.execute(query)
		query = "DELETE FROM avgstringscache_ruby"
		c.execute(query)
		print "Clearing successfull."
		conn.commit()
		
		query = "INSERT INTO avgstringscache_c SELECT package, AVG(score) FROM scores_c, stringscache_java WHERE scores_c.stringidentifier = stringscache_c.stringidentifier GROUP BY package"
		c.execute(query)
		conn.commit()
		print "Insert in avgstringscache_c successfull."
		query = "INSERT INTO avgstringscache_csharp SELECT package, AVG(score) FROM scores_csharp, stringscache_csharp WHERE scores_csharp.stringidentifier = stringscache_csharp.stringidentifier GROUP BY package"
		c.execute(query)
		conn.commit()
		print "Insert in avgstringscache_csharp successfull."
		query = "INSERT INTO avgstringscache_java SELECT package, AVG(score) FROM scores_java, stringscache_java WHERE scores_java.stringidentifier = stringscache_java.stringidentifier GROUP BY package"
		c.execute(query)
		conn.commit()
		print "Insert in avgstringscache_java successfull."
		query = "INSERT INTO avgstringscache_javascript SELECT package, AVG(score) FROM scores_javascript, stringscache_javascript WHERE scores_javascript.stringidentifier = stringscache_javascript.stringidentifier GROUP BY package"
		c.execute(query)
		conn.commit()
		print "Insert in avgstringscache_javascript successfull."
		query = "INSERT INTO avgstringscache_php SELECT package, AVG(score) FROM scores_php, stringscache_php WHERE scores_php.stringidentifier = stringscache_php.stringidentifier GROUP BY package"
		c.execute(query)
		conn.commit()
		print "Insert in avgstringscache_php successfull."
		query = "INSERT INTO avgstringscache_python SELECT package, AVG(score) FROM scores_python, stringscache_python WHERE scores_python.stringidentifier = stringscache_python.stringidentifier GROUP BY package"
		c.execute(query)
		conn.commit()
		print "Insert in avgstringscache_python successfull."
		query = "INSERT INTO avgstringscache_ruby SELECT package, AVG(score) FROM scores_ruby, stringscache_ruby WHERE scores_ruby.stringidentifier = stringscache_ruby.stringidentifier GROUP BY package"
		c.execute(query)
		conn.commit()
		print "Insert in avgstringscache_ruby successfull."
		query = "INSERT INTO avgstringscache_actionscript SELECT package, AVG(score) FROM scores_actionscript, stringscache_actionscript WHERE scores_actionscript.stringidentifier = stringscache_actionscript.stringidentifier GROUP BY package"
		c.execute(query)
		print "Insert in avgstringscache_actionscript successfull."
		conn.commit()
	except Exception, e:
		print e;
		print >>sys.stderr, "Database update failed"
		sys.exit(1)	
	
if __name__ == "__main__":
	main(sys.argv)