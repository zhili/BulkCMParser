#!/usr/bin/env python
# 2010-07-28
# huzhili@gmail.com
# parse ericsson bulkcm to extract cell information, particularly cell neighbours
import sys
#thanks to Trent Mick (http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/475126)
try:
    import xml.etree.cElementTree as ET # python >=2.5 C module
except ImportError:
    try:
         import xml.etree.ElementTree as ET # python >=2.5 pure Python module
    except ImportError:
         try:
             import cElementTree as ET # effbot's C module
         except ImportError:
             try:
                 import elementtree.ElementTree as ET # effbot's pure Python module
             except ImportError:
                 try:
                     import lxml.etree as ET # ElementTree API using libxml2
                 except ImportError:
                     import warnings
                     warnings.warn("could not import ElementTree "
                                   "(http://effbot.org/zone/element-index.htm)")
import collections

class Map(object):
    """ Map wraps a dictionary. It is essentially an abstract class from which
    specific multimaps are subclassed. """
    def __init__(self):
        self._dict = {}

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, repr(self._dict))

    __str__ = __repr__

    def __getitem__(self, key):
        return self._dict[key]

    def __setitem__(self, key, value):
        self._dict[key] = value

    def __delitem__(self, key):
        del self._dict[key]

    def remove(self, key, value):
        del self._dict[key]

    def dict(self):
        """ Allows access to internal dictionary, if necessary. Caution: multimaps 
        will break if keys are not associated with proper container."""
        return self._dict

class ListMultimap(Map):
    """ ListMultimap is based on lists and allows multiple instances of same value. """
    def __init__(self):
        self._dict = collections.defaultdict(list)

    def __setitem__(self, key, value):
        self._dict[key].append(value)

    def remove(self, key, value):
        self._dict[key].remove(value)
								
class EsBulkCMCell():
	"""docstring for EsBulkCMCell"""
	def __init__(self, name):
		self.name = name
		self.latitude = 0
		self.longitude = 0
		self.beamDirection = []
		self.utranNeighbor = []
		self.gsmNeighbor = []
	def PrintMe(self):
		print '*'*30
		print self.name
		print "lat: %s, lon: %s" % (self.latitude, self.longitude)
		print "beamDirection: %s" % self.beamDirection
		print "--",
		print self.utranNeighbor
		print "--",
		print self.gsmNeighbor

def main(bulkcm_name): 
	sectorsMap = ListMultimap() # sectors with mulitmap dict
	Cells = []
	for event, node in ET.iterparse(bulkcm_name,  events=('start', 'end', 'start-ns', 'end-ns')):
		# if event == 'end' and node.tag:
			#print node.tag, node.attrib
			# pass
		if event == 'end' and node.tag == '{genericNrm.xsd}MeContext':
			# print node.tag, node.attrib['id']
			for nn in node:
				if nn.tag == '{genericNrm.xsd}ManagedElement':
					for n in nn:
						if n.tag == '{utranNrm.xsd}NodeBFunction':
							for nv in n:
								if nv.tag == '{genericNrm.xsd}VsDataContainer':
									for nvv in nv:
										if nvv.tag == '{genericNrm.xsd}attributes':
											sectordatas = nvv.find('{EricssonSpecificAttributes.7.3.xsd}vsDataSector')
											if sectordatas:
												# print sectordatas.tag
												# for elm in sectordatas:
												longitude = sectordatas.find('{EricssonSpecificAttributes.7.3.xsd}longitude')
												beamDirection = sectordatas.find('{EricssonSpecificAttributes.7.3.xsd}beamDirection')
												latitude =	sectordatas.find('{EricssonSpecificAttributes.7.3.xsd}latitude')
												sectorsMap[(int(latitude.text), int(longitude.text))] = int(beamDirection.text)

			node.clear()
		if event == 'end' and node.tag == '{utranNrm.xsd}UtranCell':
				# print '*'*30

				cellproperty = node.find('{genericNrm.xsd}VsDataContainer')
				if cellproperty.get('id') == node.get('id'):
					aCell = EsBulkCMCell(node.get('id'))
					vsdata = cellproperty[0].find('{EricssonSpecificAttributes.7.3.xsd}vsDataUtranCell')
					antennaPosition = vsdata.find('{EricssonSpecificAttributes.7.3.xsd}antennaPosition')
					lat = antennaPosition.find('{EricssonSpecificAttributes.7.3.xsd}latitude')
					lon = antennaPosition.find('{EricssonSpecificAttributes.7.3.xsd}longitude')
					aCell.beamDirection = sectorsMap[(int(lat.text), int(lon.text))]
					aCell.latitude = float(lat.text) / 93206.7  # 24bit latitude and longitude
					aCell.longitude = float(lon.text) / 46603.4
					# print latitude.text
				else:
					print >>sys.stderr, "bulkcm format error."
					sys.exit(2)
				utranrelation = node.findall('{utranNrm.xsd}UtranRelation')
				gsmrelation = node.findall('{geranNrm.xsd}GsmRelation')
				for utrancell in utranrelation:
					# print '--%s, %s' % (utrancell.tag, utrancell.attrib['id'])
					cellattributes = utrancell.find('{utranNrm.xsd}attributes')
					for ca in cellattributes:
						cadict = ca.text.split(',')
						# print '---%s' % cadict[-1]
						aCell.utranNeighbor.append(cadict[-1])
		
				for gsmcell in gsmrelation:
					# print '--%s, %s' % (gsmcell.tag, gsmcell.attrib['id'])
					gcellattributes = gsmcell.find('{geranNrm.xsd}attributes')
					for gca in gcellattributes:
						gcadict = gca.text.split(',')
						# print '---%s' % gcadict[-1]
						aCell.gsmNeighbor.append(gcadict[-1])
		
				Cells.append(aCell)
				del aCell
				node.clear()

			# print '*'*30
		elif event == 'start-ns':
			#print 'start-ns'
			pass
		elif event == 'end-ns':
			# print 'end-ns'
			pass
		else:
			# print 'none'
			pass

	for c in Cells:
		c.PrintMe()
# 			
# import cProfile
# cProfile.run('main()')

if __name__ == "__main__":
	if len(sys.argv) != 2:
		sys.exit(1)
	try:
		main(sys.argv[1])
	except KeyboardInterrupt:
		print >>sys.stderr, "system interrupted."
		sys.exit(1)