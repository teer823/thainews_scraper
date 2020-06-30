from sqlalchemy.orm.state import InstanceState
from .models import News, Tag, News_tag
from . import db
from datetime import timedelta
from flask import Blueprint, jsonify, request, render_template, redirect, url_for, current_app, make_response, Response
from flask_cors import CORS, cross_origin
from functools import update_wrapper
from collections import deque
import subprocess
import threading


main = Blueprint('main', __name__)
output_data = []
scrape_in_progress = False
scrape_complete = False
queue = deque()


def progressFinishCheck():
    global scrape_in_progress
    global queue
    if len(queue) == 0:
        scrape_in_progress = False
    print('gets called')


def popenAndCall(onExit, *popenArgs, **popenKWArgs):
    """
    Runs a subprocess.Popen, and then calls the function onExit when the
    subprocess completes.
    Use it exactly the way you'd normally use subprocess.Popen, except include a
    callable to execute as the first argument. onExit is a callable object, and
    *popenArgs and **popenKWArgs are simply passed up to subprocess.Popen.
    """
    def runInThread(onExit, popenArgs, popenKWArgs):
        proc = subprocess.Popen(*popenArgs, **popenKWArgs)
        proc.wait()
        onExit()
        return

    thread = threading.Thread(target=runInThread,
                              args=(onExit, popenArgs, popenKWArgs))
    thread.start()

    return thread  # returns immediately after the thread starts


@main.route('/scraping', methods=['POST'])
def hello_world():
    global scrape_in_progress
    global scrape_complete
    global queue
    search_keyword = request.get_json()
    search_field = search_keyword['search_field']
    # search_field = request.args.get('search_field')
    queue.append(search_field)
    if not scrape_in_progress:
        scrape_in_progress = True
        while len(queue) > 0:
            field = queue.pop()
            # popenAndCall(progressFinishCheck, ['ls'], cwd='./spider')
            popenAndCall(progressFinishCheck, [
                         'python', 'run_spiders.py', field], cwd='./spider')
    return 'SCRAPE IN PROGRESS'


@main.route('/news')
def news_gather():
    news_list = News.query.all()
    news_array = []

    for one in news_list:
        news_array.append({'id': one.id, 'title': one.title, 'body': one.body, 'date': one.date,
                           'author': one.author, 'url': one.url, 'category': one.category  # , 'tags': one.tags ##
                           })
    return jsonify({'news': news_array})


@main.route('/news/csv')
def news_gatherCSV():
    news_list = News.query.all()
    # generateCSVFromSQLAlchemy(news_list,True)
    # return None
    return Response(generateCSVFromSQLAlchemy(news_list, True), mimetype='text/csv')


def generateCSVFromSQLAlchemy(sqlQueryList, withKeys):
    i = 0
    for one in sqlQueryList:
        if i == 0 and withKeys:

            yield ','.join(filter(lambda x: not x.startswith('_'), one.__dict__.keys()))+'\n'
            i += 1
        yield ','.join([(str(i).replace(",", ""))for i in filter(lambda x: not isinstance(x, InstanceState), one.__dict__.values())]) + '\n'


@main.route('/searching', methods=['POST'])
def searching():
    tag = request.args.get('search_field')
    search = "%{}%".format(tag)
    posts = News.query.filter(News.title.like(search)).all()
    news_array = []

    for one in posts:
        news_array.append({'id': one.id, 'title': one.title, 'body': one.body, 'date': one.date,
                           'author': one.author, 'url': one.url, 'category': one.category  # , 'tags': one.tags ##
                           })
    return jsonify({'news': news_array})