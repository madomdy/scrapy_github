import scrapy
import json


class UserNode(object):
    def __init__(self, **kwargs):
        self.info = kwargs
        self.children = []

    def to_dict(self):
        return self.info


class Tree(object):
    def __init__(self, root=None, max_deep=3):
        self.root = root
        self.max_deep = max_deep
        self.usernames = set()

    def serialize_node(self, node):
        d = node.to_dict()
        if node.children:
            d['followers'] = [self.serialize_node(child)
                              for child in node.children]
        return d

    def serialize(self):
        return self.serialize_node(self.root)

    def is_overflow(self, deep):
        return True if deep >= self.max_deep else False

    def add_node(self, child, parent):
        if parent is None:
            self.root = child
        else:
            parent.children.append(child)


class QuotesSpider(scrapy.Spider):
    name = "quotes"

    def __init__(self, *args, **kwargs):
        super(QuotesSpider, self).__init__(*args, **kwargs)
        self.start_urls = [
            'https://github.com/' + kwargs.pop('username', 'koder-ua')
        ]
        max_deep = int(kwargs.pop('max_deep', 3))
        self.tree = Tree(max_deep=max_deep)

    @staticmethod
    def _get_link(links, pattern="followers"):
        for link in links:
            if pattern in link:
                return link
        return None

    @staticmethod
    def _parse_statistics_on_page(response):
        info = {
            'username': response.css(
                'span.vcard-username::text').extract_first(),
            'fullname': response.css(
                'span.vcard-fullname::text').extract_first(),
        }
        stat_names = response.css('a.underline-nav-item::text').extract()
        stat_values = response.css(
            'a.underline-nav-item span.counter::text').extract()
        clear_values = [s.strip() for s in stat_values if s.strip()]
        clear_names = [s.strip().lower()
                       for s in stat_names
                       if s.strip()][-len(clear_values):]
        for key, value in zip(clear_names, clear_values):
            if value.endswith('k'):
                value = int(float(value[:-1]) * 1000)
            else:
                value = int(value)
            info[key] = value
        return info

    @staticmethod
    def parse_repo(response):
        languages = [s for s in response.css('div.select-menu-item.'
                                             'js-navigation-item '
                                             'input[name="language"]'
                                             '::attr(value)').extract() if s]
        response.meta['user'].info['languages'] = languages

    def parse_links_page(self, response):
        links = response.css(
            'a.d-inline-block.no-underline.mb-1::attr(href)').extract()
        for link in links:
            next_page = response.urljoin(link)
            request = scrapy.Request(next_page, callback=self.parse)
            request.meta['parent'] = response.meta['parent']
            request.meta['deep'] = response.meta['deep']
            yield request

    def parse(self, response):
        info = self._parse_statistics_on_page(response)
        if info['username'] in self.tree.usernames:
            return None
        self.tree.usernames.add(info['username'])

        parent = response.meta.get('parent', None)
        deep = response.meta.get('deep', 1)
        user = UserNode(**info)

        self.tree.add_node(user, parent)

        links = response.css('a.underline-nav-item::attr(href)').extract()
        next_page = self._get_link(links)
        repo_page = self._get_link(links, pattern="repositories")

        request = scrapy.Request(response.urljoin(repo_page),
                                 callback=self.parse_repo)
        request.meta['user'] = user
        yield request

        if not (next_page is None or self.tree.is_overflow(deep)):
            next_page = response.urljoin(next_page)
            request = scrapy.Request(next_page,
                                     callback=self.parse_links_page)
            request.meta['parent'] = user
            request.meta['deep'] = deep + 1
            yield request

    def closed(self, reason):
        tree = self.tree.serialize()
        with open('users.json', 'w') as outfile:
            json.dump(tree, outfile)
            print("Data is dumped")
