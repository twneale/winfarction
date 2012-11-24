import xmlrpclib
import functools
import types
from operator import itemgetter
import logbook


logger = logbook.Logger('winfarction')


def log(before, after=None):
    '''Log messages before/after running the decorated function.'''
    def wrapperwrapper(f):
        @functools.wraps(f)
        def wrapper(*args, **kw):
            self = args[0]
            vals = dict(self.__class__.__dict__)
            vals.update(self.__dict__)
            logger.info(before.format(**vals))
            ret = f(*args, **kw)
            if after:
                logger.info(after.format(**vals))
            else:
                logger.info('  ==> %r' % (ret,))
            return ret
        return wrapper
    return wrapperwrapper


class CustomRepr(object):
    '''A custom repr solution that tries to filter
    out non-data attributes.
    '''
    def no_dunder(self, item):
        key, value = item
        return not key.startswith('__')

    def no_methods(self, item):
        key, value = item
        return not isinstance(value, types.MethodType)

    def items(self, instance):
        if isinstance(instance, _Base):
            items = instance.__class__.__dict__.items()
        else:
            items = instance.__dict__.items()
        items = filter(self.no_dunder, items)
        items = filter(self.no_methods, items)
        return items

    def __get__(self, obj, objtype=None):
        items = self.items(obj)
        vals = ', '.join('%s=%r' % item for item in items)
        if hasattr(obj, '__name__'):
            return lambda: '%s(%s)' % (obj.__name__, vals)
        else:
            return lambda: '%s(%s)' % (obj.__class__.__name__, vals)


class _BaseType(type):
    '''Define a more descriptive __repr__ for declarative
    api classes.
    '''
    __repr__ = CustomRepr()


class _Base(object):
    __metaclass__ = _BaseType

    __repr__ = CustomRepr()


class _AppBase(_Base):

    autostart = False
    extra_info = ''

    @log('Creating app {name!r}')
    def create(self):
        return self.server.create_app(
            self.session_id,
            self.name,
            self.type_,
            self.autostart,
            self.extra_info)

    @log('Updating app {name!r}...')
    def update(self):
        app_names = map(itemgetter('name'), self.session.list_apps())
        res = []
        if self.name not in app_names:
            res.append(self.create())
        return res

    @log('Deleting app {name!r}')
    def delete(self):
        try:
            return self.server.delete_app(
                self.session_id,
                self.name)
        except xmlrpclib.Fault as exc:
            if 'not found' in exc.faultString:
                logger.warning('...not deleting nonexistent app.' % self)


class _DomainBase(_Base):

    def __init__(self, domain=None, subdomains=None):
        self.domain = getattr(self, 'domain', domain)
        self.subdomains = getattr(self, 'subdomains', subdomains or [])

    @log('Creating domain {domain!r}...')
    def create(self):
        '''http://docs.webfaction.com/xmlrpc-api/apiref.html#create_domain
        '''
        return self.server.create_domain(
            self.session_id,
            self.domain,
            *self.subdomains)

    @log('Deleting domain {domain!r}...')
    def delete(self):
        try:
            return self.server.delete_domain(
                self.session_id,
                self.domain,
                *self.subdomains)
        except xmlrpclib.Fault as exc:
            if 'not found' in exc.faultString:
                logger.warning('...not deleting nonexistent domain.' % self)


class _WebsiteBase(_Base):
    '''
    '''
    https = False

    @log('Creating website {name!r}.')
    def create(self):
        '''http://docs.webfaction.com/xmlrpc-api/apiref.html#create_website
        '''
        site_apps = [(app.name, mount_point) for (app, mount_point)
                     in self.site_apps]
        return self.server.create_website(
            self.session_id,
            self.name,
            self.ip,
            self.https,
            self.subdomains,
            *site_apps)

    @log('Updating website {name!r}.')
    def update(self):
        '''http://docs.webfaction.com/xmlrpc-api/apiref.html#update_website
        '''
        site_apps = [(app.name, mount_point) for (app, mount_point)
                     in self.site_apps]
        return self.server.update_website(
            self.session_id,
            self.name,
            self.ip,
            self.https,
            self.subdomains,
            *site_apps)

    @log('Deleting website {name!r}.')
    def delete(self):
        try:
            return self.server.delete_website(
                self.session_id,
                self.name,
                self.ip,
                self.https)
        except xmlrpclib.Fault as exc:
            if 'not found' in exc.faultString:
                logger.warning('...not deleting nonexistent website.' % self)

    def deploy(self):

        # Create the apps.
        for app, mount_point in self.site_apps:
            app().update()

        # Configure the domains.
        for domain in self.subdomains:
            self.session.Domain(domain).create()

        # Create the website.
        return self.create()

    def teardown(self):

        # Create the apps.
        for app, mount_point in self.site_apps:
            app().delete()

        # Configure the domains.
        for domain in self.subdomains:
            self.session.Domain(domain).delete()

        # Create the website.
        return self.delete()


class Session(_Base):

    def __init__(self, webfaction_user, webfaction_password):
        self.webfaction_user = webfaction_user
        self.login(webfaction_user, webfaction_password)

    @property
    def _base(self):
        return type('SessionBase', (object,), self.__dict__)

    @log('Logging into webfaction...')
    def login(self, webfaction_user, webfaction_password):
        server = xmlrpclib.ServerProxy('https://api.webfaction.com/')
        self.session_id, self.account = server.login(
            webfaction_user,
            webfaction_password)
        self.server = server
        return self.session_id, self.account

    @property
    def App(self):
        return type('App', (self._base, _AppBase), dict(session=self))

    @property
    def Website(self):
        return type('Website', (self._base, _WebsiteBase), dict(session=self))

    @property
    def Domain(self):
        return type('Domain', (self._base, _DomainBase), dict(session=self))

    def list_apps(self):
        return self.server.list_apps(self.session_id)

    def list_app_types(self):
        return self.server.list_app_types(self.session_id)

    def list_domains(self):
        self.server.list_domains(self.session_id)

    def list_websites(self):
        return self.server.list_websites(self.session_id)

    def list_dbs(self):
        return self.server.list_dbs(self.session_id)
