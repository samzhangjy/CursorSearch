from cursorsearch.core.engine import Searcher
from cursorsearch.crawl.crawler import Crawler

class CursorSearch(object):
    def __init__(self, database_name: str = "search_index.db", predictor_database_name: str = "predictor.db", weights: list = []) -> None:
        """Cursor Search Engine

        CursorSearch is a simple search engine based on Python. It supports Unicode-like word seperation using the 
        open source package Jieba.

        The search engine also includes Deep Learning to learn from the users' clicks.

        Before you start searching, you'll need a database with crawled results stored. You can do this by the 
        `crawl` function. See the example below.

        ```python
        from cursorsearch import CursorSearch

        cursor_search = CursorSearch("your_db_name_here.db")  # Initialize CursorSearch
        cursor_search.crawl(["your_start_url(s)_here"])  # Fill in the URL of the website that you're going to crawl
        ```

        To search for results, use the method `search`.

        ```python
        from cursorsearch import CursorSearch

        cursor_search = CursorSearch("your_db_name_here.db")
        print(cursor_search.search("your search query here"))  # Search it!
        ```

        And you even have the chance to change the calculation of the weights to each URL!

        ```python
        from cursorsearch import CursorSearch
        from cursorsearch.scoring.scoring import Scoring

        def custom_score(rows, **kwargs): pass  # Your custom scoring function

        cursor_search = CursorSearch("your_db_name_here.db", weights=[  # Caution! List here!
            (1.5, Scoring.pagerank_score),  # The first parameter is the weight of the scoring method function behiind it
            (1.0, Scoring.distance_score),  # You can define more!
            (2.0, custom_score)  # Custom scoring function works too!
        ])
        ```

        For more details on the usage, please refer to the documentation.

        Args:
            database_name (str, optional): Path to the main data storage database. Defaults to "search_index.db".
            predictor_database_name (str, optional): Path to the predictor datanase. Defaults to "predictor.db".
            weights (list, optional): List of method used to calculate weights of URLs. Defaults to [].
        """
        super().__init__()
        self.searcher = Searcher(database_name, predictDbName=predictor_database_name, weights=weights)
        self.crawler = Crawler(database_name)
        self.predictor = self.searcher.predictor
    
    def search(self, query: str = 0, **kwargs) -> dict:
        """Search for something.

        Args:
            query (str, optional): Query to search in the database. Defaults to 0.

        Returns:
            dict: Results!
        """
        return self.searcher.query(query)
    
    def crawl(self, start_urls: list) -> None:
        """Crawl the website and store the data.

        Args:
            start_urls (list): The URLs to start with.
        """
        self.crawler.crawl(start_urls)
        self.crawler.calculate_pagerank()
    
    def train(self, query_word_ids: list, url_ids: list, selected_url_id: int):
        """Learn from the users' clicks.

        Args:
            query_word_ids (list): The list of splitted query word ids.
            url_ids (list): The list of matched URLs that showed to the user.
            selected_url_id (int): The URL id of the one the user clicked.
        """
        self.predictor.train_query(query_word_ids, url_ids, selected_url_id)
