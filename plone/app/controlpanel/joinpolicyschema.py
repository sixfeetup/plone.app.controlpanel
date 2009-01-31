from zope import schema
from zope.interface import Interface
from zope.schema.vocabulary import SimpleVocabulary
from zope.formlib import form
from zope.app.form.browser import OrderedMultiSelectWidget

from plone.app.users.browser.userdata import IUserDataSchema

class IJoinPolicySchema(Interface):

    joinfields = schema.Tuple(title=u'joinfields',
                    description=u'Select the fields for the join form')



def UserDataWidget(field, request):

    """ Create selector with schema fields vocab """

    values = [(f.__name__, f.__name__) for f in form.Fields(IUserDataSchema)]
    
    vocabulary = SimpleVocabulary.fromItems(values)
    
    return OrderedMultiSelectWidget(field, vocabulary, request)
