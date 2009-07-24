from setuptools import setup, find_packages
import os

version = '3.0'

setup(name='plone.app.controlpanel',
      version=version,
      description="Formlib-based controlpanels for Plone.",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='plone controlpanel formlib',
      author='Plone Foundation',
      author_email='plone-developers@lists.sourceforge.net',
      url='http://pypi.python.org/pypi/plone.app.controlpanel',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages = ['plone', 'plone.app'],
      include_package_data=True,
      zip_safe=False,
      extras_require=dict(
        test=[
            'zope.publisher',
            'Products.PloneTestCase',
        ]
      ),
      install_requires=[
        'setuptools',
        'plone.fieldsets',
        'plone.locking',
        'plone.memoize',
        'plone.protect',
        'plone.app.form',
        'plone.app.vocabularies',
        'plone.app.workflow',
        'zope.component',
        'zope.datetime',
        'zope.event',
        'zope.formlib',
        'zope.i18n',
        'zope.i18nmessageid',
        'zope.interface',
        'zope.ramcache',
        'zope.schema',
        'zope.site',
        'zope.app.form',
        'Products.CMFCore',
        'Products.statusmessages',
        'Acquisition',
        'DateTime',
        'Zope2',
      ],
      )
