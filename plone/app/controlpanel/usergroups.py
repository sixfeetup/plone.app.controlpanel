# -*- coding: utf-8 -*-
# $Id$
"""Users and groups control panel"""

import urlparse
from itertools import chain

from Acquisition import aq_inner
from ZTUtils import make_query

from zope.interface import Interface
from zope.component import adapts
from zope.component import getMultiAdapter
from zope.formlib.form import FormFields
from zope.interface import implements
from zope.schema import Bool

from plone.memoize.view import memoize
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

###
## Utility resources for all/most user/groups control panels
###

class BaseUserGroupsControlPanel(object):
    """Resources for all control panels
    """

    usergroups_controlpanel_macros = ViewPageTemplateFile('usergroups_controlpanel_macros.pt').macros

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
        self.searchResults = self.makeBatch(raw_results, b_size, self.b_start, orphan=1)
        return


    def doSearch(self, searchstring):
        """Must be provided by subclasses
        returns a sequence of results according to the searchsting
        """
        raise NotImplementedError("Subclass BaseUserGroupsControlPanel and provide doSearch method")


    def makeBatch(self, results, size, start, orphan=1):
        """Must be provided by susbclasses that use processSearch method
        """
        raise NotImplementedError("Subclass BaseUserGroupsControlPanel and provide makeBatch method")


    @property
    @memoize
    def portal_roles(self):
        plone_tools = getMultiAdapter((aq_inner(self.context), self.request),
                                      name=u'plone_tools')
        portal_membership = plone_tools.membership()
        return [r for r in portal_membership.getPortalRoles() if r != 'Owner']


class BatchWrapper(object):
    """Provides other attributes on batch items, wrapping elements from
    original batch, and provides minimal Batch API for views
    Attributes:
    - _batch: a Products.CMFPlone.Batch or subclass
    - _wrapper_class: a class that wraps each object of batch
    - _wrapper_args: copy of additional args passed to _wrapper_class constructor
    - _wrapper_kw: copy of additional keyword args passed to _wrapper_class constructor
    """
    def __init__(self, batch, wrapper_class, *args, **kw):
        self._batch = batch
        self._wrapper_class = wrapper_class
        self._wrapper_args = args
        self._wrapper_kw = kw
        return


    def __getitem__(self, index):
        item = self._batch[index]
        return self._wrapper_class(item, *self._wrapper_args,**self._wrapper_kw)


    def __getattr__(self, attrname):
        return getattr(self._batch, attrname)


###
## Users/groups general preferences
###

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



class UserGroupsSettingsControlPanel(ControlPanelForm, BaseUserGroupsControlPanel):

    base_template = ControlPanelForm.template
    template = ViewPageTemplateFile('usergroupssettings.pt')

    form_fields = FormFields(IUserGroupsSettingsSchema)

    label = _("User/Groups settings")
    description = _("User and groups settings for this site.")
    form_name = _("User/Groups settings")

###
## Users main control panel
###

class UsersOverviewControlPanel(ControlPanelView, BaseUserGroupsControlPanel):

    def __call__(self):
        """Template is published
        """
        form = self.request.form
        submitted = form.get('form.submitted', False)
        findAll = form.get('form.button.FindAll', None) is not None
        self.b_start = int(self.request.get('b_start', 0))
        self.searchString = not findAll and form.get('searchstring', '') or ''
        self.searchResults = self.makeBatch([], 0, 0, orphan=1)
        if submitted:
            if form.get('form.button.Modify', None) is not None:
                self.manageUser(form.get('users', None),
                                form.get('resetpassword', []),
                                form.get('delete', []))

        # Only search for all ('') if the many_users flag is not set.
        if not(self.many_users) or bool(self.searchString):
            self.processSearch()

        return self.index()


    def makeBatch(self, results, size, start, orphan=1):
        """Override required from BaseUserGroupsControlPanel
        """
        context = aq_inner(self.context)
        plone_portal_state = getMultiAdapter((context, self.request),
                                             name=u'plone_portal_state')
        plone_tools = getMultiAdapter((context, self.request),
                                      name=u'plone_tools')
        portal_url = plone_portal_state.portal_url()
        portal_membership = plone_tools.membership()
        batch = Batch(results, size, start, orphan=orphan)
        return BatchWrapper(batch, UserViewAdapter, portal_url=portal_url, portal_membership=portal_membership, portal_roles=self.portal_roles)


    def doSearch(self, searchString):
        """Override required from BaseUserGroupsControlPanel
        """
        # We push this in the request such IRoles plugins don't provide
        # the roles from the groups the principal belongs.
        self.request.set('__ignore_group_roles__', True)
        searchView = getMultiAdapter((aq_inner(self.context), self.request), name='pas_search')
        return searchView.merge(chain(*[searchView.searchUsers(**{field: searchString}) for field in ['login', 'fullname', 'email']]), 'userid')


    @property
    @memoize
    def many_users(self):
        plone_tools = getMultiAdapter((aq_inner(self.context), self.request),
                                      name=u'plone_tools')
        portal_properties = plone_tools.properties()
        return portal_properties.site_properties.many_users


    def manageUser(self, users=[], resetpassword=[], delete=[]):
        """Process changes from the submitted form
        """
        CheckAuthenticator(self.request)
        context = aq_inner(self.context)
        acl_users = getToolByName(context, 'acl_users')
        plone_tools = getMultiAdapter((aq_inner(self.context), self.request),
                                      name=u'plone_tools')
        mtool = plone_tools.membership()
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
            # deletion, as well as properties in various PAS plugins.
            # Use events for this
            mtool.deleteMembers(delete, delete_memberareas=0, delete_localroles=1, REQUEST=context.REQUEST)
        utils.addPortalMessage(_(u'Changes applied.'))


class UserViewAdapter(object):
    """Wraps a user info set for template view
    """

    def __init__(self, user_info, portal_url=None, portal_membership=None, portal_roles=None):
        self.user_info = user_info
        self.portal_url = portal_url
        self.user = portal_membership.getMemberById(user_info['userid'])
        self.portal_roles = portal_roles
        return


    def email(self):
        return self.user.getProperty('email')


    def user_details_link(self):
        query = make_query(userid=self.user_info['userid'])
        return "%s/prefs_user_details?%s" % (self.portal_url, query)


    def id_and_fullname(self):
        fullname = self.user.getProperty('fullname').strip()
        if len(fullname) > 0:
            return "%s (%s)" % (self.user_info['userid'], fullname)
        else:
            return self.user_info['userid']


    def set_email_disabled(self):
        return None if self.user.canWriteProperty('email') else 'disabled'


    def roles_subform_view(self):
        user = self.user
        user_roles = user.getRoles()
        view = []
        for role in self.portal_roles:
            role_features = {
                'role_name': role,
                'role_checked': 'checked' if role in user_roles else None,
                'set_role_disabled': None if user.canAssignRole(role) else 'disabled',
                }
            view.append(role_features)
        return view


    def set_password_disabled(self):
        return None if self.user.canPasswordSet() else 'disabled'


    def user_delete_disabled(self):
        return None if self.user.canDelete() else 'disabled'


    def is_valid_user(self):
        return self.user is not None


    def __getattr__(self, name):
        return getattr(self.user_info, name)


    def __getitem__(self, index):
        return self.user_info[index]



###
## Groups main control panel
###

class GroupsOverviewControlPanel(ControlPanelView, BaseUserGroupsControlPanel):

    def __call__(self):
        """Template is published
        """
        form = self.request.form
        submitted = form.get('form.submitted', False)
        findAll = form.get('form.button.FindAll', None) is not None
        self.b_start = int(self.request.get('b_start', 0))
        self.searchString = not findAll and form.get('searchstring', '') or ''
        self.searchResults = self.makeBatch([], 0, 0, orphan=1)
        if submitted:
            if form.get('form.button.Modify', None) is not None:
                self.manageGroup([group[len('group_'):] for group in self.request.keys() if group.startswith('group_')],
                                 form.get('delete', []))

        # Only search for all ('') if the many_users flag is not set.
        if not(self.many_groups) or bool(self.searchString):
            self.processSearch()

        return self.index()


    def makeBatch(self, results, size, start, orphan=1):
        """Override required from BaseUserGroupsControlPanel
        """
        context = aq_inner(self.context)
        plone_portal_state = getMultiAdapter((context, self.request),
                                             name=u'plone_portal_state')
        plone_tools = getMultiAdapter((self.context, self.request),
                                      name=u'plone_tools')
        portal_url = plone_portal_state.portal_url()
        acl_users = context.acl_users
        batch = Batch(results, size, start, orphan=orphan)
        return BatchWrapper(batch, GroupViewAdapter, portal_url=portal_url, acl_users=acl_users, portal_roles=self.portal_roles)


    def doSearch(self, searchString):
        """Override required from BaseUserGroupsControlPanel
        """
        searchView = getMultiAdapter((aq_inner(self.context), self.request), name='pas_search')
        return searchView.merge(chain(*[searchView.searchGroups(**{field: searchString}) for field in ['id', 'title']]), 'id')


    def manageGroup(self, groups=[], delete=[]):
        """Process changes from the submitted form
        """
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
        return


    def warn_groups_listing(self):
        """Should we display warning about unlisted groups?
        """
        context = aq_inner(self.context)
        return not (self.many_groups or self.searchString) and not context.acl_users.canListAllGroups()


    @property
    @memoize
    def many_groups(self):
        plone_tools = getMultiAdapter((aq_inner(self.context), self.request),
                                      name=u'plone_tools')
        portal_properties = plone_tools.properties()
        return portal_properties.site_properties.many_groups


class GroupViewAdapter(object):
    """Wraps a user info set for template view
    """
    def __init__(self, group_info, portal_url=None, acl_users=None, portal_roles=None):
        self.group_info = group_info
        self.portal_url = portal_url
        self.portal_roles = portal_roles
        self.group = acl_users.getGroupById(group_info['groupid'])
        return


    def hidden_input_name(self):
        return "group_%s:list" % self.group_info['groupid']


    def group_details_link(self):
        query = make_query(groupname=self.group_info['groupid'])
        return "%s/prefs_group_members?%s" % (self.portal_url, query)


    def id_and_title(self):
        title = self.group_info['title'].strip()
        if title:
            return "%s (%s)" % (self.group_info['groupid'], title)
        else:
            return self.group_info['groupid']


    def title_or_id(self):
        title = self.group_info['title'].strip()
        if title:
            return title
        else:
            return self.group_info['groupid']


    def roles_subform_view(self):
        group_info = self.group_info
        group = self.group
        group_roles = group.getRoles()
        view = []
        for role in self.portal_roles:
            role_features = {
                'checkbox_input_name': 'group_%s:list' % group_info['groupid'],
                'role_name': role,
                'role_checked': 'checked' if role in group_roles else None,
                'set_role_disabled': None if group.canAssignRole(role) else 'disabled',
                }
            view.append(role_features)
        return view


    def group_delete_disabled(self):
        return None if self.group.canDelete() else 'disabled'


    def __getattr__(self, name):
        return getattr(self.group_info, name)


    def __getitem__(self, index):
        return self.group_info[index]
