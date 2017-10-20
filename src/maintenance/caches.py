#!/usr/bin/python

'''
This script first clears all caches in the given Database, except
the avgstringscaches. After the caches were cleared, the script
reinitiates those caches with new values.
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
		query = "DELETE FROM stringscache_actionscript"
		c.execute(query)
		query = "DELETE FROM stringscache_c"
		c.execute(query)
		query = "DELETE FROM stringscache_csharp"
		c.execute(query)
		query = "DELETE FROM stringscache_java"
		c.execute(query)
		query = "DELETE FROM stringscache_javascript"
		c.execute(query)
		query = "DELETE FROM stringscache_php"
		c.execute(query)
		query = "DELETE FROM stringscache_python"
		c.execute(query)
		query = "DELETE FROM stringscache_ruby"
		c.execute(query)
		
		query = "DELETE FROM fieldcache_java"
		c.execute(query)
		
		query = "DELETE FROM classcache_java"
		c.execute(query)
		
		query = "DELETE FROM varnamecache_c"
		c.execute(query)
		
		query = "DELETE FROM functionnamecache_c"
		c.execute(query)
		query = "DELETE FROM functionnamecache_java"
		c.execute(query)
		print "Clearing successfull"
		conn.commit()
		
		query = "INSERT INTO stringscache_java SELECT DISTINCT stringidentifier, package, filename FROM extracted_string, processed_file WHERE extracted_string.checksum = processed_file.checksum AND language = 'Java';"
		c.execute(query)
		conn.commit()
		print "Insert in stringscache_java successfull"
		query = "INSERT INTO stringscache_c SELECT DISTINCT stringidentifier, package, filename FROM extracted_string, processed_file WHERE extracted_string.checksum = processed_file.checksum AND language = 'C';"
		c.execute(query)
		conn.commit()
		print "Insert in stringscache_c successfull"
		query = "INSERT INTO stringscache_javascript SELECT DISTINCT stringidentifier, package, filename FROM extracted_string, processed_file WHERE extracted_string.checksum = processed_file.checksum AND language = 'JavaScript';"
		c.execute(query)
		conn.commit()
		print "Insert in stringscache_javascript successfull"
		query = "INSERT INTO stringscache_csharp SELECT DISTINCT stringidentifier, package, filename FROM extracted_string, processed_file WHERE extracted_string.checksum = processed_file.checksum AND language = 'C#';"
		c.execute(query)
		conn.commit()
		print "Insert in stringscache_csharp successfull"
		query = "INSERT INTO stringscache_php SELECT DISTINCT stringidentifier, package, filename FROM extracted_string, processed_file WHERE extracted_string.checksum = processed_file.checksum AND language = 'PHP';"
		c.execute(query)
		conn.commit()
		print "Insert in stringscache_php successfull"
		query = "INSERT INTO stringscache_python SELECT DISTINCT stringidentifier, package, filename FROM extracted_string, processed_file WHERE extracted_string.checksum = processed_file.checksum AND language = 'Python';"
		c.execute(query)
		conn.commit()
		print "Insert in stringscache_python successfull"
		query = "INSERT INTO stringscache_ruby SELECT DISTINCT stringidentifier, package, filename FROM extracted_string, processed_file WHERE extracted_string.checksum = processed_file.checksum AND language = 'Ruby';"
		c.execute(query)
		conn.commit()
		print "Insert in stringscache_ruby successfull"
		query = "INSERT INTO stringscache_actionscript SELECT DISTINCT stringidentifier, package, filename FROM extracted_string, processed_file WHERE extracted_string.checksum = processed_file.checksum AND language = 'ActionScript';"
		c.execute(query)
		conn.commit()
		print "Insert in stringscache_actionscript successfull"
		
		query = "INSERT INTO fieldcache_java SELECT DISTINCT name, package FROM extracted_name, processed_file WHERE extracted_name.type = 'field' AND extracted_name.checksum = processed_file.checksum AND extracted_name.language = 'Java';"
		c.execute(query)
		conn.commit()
		print "Insert in fieldcache_java successfull"
		
		query = "INSERT INTO classcache_java SELECT DISTINCT name, package FROM extracted_name, processed_file WHERE extracted_name.type = 'class' AND extracted_name.checksum = processed_file.checksum AND extracted_name.language = 'Java';"
		c.execute(query)
		conn.commit()
		print "Insert in classcache_java successfull"
		
		query = "INSERT INTO varnamecache_c SELECT DISTINCT name, package FROM extracted_name, processed_file WHERE extracted_name.type = 'variable' AND extracted_name.checksum = processed_file.checksum AND extracted_name.language = 'C';"
		c.execute(query)
		conn.commit()
		print "Insert in varnamecache_c successfull"
		
		query = "INSERT INTO functionnamecache_c SELECT DISTINCT functionname, package FROM extracted_function, processed_file WHERE extracted_function.checksum = processed_file.checksum AND extracted_function.language = 'C';"
		c.execute(query)
		conn.commit()
		print "Insert in functionnamecache_c successfull"
		query = "INSERT INTO functionnamecache_java SELECT DISTINCT functionname, package FROM extracted_function, processed_file WHERE extracted_function.checksum = processed_file.checksum AND extracted_function.language = 'Java';"
		c.execute(query)
		conn.commit()
		print "Insert in functionnamecache_java successfull"
	except Exception, e:
		print e
		print >>sys.stderr, "Database update failed"
		sys.exit(1)
	
if __name__ == "__main__":
	main(sys.argv)