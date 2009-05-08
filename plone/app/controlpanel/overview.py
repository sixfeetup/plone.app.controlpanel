from plone.memoize.instance import memoize
from zope.i18n import translate

from Acquisition import aq_base
from Acquisition import aq_inner
from Globals import DevelopmentMode

from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.app.controlpanel.form import ControlPanelView

_DEFAULT_PROFILE = 'Products.CMFPlone:plone'


def three_column_list(input_list):
    list_len = len(input_list)

    # Calculate the length of the sublists
    sublist_len = (list_len % 3 == 0 and list_len / 3 or list_len / 3 + 1)

    # Calculate the list end point given the list number
    def _list_end(num):
        return (num == 2 and list_len or (num + 1) * sublist_len)

    # Generate only filled columns
    final = []
    for i in range(3):
        column = input_list[i*sublist_len:_list_end(i)]
        if len(column) > 0:
            final.append(column)
    return final


class OverviewControlPanel(ControlPanelView):

    template = ViewPageTemplateFile('overview.pt')

    base_category = 'controlpanel'
    ignored_category = 'controlpanel_user'

    def __call__(self):
        self.request.set('disable_border', 1)
        return self.template()

    @memoize
    def action(self):
        return getToolByName(aq_inner(self.context), 'portal_actions')

    @memoize
    def core_versions(self):
        """ Useful core information """
        context = aq_inner(self.context)
        setup = getToolByName(context, 'portal_setup')

        current_version = setup.getVersionForProfile(_DEFAULT_PROFILE)
        available_version = setup.getLastVersionForProfile(_DEFAULT_PROFILE)
        if isinstance(available_version, tuple):
            available_version = '.'.join(available_version)

        cp = context.Control_Panel
        var = {}
        var['Python'] = cp.sys_version()
        var['Platform'] = cp.sys_platform()
        var['Plone Current Configuration'] = current_version
        var['Plone Available Configuartion'] = available_version
        var['Debug mode'] = DevelopmentMode and 'Yes' or 'No'
        return var

    def version_overview(self):
        core_versions = self.core_versions()
        plone = core_versions.get('Plone Current Configuration')
        versions = [
            'Plone ' + plone,
        ]
        for v in ('Python', ):
            versions.append(v + ' ' + core_versions.get(v))
        return versions

    @memoize
    def is_dev_mode(self):
        return bool(DevelopmentMode)

    def mailhost_warning(self):
        mailhost = getToolByName(aq_inner(self.context), 'MailHost', None)
        if mailhost is None:
            return True
        mailhost = getattr(aq_base(mailhost), 'smtp_host', None)
        email = getattr(aq_inner(self.context), 'email_from_address', None)
        if mailhost and email:
            return False
        return True

    def categories(self):
        root = self.action().get(self.base_category, None)
        if root is None:
            return ()
        category_ids = [i for i in root
                          if i != self.ignored_category]
        def _title(id):
            title = root[c].getProperty('title')
            domain = root[c].getProperty('i18n_domain', 'plone')
            return translate(title, domain=domain, context=self.request)
        return [dict(id=c, title=_title(c)) for c in category_ids]

    def sublists(self, category):
        category = self.base_category + '/' + category
        actions = self.action().listActionInfos(category=category)
        def _title(v):
            return translate(v.get('title'),
                             domain='plone',
                             context=self.request)
        actions.sort(key=_title)
        return three_column_list(actions)
