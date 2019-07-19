import HTMLReader
import os
import re

URL_MINIMUM_WAGES = 'https://en.wikipedia.org/wiki/List_of_minimum_wages_by_country'
URL_AVERAGE_WAGES = 'https://en.wikipedia.org/wiki/List_of_countries_by_average_wage'
URL_IPAD_PRICES = 'https://en.wikipedia.org/wiki/Purchasing_power_parity'
URL_LIVING_COSTS = 'https://www.numbeo.com/cost-of-living/country_result.jsp?country={}&displayCurrency=USD'

#output PATH
OUTPUT_DIR = 'outputs'
FILE_MINIMUM_WAGES = f'{OUTPUT_DIR}/minimum_wages.txt'
FILE_AVERAGE_WAGES = f'{OUTPUT_DIR}/average_wages.txt'

reader = HTMLReader.HTMLReader()

def fetch_number(value):
    return re.search('(\d+,?)+\.\d+', value)

def print_progress(value, limit):
    str_format = f'progress:{round(value / limit * 100)}%'
    if(value != limit):
        print(str_format, end='\r')
    else:
        print(str_format)
        
class Wages:
    def __init__(self, url):
        self.__wages__ = []
        self.__supported_countries__ = set()
        self.__output_path__ = None
        
        reader.getHtmlContent(url)
        
    def getSupportedCountries(self):
        return self.__supported_countries__
    
    def getWage(self, country): 
        return next((tp_wage[1] for tp_wage in self.__wages__ if country.lower() in tp_wage), 0.0)

    def getPath(self):
        return self.__output_path__
    
class MinimumWages(Wages):
    def __init__(self):
        super().__init__(URL_MINIMUM_WAGES)
        self.__output_path__ = FILE_MINIMUM_WAGES
        self.__html_element__ = reader.getElementFromHtml('sortable wikitable')
        self.__tr__ = reader.getRowsFromTableElement(self.__html_element__)

        self.__fetchData__()

    def __fetchData__(self):
        for country, _, value, *_ in reader.getDataFromTableElement(self.__tr__):
            value = reader.selectTag(value, 'span')
            country = reader.selectTag(country, 'a')[0]
            if(value):
                #adjust country names
                if(country == "Côte d'Ivoire"):
                    country = 'Ivory Coast'
                #
                self.__supported_countries__.update([country])
                tp = str.lower(country), str.replace(value[0], ',', '')
                self.__wages__.append(tp)

class AverageWages(Wages):
    def __init__(self):
        super().__init__(URL_AVERAGE_WAGES)
        self.__output_path__ = FILE_AVERAGE_WAGES
        self.__html_element__ = reader.getElementFromHtml('wikitable sortable')
        self.__tr__ = reader.getRowsFromTableElement(self.__html_element__)

        self.__fetchData__()
    
    def __fetchData__(self):
        for country, _, value in reader.getDataFromTableElement(self.__tr__):
            country = reader.selectTag(country, 'a')[0]
            #adjust country names
            if(country == 'Slovak Republic'):
                country = 'Slovakia'
            #
            self.__supported_countries__.update([country])
            tp = str.lower(country), str.replace(value.get_text(), ',', '')
            self.__wages__.append(tp)
    
class LivingCost:
    def __init__(self, wages_type):
        self.__country_living_cost_data__ = {}
        self.__wages_type__ = wages_type

        class Metrics:
            def __init__(self):
                self.__country_living_cost_data_len__ = 0
                self.__supported_countries_len__ = 0
                self.__max_prop_length__ = 0

            def getCountryLivingCostLen(self):
                return self.__country_living_cost_data_len__

            def getSupportedCountriesLen(self):
                return self.__supported_countries_len__
            
            def getMaxPropLength(self):
                return self.__max_prop_length__

            def setCountryLivingCostLen(self, value):
                self.__country_living_cost_data_len__ = value

            def setSupportedCountriesLen(self, value):
                self.__supported_countries_len__ = value
                
            def setMaxPropLength(self, value):
                if(self.__max_prop_length__ < value):
                    self.__max_prop_length__ = value
            
        self.__metrics__ = Metrics()
        
    def __removeRedundantData__(self):
        for data in list(self.__country_living_cost_data__.items()):
            prop, values = data
            if(len(values) != len(self.__wages_type__.getSupportedCountries())):
                self.__country_living_cost_data__.pop(prop)
        
    def getData(self):
        supported_countries_list = list(self.__wages_type__.getSupportedCountries())
        for idx, country in enumerate(supported_countries_list):
            reader.getHtmlContent(URL_LIVING_COSTS.format(country.replace(' ', '%20')))
            html_element = reader.getElementFromHtml('data_wide_table')
            tr = reader.getRowsFromTableElement(html_element)
            if(tr):
                data = reader.getDataFromTableElement(tr)
                for name, value, _ in data:
                    name = name.get_text()
                    value = fetch_number(value.get_text())
                    value = float(value.group(0).replace(',', '')) if value else float(0)
                    #handle special cases here
                    if('Price per Square Meter to Buy Apartment' in name): #price for 85 squere meter apartment inside/outside city
                        value *= 85
                        name += '(85m2) '
                    #           
                    value = round(value, 2)
                    prop = self.__country_living_cost_data__.get(name)
                    if(prop == None):
                        self.__country_living_cost_data__.update({name: [(country, value)]})
                    else:
                        prop.append((country, value))
                        
                    self.__metrics__.setMaxPropLength(len(name))
            else:
                self.__wages_type__.getSupportedCountries().remove(country)
                print(f'Warning: there is not data for "{country}"!')
            print_progress(idx + 1, len(supported_countries_list))
                
        self.__removeRedundantData__()
        self.__metrics__.setCountryLivingCostLen(len(self.__country_living_cost_data__))
        self.__metrics__.setSupportedCountriesLen(len(self.__wages_type__.getSupportedCountries()))
        
    def processData(self):
        if(not os.path.exists(OUTPUT_DIR)):
            os.makedirs(OUTPUT_DIR)
            
        output_file = open(self.__wages_type__.getPath(), 'w')

        PADDING_1ST_COLUMN = 5
        PADDING_3RD_COLUMN = 10
        max_prop_len = self.__metrics__.getMaxPropLength()
        prop_len_field = max_prop_len
        country_living_cost_len = self.__metrics__.getCountryLivingCostLen()
        supported_coutries_len = self.__metrics__.getSupportedCountriesLen()
        
        #table of contents
        for idx, prop in enumerate(self.__country_living_cost_data__.keys()):
            print(f'{idx + 1:{PADDING_1ST_COLUMN}}.{prop:.<{prop_len_field}}{idx * supported_coutries_len + country_living_cost_len + idx + 1:.>{PADDING_3RD_COLUMN}}', file=output_file)
            
        for idx, tp in enumerate(self.__country_living_cost_data__.items()):
            prop, tp_values = tp
            tp_values = sorted([(value[0], round(float(self.__wages_type__.getWage(value[0])) / value[1], 3)) if value[1] else (value[0], 0.0) for value in tp_values], key=lambda values: values[1], reverse=True)
            print(f'{idx + 1}.{prop}:', file=output_file)
            for country, value in tp_values:
                print(f'\t-"{country}" purchasing power: {value}x', file=output_file)
            print_progress(idx + 1, country_living_cost_len)
        
    def addRowToData(self, prop, item_list):
        self.__country_living_cost_data__.update({prop: item_list})
        old_len = self.__metrics__.getCountryLivingCostLen()
        self.__metrics__.setCountryLivingCostLen(old_len + 1)
        
class InputManager():
    def __init__(self):
        self.__end__ = False
        self.__living_cost__ = [None, None]
        self.__index__ = 0
        
    def collectData(self, wage_type):
        print('collecting data...')
        self.__living_cost__[self.__index__] = LivingCost(wage_type)
        self.__living_cost__[self.__index__].getData()
        self.__living_cost__[self.__index__].addRowToData('Electronics (iPad) ', getIpadPrice(wage_type.getSupportedCountries()))
        print('done!')

    def processData(self):
        print('processing data...')
        self.__living_cost__[self.__index__].processData()
        print('done!')

    def setWageType(self, user_input):
        self.__index__ = int(user_input) - 1
        wage_type = {0: MinimumWages, 1: AverageWages}[self.__index__]
        if(not self.__living_cost__[self.__index__]):
            self.collectData(wage_type())
            self.processData()
        else:
            self.processData()
        
    def handle(self):
        print('All values are a ratio of annual salary divided by cost of goods or services.')
        while not self.__end__:
            print('choose wage type (1) - minimum (2) - average (q) - quit:', end=' ')
            user_input = input().lower().strip()
            if(user_input == '1' or user_input == '2'):
                self.setWageType(user_input)
            elif(user_input == 'q'):
                self.__end__ = True
            else:
                print(f'Error: incorrect input "{user_input}"')
                
#user define function which provide array of costs in order of occurence in supported_countries; TODO(SyntaX): explain it better!
def getIpadPrice(supported_countries):
    reader.getHtmlContent(URL_IPAD_PRICES)

    html_elements = reader.getElementsFromHtml('sortable wikitable')[1]
    tr = reader.getRowsFromTableElement(html_elements)

    ipad_prices = {}

    for country, value in reader.getDataFromTableElement(tr):
        country = country.getText()
        #adjust country names
        if(country == 'US (California)'):
            country = 'United States'
        if(country == 'Canada (Montréal)'):
            country = 'Canada'
        #
        value = fetch_number(value.get_text())
        value = float(value.group(0).replace(',', '')) if value else float(0)
        ipad_prices.update({country: value})

    data = []

    for country in supported_countries:
        value = ipad_prices.get(country)
        if(value == None):
            value = 0.0
        data.append((country, value))
            
    return data

user_input_manager = InputManager()
user_input_manager.handle()
