from helpers import *

for line in open('migration.sql'):
	makeRequest(line)