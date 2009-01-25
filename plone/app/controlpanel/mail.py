from zope.interface import Interface
from zope.component import adapts
from zope.component import getUtility
from zope.formlib import form
from zope.interface import implements
from zope.schema import Int
from zope.schema import TextLine
from zope.schema import ASCII
from zope.app.form.browser.textwidgets import ASCIIWidget

from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.utils import getToolByName

from plone.app.controlpanel import PloneMessageFactory as _
from plone.app.controlpanel.form import ControlPanelForm
from plone.app.controlpanel.utils import ProxyFieldProperty
from plone.app.controlpanel.utils import SchemaAdapterBase
from plone.app.controlpanel.widgets import PasswordWidget


class IMailSchema(Interface):
    """Combined schema for the adapter lookup.
    """

    smtp_host = TextLine(title=_(u'label_smtp_server',
                                 default=u'SMTP server'),
                         description=_(u"help_smtp_server",
                                       default=u"The address of your local "
                                       "SMTP (outgoing e-mail) server. Usually "
                                       "'localhost', unless you use an "
                                       "external server to send e-mail."),
                         default=u'localhost',
                         required=True)

    smtp_port = Int(title=_(u'label_smtp_port',
                            default=u'SMTP port'),
                    description=_(u"help_smtp_port",
                                  default=u"The port of your local SMTP "
                                  "(outgoing e-mail) server. Usually '25'."),
                    default=25,
                    required=True)

    smtp_uid = TextLine(title=_(u'label_smtp_userid',
                                default=u'ESMTP username'),
                        description=_(u"help_smtp_userid",
                                      default=u"Username for authentication "
                                      "to your e-mail server. Not required "
                                      "unless you are using ESMTP."),
                        default=u'',
                        required=False)

    smtp_pwd = TextLine(title=_(u'label_smtp_pass',
                                default=u'ESMTP password'),
                        description=_(u"help_smtp_pass",
                                      default=u"The password for the ESMTP "
                                      "user account."),
                        default=u'',
                        required=False)

    email_from_name = TextLine(title=_(u"Site 'From' name"),
                               description=_(u"Plone generates e-mail using "
                                              "this name as the e-mail "
                                              "sender."),
                               default=u'',
                               required=True)

    email_from_address = ASCII(title=_(u"Site 'From' address"),
                               description=_(u"Plone generates e-mail using "
                                              "this address as the e-mail "
                                              "return address. It is also "
                                              "used as the destination "
                                              "address on the site-wide "
                                              "contact form."),
                               default='',
                               required=True)


class MailControlPanelAdapter(SchemaAdapterBase):

    adapts(ISiteRoot)
    implements(IMailSchema)

    def __init__(self, context):
        super(MailControlPanelAdapter, self).__init__(context)
        self.context = getToolByName(context, 'MailHost')

    smtp_host = ProxyFieldProperty(IMailSchema['smtp_host'])
    smtp_port = ProxyFieldProperty(IMailSchema['smtp_port'])
    smtp_pwd = ProxyFieldProperty(IMailSchema['smtp_pwd'])

    def get_smtp_uid(self):
        uid = getattr(self.context, 'smtp_uid', None)
        if uid is None:
            return u''
        return uid

    def set_smtp_uid(self, value):
        if value is None:
            self.context.smtp_uid = u''
        else:
            self.context.smtp_uid = value

    smtp_uid = property(get_smtp_uid, set_smtp_uid)

    def get_email_from_name(self):
        return getattr(getUtility(ISiteRoot), 'email_from_name', '')

    def set_email_from_name(self, value):
        getUtility(ISiteRoot).email_from_name = value

    email_from_name = property(get_email_from_name, set_email_from_name)

    def get_email_from_address(self):
        return getattr(getUtility(ISiteRoot), 'email_from_address', '')

    def set_email_from_address(self, value):
        getUtility(ISiteRoot).email_from_address = value

    email_from_address = property(get_email_from_address,
                                  set_email_from_address)


class MailControlPanel(ControlPanelForm):

    form_fields = form.FormFields(IMailSchema)
    form_fields['email_from_address'].custom_widget = ASCIIWidget
    form_fields['smtp_pwd'].custom_widget = PasswordWidget
    label = _("Mail settings")
    description = _("Mail settings for this site.")
    form_name = _("Mail settings")
