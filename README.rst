============
winfarction
============

An attack of winning
++++++++++++++++++++++++

Automated deployment for webfaction through a declarative API: ::

    from winfarction import Session
    import settings


    wbf = Session(settings.webfaction_user, settings.webfaction_password)

    class StaticApp(wbf.App):
        name = 'tym_static'
        type_ = 'static'

    class FlaskApp(wbf.App):
        name = 'tym_flask'
        type_ = 'mod_wsgi33-python27'

    class Website(wbf.Website):
        subdomains = ['textyourmom.com']
        site_apps = [(FlaskApp, '/'), (StaticApp, '/static')]
        ip = '123.45.67.89'
        name = 'textyourmom'

    Website().deploy()

The above snippet establishes a session with the webfaction xml-rpc server,
creates a static app calls 'tym_static', a Python 2.7/wsgi 3.3 app named 'tym_flask', and configures DNS to route incoming requests to 'textyourmom.com' to the box
with the stated ip address, with requests to '/static' and '/' handled by the
static and wsgi apps, respectively.

Author
======
Thom Neale (@twneale)