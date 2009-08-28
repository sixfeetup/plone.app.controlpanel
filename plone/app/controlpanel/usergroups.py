# -*- coding: utf-8 -*-
# $Id$
"""Users and groups control panel"""

import urlparse
from itertools import chain
from Acquisition import aq_inner

from zope.interface import Interface
from zope.component import adapts
from zope.component import getMultiAdapter
from zope.formlib.form import FormFields
from zope.interface import implements
from zope.schema import Bool

from plone.protect import CheckAuthenticator
from Products.CMFCore.utils import getToolByName
from Products.CMFDefault.formlib.schema import ProxyFieldProperty
from Products.CMFDefault.formlib.schema import SchemaAdapterBase
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFPlone import Batch
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from form import ControlPanelForm, ControlPanelView


BATCH_SIZE = 20


class IUserGroupsSettingsSchema(Interface):

    many_groups = Bool(title=_(u'Many groups?'),
                       description=_(u"Determines if your Plone is optimized "
                           "for small or large sites. In environments with a "
                           "lot of groups it can be very slow or impossible "
                           "to build a list all groups. This option tunes the "
                           "user interface and behaviour of Plone for this "
                           "case by allowing you to search for groups instead "
                           "of listing all of them."),
                       default=False)

    many_users = Bool(title=_(u'Many users?'),
                      description=_(u"Determines if your Plone is optimized "
                          "for small or large sites. In environments with a "
                          "lot of users it can be very slow or impossible to "
                          "build a list all users. This option tunes the user "
                          "interface and behaviour of Plone for this case by "
                          "allowing you to search for users instead of "
                          "listing all of them."),
                      default=False)


class UserGroupsSettingsControlPanelAdapter(SchemaAdapterBase):

    adapts(IPloneSiteRoot)
    implements(IUserGroupsSettingsSchema)

    def __init__(self, context):
        super(UserGroupsSettingsControlPanelAdapter, self).__init__(context)
        pprop = getToolByName(context, 'portal_properties')
        self.context = pprop.site_properties

    many_groups = ProxyFieldProperty(IUserGroupsSettingsSchema['many_groups'])
    many_users = ProxyFieldProperty(IUserGroupsSettingsSchema['many_users'])


class BaseUserGroupsControlPanel(object):
    """Resources for all control panels
    """

    ursergroups_controlpanel_macros = ViewPageTemplateFile('usergroups_controlpanel_macros.pt').macros

    def contentViewsTabs(self):
        """Data for 'contentviewstabs' macro:
        Any subclass could override returning:
        [{'label': (translated) tab title,
          'link': target url,
          'li_class': 'selected' for actual tab otherwise None
        """
        this_view = urlparse.urlsplit(self.request.URL)[2].split('/')[-1]
        tab_infos = [
            {'label': _(u'label_users', default=u"Users"),
             'link': '@@usergroup-userprefs'},
            {'label': _(u'label_groups', default=u"Groups"),
             'link': '@@usergroup-groupprefs'},
            {'label': _(u'label_usergroup_settings', default=u"Settings"),
             'link': '@@usergroup-controlpanel'}
            ]
        for ti in tab_infos:
            ti['li_class'] = 'selected' if ti['link'] == this_view else None
        return tab_infos


    def processSearch(self):
        """Search relevant principals
        """
        request = self.request
        raw_results = self.doSearch(self.searchString)
        b_size = int(request.get('b_size', BATCH_SIZE))
        self.searchResults = Batch(raw_results, b_size, self.b_start, orphan=1)
        return


    def doSearch(self, searchstring):
        """Must be provided by subclasses
        """
        raise NotImplementedError('Subclass BaseUserGroupsControlPanel and provide doSearch methos')


class UserGroupsSettingsControlPanel(ControlPanelForm, BaseUserGroupsControlPanel):

    base_template = ControlPanelForm.template
    template = ViewPageTemplateFile('usergroupssettings.pt')

    form_fields = FormFields(IUserGroupsSettingsSchema)

    label = _("User/Groups settings")
    description = _("User and groups settings for this site.")
    form_name = _("User/Groups settings")


class UsersOverviewControlPanel(ControlPanelView, BaseUserGroupsControlPanel):

    def __call__(self):

        form = self.request.form
        submitted = form.get('form.submitted', False)
        findAll = form.get('form.button.FindAll', None) is not None
        self.b_start = int(self.request.get('b_start', 0))
        self.searchString = not findAll and form.get('searchstring', '') or ''
        self.searchResults = Batch([], 0, 0, orphan=1)
        if submitted:
            if form.get('form.button.Modify', None) is not None:
                self.manageUser(form.get('users', None),
                                form.get('resetpassword', []),
                                form.get('delete', []))

        # Only search for all ('') if the many_users flag is not set.
        if not(self.many_users) or bool(self.searchString):
            self.processSearch()

        return self.index()

    def doSearch(self, searchString):
        # We push this in the request such IRoles plugins don't provide
        # the roles from the groups the principal belongs.
        self.request.set('__ignore_group_roles__', True)
        searchView = getMultiAdapter((aq_inner(self.context), self.request), name='pas_search')
        return searchView.merge(chain(*[searchView.searchUsers(**{field: searchString}) for field in ['login', 'fullname', 'email']]), 'userid')

    @property
    def many_users(self):
        pprop = getToolByName(aq_inner(self.context), 'portal_properties')
        return pprop.site_properties.many_users

    def manageUser(self, users=[], resetpassword=[], delete=[]):
        CheckAuthenticator(self.request)
        context = aq_inner(self.context)
        acl_users = getToolByName(context, 'acl_users')
        mtool = getToolByName(context, 'portal_membership')
        regtool = getToolByName(context, 'portal_registration')

        utils = getToolByName(context, 'plone_utils')
        for user in users:
            # Don't bother if the user will be deleted anyway
            if user.id in delete:
                continue

            member = mtool.getMemberById(user.id)
            # If email address was changed, set the new one
            if hasattr(user, 'email'):
                # If the email field was disabled (ie: non-writeable), the
                # property might not exist.
                if user.email != member.getProperty('email'):
                    utils.setMemberProperties(member, REQUEST=context.REQUEST, email=user.email)
                    utils.addPortalMessage(_(u'Changes applied.'))

            # If reset password has been checked email user a new password
            pw = None
            if hasattr(user, 'resetpassword'):
                if not context.unrestrictedTraverse('@@overview-controlpanel').mailhost_warning():
                    pw = regtool.generatePassword()
                else:
                    utils.addPortalMessage(_(u'No mailhost defined. Unable to reset passwords.'), type='error')

            acl_users.userFolderEditUser(user.id, pw, user.get('roles',[]), member.getDomains(), REQUEST=context.REQUEST)
            if pw:
                context.REQUEST.form['new_password'] = pw
                regtool.mailPassword(user.id, context.REQUEST)

        if delete:
            # TODO We should eventually have a global switch to determine member area
            # deletion
            mtool.deleteMembers(delete, delete_memberareas=0, delete_localroles=1, REQUEST=context.REQUEST)
        utils.addPortalMessage(_(u'Changes applied.'))

    @property
    def portal_roles(self):
        pmemb = getToolByName(aq_inner(self.context), 'portal_membership')
        return [r for r in pmemb.getPortalRoles() if r != 'Owner']


class GroupsOverviewControlPanel(ControlPanelView, BaseUserGroupsControlPanel):

    def __call__(self):
        form = self.request.form
        submitted = form.get('form.submitted', False)
        findAll = form.get('form.button.FindAll', None) is not None
        self.b_start = int(self.request.get('b_start', 0))
        self.searchString = not findAll and form.get('searchstring', '') or ''
        self.searchResults = Batch([], 0, 0, orphan=1)
        if submitted:
            if form.get('form.button.Modify', None) is not None:
                self.manageGroup([group[len('group_'):] for group in self.request.keys() if group.startswith('group_')],
                                 form.get('delete', []))

        # Only search for all ('') if the many_users flag is not set.
        if not(self.many_groups) or bool(self.searchString):
            self.processSearch()

        return self.index()

    def doSearch(self, searchString):
        searchView = getMultiAdapter((aq_inner(self.context), self.request), name='pas_search')
        return searchView.merge(chain(*[searchView.searchGroups(**{field: searchString}) for field in ['id', 'title']]), 'id')

    def manageGroup(self, groups=[], delete=[]):
        CheckAuthenticator(self.request)
        context = aq_inner(self.context)

        groupstool=context.portal_groups
        utils = getToolByName(context, 'plone_utils')
        groupstool = getToolByName(context, 'portal_groups')

        message = _(u'No changes done.')

        for group in groups:
            roles=[r for r in self.request.form['group_' + group] if r]
            groupstool.editGroup(group, roles=roles, groups=())
            message = _(u'Changes saved.')

        if delete:
            groupstool.removeGroups(delete)
            message=_(u'Group(s) deleted.')

        utils.addPortalMessage(message)
        #return state

    @property
    def portal_roles(self):
        pmemb = getToolByName(aq_inner(self.context), 'portal_membership')
        return [r for r in pmemb.getPortalRoles() if r != 'Owner']

    @property
    def many_groups(self):
        pprop = getToolByName(aq_inner(self.context), 'portal_properties')
        return pprop.site_properties.many_groups
