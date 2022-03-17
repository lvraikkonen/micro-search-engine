from typing import Optional
import xml.etree.ElementTree as ET
from datetime import datetime, time, timedelta
import configparser

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from search_engine import SearchEngine

app = FastAPI()

doc_dir_path = ''
db_path = ''
global page
global keys


def init():
    config = configparser.ConfigParser()
    config.read('../config.ini', 'utf-8')
    global dir_path, db_path
    dir_path = config['DEFAULT']['doc_dir_path']
    db_path = config['DEFAULT']['db_path']


## Model part
class News(BaseModel):
    docid: int
    date_time: Optional[datetime]
    title: str
    content: str


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}


# 将需要的数据以字典形式打包传递给search函数
def find(docid, extra=False):
    docs = []
    global dir_path, db_path
    for id in docid:
        root = ET.parse(dir_path + '%s.xml' % id).getroot()
        url = root.find('url').text
        title = root.find('title').text
        body = root.find('body').text
        snippet = root.find('body').text[0:120] + '……'
        time = root.find('datetime').text.split(' ')[0]
        datetime = root.find('datetime').text
        doc = {'url': url, 'title': title, 'snippet': snippet, 'datetime': datetime, 'time': time, 'body': body,
               'id': id, 'extra': []}
        typed_doc = News(docid=doc['id'], date_time=doc['datetime'], title=doc['title'], content=doc['snippet'])
        # if extra:
        #     temp_doc = get_k_nearest(db_path, id)
        #     for i in temp_doc:
        #         root = ET.parse(dir_path + '%s.xml' % i).getroot()
        #         title = root.find('title').text
        #         doc['extra'].append({'id': i, 'title': title})
        docs.append(typed_doc)
    return docs


def searchidlist(key, selected=0):
    global page
    global doc_id
    se = SearchEngine('../config.ini', 'utf-8')
    flag, id_scores = se.search(key, selected)
    # 返回docid列表
    doc_id = [i for i, s in id_scores]
    page = []
    for i in range(1, (len(doc_id) // 10 + 2)):
        page.append(i)
    return flag, page


def cut_page(page, no):
    docs = find(doc_id[no*10:page[no]*10])
    return docs


@app.get("/search/{doc_id}", response_model=News)
def content(doc_id: int):
    try:
        doc = find([doc_id], extra=True)
        typed_doc = doc[0]
        return typed_doc
    except:
        print('content error')


@app.post("/search/{keywords}")
def search_by_keywords(keywords: str):
    try:
        flag, page = searchidlist(keywords, 0)
        docs = cut_page(page, 0)
        return docs
    except:
        print("search keywords error")


if __name__ == "__main__":
    init()
    uvicorn.run(app, host="0.0.0.0", port=8000)