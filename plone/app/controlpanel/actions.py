from Acquisition import aq_inner
from zope.interface import implements, Interface
from zope.component import getUtilitiesFor, getMultiAdapter, getUtility, adapts
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.controlpanel.form import ControlPanelView
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from plone.memoize.instance import memoize
from zope.schema.vocabulary import SimpleVocabulary
from Products.CMFCore.interfaces import IAction
from Products.CMFDefault.formlib.schema import SchemaAdapterBase
from zope import schema
from zope.formlib import form
from Products.Five.formlib import formbase
from plone.app.form.validators import null_validator
from Products.Five.browser import BrowserView
 
from plone.app.form import named_template_adapter


class ActionsControlPanel(ControlPanelView):


    template = ViewPageTemplateFile('actions.pt')

    def __call__(self):
        """Perform the update and redirect if necessary, or render the page
        """
        return self.template()

    def portal_url(self):
        portal_state = getMultiAdapter((self.context, self.request),
                                            name=u'plone_portal_state')
        return portal_state.portal_url()

    @property
    @memoize
    def category_id(self):
        return self.request.get('category_id', '')

    @memoize
    def selectable_categories(self):
        context = aq_inner(self.context)
        actions_tool = getToolByName(context, 'portal_actions')

        categories = []
        for name, utility in getUtilitiesFor(IManagedActionCategory):
            categories.append({'id': name, 'title': utility.title})
        
        return categories
    
    
    def categoryDescription(self, category=None):
        if category is None:
            category = self.category_id
        utility = getUtility(IManagedActionCategory, name=category)
        return utility.description
        
    @memoize
    def actionsForCategory(self, category):
        context = aq_inner(self.context)
        actions_tool = getToolByName(context, 'portal_actions')

        return actions_tool.listActionInfos(
            object=context,
            categories=(category,),
            check_visibility=0,
            check_permissions=0,
            check_condition=0,
            )

    def getEditURL(self, action_info):
        return '%s/portal_actions/%s/%s/edit_action_form' % (
            self.portal_url(),
            action_info['category'],
            action_info['id'],)

    def getDeleteURL(self, action_info):
        return '%s/portal_actions/%s/delete_portal_action?action_id=%s' % (
            self.portal_url(),
            action_info['category'],
            action_info['id'],)


class DeletePortalAction(BrowserView):

    def __call__(self):
        action_id = self.request.get('action_id', None)
        if action_id:
            context = aq_inner(self.context)
            context.manage_delObjects([action_id])
    
            plone_utils = getToolByName(context, 'plone_utils')
            plone_utils.addPortalMessage('Action removed.', type='info')
        nextURL = self.nextURL()
        if nextURL:
            self.request.response.redirect(self.nextURL())
        return ''

    def portal_url(self):
        portal_state = getMultiAdapter((self.context, self.request),
                                            name=u'plone_portal_state')
        return portal_state.portal_url()

    def nextURL(self):
        return self.portal_url() + '/@@actions-controlpanel'

# Definition of managed categories
       
class IManagedActionCategory(Interface):
    """ Objects implementing this interface, define a managed action category. """

 
class UserActions(object):
    implements(IManagedActionCategory)
    title = _(u"User actions")
    description = _(u"User actions available at the personal bar.")

class DocumentActions(object):
    implements(IManagedActionCategory)
    title = _(u"Document actions")
    description = _(u"Actions available in content visualization.")

class SiteActions(object):
    implements(IManagedActionCategory)
    title = _(u"Site actions")
    description = _(u"Site-wide links that will be shown on every pages.")

class PortalTabs(object):
    implements(IManagedActionCategory)
    title = _(u"Portal tabs")
    description = _(u"Tabs shown in the horizontal navigation menu.")


def ManagedCategoriesVocabularyFactory(context):
    items = []
    for name, utility in getUtilitiesFor(IManagedActionCategory):
        items.append((utility.title, name))
    return SimpleVocabulary.fromItems(items)


# Action add and edit forms


class IPortalActionSchema(Interface):
    """ This interface describes the schema of a portal action. """

    title = schema.TextLine(title=_(u'Title'))

    description = schema.Text(title=_(u'Description'), required=False)

    url_expr = schema.TextLine(title=_(u'URL expression'))

    icon_expr = schema.TextLine(title=_(u'Icon'), required=False)

    available_expr = schema.TextLine(title=_(u'Condition'), required=False)

    permissions = schema.Tuple(
        title=_(u'Permissions'),
        description=_(u'Select permissions that will guard this action.'),
        required=True,
        default=('View',),
        value_type=schema.Choice(
            vocabulary='plone.app.controlpanel.SiteWidePermissions'))

    visible = schema.Bool(title=_('Visible'), default=True)



class IPortalActionsForm(Interface):
    """ Marker interface for portal actions forms. """

_template = ViewPageTemplateFile('actions-pageform.pt')
actions_named_template_adapter = named_template_adapter(_template)


class AddPortalActionForm(formbase.AddFormBase):

    implements(IPortalActionsForm)

    form_fields = form.Fields(IPortalActionSchema)
    label = _(u'Add portal action')
    description = _(u'Enter portal action information.')

    def portal_url(self):
        portal_state = getMultiAdapter((self.context, self.request),
                                            name=u'plone_portal_state')
        return portal_state.portal_url()

    def nextURL(self):
        return self.portal_url() + '/@@actions-controlpanel'

    @form.action(_(u"label_save", default=u"Save"), name=u'save')
    def handle_save_action(self, action, data):
        self.createAndAdd(data)

    @form.action(_(u"label_cancel", default=u"Cancel"),
                 validator=null_validator,
                 name=u'cancel')
    def handle_cancel_action(self, action, data):
        context = aq_inner(self.context)
        nextURL = self.nextURL()
        if nextURL:
            plone_utils = getToolByName(context, 'plone_utils')
            plone_utils.addPortalMessage('Cancelled.', type='info')
            self.request.response.redirect(self.nextURL())
        return ''
    
    def createAndAdd(self, data):
        context = aq_inner(self.context)

        plone_utils = getToolByName(context, 'plone_utils')

        action_id = plone_utils.normalizeString(data['title'])

        from Products.CMFCore.ActionInformation import Action
        action = Action(
            action_id,
            title=data['title'],
            description=data.get('description', ''),
            i18n_domain='plone',
            url_expr=data['url_expr'],
            available_expr=data.get('available_expr', ''),
            permissions=data['permissions'],
            visible=data['visible'],
            icon_expr=data.get('icon_expr', ''),
            link_target='',
            )
        
        context._setObject(action_id, action)

        plone_utils.addPortalMessage('New action added.', type='info')

        nextURL = self.nextURL()
        if nextURL:
            self.request.response.redirect(self.nextURL())
        return ''


class PortalActionSchemaAdapter(SchemaAdapterBase):

    adapts(IAction)
    implements(IPortalActionSchema)
    
    def __init__(self, context):
        self.context = context
    
    def possible_permissions(self):
        return self.context.possible_permissions()
    
    def get_title(self):
        return self.context.getProperty('title')
    
    def set_title(self, value):
        return self.context.updateProperty('title', value)
    
    title = property(get_title, set_title)
    
    def get_description(self):
        return self.context.getProperty('description')
    
    def set_description(self, value):
        return self.context.updateProperty('description', value)
 
    description = property(get_description, set_description)

    def get_url_expr(self):
        return self.context.getProperty('url_expr')
    
    def set_url_expr(self, value):
        return self.context.updateProperty('url_expr', value)
    
    url_expr = property(get_url_expr, set_url_expr)

    def get_available_expr(self):
        return self.context.getProperty('available_expr')
    
    def set_available_expr(self, value):
        return self.context.updateProperty('available_expr', value)
    
    available_expr = property(get_available_expr, set_available_expr)

    def get_permissions(self):
        return self.context.getProperty('permissions')
    
    def set_permissions(self, value):
        return self.context.updateProperty('permissions', value)
    
    permissions = property(get_permissions, set_permissions)

    def get_visible(self):
        return self.context.getProperty('visible')
    
    def set_visible(self, value):
        return self.context.updateProperty('visible', value)

    visible = property(get_visible, set_visible)

    def get_icon_expr(self):
        return self.context.getProperty('icon_expr')
    
    def set_icon_expr(self, value):
        return self.context.updateProperty('icon_expr', value)
    
    icon_expr = property(get_icon_expr, set_icon_expr)


class EditPortalActionForm(formbase.EditFormBase):

    implements(IPortalActionsForm)

    form_fields = form.Fields(IPortalActionSchema)
    label = _(u'Edit portal action')
    description = _(u'Enter portal action information.')

    def portal_url(self):
        portal_state = getMultiAdapter((self.context, self.request),
                                            name=u'plone_portal_state')
        return portal_state.portal_url()

    def nextURL(self):
        return self.portal_url() + '/@@actions-controlpanel'

    @form.action(_("Apply"))
    def handle_edit_action(self, action, data):
        self.edit(data)

    @form.action(_(u"label_cancel", default=u"Cancel"),
                 validator=null_validator,
                 name=u'cancel')
    def handle_cancel_action(self, action, data):
        nextURL = self.nextURL()
        if nextURL:
            self.request.response.redirect(self.nextURL())
        return ''

    def edit(self, data):
        context = aq_inner(self.context)

        portal_actions = getToolByName(context, 'portal_actions')
        plone_utils = getToolByName(context, 'plone_utils')

        action_id = context.getId()

        context.manage_changeProperties(data)

        plone_utils.addPortalMessage('Action edited.', type='info')

        nextURL = self.nextURL()
        if nextURL:
            self.request.response.redirect(self.nextURL())
        return ''

# Other vocabularies

@memoize
def PermissionsVocabularyFactory(context):
    #FIXME: it should return only a subset of common permissions
    return SimpleVocabulary.fromItems([(v, v) for v in context.possible_permissions()])



