import logging

#from django.utils.text import slugify

from bs4 import BeautifulSoup
from contentimport.lib import u_slugify

logger = logging.getLogger(__name__)

class ManifestParser:

    def parse_manifests(self, manifest_xml):
        """
        accept a xml file to parse
        """
        soup = BeautifulSoup(manifest_xml, 'xml')

        data = {
            'manifests': [],
            'tags': [],
            'categories': []
        }

        for manifest in soup.find_all('manifest'):
            title = None
            description = None
            keywords = None
            categories = None

            m_title, m_description, m_keywords, m_categories = self.pull_metadata(manifest.metadata)

            m = {
                'package': {
                    'title': m_title,
                    'description': m_description,
                    'identifier': manifest['identifier'],
                    'version': manifest['version'] if 'version' in manifest else '0.0',
                    'categories': m_categories,
                },
                'resources': [],
            }

            organizations = manifest.find('organizations')
            
            if 'default' in organizations:
                o_default = organizations['default']
                if o_default is not None:
                    organization = organizations.find(identifier=o_default)
            else:
                organization = organizations.find('organization')

            for resource in manifest.find_all('resource'):
                item = None
                
                # check for href!
                r_href = resource['href']
                if r_href is None:
                    continue

                r_identifier = resource['identifier']
                position = None

                if organization is not None:
                    position = 0
                    # check if this resource is in org
                    item = organization.find('item', identifierref=r_identifier)
                    if item is None:
                        continue

                    title, description, keywords, categories = self.pull_metadata(item.metadata)
                    position = len(item.find_previous_siblings('item'))

                    # Use the <title> tag if there was no md
                    if title is None:
                        title = item.title.string

                    # If there was no <item> metadata, then use <organization>
                    if not all([title, description, keywords]):
                        o_title, o_description, o_keywords, o_categories = self.pull_metadata(organization.metadata)

                    if keywords is None: keywords = o_keywords
                    if categories is None: categories = o_categories

                if not all([title, description, keywords]):
                    r_title, r_description, r_keywords, r_categories = self.pull_metadata(resource.metadata)

                # If there was no md yet, then use <resource>'s'
                if title is None: title = r_title
                if description is None: description = r_description
                if keywords is None: keywords = r_keywords
                if categories is None: categories = r_categories

                # Manifest is the source of last resort for keywords and categories
                if keywords is None: keywords = m_keywords
                if categories is None: categories = m_categories

                # Limit size of categories
                if categories is not None and len(categories) > 3: categories = categories[:3]

                # slugify tags
                slug_keywords = []
                if keywords is not None:
                    for tag in keywords['list']:

                        logger.info('--------TAG--------')
                        logger.info(tag)
                        slugged_tag = u_slugify(tag)
                        logger.info(slugged_tag)
                        slug_keywords.append(slugged_tag)

                    keywords = {'ids': False, 'list': slug_keywords, }

                r = {
                    'identifier': r_identifier,
                    'path': r_href,
                    'title': title,
                    'description': description,
                    'tags': keywords,
                    'categories': categories,
                    'position': position,
                }

                m['resources'].append(r)
                if keywords is not None:
                    data['tags'] = list(set(data['tags'] + keywords['list']))

                if categories is not None:
                    if 'list' in categories:
                        if not all(x is None for x in categories['list']):
                            data['categories'].append(categories['list'])

            data['manifests'].append(m)

        # Remove duplicate categories
        cat_sorted = sorted(data['categories'])
        cat_clean = [cat_sorted[i] for i in range(len(cat_sorted)) if i == 0 or cat_sorted[i] != cat_sorted[i-1]]
        data['categories'] = cat_clean

        return data


    def pull_langstrings(self, tag, lang, limit=False):
        """
        return a list of imsmd:langstrings matching lang, limited to one if limit atr is set
        """
        try:
            results = []
            matching = []

            langstrings = tag.find_all('langstring', attrs={"lang": lang})
            for ls in langstrings:
                matching.append(ls.string)

            if matching:
                if limit:
                    return matching[0].string

                for match in matching:
                    results.append(match.string)
                return results
            else:
                return None
        except:
            return None


    def pull_metadata(self, tag):
        """
        given a tag, find a metadata tag inside and return 
        """
        if tag is None:
            return None, None, None, None

        title = self.pull_langstrings(tag=tag.find('title'), lang='en', limit=True)
        description = self.pull_langstrings(tag=tag.find('description'), lang='en', limit=True)
        keywords = {
            'ids': False,
            'list': self.pull_langstrings(tag=tag.find('keyword'), lang='en', limit=False)
        }
        categories = {
            'ids': False,
            'list': []
        }

        taxons = tag.find_all('taxon')
        for taxon in taxons:
            #logger.info(taxon)
            categories['list'].append(self.pull_langstrings(tag=taxon.entry, lang='en', limit=True))

        if not categories['list']:
            categories = None

        if not keywords['list']:
            keywords = None

        return title, description, keywords, categories
