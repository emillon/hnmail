import requests

URL = 'http://api.thriftdb.com/api.hnsearch.com/items/_search'

def main():
    r = requests.get(URL)
    print r.text

if __name__ == '__main__':
    main()
