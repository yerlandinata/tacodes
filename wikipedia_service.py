import wikipedia

class WikipediaService:
    def __init__(self):
        self.__page_title_cache = dict()
        self.__page_cache = dict()
        self.__cooccur_cache = dict()
    
    def get_page_list(self, query):
        if query in self.__page_title_cache.keys():
            return self.__page_title_cache[query]
        wikipedia.set_lang('id')
        search_result = wikipedia.search(query)
        self.__page_title_cache[query] = search_result
        return search_result

    def get_page(self, page):
        if page in self.__page_cache.keys():
            return self.__page_cache[page]
        wikipedia.set_lang('id')
        text = wikipedia.page(page).content
        self.__page_cache[page] = text
        return text

    def is_term_cooccur(self, term1, term2, page):
        print('querying is_term_coocur:', term1, term2, page, 'result:', end='')
        if (term1, term2, page) in self.__cooccur_cache.keys():
            print(self.__cooccur_cache[(term1, term2, page)])
            return self.__cooccur_cache[(term1, term2, page)]
        try:
            text = self.get_page(page)
        except:
            text = ''
        result = term1 in text and term2 in text
        self.__cooccur_cache[(term1, term2, page)] = result
        print(result)
        return result

wikipedia_service = WikipediaService()
