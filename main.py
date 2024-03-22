import os
import yaml, json, requests, logging
from bs4 import BeautifulSoup
from yaml.loader import SafeLoader

# System VARS
CURR_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(CURR_DIR)
OUT_DIR = os.path.join(CURR_DIR, 'res')
TMP_DIR = os.path.join(CURR_DIR, 'tmp')
INDEX_DIR = os.path.join(TMP_DIR, 'index')
PRODUCT_DIR = os.path.join(TMP_DIR, 'product')

for _dir in [OUT_DIR, TMP_DIR, INDEX_DIR, PRODUCT_DIR]:
    if not os.path.isdir(_dir):
        os.mkdir(_dir)

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
_handler = logging.StreamHandler()
_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_handler.setFormatter(_formatter)
LOGGER.addHandler(_handler)
log_file = os.path.join(CURR_DIR, 'logs.log')
if log_file:
    _filehandler = logging.FileHandler(log_file)
    _filehandler.setLevel(logging.INFO)
    _filehandler.setFormatter(_formatter)
    LOGGER.addHandler(_filehandler)

# Configurations
CONFIS_PATH = os.path.join(CURR_DIR, 'config.yaml')
# Website VARS
WEB_HOST = 'https://tidalgardens.com/corals.html'

# Function to fetch webpage content
def fetch_webpage(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    LOGGER.error(f"Failed to fetch webpage: {response.status_code}")
    return None

# Function to extract product URLs from the webpage
def extract_html_subsection(html_content:str, tag:str, selector:str, tag_selector:str, find_all:bool=False, verbose:bool=False):
    """
    Retrieve Subsection of HTML with the power of `BeautifulSoup` 🧝‍♂️
    
    :param html_content: HTML source to extract data from
    :param tag: HTML tag
    :param selector: Developer tag
    :param tag_selector: choose one of the following [ 'id', 'class_', 'attrs'], [more info](https://scrapeops.io/python-web-scraping-playbook/python-beautifulsoup-find/#find-by-class-and-ids)
    :param find_all [ OPTIONAL ]: retrieve all occurences 
    :param verbose [ OPTIONAL ]: print input arguments (4debug) 
    :return: requested HTML subsection
    """
    if verbose:
        print('[ extract_html_subsection.info ] html_content:', html_content[:80])
        print('[ extract_html_subsection.info ] tag:', tag)
        print('[ extract_html_subsection.info ] selector:', selector)
        print('[ extract_html_subsection.info ] tag_selector:', tag_selector)
        print('[ extract_html_subsection.info ] find_all:', find_all)

    soup = BeautifulSoup(html_content, 'html.parser')
    # Implement logic to extract subsection of the HTML content
    if find_all:
        match tag_selector:
            case 'id':
                return soup.find_all(tag, id=selector)
            case 'class_':
                return soup.find_all(tag, class_=selector)
            case 'attrs':
                return soup.find_all(tag, attrs=selector)
    
    match tag_selector:
        case 'id':
            return soup.find(tag, id=selector)
        case 'class_':
            return soup.find(tag, class_=selector)
        case 'attrs':
            return soup.find(tag, attrs=selector)

class Tidal_Crawler:
    def __init__(self) -> None:
        pass
    def __crawl_init__(self) -> None:
        self.confis = self.get_configs()
        self.res_json_path = os.path.join(CURR_DIR, 'RESULT.json')
        self.result_data = {}
        if os.path.isfile(self.res_json_path):
            with open(self.res_json_path, encoding ='utf8') as json_file: 
             self.result_data = json.load(json_file)
    
    ## BCKUP methods
    def get_configs(self):
        if os.path.isfile(CONFIS_PATH):
            with open( CONFIS_PATH ) as f_user:
                return yaml.load(f_user, Loader=SafeLoader)
        else:
            raise EnvironmentError(f'Required configurations file not exist: {CONFIS_PATH}')
    def set_configs(self, id, content):
        self.confis[id] = content
        with open(CONFIS_PATH, 'w',) as fw:
            yaml.dump(self.confis, fw, sort_keys=False)

    def crawl_paginate(self, len_product_URLs):
        # PAGINATE (Handle Configs counters)
        if self.confis['product_page'] >= len_product_URLs:
            '''END OF CURR PRODUCT PAGE'''
            if self.confis['index_page'] >= self.confis['total_pages']:
                '''END OF CURR INDEX PAGE'''
                if self.confis['curr_category'] >= len(self.confis['categories']):
                    '''END OF CRAWL'''
                    self.set_configs('completed', True)
                    LOGGER.info(f'END OF CRAWL')
                    return
                '''THERE IS STILL INDEX TO CRAWL c:'''
                self.set_configs('product_page', 1)
                self.set_configs('index_page', 1)
                self.set_configs('curr_category', self.confis['curr_category']+1)
                LOGGER.info(f'END OF CURR INDEX PAGE')
                return
            '''END OF CURR PRODUCT PAGE && ! END OF CURR INDEX PAGE'''
            self.set_configs('product_page', 1)
            self.set_configs('index_page', self.confis['index_page']+1)
            LOGGER.info(f'END OF CURR PRODUCT PAGE')
            return
        
        '''THERE IS STILL PRODUCTs TO CRAWL c:'''
        self.set_configs('product_page', self.confis['product_page']+1)
        LOGGER.debug(f'There is still time to go! C:')
        
    ## CRAWL methods
    # INDEX PAGE
    def get_category(self):
        _curr_cat = self.confis['curr_category']    #.removesuffix('.html')
        _cats = self.confis['categories']    #.removesuffix('.html')
        LOGGER.debug(f'GET confis `curr_category` = {_cats[_curr_cat]}')
        print('_cats[_curr_cat]:', _cats[_curr_cat])
        return _cats[_curr_cat]
    def set_total_pages(self, index_source_html) -> None:
        '''
        GET / SET Total Pages to paginate
        '''
        # Get html `ul` _class=pages-items
        _source = BeautifulSoup(index_source_html, 'html.parser')
        _ul_span_elements = _source.find_all('ul', class_='items pages-items')[0].find_all('span')
        # _ul_total_pages = _ul_span_elements[-2].get_text()
        _total_pages = [int(i.get_text()) for i in _ul_span_elements if isinstance(i.get_text(), str) and i.get_text().isdigit()][-1]
        if self.confis['total_pages'] != _total_pages:
            self.set_configs('total_pages', _total_pages)
            LOGGER.info(f'set `total_pages` sucess: {_total_pages}')
    def process_index_source(self, index_source_html):
        # Parse the HTML content
        _source = BeautifulSoup(index_source_html, 'html.parser')

        # Find all anchor tags within the ordered list
        _product_cards = _source.find_all('ol', class_='products list items product-items')[0].find_all('li', class_='item product product-item')

        # Extract URLs from each product card
        product_URLs = []
        for card in _product_cards:
            # Find the anchor tag within the product card
            _anchor_tag = card.find('a', class_='product-item-link')
            if _anchor_tag:
                # Get the 'href' attribute which contains the URL
                _product_url = _anchor_tag.get('href')
                product_URLs.append(_product_url)
        LOGGER.debug(f'iter product_URLs res length: {len(product_URLs)}')
        return product_URLs
    def get_product_URLs(self):
        _host = self.confis['host']
        _category = self.get_category()
        # GET INDEX SOURCE PAGE
        _index_counter = self.confis['index_page']
        _index_path = os.path.join(INDEX_DIR, f'{_index_counter}.html')
        if os.path.isfile(_index_path):
            with open(_index_path, 'r') as fr:
                _index_source = fr.read()
            LOGGER.info(f'index_page retrieved from bckup: {_index_path}')
        else:
            _index_list_limit = self.confis['index_list_limit']
            _index_url = f'{_host}/{_category}.html?p={_index_counter}&product_list_limit={_index_list_limit}'
            _index_source = fetch_webpage(_index_url)
            with open(_index_path, 'w') as fw:
                fw.write(_index_source)
            LOGGER.info(f'index_page fetch sucess: {_index_path}')
        
        # SET TOTAL INDEX PAGES
        self.set_total_pages(_index_source)
        
        # RETURN PRODUCT URLs
        return self.process_index_source(_index_source)

    # PRODUCT PAGE
    def get_product_source(self, product_URL):
        if product_URL in self.result_data: # First check 👀
            return
        _index_counter = self.confis['index_page']
        _product_counter = self.confis['product_page']
        _product_path = os.path.join(PRODUCT_DIR, f'i{_index_counter}p{_product_counter}.html')
        if os.path.isfile(_product_path):
            with open(_product_path, 'r') as fr:
                _product_source = fr.read()
            LOGGER.info(f'product_page retrieved from bckup: {_product_path}')
        else:
            _product_source = fetch_webpage(product_URL)
            with open(_product_path, 'w') as fw:
                fw.write(_product_source)
            LOGGER.info(f'product_page fetch sucess: {_product_path}')
        return _product_source
    def get_product_metadata(self, product_URL, product_source_html):
        # Parse the HTML content
        _source = BeautifulSoup(product_source_html, 'html.parser')
        # Find the title
        _metadata = {
            'category': self.get_category(),
            'species': None,
            'family': None,
            'description': None,
            'care_desc': None,
            'location': None,
            'lighting': None,
            'water_flow': None,
            'feeding': None,
            'propagation': None,
            '_page_cnt': self.confis['index_page'],
            '_page_pos': self.confis['product_page'],
            '_unsaved_cats': None
        }

        # Find the species
        _species_element = _source.find('h1', class_='page-title')
        if _species_element:
            _metadata['species'] = _species_element.text.strip()

        # Find the description
        _description_element = _source.find('div', class_='value', itemprop='description')
        if _description_element:
            _metadata['description'] = _description_element.text.strip()


        _meta_divs = _source.find_all('div', {'data-content-type': 'block'})
        _debub_count = 0
        _unsaved_categories = []
        for div in _meta_divs:
            # Find the b tag inside the div
            _b_tag = div.find('b', style='font-size: 1.75em; font-family: questrial;')
            if not _b_tag:
                continue
            _b_tag_text = _b_tag.text.strip().upper()
            # Find the location
            match _b_tag_text:
                # Find the location
                case 'LOCATION':
                    # Find the p tag containing the `location` information
                    _p_tag = div.find('p')
                    if _p_tag:
                        _metadata['location'] = _p_tag.text.strip()
                # Find the lighting
                case 'LIGHTING':
                    # Find the p tag containing the `lighting` information
                    _p_tag = div.find('p')
                    if _p_tag:
                        _metadata['lighting'] = _p_tag.text.strip()
                case 'WATER FLOW':
                    # Find the p tag containing the `water_flow` information
                    _p_tag = div.find_all('p')[1]
                    if _p_tag:
                        _metadata['water_flow'] = _p_tag.text.strip()
                case 'FEEDING':
                    # Find the p tag containing the `feeding` information
                    _p_tag = div.find_all('p')[1]
                    if _p_tag:
                        _metadata['feeding'] = _p_tag.text.strip()
                case 'PROPAGATION':
                    # Find the p tag containing the `propagation` information
                    _p_tag = div.find_all('p')[1]
                    if _p_tag:
                        _metadata['propagation'] = _p_tag.text.strip()
                case 'ACCLIMATION':
                    continue
                case _:
                    if _b_tag_text.endswith(' CARE'):
                        _metadata['family'] = _b_tag_text.removesuffix(' CARE').capitalize()
                        # Find the p tag containing the `care_desc` information
                        _p_tag = div.find('p')#[1]
                        if _p_tag:
                            _metadata['care_desc'] = _p_tag.text.strip()
                    else:
                        _unsaved_categories.append(_b_tag_text)
        if _unsaved_categories:
            LOGGER.warning(f'Unsaved Categories @{product_URL.removeprefix(self.confis['host'])}: {_unsaved_categories}')
            _metadata['_unsaved_cats'] = _unsaved_categories
        _metadata_keys = [k for k in list(_metadata.keys()) if _metadata[k]]
        LOGGER.info(f'product_metadata retrieved info: {_metadata_keys}')
        return _metadata
    def append_product_metadata(self, product_URL, product_metadata) -> None:
        if product_URL in self.result_data: # Double check 👀
            return
        self.result_data[product_URL] = product_metadata
        with open(self.res_json_path, 'w', encoding ='utf8') as json_file: 
            json.dump(self.result_data, json_file, ensure_ascii = False, indent=2)
        LOGGER.info(f'success on product append: {product_URL}')
    def crawl_products(self, product_URLs) -> None:
        _product_counter = self.confis['product_page']
        _product_URL = product_URLs[_product_counter-1]
        _iter_product_source = self.get_product_source(_product_URL)
        _product_metadata = self.get_product_metadata(_product_URL, _iter_product_source)
        self.append_product_metadata(_product_URL, _product_metadata)



    # Main method
    def one_more_time(self) -> None:
        self.__crawl_init__()
        while True: # BEDUG
            # GET Product URLs from Index Page
            # try:
            _iter_product_URLs = self.get_product_URLs()
            # except Exception as e:
            #     ## 💀 PAGE ERROR 💀
            #     LOGGER.error(f'PAGE ERROR: {e}')
            #     if self.confis['total_pages'] and self.confis['index_page'] < self.confis['total_pages']:
            #         self.set_configs('index_page', self.confis['index_page']+1)
            #         # return
            #         pass # BEDUG
            #     self.set_configs('completed', True)
            #     LOGGER.info(f'END OF CRAWL')
            #     return

            # GET Products Metadata
            # try:
            self.crawl_products(_iter_product_URLs)
            # except Exception as e:
            #     ## 💀 PRODUCT ERROR 💀
            #     LOGGER.error(f'PRODUCT ERROR: {e}')
            #     pass

            # SET PAGINATION
            try:
                self.crawl_paginate(len(_iter_product_URLs))
                # return
                continue # BEDUG
            except Exception as e:
                ## 💀 PAGINATION ERROR 💀
                LOGGER.error(f'PAGINATION ERROR: {e}')
                raise e


if __name__ == "__main__":
    crawler = Tidal_Crawler()
    crawler.one_more_time()
 