from collections import namedtuple

from lxml import etree

from cassis.typesystem import TypeSystem, Type, Feature

class TypeSystemDeserializer():

    def parse(self, source):
        """

        Args:
            source: a filename or file object containing XML data

        Returns:
            typesystem (TypeSystem):
        """
        types = []

        context = etree.iterparse(source, events=('end', ), tag=('{*}typeDescription', ))
        for action, elem in context:
            name = elem.find('{*}name').text or ''
            description = elem.find('{*}description').text or ''
            supertypeName = elem.find('{*}supertypeName').text or ''
            features = []

            for feature_description in elem.iterfind('{*}features/{*}featureDescription'):
                feature = self._parse_feature(feature_description)
                features.append(feature)

            type = Type(name, description, supertypeName, features)
            types.append(type)

            # https://www.ibm.com/developerworks/xml/library/x-hiperfparse/
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]
        del context

        return TypeSystem(types)

    def _parse_feature(self, elem):
        name = elem.find('{*}name').text or ''
        description = elem.find('{*}description').text or ''
        rangeTypeName = elem.find('{*}rangeTypeName').text or ''
        return Feature(name, description, rangeTypeName)