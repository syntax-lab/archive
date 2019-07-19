import urllib
import urllib.request
import bs4

class HTMLReader:        
    def getUrl(self):
        return self.__url__

    def getHtml(self):
        return self.__html_buffer__

    def getHtmlContent(self, url): #[[maybe_unused]]
        self.setUrl(url)
        self.__html_buffer__ = urllib.request.urlopen(self.__url__).read()
        self.__soup__ = bs4.BeautifulSoup(self.__html_buffer__, 'lxml')
        return self.__soup__
        
    def getElementFromHtml(self, name):
        return self.__soup__.find(class_ = name)

    def getElementsFromHtml(self, name):
        return self.__soup__.findAll(class_ = name)
    
    def getRowsFromTableElement(self, table):
        if(table):
            return table.find_all('tr')
        return None

    def getDataFromTableElement(self, table_row):
        result = []
        for row in table_row:
            table_entry = row.find_all('td')
            if(table_entry):
                #WARNING: ensure that each entry has same amount of fields
                result.append(table_entry)
        return result

    def selectTag(self, html, tag):
        return [element.get_text() for element in html.select(tag)]

    def setUrl(self, new_url):
        self.__url__ = new_url

