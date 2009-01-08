The following changes were made to plone.app.controlpanel:

 * Added basic functional test coverage to types configlet.  Just because it 
   was non-existent.
 * Added conditional 'Redirect links to remote url' checkbox.  This just begs
   to be on the types configlet IMO.  Though it makes the template code less
   pretty.  It would be trivial to add this also to the Site configlet or it 
   could live at both or we could abstract some code to handle the "some 
   types need this option" business logic.
 * Functional tests of configuration of redirect_links option

What this needs:

 * Possibly the language 'Redirect links to remote url for non-editors' is not
   good.  It was the best thing I could come up with in a few words.
 * Translations
