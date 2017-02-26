## Synopsis

This project provides an ability to get nested info about github users. For the given user, it recursively traverses followers till achieving provided depth. Each user is described with its `fullname, username, list of programming languages, list of followers; count of stars, following and repositories`.

## Example

The result for exporing [koder-ua](https://github.com/koder-ua) with `depth=3` are stored as JSON and it's available [here](https://jsonblob.com/c4e9fb60-fc15-11e6-a0ba-499cf00ed991).

## Installation

Installation commands using python 3.5:

```bash
git clone https://github.com/madomdy/scrapy_github.git
cd scrapy_github
pyvenv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

## Usage

After installation you can run the following code:

```
scrapy runspider crawler.py -a username=koder-ua -a deep=3
```

The result of crawling is stored as `users.json`.
