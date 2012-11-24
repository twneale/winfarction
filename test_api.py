from operator import itemgetter

import nose.tools
from winfarction import Session

import settings


wbf = Session(settings.webfaction_user,
              settings.webfaction_password)


class StaticApp(wbf.App):
    name = 'tym_static'
    type_ = 'static'


class FlaskApp(wbf.App):
    name = 'tym_flask'
    type_ = 'mod_wsgi33-python27'


class Website(wbf.Website):
    subdomains = ['textyourmom.com']
    site_apps = [(FlaskApp, '/'), (StaticApp, '/static')]
    ip = settings.ip
    name = 'textyourmom'


def test_create_website():
    result = Website().deploy()
    id_ = result['id']
    expected = {
        'name': Website.name,
        'ip': Website.ip,
        'subdomains': Website.subdomains,
        'https': Website.https,
        'id': id_,
        'site_apps': [
            ['tym_flask', '/'],
            ['tym_static', '/static']]}
    nose.tools.eq_(result, expected)


def test_teardown_website():
    Website().teardown()
    site_names = map(itemgetter('name'), wbf.list_websites())
    nose.tools.eq_((Website.name not in site_names), True)
