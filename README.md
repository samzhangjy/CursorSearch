# Cursor Search

Cursor Search is a simple search engine build with Python. It's simple to use, fully customizible, and, most importantly, light-weight.

It supports Unicode-like word separation using the open source package Jieba.

The search engine also includes Deep Learning to learn from the users' clicks.

## Installation

First, clone this repo:

```bash
$ git clone git@github.com:EHStudio/CursorSearch.git
```

Then install the dependencies:

```bash
$ pip install -r requirements.txt
```

And you're ready to go!

## Usage

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

Well, we've provided seven different scoring methods for you to use. See file `cursorsearch/scoring/scoring.py`!

Of course, you can always add your own method to the engine...

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

## Contributing

We welcome all kinds of contributions! Including issues, pull requests, or feature requests!

## License

Please refer to the LICENSE file in the root for details.

Enjoy!
